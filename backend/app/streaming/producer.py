"""Kafka Asynchronous Telemetry Producer for APEX Race Intelligence."""
import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from backend.app.streaming.event_schemas import (
    BaseStreamingEvent,
    DeadLetterEvent,
    RaceControlEvent,
    StrategyDecisionEvent,
    TelemetryEvent,
    TyreDegradationEvent,
    WeatherEvent,
)
from backend.app.streaming.kafka_config import kafka_settings

logger = logging.getLogger("apex.streaming.producer")


class InMemoryEventBus:
    """Zero-dependency in-memory event bus simulating a multi-topic partitioned broker."""
    def __init__(self, max_buffer_per_topic: int = 5000):
        self.max_buffer = max_buffer_per_topic
        self.topics: Dict[str, List[Dict[str, Any]]] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}

    def publish_sync(self, topic: str, key: str, value: Dict[str, Any]) -> None:
        if topic not in self.topics:
            self.topics[topic] = []
        self.topics[topic].append({"key": key, "value": value, "offset": len(self.topics[topic])})
        if len(self.topics[topic]) > self.max_buffer:
            self.topics[topic].pop(0)

        # Notify real-time consumer queues immediately
        if topic in self.subscribers:
            for q in list(self.subscribers[topic]):
                try:
                    q.put_nowait({"topic": topic, "key": key, "value": value})
                except asyncio.QueueFull:
                    pass

    async def publish(self, topic: str, key: str, value: Dict[str, Any]) -> None:
        self.publish_sync(topic, key, value)

    def subscribe(self, topic: str) -> asyncio.Queue:
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        q: asyncio.Queue = asyncio.Queue(maxsize=5000)
        self.subscribers[topic].append(q)
        return q

    def unsubscribe(self, topic: str, q: asyncio.Queue) -> None:
        if topic in self.subscribers and q in self.subscribers[topic]:
            self.subscribers[topic].remove(q)

    def get_topic_count(self, topic: str) -> int:
        return len(self.topics.get(topic, []))


# Global singleton in-memory event bus
in_memory_bus = InMemoryEventBus()


class ApexKafkaProducer:
    """Enterprise asynchronous event producer with Kafka and In-Memory fallback."""

    _instance: Optional["ApexKafkaProducer"] = None

    def __init__(self):
        self.settings = kafka_settings
        self._aiokafka_producer = None
        self._is_connected = False
        self._produced_count = 0

    @classmethod
    def get_instance(cls) -> "ApexKafkaProducer":
        if cls._instance is None:
            cls._instance = ApexKafkaProducer()
        return cls._instance

    async def start(self) -> None:
        """Initializes Kafka producer connection or falls back to in-memory bus."""
        if self.settings.mock_mode:
            self._is_connected = True
            logger.info("[Kafka Producer] Operating in MOCK / In-Memory EventBus mode.")
            return

        try:
            from aiokafka import AIOKafkaProducer  # type: ignore

            self._aiokafka_producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.server_list,
                client_id=self.settings.client_id,
                linger_ms=self.settings.linger_ms,
                compression_type=self.settings.compression_type,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await self._aiokafka_producer.start()
            self._is_connected = True
            logger.info(f"[Kafka Producer] Connected to Kafka brokers: {self.settings.bootstrap_servers}")
        except Exception as e:
            logger.warning(f"[Kafka Producer] Broker connection unavailable ({e}). Falling back to In-Memory EventBus.")
            self._aiokafka_producer = None
            self._is_connected = True

    async def stop(self) -> None:
        """Gracefully shuts down the Kafka producer."""
        if self._aiokafka_producer:
            try:
                await self._aiokafka_producer.stop()
            except Exception as e:
                logger.error(f"[Kafka Producer] Error stopping producer: {e}")
        self._is_connected = False
        logger.info("[Kafka Producer] Stopped.")

    async def publish_event(self, topic: str, key: str, event_data: BaseStreamingEvent) -> bool:
        """Publishes a typed event to the targeted topic."""
        payload = event_data.model_dump()
        return await self._send_raw(topic, key, payload)

    async def _send_raw(self, topic: str, key: str, payload: Dict[str, Any]) -> bool:
        try:
            if self._aiokafka_producer:
                await self._aiokafka_producer.send_and_wait(topic, value=payload, key=key)
            else:
                await in_memory_bus.publish(topic, key, payload)

            self._produced_count += 1
            self._record_prometheus_metric(topic)
            return True
        except Exception as e:
            logger.error(f"[Kafka Producer] Failed to publish to topic {topic}: {e}")
            await self.publish_to_dlq(
                original_topic=topic,
                raw_payload=json.dumps(payload),
                error_reason=str(e),
                source_group="producer-dispatch",
            )
            return False

    async def publish_telemetry(self, event: TelemetryEvent) -> bool:
        key = f"{event.session_id}:{event.car_id}"
        return await self.publish_event(self.settings.telemetry_topic, key, event)

    async def publish_weather(self, event: WeatherEvent) -> bool:
        key = event.session_id
        return await self.publish_event(self.settings.weather_topic, key, event)

    async def publish_tyre(self, event: TyreDegradationEvent) -> bool:
        key = f"{event.session_id}:{event.car_id}"
        return await self.publish_event(self.settings.tyre_topic, key, event)

    async def publish_race_control(self, event: RaceControlEvent) -> bool:
        key = event.session_id
        return await self.publish_event(self.settings.race_control_topic, key, event)

    async def publish_strategy_decision(self, event: StrategyDecisionEvent) -> bool:
        key = f"{event.session_id}:{event.target_car_id}"
        return await self.publish_event(self.settings.strategy_events_topic, key, event)

    async def publish_to_dlq(
        self, original_topic: str, raw_payload: str, error_reason: str, source_group: str
    ) -> bool:
        dlq_event = DeadLetterEvent(
            dlq_id=str(uuid.uuid4()),
            original_topic=original_topic,
            raw_payload=raw_payload,
            error_reason=error_reason,
            source_consumer_group=source_group,
        )
        return await self._send_raw(self.settings.dlq_topic, dlq_event.dlq_id, dlq_event.model_dump())

    def _record_prometheus_metric(self, topic: str) -> None:
        try:
            from backend.app.api.metrics import APEX_KAFKA_MESSAGES_PRODUCED
            APEX_KAFKA_MESSAGES_PRODUCED.labels(topic=topic).inc()
        except Exception:
            pass

    @property
    def total_produced(self) -> int:
        return self._produced_count
