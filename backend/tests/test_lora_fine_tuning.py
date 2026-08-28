"""Unit & integration tests for Strategy Transformer & PEFT LoRA Fine-Tuning."""
import tempfile
from pathlib import Path

import pytest
import torch

from backend.training.bid_value_network import (
    StrategyTransformerEncoder,
    create_lora_bid_value_network,
    get_trainable_parameters_summary,
    load_lora_checkpoint,
    save_lora_checkpoint,
)
from backend.training.train_advanced_fine_tuning import (
    generate_synthetic_stint_dataset,
    run_lora_fine_tuning,
)


def test_strategy_transformer_forward():
    """Verify base StrategyTransformerEncoder forward pass and output dimensions."""
    model = StrategyTransformerEncoder(input_dim=28, d_model=128)
    dummy_input = torch.randn(4, 8, 28)  # [batch=4, seq_len=8, dim=28]

    bid_value, action_logits = model(dummy_input)

    assert bid_value.shape == (4, 1)
    assert action_logits.shape == (4, 8)


def test_lora_parameter_freezing():
    """Verify that PEFT LoRA adapter freezes base weights and trains < 15% of parameters."""
    model, summary = create_lora_bid_value_network(input_dim=28, d_model=128, r=8)

    assert summary["total_parameters"] > 0
    assert summary["trainable_parameters"] > 0
    assert summary["trainable_percentage"] < 25.0
    assert summary["parameter_reduction_ratio"] > 1.0


def test_synthetic_stint_dataset_generation():
    """Verify synthetic dataset generator shapes and types."""
    X, y_bid, y_act = generate_synthetic_stint_dataset(n_samples=50, seq_len=6, input_dim=28)

    assert X.shape == (50, 6, 28)
    assert y_bid.shape == (50, 1)
    assert y_act.shape == (50,)


def test_lora_fine_tuning_and_checkpoint_saving():
    """Verify that LoRA fine-tuning converges, saves adapter checkpoint, and reloads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        report = run_lora_fine_tuning(
            epochs=3,
            batch_size=16,
            learning_rate=1e-3,
            rank=4,
            output_dir=temp_dir,
            verbose=False,
        )

        assert report["status"] == "CONVERGED"
        assert report["epochs_trained"] == 3
        assert (Path(temp_dir) / "training_summary.json").exists()

        # Reload LoRA checkpoint
        loaded_model = load_lora_checkpoint(checkpoint_dir=temp_dir)
        assert loaded_model is not None

        test_input = torch.randn(2, 6, 28)
        with torch.no_grad():
            bid_val, act_logits = loaded_model(test_input)
            assert bid_val.shape == (2, 1)
            assert act_logits.shape == (2, 8)
