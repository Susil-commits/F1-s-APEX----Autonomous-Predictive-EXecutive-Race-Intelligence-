"""Evaluation, ablation, benchmarking, and regression testing harness for APEX."""
from backend.eval.ablation_runner import ABLATION_CONFIGS, AblationRunner
from backend.eval.run_eval import (
    evaluate_dqn_policy,
    evaluate_rag_retrieval,
    evaluate_shap_surrogate,
    evaluate_tyre_model_calibration,
    run_full_evaluation,
)

__all__ = [
    "ABLATION_CONFIGS",
    "AblationRunner",
    "evaluate_dqn_policy",
    "evaluate_rag_retrieval",
    "evaluate_shap_surrogate",
    "evaluate_tyre_model_calibration",
    "run_full_evaluation",
]
