"""Unit tests for TreeSHAP Explainability Engine and Distilled Surrogate Model."""
import os

import numpy as np
import pytest

from backend.app.intelligence.feature_builder import FEATURE_DIM
from backend.app.intelligence.shap_explainer import (
    DEFAULT_SURROGATE_PATH,
    TreeSHAPExplainer,
)


@pytest.fixture(autouse=True)
def reset_explainer_singleton():
    """Ensures singleton state is reset before each test."""
    TreeSHAPExplainer.reset_instance()
    yield
    TreeSHAPExplainer.reset_instance()


def test_shap_explainer_distilled_initialization():
    """Tests loading the distilled GradientBoosting surrogate if present on disk."""
    explainer = TreeSHAPExplainer.get_instance()
    assert explainer.model is not None
    assert explainer.explainer is not None
    assert isinstance(explainer.base_value, float)
    if os.path.exists(DEFAULT_SURROGATE_PATH):
        assert explainer.is_distilled is True
        # Verify drift check on live models
        assert explainer.surrogate_drift_detected is False


def test_shap_explainer_fallback_mode():
    """Tests graceful fallback to heuristic surrogate when given non-existent model path."""
    fake_path = "backend/models/non_existent_surrogate.joblib"
    explainer = TreeSHAPExplainer(model_path=fake_path)
    assert explainer.is_distilled is False
    assert explainer.model is not None
    assert explainer.explainer is not None

    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))
    res = explainer.explain(dummy_features)
    assert res["is_distilled"] is False
    assert res["surrogate_type"] == "heuristic_fallback"


def test_shap_explainer_drift_detection_on_hash_mismatch(tmp_path):
    """Tests that a mismatch between DQN checkpoint and surrogate metadata triggers drift warning and flag."""
    import json
    # Create temp metadata file with mismatched hash
    meta_file = tmp_path / "shap_surrogate_meta.json"
    meta_payload = {
        "dqn_model_hash": "mismatched_deadbeef_hash_12345",
        "distilled_at": "2026-08-16T12:00:00+00:00"
    }
    meta_file.write_text(json.dumps(meta_payload))

    explainer = TreeSHAPExplainer(meta_path=str(meta_file))
    if explainer.is_distilled and explainer.active_dqn_hash:
        assert explainer.surrogate_drift_detected is True
        res = explainer.explain(np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,)))
        assert res["surrogate_drift_detected"] is True


def test_shap_explainer_output_structure():
    """Tests that explain() returns the expected dictionary contract."""
    explainer = TreeSHAPExplainer.get_instance()
    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))

    result = explainer.explain(dummy_features)
    assert "base_value" in result
    assert "prediction" in result
    assert "top_features" in result
    assert "all_features" in result
    assert "is_distilled" in result
    assert "surrogate_type" in result
    assert len(result["top_features"]) == 10
    assert len(result["all_features"]) == FEATURE_DIM

    # Check feature contribution structure
    top_feat = result["top_features"][0]
    assert "feature" in top_feat
    assert "feature_value" in top_feat
    assert "shap_value" in top_feat
    assert "impact" in top_feat
    assert top_feat["impact"] in ("positive", "negative")
    assert "abs_magnitude" in top_feat


def test_shap_explainer_additive_property():
    """Tests that TreeSHAP satisfies the exact additive efficiency axiom: f(x) = E[f(x)] + sum(phi_i)."""
    explainer = TreeSHAPExplainer.get_instance()
    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))
    result = explainer.explain(dummy_features)

    # In TreeSHAP, sum of all phi_i + base_value equals the model prediction f(x)
    total_shap = sum(f["shap_value"] for f in result["all_features"])
    expected_pred = result["base_value"] + total_shap
    assert abs(expected_pred - result["prediction"]) < 0.05


def test_shap_explainer_pairwise_differential():
    """Tests differential Shapley attribution: 'Why Action A over Action B?'."""
    explainer = TreeSHAPExplainer.get_instance()
    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))
    diff_res = explainer.explain_pairwise_actions(
        features=dummy_features,
        action_a="PUSH",
        action_b="CONSERVE",
    )

    assert "action_a" in diff_res
    assert "action_b" in diff_res
    assert "delta_q" in diff_res
    assert "preferred_action" in diff_res
    assert "top_differential_features" in diff_res
    assert len(diff_res["top_differential_features"]) == 10

    top_diff = diff_res["top_differential_features"][0]
    assert "delta_shap" in top_diff
    assert "favors" in top_diff
    assert "abs_magnitude" in top_diff


def test_shap_explainer_all_actions():
    """Tests predicted Q-value rankings across all 8 actions."""
    explainer = TreeSHAPExplainer.get_instance()
    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))
    all_res = explainer.explain_all_actions(dummy_features)

    assert "action_rankings" in all_res
    assert len(all_res["action_rankings"]) == 8
    assert "recommended_action" in all_res
    assert "q_margin_top2" in all_res

