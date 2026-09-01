"""APEX Core Model Training and Evaluation Modules."""
from core.training.train import train_finishing_position_model
from core.training.evaluate import evaluate_model_temporal

__all__ = ["train_finishing_position_model", "evaluate_model_temporal"]
