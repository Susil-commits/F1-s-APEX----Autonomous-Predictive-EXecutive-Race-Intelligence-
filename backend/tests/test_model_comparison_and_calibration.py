"""Unit and integration tests for 4-Model Comparison & Conformal Prediction Calibration."""
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.intelligence.conformal_calibration import (
    ConformalCalibrator,
    compute_calibration_metrics,
)
from backend.app.intelligence.tyre_model import (
    TyreMLSuite,
    TyreModel,
    _ML_SUITE,
)
from backend.app.main import app
from backend.app.simulator.models import TyreCompound


def test_conformal_calibrator_q_hat_and_intervals():
    """Verifies that ConformalCalibrator calculates rigorous quantile thresholds."""
    calibrator = ConformalCalibrator(target_coverage=0.95)
    assert not calibrator.is_fitted

    y_val_true = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
    y_val_pred = np.array([0.48, 1.05, 1.45, 2.10, 2.45, 3.10, 3.40, 4.05, 4.60, 4.90])

    calibrator.fit_on_residuals(y_val_true, y_val_pred)
    assert calibrator.is_fitted
    assert calibrator.q_hat > 0.0

    # Test prediction interval creation
    point_preds = np.array([1.0, 2.0, 3.0])
    lower, upper = calibrator.predict_intervals(point_preds)

    assert len(lower) == 3
    assert len(upper) == 3
    for l, u, p in zip(lower, upper, point_preds):
        assert l < p < u
        assert round(u - l, 4) == round(2 * calibrator.q_hat, 4)


def test_calibration_metrics_ece_and_picp():
    """Verifies calculation of ECE, PICP coverage, MPIW, and reliability bins."""
    y_true = np.linspace(0.0, 5.0, 100)
    y_pred = y_true + np.random.normal(0, 0.1, 100)
    q_hat = 0.25

    lower = y_pred - q_hat
    upper = y_pred + q_hat

    metrics = compute_calibration_metrics(y_true, y_pred, lower, upper)
    assert 0.85 <= metrics.coverage_probability_95 <= 1.0
    assert 0.0 <= metrics.expected_calibration_error <= 0.10
    assert metrics.mean_interval_width_s > 0.0
    assert isinstance(metrics.is_well_calibrated, bool)

    bins = ConformalCalibrator.generate_reliability_diagram_bins(y_true, y_pred)
    assert len(bins) == 10
    assert bins[-1]["nominal_confidence"] == 0.99


def test_ml_model_suite_four_model_hierarchy():
    """Verifies that all 4 models (Linear, RF, XGBoost, XGBoost+Calib) evaluate cleanly."""
    suite = TyreMLSuite()
    comparison = suite.evaluate_model_comparison()

    assert len(comparison) == 4
    model_ids = [m["model_id"] for m in comparison]
    assert "linear_baseline" in model_ids
    assert "random_forest" in model_ids
    assert "xgboost" in model_ids
    assert "xgboost_calibrated" in model_ids

    # R2 progression: Linear < RF
    linear_m = next(m for m in comparison if m["model_id"] == "linear_baseline")
    rf_m = next(m for m in comparison if m["model_id"] == "random_forest")
    xgb_cal_m = next(m for m in comparison if m["model_id"] == "xgboost_calibrated")

    assert linear_m["r2"] > 0.30
    assert rf_m["r2"] > 0.30
    assert xgb_cal_m["r2"] > 0.30
    assert xgb_cal_m["is_calibrated"] is True
    assert xgb_cal_m["coverage_probability_95"] >= 0.80


def test_tyre_model_predict_delta_with_95_ci():
    """Verifies predict_delta returns 95% confidence intervals and calibration metadata."""
    pred, (ci_low, ci_high), meta = _ML_SUITE.predict_delta(
        compound=TyreCompound.MEDIUM,
        tyre_age=15,
        model_type="xgb_calibrated",
    )

    assert pred > 0.0
    assert ci_low < pred < ci_high
    assert "model_type" in meta
    assert meta["nominal_coverage"] == 0.95


@pytest.mark.asyncio
async def test_api_model_comparison_and_calibration():
    """Tests GET /api/intelligence/model-comparison and GET /api/intelligence/calibration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_comp = await ac.get("/api/intelligence/model-comparison")
        assert res_comp.status_code == 200
        data_comp = res_comp.json()
        assert len(data_comp["models"]) == 4
        assert "Train: 2018-2022" in data_comp["split"]

        res_cal = await ac.get("/api/intelligence/calibration?compound=MEDIUM&age=20")
        assert res_cal.status_code == 200
        data_cal = res_cal.json()
        assert "predicted_degradation_s" in data_cal
        assert len(data_cal["confidence_interval_95"]) == 2
        assert data_cal["calibration_error"]["target_nominal_coverage"] == 0.95
        assert data_cal["calibration_error"]["expected_calibration_error"] <= 0.05
        assert len(data_cal["reliability_diagram_bins"]) == 10
