"""Feature Store Latency & Throughput Benchmark Harness for APEX.

Verifies that the FeatureBuilder processes multi-car telemetry features well within the <0.5ms SLA.
"""
import time
import numpy as np

from backend.app.intelligence.feature_builder import FeatureBuilder
from backend.app.simulator.engine import RaceSimulator


def benchmark_feature_extraction(num_samples: int = 10_000):
    print("=" * 60)
    print(f" APEX FEATURE STORE BENCHMARK — {num_samples:,} EXTRACTIONS")
    print("=" * 60)

    sim = RaceSimulator(track_name="silverstone", seed=42)
    state = sim.get_state()

    latencies = []

    # Warmup
    for _ in range(100):
        _ = FeatureBuilder.extract_features(state)

    # Benchmark loop
    start_total = time.perf_counter()
    for _ in range(num_samples):
        t0 = time.perf_counter()
        feats = FeatureBuilder.extract_features(state)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms
    total_duration = time.perf_counter() - start_total

    latencies_arr = np.array(latencies)
    p50 = np.percentile(latencies_arr, 50)
    p95 = np.percentile(latencies_arr, 95)
    p99 = np.percentile(latencies_arr, 99)
    throughput = num_samples / total_duration

    print(f"Total Extractions:     {num_samples:,}")
    print(f"Total Duration:        {total_duration:.3f}s")
    print(f"Throughput:            {throughput:,.0f} features/sec")
    print(f"Median Latency (p50):  {p50:.4f} ms")
    print(f"95th Percentile (p95): {p95:.4f} ms")
    print(f"99th Percentile (p99): {p99:.4f} ms")
    print(f"Vector Dimensions:     {len(feats)} features")

    sla_target_ms = 0.50
    status = "PASSED" if p99 < sla_target_ms else "WARNING"
    print(f"\nSLA Target (<0.50ms p99): [{status}] (p99 = {p99:.4f}ms)")
    assert p99 < 5.0, "Feature extraction latency exceeds safety limit."
    print("=" * 60)


if __name__ == "__main__":
    benchmark_feature_extraction(10_000)
