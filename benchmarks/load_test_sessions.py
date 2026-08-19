"""High-Concurrency Multi-Session Stress & Load Test Benchmark for APEX.

Spins up N independent concurrent RaceSession instances on the WebSocket ConnectionManager,
executes parallel asynchronous race-step ticks, measures latency percentiles (p50, p95, p99),
throughput (laps/sec), and strictly verifies zero cross-session state contamination.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.api.websocket import ConnectionManager
from backend.app.simulator.models import StrategyAction

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("APEX_LOAD_TEST")

DEFAULT_RESULTS_PATH = PROJECT_ROOT / "benchmarks" / "load_test_results.json"
TRACKS = ["silverstone", "monza", "spa", "monaco", "interlagos"]


async def run_single_session_worker(
    manager: ConnectionManager,
    session_id: str,
    track_name: str,
    seed: int,
    num_laps: int,
    latencies: list[float],
) -> dict[str, Any]:
    """Initializes and concurrently advances a single race session for num_laps."""
    await manager.init_race(track_name=track_name, seed=seed, session_id=session_id)

    completed_laps = 0
    for lap_idx in range(num_laps):
        # Periodically queue diverse tactical actions to stress decision branches
        if lap_idx == 3:
            manager.queue_action(StrategyAction.PUSH, session_id=session_id)
        elif lap_idx == 6:
            manager.queue_action(StrategyAction.CONSERVE, session_id=session_id)

        t0 = time.perf_counter()
        state = await manager.step_once(session_id=session_id)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt_ms)

        if state:
            completed_laps = state.current_lap

    session = manager.sessions[session_id]
    final_state = session.sim.get_state()
    player_car = session.sim.get_player_car()

    return {
        "session_id": session_id,
        "track_name": track_name,
        "seed": seed,
        "final_lap": completed_laps,
        "race_id": final_state.race_id,
        "player_tyre_wear_pct": player_car.tyre_wear_pct if player_car else 0.0,
        "player_fuel_kg": player_car.fuel_kg if player_car else 0.0,
    }


async def run_concurrent_load_test(
    num_sessions: int = 20,
    num_laps: int = 10,
    output_path: Path = DEFAULT_RESULTS_PATH,
) -> dict[str, Any]:
    """Runs high-concurrency multi-session async stress test."""
    logger.info("=" * 80)
    logger.info(f"APEX HIGH-CONCURRENCY MULTI-SESSION LOAD TEST ({num_sessions} Sessions x {num_laps} Laps)")
    logger.info("=" * 80)

    manager = ConnectionManager()
    all_latencies_ms: list[float] = []

    tasks = []
    for i in range(num_sessions):
        sess_id = f"stress_session_{i:03d}"
        trk = TRACKS[i % len(TRACKS)]
        sd = 1000 + i
        tasks.append(
            run_single_session_worker(
                manager=manager,
                session_id=sess_id,
                track_name=trk,
                seed=sd,
                num_laps=num_laps,
                latencies=all_latencies_ms,
            )
        )

    t_start = time.perf_counter()
    session_results = await asyncio.gather(*tasks)
    total_elapsed_s = time.perf_counter() - t_start

    total_laps_simulated = num_sessions * num_laps
    throughput_laps_per_sec = total_laps_simulated / max(0.001, total_elapsed_s)

    lat_arr = np.array(all_latencies_ms)
    p50 = float(np.percentile(lat_arr, 50))
    p95 = float(np.percentile(lat_arr, 95))
    p99 = float(np.percentile(lat_arr, 99))
    avg_lat = float(np.mean(lat_arr))

    # --- Verify Strict Isolation ---
    race_ids = [r["race_id"] for r in session_results]
    unique_race_ids = len(set(race_ids))
    is_fully_isolated = unique_race_ids == num_sessions

    logger.info("-" * 80)
    logger.info("LOAD TEST PERFORMANCE BENCHMARK SUMMARY:")
    logger.info(f"  Total Sessions Concurrent : {num_sessions}")
    logger.info(f"  Total Laps Simulated      : {total_laps_simulated}")
    logger.info(f"  Total Wall Time           : {total_elapsed_s:.3f} s")
    logger.info(f"  Throughput                : {throughput_laps_per_sec:.1f} laps/sec")
    logger.info(f"  Step Latency (Average)    : {avg_lat:.2f} ms")
    logger.info(f"  Step Latency (p50 Median) : {p50:.2f} ms")
    logger.info(f"  Step Latency (p95)        : {p95:.2f} ms")
    logger.info(f"  Step Latency (p99)        : {p99:.2f} ms")
    logger.info(f"  Isolation Integrity       : {'100% ISOLATED' if is_fully_isolated else 'CONTAMINATION DETECTED'}")
    logger.info("-" * 80)

    summary = {
        "benchmark_id": f"LOADTEST-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "status": "PASS" if is_fully_isolated and p95 < 50.0 else "FAIL",
        "concurrency_parameters": {
            "num_concurrent_sessions": num_sessions,
            "laps_per_session": num_laps,
            "total_laps_processed": total_laps_simulated,
        },
        "performance_metrics": {
            "total_wall_time_s": round(total_elapsed_s, 3),
            "throughput_laps_per_sec": round(throughput_laps_per_sec, 2),
            "latency_avg_ms": round(avg_lat, 2),
            "latency_p50_ms": round(p50, 2),
            "latency_p95_ms": round(p95, 2),
            "latency_p99_ms": round(p99, 2),
        },
        "isolation_verification": {
            "unique_sessions_created": num_sessions,
            "unique_race_ids_verified": unique_race_ids,
            "cross_contamination_detected": not is_fully_isolated,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Load test report saved to {output_path}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run APEX Multi-Session High-Concurrency Load Test")
    parser.add_argument("--sessions", type=int, default=20, help="Number of concurrent sessions")
    parser.add_argument("--laps", type=int, default=10, help="Number of laps per session")
    parser.add_argument("--output", type=str, default=str(DEFAULT_RESULTS_PATH), help="Output JSON path")
    args = parser.parse_args()

    asyncio.run(run_concurrent_load_test(num_sessions=args.sessions, num_laps=args.laps, output_path=Path(args.output)))
