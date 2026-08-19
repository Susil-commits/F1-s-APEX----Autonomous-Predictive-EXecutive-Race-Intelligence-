"""Tests for Sim-to-Real Historical Decision Replay and Divergence Evaluation Harness."""
import json
import tempfile
from pathlib import Path
import pytest

from backend.app.simulator.historical_replay import HistoricalRaceReplay
from backend.eval.historical_replay_eval import run_historical_divergence_audit


def test_historical_replay_catalog_availability():
    """Verifies that the historical replay catalog contains key GP scenarios."""
    replays = HistoricalRaceReplay.list_available_replays()
    assert len(replays) >= 3
    ids = [r["id"] for r in replays]
    assert "silverstone_2023" in ids
    assert "monaco_2023" in ids
    assert "zandvoort_2023" in ids


def test_single_historical_replay_execution():
    """Verifies that running a single historical replay generates decision points with advantage metrics."""
    result = HistoricalRaceReplay.run_historical_replay("silverstone_2023")
    assert result["race_id"] == "silverstone_2023"
    assert result["total_decisions_evaluated"] >= 2
    assert "agreement_rate_pct" in result
    assert len(result["decision_points"]) >= 2

    dp = result["decision_points"][0]
    assert "lap" in dp
    assert "trigger_event" in dp
    assert "apex_recommended_action" in dp
    assert "counterfactual_advantage_s" in dp


def test_run_historical_divergence_audit_full():
    """Verifies that run_historical_divergence_audit produces valid JSON audit report with aggregate metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_divergence_report.json"
        audit = run_historical_divergence_audit(output_path=report_path)

        assert audit["status"] == "PASS"
        assert audit["aggregate_metrics"]["total_grand_prix_audited"] >= 3
        assert audit["aggregate_metrics"]["total_critical_decisions_evaluated"] >= 4
        assert audit["aggregate_metrics"]["cumulative_counterfactual_advantage_s"] > 0
        assert report_path.exists()

        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["status"] == "PASS"
            assert "case_studies" in data
