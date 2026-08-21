"""Pytest suite for Kafka event streaming, multi-topic producers, consumer groups, and DLQ."""
import asyncio
import time
import pytest

from backend.app.streaming.consumer import ApexTelemetryConsumerGroup
from backend.app.streaming.event_schemas import (
    RaceControlEvent,
    StrategyDecisionEvent,
    TelemetryEvent,
    TyreDegradationEvent,
    WeatherEvent,
)
from backend.app.streaming.kafka_config import kafka_settings
from backend.app.streaming.producer import ApexKafkaProducer, in_memory_bus


@pytest.mark.asyncio
async def test_kafka_producer_publish_telemetry():
    producer = ApexKafkaProducer.get_instance()
    await producer.start()

    event = TelemetryEvent(
        event_id="test-evt-01",
        session_id="test-race-session",
        car_id="HAM_44",
        driver_name="Lewis Hamilton",
        driver_code="HAM",
        team_name="Ferrari",
        lap_number=5,
        lap_progress=0.45,
        speed_kmh=295.0,
        throttle_pct=100.0,
        brake_pct=0.0,
        gear=7,
        rpm=11500,
        fuel_remaining_kg=55.0,
        tyre_compound="MEDIUM",
        tyre_surface_temp_c=98.0,
        tyre_carcass_temp_c=95.0,
        position=2,
    )

    success = await producer.publish_telemetry(event)
    assert success is True
    assert producer.total_produced >= 1


@pytest.mark.asyncio
async def test_kafka_producer_publish_weather_and_tyre():
    producer = ApexKafkaProducer.get_instance()
    await producer.start()

    weather = WeatherEvent(
        event_id="test-wx-01",
        session_id="test-race-session",
        air_temp_c=22.5,
        track_temp_c=34.0,
        humidity_pct=60.0,
        rain_intensity_pct=15.0,
        track_wetness_index=0.18,
        forecast_next_10min_rain_prob=0.45,
    )
    assert await producer.publish_weather(weather) is True

    tyre = TyreDegradationEvent(
        event_id="test-tyre-01",
        session_id="test-race-session",
        car_id="NOR_04",
        compound="SOFT",
        stint_lap_age=12,
        wear_percentage=48.5,
        thermal_deg_index=1.15,
        pinn_residual_offset=-0.04,
        cliff_proximity_pct=25.0,
        estimated_laps_remaining=8.5,
    )
    assert await producer.publish_tyre(tyre) is True


@pytest.mark.asyncio
async def test_consumer_group_dispatch_and_dlq():
    producer = ApexKafkaProducer.get_instance()
    await producer.start()

    received_events = []

    async def on_race_control(payload):
        received_events.append(payload)

    consumer = ApexTelemetryConsumerGroup(group_id="test-rc-group")
    consumer.register_handler(kafka_settings.race_control_topic, on_race_control)
    await consumer.start()

    try:
        # Publish valid race control event
        rc_event = RaceControlEvent(
            event_id="test-rc-01",
            session_id="test-race-session",
            flag_status="SAFETY_CAR",
            message="Safety Car Deployed in Sector 2",
            laps_under_neutralization=1,
            drs_disabled=True,
        )
        await producer.publish_race_control(rc_event)
        await asyncio.sleep(0.15)

        assert len(received_events) >= 1
        assert received_events[0]["flag_status"] == "SAFETY_CAR"

        # Publish poison pill payload to trigger DLQ
        initial_dlq = in_memory_bus.get_topic_count(kafka_settings.dlq_topic)
        await in_memory_bus.publish(kafka_settings.race_control_topic, "bad-key", {"bad": "data"})
        await asyncio.sleep(0.15)

        new_dlq = in_memory_bus.get_topic_count(kafka_settings.dlq_topic)
        assert new_dlq > initial_dlq
    finally:
        await consumer.stop()
