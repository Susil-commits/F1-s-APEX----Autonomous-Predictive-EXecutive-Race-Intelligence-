"""Kafka Asynchronous Telemetry Consumer Group for APEX Race Intelligence."""
import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional

from backend.app.streaming.event_schemas import (
    RaceControlEvent,
    StrategyDecisionEvent,
    TelemetryEvent,
    TyreDegradationEvent,
    WeatherEvent,
)
from backend.app.streaming.kafka_config import kafka_settings
from backend.app.streaming.producer import ApexKafkaProducer, in_memory_bus

logger = logging.getLogger("apex.streaming.consumer")

EventHandler = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]


class ApexTelemetryConsumerGroup:
    """Enterprise asynchronous consumer group processing real-time telemetry streams."""

    def __init__(
        self,
        group_id: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ):
        self.settings = kafka_settings
        self.group_id = group_id or self.settings.group_id
        self.topics = topics or [
            self.settings.telemetry_topic,
            self.settings.weather_topic,
            self.settings.tyre_topic,
            self.settings.race_control_topic,
            self.settings.strategy_events_topic,
        ]
        self._aiokafka_consumer = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._handlers: Dict[str, List[EventHandler]] = {topic: [] for topic in self.topics}
        self._in_memory_queues: Dict[str, asyncio.Queue] = {}
        self._consumed_count = 0
        self._error_count = 0

    def register_handler(self, topic: str, handler: EventHandler) -> None:
        """Registers an async callback handler for a specific topic."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)

    async def start(self) -> None:
        """Starts background consumption loop."""
        if self._running:
            return

        self._running = True

        if not self.settings.mock_mode:
            try:
                from aiokafka import AIOKafkaConsumer  # type: ignore

                self._aiokafka_consumer = AIOKafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.settings.server_list,
                    group_id=self.group_id,
                    auto_offset_reset=self.settings.auto_offset_reset,
                    enable_auto_commit=self.settings.enable_auto_commit,
                    max_poll_records=self.settings.max_poll_records,
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                )
                await self._aiokafka_consumer.start()
                logger.info(f"[Kafka Consumer] Started group '{self.group_id}' on topics {self.topics}")
                self._task = asyncio.create_task(self._kafka_poll_loop())
                return
            except Exception as e:
                logger.warning(f"[Kafka Consumer] Kafka broker unavailable ({e}). Falling back to In-Memory bus.")
                self._aiokafka_consumer = None

        # Pre-attach queues to in_memory_bus synchronously before yielding
        self._in_memory_queues = {t: in_memory_bus.subscribe(t) for t in self.topics}
        self._task = asyncio.create_task(self._in_memory_poll_loop())
        logger.info(f"[Kafka Consumer] Started In-Memory event bus consumer for topics: {self.topics}")

    async def stop(self) -> None:
        """Gracefully shuts down consumer loop and commits final offsets."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        for topic, q in list(self._in_memory_queues.items()):
            in_memory_bus.unsubscribe(topic, q)
        self._in_memory_queues.clear()

        if self._aiokafka_consumer:
            try:
                await self._aiokafka_consumer.stop()
            except Exception as e:
                logger.error(f"[Kafka Consumer] Error stopping consumer: {e}")

        logger.info(f"[Kafka Consumer] Stopped group '{self.group_id}'.")

    async def _kafka_poll_loop(self) -> None:
        """Continuous polling loop for real Kafka broker."""
        while self._running:
            try:
                msg_batch = await self._aiokafka_consumer.getmany(timeout_ms=500, max_records=200)
                for tp, messages in msg_batch.items():
                    for msg in messages:
                        await self._process_message(msg.topic, msg.key, msg.value)
                        self._consumed_count += 1
                        self._record_prometheus_metric(msg.topic)
                await self._aiokafka_consumer.commit()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Kafka Consumer] Error during Kafka poll: {e}")
                await asyncio.sleep(1.0)

    async def _in_memory_poll_loop(self) -> None:
        """Polling loop for in-memory broker fallback."""
        try:
            while self._running:
                for topic, q in self._in_memory_queues.items():
                    while not q.empty():
                        item = q.get_nowait()
                        await self._process_message(topic, item["key"], item["value"])
                        self._consumed_count += 1
                        self._record_prometheus_metric(topic)
                await asyncio.sleep(0.005)  # 5ms poll yield
        except asyncio.CancelledError:
            pass

    async def _process_message(self, topic: str, key: Any, payload: Dict[str, Any]) -> None:
        """Validates payload schema and invokes registered handler callbacks."""
        try:
            # Schema validation check
            self._validate_schema(topic, payload)

            # Invoke handlers concurrently
            handlers = self._handlers.get(topic, [])
            for handler in handlers:
                try:
                    await handler(payload)
                except Exception as handler_err:
                    logger.error(f"[Kafka Consumer] Handler error on topic '{topic}': {handler_err}")

        except Exception as validation_err:
            self._error_count += 1
            logger.warning(f"[Kafka Consumer] Validation/Processing error on topic '{topic}': {validation_err}")
            # Route poison pill to Dead-Letter Queue (DLQ)
            producer = ApexKafkaProducer.get_instance()
            await producer.publish_to_dlq(
                original_topic=topic,
                raw_payload=json.dumps(payload),
                error_reason=str(validation_err),
                source_group=self.group_id,
            )

    def _validate_schema(self, topic: str, payload: Dict[str, Any]) -> None:
        """Validates event schemas based on target topic."""
        if topic == self.settings.telemetry_topic:
            TelemetryEvent.model_validate(payload)
        elif topic == self.settings.weather_topic:
            WeatherEvent.model_validate(payload)
        elif topic == self.settings.tyre_topic:
            TyreDegradationEvent.model_validate(payload)
        elif topic == self.settings.race_control_topic:
            RaceControlEvent.model_validate(payload)
        elif topic == self.settings.strategy_events_topic:
            StrategyDecisionEvent.model_validate(payload)

    def _record_prometheus_metric(self, topic: str) -> None:
        try:
            from backend.app.api.metrics import APEX_KAFKA_MESSAGES_CONSUMED
            APEX_KAFKA_MESSAGES_CONSUMED.labels(topic=topic, group=self.group_id).inc()
        except Exception:
            pass

    @property
    def total_consumed(self) -> int:
        return self._consumed_count

    @property
    def total_errors(self) -> int:
        return self._error_count
