"""TreeSHAP Feature Explainer for APEX Decision Intelligence.

Provides single-policy attributions and pairwise multi-action differential explanations
(e.g., 'Why Action A over Action B?') using distilled tree surrogate models.
"""
from typing import Dict, List, Any, Optional, Union
import os
import logging
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import shap

from backend.app.simulator.models import RaceState, StrategyAction
from backend.app.strategy.gym_env import ACTION_MAP
from backend.app.intelligence.feature_builder import FeatureBuilder, FEATURE_NAMES, FEATURE_DIM

logger = logging.getLogger(__name__)

DEFAULT_SURROGATE_JOBLIB = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "shap_surrogate.joblib"
)
DEFAULT_MULTI_ACTION_SURROGATE_JOBLIB = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "shap_multi_action_surrogate.joblib"
)
DEFAULT_SURROGATE_PKL = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "shap_surrogate.pkl"
)
DEFAULT_SURROGATE_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "shap_surrogate.json"
)
DEFAULT_SURROGATE_PATH = DEFAULT_SURROGATE_JOBLIB

NAME_TO_ACTION_IDX = {
    "MAINTAIN": 0,
    "PUSH": 1,
    "CONSERVE": 2,
    "PIT_SOFT": 3,
    "PIT_MEDIUM": 4,
    "PIT_HARD": 5,
    "PIT_INTER": 6,
    "PIT_WET": 7,
}


class TreeSHAPExplainer:
    """Computes exact Shapley feature attributions (TreeSHAP) for strategic decision states.
    
    Explains the DQN policy's decision surface via tree ensemble surrogates distilled
    directly from real DQN rollouts and telemetry. Supports differential attribution between actions.
    """

    _instance: Optional["TreeSHAPExplainer"] = None

    def __init__(
        self,
        model_path: Optional[str] = None,
        multi_action_path: Optional[str] = None,
    ):
        self.model_path = model_path
        self.multi_action_path = multi_action_path or DEFAULT_MULTI_ACTION_SURROGATE_JOBLIB
        self.model: Optional[Any] = None
        self.explainer: Optional[shap.TreeExplainer] = None
        self.base_value: float = 0.0
        self.is_distilled: bool = False

        # Multi-action surrogate models and explainers
        self.action_models: Dict[int, Any] = {}
        self.action_explainers: Dict[int, shap.TreeExplainer] = {}
        self.action_base_values: Dict[int, float] = {}

        self._fit_surrogate_model()
        self._load_or_fit_multi_action_models()

    @classmethod
    def get_instance(
        cls,
        model_path: Optional[str] = None,
        multi_action_path: Optional[str] = None,
    ) -> "TreeSHAPExplainer":
        if cls._instance is None:
            cls._instance = TreeSHAPExplainer(
                model_path=model_path,
                multi_action_path=multi_action_path,
            )
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resets the singleton instance for testing or model reloading."""
        cls._instance = None

    def _resolve_model_path(self) -> Optional[str]:
        """Resolves available surrogate model artifact path."""
        if self.model_path:
            return self.model_path if os.path.exists(self.model_path) else None

        for path in (DEFAULT_SURROGATE_JOBLIB, DEFAULT_SURROGATE_PKL, DEFAULT_SURROGATE_JSON):
            if os.path.exists(path):
                return path
        return None

    def _fit_surrogate_model(self):
        """
        Loads the pre-trained surrogate distilled from the DQN policy.
        If no distilled model artifact exists, falls back gracefully to a domain heuristic surrogate.
        """
        resolved_path = self._resolve_model_path()

        if resolved_path and os.path.exists(resolved_path):
            try:
                if resolved_path.endswith(".joblib") or resolved_path.endswith(".pkl"):
                    self.model = joblib.load(resolved_path)
                elif resolved_path.endswith(".json"):
                    import xgboost as xgb
                    surrogate = xgb.XGBRegressor()
                    surrogate.load_model(resolved_path)
                    self.model = surrogate

                self.explainer = shap.TreeExplainer(self.model)
                expected = self.explainer.expected_value
                self.base_value = float(np.mean(expected)) if hasattr(expected, "__iter__") else float(expected)
                self.is_distilled = True
                print(f"[TreeSHAPExplainer] Successfully loaded distilled DQN tree surrogate from {resolved_path}")
                return
            except Exception as e:
                print(f"[TreeSHAPExplainer] Warning: Failed to load distilled model from {resolved_path}: {e}")

        # Fallback: domain heuristic surrogate
        target_display_path = self.model_path or DEFAULT_SURROGATE_JOBLIB
        print(
            f"[TreeSHAPExplainer] No distilled surrogate found at {target_display_path} — "
            "using synthetic fallback heuristic."
        )
        np.random.seed(42)
        n_samples = 1000
        X = np.random.uniform(0.0, 1.0, size=(n_samples, FEATURE_DIM))

        # Ground truth target: strategy score / expected delta-t advantage
        y = (
            - 3.5 * (X[:, 11] ** 2)                  # heavy penalty for high tyre wear
            - 4.0 * X[:, 21] * (1.0 - X[:, 9])       # wet track penalty without wet tyres
            + 2.0 * (1.0 - X[:, 0])                  # position reward
            + 1.8 * X[:, 25] * (X[:, 11] > 0.5)     # safety car pit advantage on worn tyres
            - 1.2 * X[:, 4]                          # dirty air wake from close car ahead
            + 0.8 * X[:, 14] * (1.0 - X[:, 11])      # push mode advantage on fresh tyres
            + np.random.normal(0, 0.05, size=n_samples)
        )

        self.model = GradientBoostingRegressor(
            n_estimators=40,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
        )
        self.model.fit(X, y)

        # Initialize TreeExplainer
        self.explainer = shap.TreeExplainer(self.model)
        expected = self.explainer.expected_value
        self.base_value = float(np.mean(expected)) if hasattr(expected, "__iter__") else float(expected)
        self.is_distilled = False

    def _load_or_fit_multi_action_models(self):
        """Loads per-action surrogate tree models or fits synthetic fallbacks."""
        if os.path.exists(self.multi_action_path):
            try:
                loaded = joblib.load(self.multi_action_path)
                if isinstance(loaded, dict):
                    self.action_models = loaded
                    for act_idx, act_mod in self.action_models.items():
                        exp = shap.TreeExplainer(act_mod)
                        self.action_explainers[act_idx] = exp
                        ev = exp.expected_value
                        self.action_base_values[act_idx] = float(np.mean(ev)) if hasattr(ev, "__iter__") else float(ev)
                    print(f"[TreeSHAPExplainer] Loaded {len(self.action_models)} per-action models from {self.multi_action_path}")
                    return
            except Exception as e:
                print(f"[TreeSHAPExplainer] Warning loading multi-action models: {e}")

        # Fallback multi-action models: fit variations on synthetic data
        np.random.seed(42)
        X = np.random.uniform(0.0, 1.0, size=(500, FEATURE_DIM))
        for act_idx in range(8):
            # Synthetic Q profile with action-specific biases
            bias = 2.0 if act_idx in (0, 1) else 1.0
            wear_weight = 4.0 if act_idx == 1 else (1.0 if act_idx in (3, 4, 5) else 2.5)
            y_act = bias - wear_weight * X[:, 11] + 1.5 * (1.0 - X[:, 0]) + np.random.normal(0, 0.05, size=500)
            m = GradientBoostingRegressor(n_estimators=30, max_depth=3, random_state=42 + act_idx)
            m.fit(X, y_act)
            exp = shap.TreeExplainer(m)
            self.action_models[act_idx] = m
            self.action_explainers[act_idx] = exp
            ev = exp.expected_value
            self.action_base_values[act_idx] = float(np.mean(ev)) if hasattr(ev, "__iter__") else float(ev)

    def _resolve_action_index(self, action: Union[int, str, StrategyAction]) -> int:
        """Helper to convert action representation to integer index [0..7]."""
        if isinstance(action, int):
            return max(0, min(7, action))
        if isinstance(action, StrategyAction):
            action_str = action.value
        else:
            action_str = str(action).upper().replace("STRATEGYACTION.", "")
        return NAME_TO_ACTION_IDX.get(action_str, 0)

    def explain(self, features: np.ndarray) -> Dict[str, Any]:
        """
        Computes exact TreeSHAP additive feature contributions for the chosen/global model.
        Returns:
            base_value: E[f(x)]
            prediction: f(x)
            contributions: list of {feature, value, shap_value, impact}
            is_distilled: bool
            surrogate_type: str
        """
        if features.ndim == 1:
            feat_matrix = features.reshape(1, -1)
        else:
            feat_matrix = features

        shap_values = self.explainer.shap_values(feat_matrix)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        if isinstance(shap_values, np.ndarray) and shap_values.ndim == 2:
            row_shap = shap_values[0]
        else:
            row_shap = shap_values

        prediction = float(self.model.predict(feat_matrix)[0])

        contributions: List[Dict[str, Any]] = []
        for i, (name, val, phi) in enumerate(zip(FEATURE_NAMES, feat_matrix[0], row_shap)):
            contributions.append({
                "feature": name,
                "feature_index": i,
                "feature_value": round(float(val), 3),
                "shap_value": round(float(phi), 4),
                "impact": "positive" if phi > 0 else "negative",
                "abs_magnitude": round(abs(float(phi)), 4),
            })

        # Sort by absolute impact descending
        contributions.sort(key=lambda c: c["abs_magnitude"], reverse=True)

        return {
            "base_value": round(self.base_value, 4),
            "prediction": round(prediction, 4),
            "top_features": contributions[:10],
            "all_features": contributions,
            "formula": "f(x) = E[f(x)] + SUM(phi_i)",
            "is_distilled": self.is_distilled,
            "surrogate_type": "distilled_dqn_surrogate" if self.is_distilled else "heuristic_fallback",
        }

    def explain_pairwise_actions(
        self,
        features: np.ndarray,
        action_a: Union[int, str, StrategyAction] = 1, # e.g. PUSH
        action_b: Union[int, str, StrategyAction] = 2, # e.g. CONSERVE
    ) -> Dict[str, Any]:
        """
        Computes differential TreeSHAP attributions: 'Why Action A over Action B?'.
        Decomposes Delta Q = Q(s, a_A) - Q(s, a_B) into additive feature diffs:
            Delta Q = (E[f_A] - E[f_B]) + sum(phi_i(a_A) - phi_i(a_B))
        """
        idx_a = self._resolve_action_index(action_a)
        idx_b = self._resolve_action_index(action_b)

        name_a = ACTION_MAP.get(idx_a, StrategyAction.MAINTAIN).value
        name_b = ACTION_MAP.get(idx_b, StrategyAction.CONSERVE).value

        if features.ndim == 1:
            feat_matrix = features.reshape(1, -1)
        else:
            feat_matrix = features

        exp_a = self.action_explainers.get(idx_a, self.explainer)
        exp_b = self.action_explainers.get(idx_b, self.explainer)
        mod_a = self.action_models.get(idx_a, self.model)
        mod_b = self.action_models.get(idx_b, self.model)

        # Computations for Action A
        shap_a = exp_a.shap_values(feat_matrix)
        if isinstance(shap_a, list):
            shap_a = shap_a[0]
        row_shap_a = shap_a[0] if (isinstance(shap_a, np.ndarray) and shap_a.ndim == 2) else shap_a
        pred_a = float(mod_a.predict(feat_matrix)[0])
        base_a = self.action_base_values.get(idx_a, self.base_value)

        # Computations for Action B
        shap_b = exp_b.shap_values(feat_matrix)
        if isinstance(shap_b, list):
            shap_b = shap_b[0]
        row_shap_b = shap_b[0] if (isinstance(shap_b, np.ndarray) and shap_b.ndim == 2) else shap_b
        pred_b = float(mod_b.predict(feat_matrix)[0])
        base_b = self.action_base_values.get(idx_b, self.base_value)

        delta_q = pred_a - pred_b
        delta_base = base_a - base_b

        differential_contributions: List[Dict[str, Any]] = []
        for i, (name, val, phi_a, phi_b) in enumerate(zip(FEATURE_NAMES, feat_matrix[0], row_shap_a, row_shap_b)):
            delta_phi = float(phi_a - phi_b)
            differential_contributions.append({
                "feature": name,
                "feature_index": i,
                "feature_value": round(float(val), 3),
                "shap_action_a": round(float(phi_a), 4),
                "shap_action_b": round(float(phi_b), 4),
                "delta_shap": round(delta_phi, 4),
                "favors": name_a if delta_phi > 0 else name_b,
                "abs_magnitude": round(abs(delta_phi), 4),
            })

        differential_contributions.sort(key=lambda c: c["abs_magnitude"], reverse=True)

        return {
            "action_a": name_a,
            "action_b": name_b,
            "q_value_action_a": round(pred_a, 4),
            "q_value_action_b": round(pred_b, 4),
            "delta_q": round(delta_q, 4),
            "preferred_action": name_a if delta_q >= 0 else name_b,
            "delta_base_value": round(delta_base, 4),
            "top_differential_features": differential_contributions[:10],
            "all_differential_features": differential_contributions,
            "formula": "ΔQ(A - B) = (E[f_A] - E[f_B]) + Σ (φ_i(A) - φ_i(B))",
            "is_distilled": self.is_distilled,
        }

    def explain_all_actions(self, features: np.ndarray) -> Dict[str, Any]:
        """Computes predicted Q-value ratings across all 8 strategic actions."""
        if features.ndim == 1:
            feat_matrix = features.reshape(1, -1)
        else:
            feat_matrix = features

        action_evaluations: List[Dict[str, Any]] = []
        for act_idx in range(8):
            act_name = ACTION_MAP.get(act_idx, StrategyAction.MAINTAIN).value
            mod = self.action_models.get(act_idx, self.model)
            q_val = float(mod.predict(feat_matrix)[0])
            action_evaluations.append({
                "action_index": act_idx,
                "action_name": act_name,
                "q_value": round(q_val, 4),
            })

        action_evaluations.sort(key=lambda x: x["q_value"], reverse=True)
        return {
            "action_rankings": action_evaluations,
            "recommended_action": action_evaluations[0]["action_name"],
            "q_margin_top2": round(action_evaluations[0]["q_value"] - action_evaluations[1]["q_value"], 4),
        }
