"""Physics-Informed Neural Network (PINN) Tyre Residual Compensator for APEX.

Combines classical empirical Pacejka tyre wear dynamics with a deep residual neural network
initialized on a physics-motivated prior (capturing non-linear thermal blistering over 60% wear),
with support for online/offline fine-tuning on live or historical FastF1 session telemetry:
Delta_t_lap = PhysicsModel(compound, wear) + PINN_residual(track_severity, thermal_load, moisture, mode)
"""
import os
from typing import Any, Optional

import numpy as np
import torch
from torch import nn

from backend.app.intelligence.tyre_model import TyreModel
from backend.app.simulator.models import DrivingMode, TyreCompound

COMPOUND_SOFTNESS: dict[TyreCompound, float] = {
    TyreCompound.SOFT: 1.0,
    TyreCompound.MEDIUM: 0.7,
    TyreCompound.HARD: 0.4,
    TyreCompound.INTERMEDIATE: 0.5,
    TyreCompound.WET: 0.3,
}

MODE_INTENSITY: dict[DrivingMode, float] = {
    DrivingMode.PUSH: 1.25,
    DrivingMode.NORMAL: 1.0,
    DrivingMode.CONSERVE: 0.75,
}


class PINNResidualMLP(nn.Module):
    """Lightweight PyTorch MLP modeling non-linear tyre degradation residuals."""

    def __init__(self, in_features: int = 6, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class PINNTyreResidualCompensator:
    """Physics-Informed Neural Network (PINN) hybrid tyre degradation compensator."""

    _instance: Optional["PINNTyreResidualCompensator"] = None

    def __init__(self, weights_path: str | None = None):
        self.model = PINNResidualMLP(in_features=6, hidden_dim=32)
        self.weights_path = weights_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "models", "pinn_tyre_weights.pt"
        )
        self._load_or_initialize()

    def _load_or_initialize(self):
        """Loads pre-trained PINN residual weights or trains an initial zero-centered prior."""
        if os.path.exists(self.weights_path):
            try:
                state_dict = torch.load(self.weights_path, map_location="cpu", weights_only=True)
                self.model.load_state_dict(state_dict)
                self.model.eval()
                return
            except Exception:
                pass

        # Initialize with a regularized physics prior:
        # Train lightly on synthetic non-linear thermal blistering data
        self._train_initial_prior()

    def _train_initial_prior(self):
        """Trains an initial PINN prior matching non-linear thermal blistering over 60% wear."""
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=0.01, weight_decay=1e-4)

        # Generate 500 synthetic calibration points
        np.random.seed(42)
        X = np.random.uniform(0.0, 1.0, size=(500, 6)).astype(np.float32)
        # Synthetic residual physics target: exponential blistering beyond 65% wear (X[:, 1])
        y = np.where(X[:, 1] > 0.65, 0.45 * np.exp(3.0 * (X[:, 1] - 0.65)) * X[:, 3], 0.0).astype(np.float32)
        y = y.reshape(-1, 1)

        t_X = torch.from_numpy(X)
        t_y = torch.from_numpy(y)

        criterion = nn.MSELoss()
        for _ in range(80):
            optimizer.zero_grad()
            pred = self.model(t_X)
            loss = criterion(pred, t_y)
            loss.backward()
            optimizer.step()

        self.model.eval()
        try:
            os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
            torch.save(self.model.state_dict(), self.weights_path)
        except Exception:
            pass

    def predict_residual_delta_s(
        self,
        compound: TyreCompound,
        current_wear_pct: float,
        mode: DrivingMode,
        track_name: str = "silverstone",
        track_temp_c: float = 35.0,
        rain_intensity: float = 0.0,
    ) -> float:
        """
        Computes the neural residual lap-time penalty delta (in seconds)
        added to base Pacejka physics wear predictions.
        """
        softness = COMPOUND_SOFTNESS.get(compound, 0.6)
        wear_norm = float(np.clip(current_wear_pct / 100.0, 0.0, 1.0))
        mode_intensity = MODE_INTENSITY.get(mode, 1.0)
        track_sev = TyreModel.get_circuit_degradation_factor(track_name)
        temp_norm = float(np.clip(track_temp_c / 60.0, 0.0, 1.0))
        rain_norm = float(np.clip(rain_intensity, 0.0, 1.0))

        feat_vector = np.array(
            [[softness, wear_norm, mode_intensity, track_sev, temp_norm, rain_norm]],
            dtype=np.float32,
        )

        with torch.no_grad():
            t_in = torch.from_numpy(feat_vector)
            delta = float(self.model(t_in).item())

        return max(0.0, round(delta, 3))

    def fine_tune_on_session_telemetry(
        self,
        telemetry_samples: list[dict[str, Any]],
        learning_rate: float = 0.001,
        epochs: int = 10,
    ) -> float:
        """
        Online fine-tuning of PINN residual weights on live race session telemetry.
        Each sample dict contains: {compound, wear_pct, mode, track_name, track_temp_c, rain_intensity, actual_lap_time_loss}
        """
        if not telemetry_samples:
            return 0.0

        X_list = []
        y_list = []
        for s in telemetry_samples:
            softness = COMPOUND_SOFTNESS.get(s["compound"], 0.6)
            wear_norm = float(np.clip(s["wear_pct"] / 100.0, 0.0, 1.0))
            mode_intensity = MODE_INTENSITY.get(s["mode"], 1.0)
            track_sev = TyreModel.get_circuit_degradation_factor(s.get("track_name", "silverstone"))
            temp_norm = float(np.clip(s.get("track_temp_c", 35.0) / 60.0, 0.0, 1.0))
            rain_norm = float(np.clip(s.get("rain_intensity", 0.0), 0.0, 1.0))
            
            X_list.append([softness, wear_norm, mode_intensity, track_sev, temp_norm, rain_norm])
            y_list.append([float(s.get("actual_lap_time_loss", 0.0))])

        t_X = torch.tensor(X_list, dtype=torch.float32)
        t_y = torch.tensor(y_list, dtype=torch.float32)

        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        final_loss = 0.0
        for _ in range(epochs):
            optimizer.zero_grad()
            preds = self.model(t_X)
            loss = criterion(preds, t_y)
            loss.backward()
            optimizer.step()
            final_loss = float(loss.item())

        self.model.eval()
        try:
            torch.save(self.model.state_dict(), self.weights_path)
        except Exception:
            pass

        return round(final_loss, 4)

    @classmethod
    def get_instance(cls) -> "PINNTyreResidualCompensator":
        """Returns singleton PINN compensator instance."""
        if cls._instance is None:
            cls._instance = PINNTyreResidualCompensator()
        return cls._instance
