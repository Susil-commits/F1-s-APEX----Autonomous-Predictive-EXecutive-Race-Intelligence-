"""Kafka streaming configuration settings for APEX Race Intelligence."""
import os
from typing import List
from pydantic import BaseModel, Field


class KafkaSettings(BaseModel):
    """Kafka broker and consumer group settings with sensible development defaults."""
    bootstrap_servers: str = Field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    )
    client_id: str = Field(
        default_factory=lambda: os.getenv("KAFKA_CLIENT_ID", "apex-telemetry-engine")
    )
    group_id: str = Field(
        default_factory=lambda: os.getenv("KAFKA_GROUP_ID", "apex-stream-processor")
    )
    
    # Topic names
    telemetry_topic: str = "f1.telemetry.raw"
    weather_topic: str = "f1.weather.events"
    tyre_topic: str = "f1.tyre.degradation"
    race_control_topic: str = "f1.race.control"
    dlq_topic: str = "f1.dlq.failed_events"
    strategy_events_topic: str = "f1.strategy.decisions"
    
    # Producer / Consumer parameters
    batch_size_bytes: int = 65536  # 64 KB batch
    linger_ms: int = 5  # 5ms micro-batching for high throughput
    compression_type: str = "gzip"
    max_poll_records: int = 500
    enable_auto_commit: bool = False
    session_timeout_ms: int = 30000
    auto_offset_reset: str = "latest"
    
    # Mode: Auto-detect or mock when standalone
    mock_mode: bool = Field(
        default_factory=lambda: os.getenv("KAFKA_MOCK_MODE", "1").lower() in ("1", "true", "yes")
    )

    @property
    def server_list(self) -> List[str]:
        return [s.strip() for s in self.bootstrap_servers.split(",") if s.strip()]


kafka_settings = KafkaSettings()
