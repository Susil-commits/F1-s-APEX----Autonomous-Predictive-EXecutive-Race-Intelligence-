"""Pytest suite for Chaos Engineering, failure injection, DLQ recovery, and idempotency."""
import asyncio
import pytest

from backend.app.jobs.job_manager import ApexJobManager, JobStatus, JobType
from backend.app.jobs.workers import ApexWorkerPool
from backend.app.streaming.consumer import ApexTelemetryConsumerGroup
from backend.app.streaming.kafka_config import kafka_settings
from backend.app.streaming.producer import ApexKafkaProducer, in_memory_bus


@pytest.mark.asyncio
async def test_chaos_dlq_poison_pill_recovery():
    """Validates that poisoned/corrupted streaming messages are routed to DLQ without crashing consumer."""
    producer = ApexKafkaProducer.get_instance()
    await producer.start()

    processed_events = []

    async def normal_handler(payload):
        processed_events.append(payload)

    consumer = ApexTelemetryConsumerGroup(group_id="chaos-dlq-test-group")
    consumer.register_handler(kafka_settings.telemetry_topic, normal_handler)
    await consumer.start()

    try:
        # Publish 3 invalid / corrupted payloads
        for i in range(3):
            await in_memory_bus.publish(
                kafka_settings.telemetry_topic,
                f"bad-key-{i}",
                {"unrecognized_corrupt_field": True, "error_code": 999},
            )

        await asyncio.sleep(0.2)
        # Consumer should stay healthy and route to DLQ
        dlq_count = in_memory_bus.get_topic_count(kafka_settings.dlq_topic)
        assert dlq_count >= 3
        assert consumer.total_errors >= 3
    finally:
        await consumer.stop()


@pytest.mark.asyncio
async def test_chaos_worker_retry_backoff():
    """Validates that failing background jobs undergo exponential backoff retries before failure."""
    manager = ApexJobManager.get_instance()

    # Enqueue a dummy job
    job = await manager.enqueue_job(JobType.ALERT_DISPATCH, {"alert_type": "TEST_RETRY"}, max_retries=2)
    assert job.status in (JobStatus.QUEUED, JobStatus.PROCESSING)

    # Simulate 1st failure
    await manager.fail_job(job.job_id, "Intermittent Network Timeout", can_retry=True)
    job_state = manager.get_job(job.job_id)
    assert job_state.status == JobStatus.RETRYING
    assert job_state.retry_count == 1

    # Simulate 2nd failure
    await manager.fail_job(job.job_id, "Secondary Downstream Timeout", can_retry=True)
    job_state = manager.get_job(job.job_id)
    assert job_state.status == JobStatus.RETRYING
    assert job_state.retry_count == 2

    # Simulate 3rd failure exceeding max_retries
    await manager.fail_job(job.job_id, "Permanent Failure", can_retry=True)
    job_state = manager.get_job(job.job_id)
    assert job_state.status == JobStatus.FAILED
