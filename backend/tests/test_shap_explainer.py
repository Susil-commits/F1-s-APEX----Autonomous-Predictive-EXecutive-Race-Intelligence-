"""Unit tests for TreeSHAP Explainability Engine."""
import pytest
import numpy as np
from backend.app.intelligence.shap_explainer import TreeSHAPExplainer
from backend.app.intelligence.feature_builder import FEATURE_DIM, FEATURE_NAMES


def test_shap_explainer_initialization():
    explainer = TreeSHAPExplainer.get_instance()
    assert explainer.model is not None
    assert explainer.explainer is not None
    assert isinstance(explainer.base_value, float)


def test_shap_explainer_output_structure():
    explainer = TreeSHAPExplainer.get_instance()
    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))
    
    result = explainer.explain(dummy_features)
    assert "base_value" in result
    assert "prediction" in result
    assert "top_features" in result
    assert len(result["top_features"]) == 10
    
    # Check feature structure
    top_feat = result["top_features"][0]
    assert "feature" in top_feat
    assert "feature_value" in top_feat
    assert "shap_value" in top_feat
    assert "impact" in top_feat
    assert top_feat["impact"] in ("positive", "negative")


def test_shap_explainer_additive_property():
    explainer = TreeSHAPExplainer.get_instance()
    dummy_features = np.random.uniform(0.0, 1.0, size=(FEATURE_DIM,))
    result = explainer.explain(dummy_features)

    # In TreeSHAP, sum of all phi_i + base_value equals the model prediction f(x)
    total_shap = sum(f["shap_value"] for f in result["all_features"])
    expected_pred = result["base_value"] + total_shap
    assert abs(expected_pred - result["prediction"]) < 0.05
