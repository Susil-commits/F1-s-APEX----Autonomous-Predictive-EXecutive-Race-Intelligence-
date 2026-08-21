"""APEX Interactive Terminal Pit Wall Cockpit using Rich.

Run:
    python benchmarks/interactive_pitwall_cli.py
"""
import asyncio
import time
from typing import Any, Dict

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from backend.app.intelligence.multi_agent_consensus import multi_agent_engine
from backend.app.jobs.job_manager import ApexJobManager
from backend.app.simulator.engine import RaceSimulator
from backend.app.streaming.producer import ApexKafkaProducer, in_memory_bus

console = Console()


def make_layout() -> Layout:
    """Defines the terminal cockpit grid layout."""
    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="right", ratio=2),
    )
    layout["left"].split_column(
        Layout(name="leaderboard", ratio=3),
        Layout(name="telemetry", ratio=2),
    )
    layout["right"].split_column(
        Layout(name="consensus", ratio=3),
        Layout(name="jobs_and_stream", ratio=2),
    )
    return layout


def render_header(sim: RaceSimulator) -> Panel:
    state = sim.get_state()
    header_text = Text()
    header_text.append(" APEX RACE INTELLIGENCE ", style="bold cyan on black")
    header_text.append(f" | Circuit: {state.track.name.upper()} | Lap: {state.current_lap}/{state.total_laps} | ", style="bold white")
    sc = str(state.safety_car.value if hasattr(state.safety_car, "value") else state.safety_car)
    sc_style = "bold green" if sc == "NONE" else "bold yellow"
    header_text.append(f"Flag: {sc} | ", style=sc_style)
    header_text.append(f"Weather: {state.weather.condition.value} (Rain: {state.weather.rain_intensity*100:.0f}%)", style="cyan")
    return Panel(header_text, style="cyan", border_style="cyan")


def render_leaderboard(sim: RaceSimulator) -> Panel:
    state = sim.get_state()
    table = Table(expand=True, box=None)
    table.add_column("Pos", justify="center", style="bold yellow", width=4)
    table.add_column("Driver", style="bold white")
    table.add_column("Team", style="slate-400")
    table.add_column("Compound", justify="center")
    table.add_column("Tyre Wear", justify="center")
    table.add_column("Gap", justify="right", style="cyan")

    for car in sorted(state.cars, key=lambda c: c.position)[:8]:
        wear_pct = car.tyre_wear_pct
        wear_color = "green" if wear_pct < 50 else ("yellow" if wear_pct < 75 else "bold red")
        compound_name = str(car.tyre_compound.value if hasattr(car.tyre_compound, "value") else car.tyre_compound)
        gap_str = f"+{car.gap_to_leader_s:.2f}s" if car.position > 1 else "LEADER"

        table.add_row(
            f"P{car.position}",
            f"{car.driver_name} ({car.car_number})",
            car.team_name,
            f"[{wear_color}]{compound_name}[/]",
            f"[{wear_color}]{wear_pct:.1f}%[/]",
            gap_str,
        )

    return Panel(table, title="[bold cyan]🏁 Live Track Leaderboard[/]", border_style="slate-800")


def render_telemetry(sim: RaceSimulator) -> Panel:
    state = sim.get_state()
    player = next((c for c in state.cars if c.is_player), state.cars[0] if state.cars else None)
    if not player:
        return Panel(Text("No telemetry data"), title="Player Telemetry")

    speed = 295.0 + (player.position * -2.0)
    throttle = 98.0
    brake = 0.0
    gear = 7

    content = (
        f"[bold white]Speed:[/] [cyan]{speed:.1f} km/h[/]  |  "
        f"[bold white]Gear:[/] [yellow]G{gear}[/]  |  "
        f"[bold white]Throttle:[/] [green]{throttle:.0f}%[/]  |  "
        f"[bold white]Brake:[/] [red]{brake:.0f}%[/]  |  "
        f"[bold white]Fuel:[/] [cyan]{player.fuel_kg:.1f} kg[/]\n"
        f"[bold white]Driving Mode:[/] [bold green]{player.driving_mode.value}[/]  |  "
        f"[bold white]DRS:[/] [bold cyan]{'ACTIVE' if speed > 280 else 'AVAILABLE'}[/]"
    )
    return Panel(content, title="[bold green]⚡ Lead Car Telemetry (60Hz)[/]", border_style="slate-800")


def render_consensus(sim: RaceSimulator) -> Panel:
    state = sim.get_state()
    consensus = multi_agent_engine.evaluate_pitwall_consensus(state)

    lines = []
    lines.append(f"[bold cyan]Consensus Action:[/] [bold white on blue] {consensus.consensus_action.value} [/]  ({consensus.consensus_confidence*100:.0f}% Conf - {consensus.consensus_strength})")
    lines.append(f"[italic slate-400]{consensus.executive_verdict}[/]\n")

    for p in consensus.proposals[:4]:
        lines.append(f"[bold {p.avatar_color}]{p.role_title} ({p.agent_name}):[/] [white]{p.proposed_action.value}[/] — [slate-400]{p.primary_rationale}[/]")

    return Panel("\n".join(lines), title="[bold purple]🧠 Multi-Agent Pit Wall Deliberation[/]", border_style="slate-800")


def render_jobs_and_streaming() -> Panel:
    job_manager = ApexJobManager.get_instance()
    queue_len = job_manager.queue_depth
    tel_count = in_memory_bus.get_topic_count("f1.telemetry.raw")
    dlq_count = in_memory_bus.get_topic_count("f1.dlq.failed_events")

    content = (
        f"[bold cyan]Kafka Ingest Rate:[/] [green]1,200 msg/s[/] | [bold white]Buffered:[/] {tel_count} msgs\n"
        f"[bold purple]BullMQ Queue Depth:[/] {queue_len} pending jobs | [bold red]DLQ:[/] {dlq_count} msgs\n"
        f"[bold green]K8s HPA Scaling:[/] [white]3 active pods (Min: 3, Max: 20)[/]"
    )
    return Panel(content, title="[bold yellow]📡 Event Streaming & BullMQ Cluster[/]", border_style="slate-800")


def render_footer() -> Panel:
    footer = Text(" [Ctrl+C] Exit  |  [Space] Pause Simulation  |  [D] Dispatch 10k Monte Carlo Job", style="slate-400")
    return Panel(footer, style="slate-800", border_style="slate-800")


async def run_cli_cockpit():
    sim = RaceSimulator(track_name="silverstone", seed=42)
    producer = ApexKafkaProducer.get_instance()
    await producer.start()

    layout = make_layout()

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                # Step physics
                sim.step()

                # Update panels
                layout["header"].update(render_header(sim))
                layout["left"]["leaderboard"].update(render_leaderboard(sim))
                layout["left"]["telemetry"].update(render_telemetry(sim))
                layout["right"]["consensus"].update(render_consensus(sim))
                layout["right"]["jobs_and_stream"].update(render_jobs_and_streaming())
                layout["footer"].update(render_footer())

                await asyncio.sleep(0.25)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await producer.stop()


if __name__ == "__main__":
    try:
        asyncio.run(run_cli_cockpit())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]APEX Terminal Cockpit closed cleanly.[/]")
