"""APEX Streaming Package for Kafka telemetry and event ingestion."""
from backend.app.streaming.consumer import ApexTelemetryConsumerGroup
from backend.app.streaming.event_schemas import (
    BaseStreamingEvent,
    DeadLetterEvent,
    RaceControlEvent,
    StrategyDecisionEvent,
    TelemetryEvent,
    TyreDegradationEvent,
    WeatherEvent,
)
from backend.app.streaming.kafka_config import KafkaSettings, kafka_settings
from backend.app.streaming.producer import ApexKafkaProducer, in_memory_bus

__all__ = [
    "KafkaSettings",
    "kafka_settings",
    "BaseStreamingEvent",
    "TelemetryEvent",
    "WeatherEvent",
    "TyreDegradationEvent",
    "RaceControlEvent",
    "StrategyDecisionEvent",
    "DeadLetterEvent",
    "ApexKafkaProducer",
    "ApexTelemetryConsumerGroup",
    "in_memory_bus",
]
