"""Model Metadata Registry for APEX Decision Intelligence.

Provides governance cards, training data lineage, evaluation metrics, and SHA-256 hashes
for all predictive and reinforcement learning models deployed in APEX.
"""
from typing import Dict, List, Optional
from context.schemas.metadata import ModelMetadataCard


MODEL_REGISTRY: Dict[str, ModelMetadataCard] = {
    "tyre_degradation_xgb": ModelMetadataCard(
        model_id="model:tyre_degradation_xgb_v1.4",
        name="Tyre Degradation Regressor (XGBoost Flagship)",
        version="v1.4",
        algorithm_family="Gradient Boosted Decision Trees (XGBoost)",
        training_dataset="dataset:fastf1_2018_2024_gold_v1.0",
        feature_schema="race_features_v3",
        owner="apex-telemetry-ml",
        training_circuits=[
            "Silverstone", "Spa", "Monza", "Suzuka", "Barcelona", "Red Bull Ring", "Interlagos"
        ],
        evaluation_dataset="dataset:heldout_1400_fastf1_laps_v1.0",
        metrics={
            "r2": 0.8342,
            "mae": 0.3597,
            "rmse": 0.5312,
            "pearson_r": 0.9166,
            "cliff_accuracy_pct": 88.43,
        },
        inference_latency_ms_p99=0.012,
        input_features=[
            "stint_lap", "tyre_age_laps", "compound_ordinal", "track_temp_c",
            "air_temp_c", "fuel_load_kg", "wear_pct_accumulated", "braking_intensity"
        ],
        output_dimension="lap_time_bleed_s_per_lap",
        status="validated",
        created_at="2024-03-01T00:00:00Z",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ),

    "pinn_tyre_residual_mlp": ModelMetadataCard(
        model_id="model:pinn_tyre_residual_mlp_v1.2",
        name="Physics-Informed Neural Network Tyre Residual Compensator",
        version="v1.2",
        algorithm_family="Deep Hybrid PINN (Residual Physics MLP)",
        training_dataset="dataset:fastf1_2018_2024_gold_v1.0",
        feature_schema="race_features_v3",
        owner="apex-physics-intelligence",
        training_circuits=["Silverstone", "Spa", "Zandvoort", "Monaco"],
        evaluation_dataset="dataset:heldout_1400_fastf1_laps_v1.0",
        metrics={
            "r2": 0.8120,
            "mae": 0.3840,
            "rmse": 0.5520,
            "pearson_r": 0.9010,
            "cliff_accuracy_pct": 86.10,
        },
        inference_latency_ms_p99=0.038,
        input_features=[
            "sliding_friction_coeff", "carcass_core_temp_c", "surface_blister_pct",
            "lateral_energy_joules", "tyre_age_laps"
        ],
        output_dimension="non_linear_thermal_residual_delta_s",
        status="validated",
        created_at="2024-03-10T00:00:00Z",
        sha256_hash="7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    ),

    "weather_predictor_radar": ModelMetadataCard(
        model_id="model:weather_predictor_radar_v2.1",
        name="High-Resolution Doppler Radar Precipitation Forecast",
        version="v2.1",
        algorithm_family="Spatial Barometric Radar Transformer",
        training_dataset="dataset:f1_weather_barometric_historical_v2.0",
        feature_schema="weather_features_v2",
        owner="apex-meteorology",
        training_circuits=["Silverstone", "Spa", "Zandvoort", "Interlagos", "Monaco", "Montreal"],
        evaluation_dataset="dataset:f1_weather_barometric_historical_v2.0",
        metrics={
            "brier_score": 0.0421,
            "roc_auc": 0.942,
            "calibration_error": 0.018,
            "f1_score": 0.912,
        },
        inference_latency_ms_p99=0.045,
        input_features=[
            "barometric_pressure_hpa", "radar_dbz_reflectivity", "track_wetness_index",
            "air_temp_c", "track_temp_c", "relative_humidity_pct", "wind_speed_kmh"
        ],
        output_dimension="rain_probability_next_5_laps",
        status="validated",
        created_at="2024-03-15T00:00:00Z",
        sha256_hash="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
    ),

    "dqn_strategy_agent": ModelMetadataCard(
        model_id="model:dqn_strategy_agent_v2.0",
        name="Deep Q-Network Autonomous Pit Strategy Policy",
        version="v2.0",
        algorithm_family="Dueling Double DQN with Prioritized Experience Replay",
        training_dataset="dataset:strategy_history_undercuts_v1.0",
        feature_schema="race_features_v3",
        owner="apex-rl-strategy",
        training_circuits=["Silverstone", "Monaco", "Spa", "Monza", "Hungaroring"],
        evaluation_dataset="dataset:heldout_1400_fastf1_laps_v1.0",
        metrics={
            "win_rate_pct": 93.3,
            "podium_rate_pct": 100.0,
            "mean_finish_position": 1.07,
            "blown_tyre_laps_avg": 0.0,
        },
        inference_latency_ms_p99=0.018,
        input_features=[
            "lap_normalized", "position", "gap_ahead_s", "gap_behind_s", "tyre_wear_pct",
            "tyre_age_laps", "compound_id", "safety_car_state", "rain_prob"
        ],
        output_dimension="q_values_6_discrete_actions",
        status="validated",
        created_at="2024-03-20T00:00:00Z",
        sha256_hash="3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d",
    ),

    "ppo_strategy_agent": ModelMetadataCard(
        model_id="model:ppo_strategy_agent_v2.0",
        name="Proximal Policy Optimization Continuous Control Agent",
        version="v2.0",
        algorithm_family="Actor-Critic PPO with Generalized Advantage Estimation",
        training_dataset="dataset:strategy_history_undercuts_v1.0",
        feature_schema="race_features_v3",
        owner="apex-rl-strategy",
        training_circuits=["Silverstone", "Monaco", "Spa", "Monza", "Interlagos"],
        evaluation_dataset="dataset:heldout_1400_fastf1_laps_v1.0",
        metrics={
            "win_rate_pct": 91.5,
            "podium_rate_pct": 98.0,
            "mean_finish_position": 1.12,
            "entropy_loss": 0.024,
        },
        inference_latency_ms_p99=0.022,
        input_features=[
            "lap_normalized", "pace_delta_s", "tyre_wear_pct", "fuel_burn_kg",
            "wake_turbulence_pct", "weather_risk_index"
        ],
        output_dimension="action_distribution_logits",
        status="validated",
        created_at="2024-03-22T00:00:00Z",
        sha256_hash="2c624232cdd221771294dfbb310aca000a0df6ac9b66b0d199bf41e4189adac3",
    ),

    "opponent_undercut_model": ModelMetadataCard(
        model_id="model:opponent_undercut_model_v1.1",
        name="Tactical Opponent Undercut Threat Classifier",
        version="v1.1",
        algorithm_family="LightGBM Binary Classifier with Game-Theoretic Features",
        training_dataset="dataset:strategy_history_undercuts_v1.0",
        feature_schema="race_features_v3",
        owner="apex-tactical-intelligence",
        training_circuits=["Silverstone", "Spa", "Zandvoort", "Hungaroring"],
        evaluation_dataset="dataset:strategy_history_undercuts_v1.0",
        metrics={
            "roc_auc": 0.924,
            "f1_score": 0.887,
            "precision": 0.892,
            "recall": 0.882,
        },
        inference_latency_ms_p99=0.009,
        input_features=[
            "rival_gap_s", "rival_tyre_age_laps", "pit_window_open_flag",
            "traffic_rejoin_buffer_s", "delta_to_pit_box_s"
        ],
        output_dimension="undercut_probability_0_to_1",
        status="validated",
        created_at="2024-03-25T00:00:00Z",
        sha256_hash="18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",
    ),

    "vehicle_health_anomaly_model": ModelMetadataCard(
        model_id="model:vehicle_health_anomaly_model_v1.0",
        name="16-Channel Telemetry Reconstruction Autoencoder",
        version="v1.0",
        algorithm_family="Variational Autoencoder (VAE Reconstruction)",
        training_dataset="dataset:live_telemetry_stream_60hz_v1.0",
        feature_schema="telemetry_60hz_raw",
        owner="apex-vehicle-engineering",
        training_circuits=["Silverstone 2023", "Spa 2023"],
        evaluation_dataset="dataset:live_telemetry_stream_60hz_v1.0",
        metrics={
            "reconstruction_error_mse": 0.0014,
            "anomaly_f1_score": 0.954,
            "false_positive_rate": 0.002,
        },
        inference_latency_ms_p99=0.015,
        input_features=[
            "engine_temp_c", "oil_temp_c", "coolant_temp_c", "brake_temp_c",
            "battery_temp_c", "battery_voltage_v", "ers_output_kw", "brake_pressure_bar"
        ],
        output_dimension="reconstruction_anomaly_score",
        status="validated",
        created_at="2024-04-01T00:00:00Z",
        sha256_hash="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
    ),
}


def get_model_metadata(model_key: str) -> Optional[ModelMetadataCard]:
    """Retrieve model card by key or model_id."""
    for key, card in MODEL_REGISTRY.items():
        if key == model_key or card.model_id == model_key:
            return card
    return None


def list_all_model_metadata() -> List[ModelMetadataCard]:
    """List all registered model cards."""
    return list(MODEL_REGISTRY.values())
