"""Standalone Command-Line Telemetry Streaming Daemon for APEX.

Usage:
    python -m backend.app.streaming.stream_producer_daemon --circuit silverstone --fps 60 --laps 52
"""
import argparse
import asyncio
import signal
import sys
import time

from backend.app.streaming.fastf1_streamer import fastf1_streamer
from backend.app.streaming.producer import ApexKafkaProducer


async def main(circuit: str, fps: int, laps: int):
    print("=" * 65)
    print(f" APEX TELEMETRY STREAMING DAEMON — {circuit.upper()}")
    print(f" Target Frequency: {fps} Hz | Total Laps: {laps}")
    print("=" * 65)

    producer = ApexKafkaProducer.get_instance()
    await producer.start()

    fastf1_streamer.track = circuit
    fastf1_streamer.total_laps = laps
    await fastf1_streamer.start_stream(track=circuit)

    print(f"[Daemon] Telemetry stream active on session: {fastf1_streamer.session_id}")
    print("[Daemon] Streaming 8 cars into Kafka topics (f1.telemetry.raw, f1.weather.events)...")
    print("[Daemon] Press Ctrl+C to gracefully terminate.\n")

    try:
        while fastf1_streamer.is_streaming:
            status = fastf1_streamer.get_status()
            sys.stdout.write(
                f"\r[Lap {status.current_lap}/{status.total_laps}] "
                f"Cars: {status.cars_streaming} | "
                f"Produced: {status.messages_produced:,} msgs | "
                f"Elapsed: {status.elapsed_seconds:.1f}s"
            )
            sys.stdout.flush()
            await asyncio.sleep(1.0)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("\n\n[Daemon] Shutting down telemetry streamer...")
        await fastf1_streamer.stop_stream()
        await producer.stop()
        print("[Daemon] Streamer stopped cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APEX Live Telemetry Streaming Daemon")
    parser.add_argument("--circuit", type=str, default="silverstone", help="Circuit name (silverstone, monza, spa, monaco)")
    parser.add_argument("--fps", type=int, default=60, help="Streaming frequency in Hz")
    parser.add_argument("--laps", type=int, default=52, help="Total race simulation laps")

    args = parser.parse_args()
    try:
        asyncio.run(main(args.circuit, args.fps, args.laps))
    except KeyboardInterrupt:
        print("\n[Daemon] Interrupted by user.")
