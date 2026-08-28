"""Strategy Transformer & Parameter-Efficient LoRA Bid Value Network for APEX.

Implements a transformer-based stint value network with PEFT (Parameter-Efficient Fine-Tuning)
Low-Rank Adaptation (LoRA) for high-efficiency strategy adaptation across Formula 1 circuits.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

try:
    from peft import LoraConfig, PeftModel, get_peft_model
    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    LoraConfig = None  # type: ignore[assignment,misc]
    PeftModel = None  # type: ignore[assignment,misc]
    get_peft_model = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

DEFAULT_LORA_SAVE_DIR = Path(__file__).resolve().parent.parent / "models" / "lora_adapters" / "bid_value_network"


class MultiHeadAttentionBlock(nn.Module):
    """Custom self-attention block exposing explicit linear projections for LoRA targeting."""

    def __init__(self, d_model: int = 128, n_heads: int = 4):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)
        self.out_proj = nn.Linear(d_model, d_model)

        self.norm = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, seq_len, d_model]
        batch, seq_len, _ = x.shape
        residual = x

        q = self.q_proj(x).view(batch, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch, seq_len, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch, seq_len, self.n_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) / np.sqrt(self.head_dim)
        attn = torch.softmax(scores, dim=-1)
        context = torch.matmul(attn, v).transpose(1, 2).contiguous().view(batch, seq_len, self.d_model)

        out = self.out_proj(context)
        return self.norm(residual + out)


class StrategyTransformerEncoder(nn.Module):
    """Transformer Encoder modeling sequential race telemetry and tactical stint trajectories."""

    def __init__(
        self,
        input_dim: int = 28,
        d_model: int = 128,
        n_heads: int = 4,
        num_layers: int = 2,
        d_ff: int = 256,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, d_model)
        self.pos_embedding = nn.Parameter(torch.randn(1, 64, d_model) * 0.02)

        self.layers = nn.ModuleList([
            MultiHeadAttentionBlock(d_model=d_model, n_heads=n_heads)
            for _ in range(num_layers)
        ])

        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.LayerNorm(d_model),
        )

        # Bid Value & Strategy Heads
        self.bid_value_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.SiLU(),
            nn.Linear(64, 1),
        )
        self.action_policy_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.SiLU(),
            nn.Linear(64, 8),  # 8 Discrete Strategy Actions
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # x: [batch, seq_len, input_dim] or [batch, input_dim]
        if x.dim() == 2:
            x = x.unsqueeze(1)  # [batch, 1, input_dim]

        batch, seq_len, _ = x.shape
        h = self.input_proj(x) + self.pos_embedding[:, :seq_len, :]

        for layer in self.layers:
            h = layer(h)

        h = h + self.feed_forward(h)

        # Global average pool over sequence
        pooled = h.mean(dim=1)  # [batch, d_model]

        bid_value = self.bid_value_head(pooled)  # [batch, 1]
        action_logits = self.action_policy_head(pooled)  # [batch, 8]

        return bid_value, action_logits


def get_trainable_parameters_summary(model: nn.Module) -> Dict[str, Any]:
    """Calculates total vs trainable parameters and parameter reduction percentage."""
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_pct = (trainable_params / total_params * 100.0) if total_params > 0 else 0.0

    return {
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "frozen_parameters": total_params - trainable_params,
        "trainable_percentage": round(trainable_pct, 2),
        "parameter_reduction_ratio": round(total_params / max(1, trainable_params), 1),
    }


def create_lora_bid_value_network(
    input_dim: int = 28,
    d_model: int = 128,
    r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    target_modules: Optional[List[str]] = None,
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Initializes a StrategyTransformerEncoder wrapped with a PEFT LoRA adapter.
    Freezes the base transformer parameters, training only low-rank projection adapters.
    """
    base_model = StrategyTransformerEncoder(input_dim=input_dim, d_model=d_model)

    if not PEFT_AVAILABLE or LoraConfig is None or get_peft_model is None:
        logger.warning("[PEFT] peft library not available. Freezing base layers manually.")
        # Manual fallback: freeze base layers and leave linear projections trainable
        for name, param in base_model.named_parameters():
            if "head" not in name:
                param.requires_grad = False
        summary = get_trainable_parameters_summary(base_model)
        return base_model, summary

    # Configure LoRA targeting attention projections
    targets = target_modules or ["q_proj", "v_proj", "out_proj"]
    peft_config = LoraConfig(
        r=r,
        lora_alpha=lora_alpha,
        target_modules=targets,
        lora_dropout=lora_dropout,
        bias="none",
    )

    lora_model: nn.Module = get_peft_model(base_model, peft_config)  # type: ignore[arg-type]
    summary = get_trainable_parameters_summary(lora_model)

    logger.info(
        f"[LoRA] Initialized PEFT adapter on Strategy Transformer: "
        f"{summary['trainable_parameters']:,} / {summary['total_parameters']:,} params "
        f"({summary['trainable_percentage']}% trainable, {summary['parameter_reduction_ratio']}x reduction)."
    )
    return lora_model, summary


def save_lora_checkpoint(
    model: nn.Module,
    save_dir: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> str:
    """Saves LoRA adapter checkpoint to disk."""
    out_dir = Path(save_dir or output_dir or DEFAULT_LORA_SAVE_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    save_fn = getattr(model, "save_pretrained", None)
    if callable(save_fn):
        save_fn(str(out_dir))
    else:
        # Fallback PyTorch save
        torch.save(model.state_dict(), out_dir / "adapter_model.pt")

    logger.info(f"[LoRA] Saved adapter checkpoint to {out_dir}")
    return str(out_dir)


def load_lora_checkpoint(
    base_model: Optional[nn.Module] = None,
    checkpoint_dir: Optional[str | Path] = None,
) -> nn.Module:
    """Loads a pre-trained LoRA adapter on top of the StrategyTransformerEncoder base model."""
    ckpt_dir = Path(checkpoint_dir or DEFAULT_LORA_SAVE_DIR)
    if base_model is None:
        base_model = StrategyTransformerEncoder()

    if PEFT_AVAILABLE and PeftModel is not None and ckpt_dir.exists():
        try:
            from_pretrained_fn = getattr(PeftModel, "from_pretrained", None)
            if callable(from_pretrained_fn):
                model: nn.Module = from_pretrained_fn(base_model, str(ckpt_dir))
                model.eval()
                return model
        except Exception as e:
            logger.warning(f"[LoRA] Error loading PEFT adapter ({e}). Returning base model.")

    if (ckpt_dir / "adapter_model.pt").exists():
        try:
            base_model.load_state_dict(torch.load(ckpt_dir / "adapter_model.pt", map_location="cpu", weights_only=True), strict=False)
            base_model.eval()
            return base_model
        except Exception:
            pass

    return base_model
