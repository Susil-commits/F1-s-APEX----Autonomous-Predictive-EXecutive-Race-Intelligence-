"""Locust Load Testing Scenario for APEX Core Finish Position Predictor.

Benchmarks /api/core/predict throughput, latency percentiles, and failure rates
under concurrent load (10, 50, 100 virtual users).
"""
import random
from locust import HttpUser, task, between

CANDIDATE_DRIVERS = [
    "VER", "HAM", "NOR", "LEC", "PIA", "SAI", "RUS", "ALO",
    "PER", "TSU", "HUL", "ALB", "GAS", "OCO", "MAG", "BOT",
]

CANDIDATE_CIRCUITS = [
    "silverstone", "monza", "spa", "monaco", "bahrain",
    "singapore", "baku", "vegas", "catalunya", "suzuka",
    "interlagos", "zandvoort", "hungaroring", "austria",
]


class ApexCorePredictUser(HttpUser):
    """Simulates realistic concurrent API clients requesting pre-race predictions."""

    wait_time = between(0.02, 0.08)

    @task(5)
    def predict_standard(self):
        """Simulates standard prediction payload with grid and rain."""
        driver = random.choice(CANDIDATE_DRIVERS)
        circuit = random.choice(CANDIDATE_CIRCUITS)
        grid = random.randint(1, 20)
        rain = random.choice([0.0, 0.05, 0.15, 0.35, 0.60])

        payload = {
            "race_id": circuit,
            "driver_id": driver,
            "grid_position": grid,
            "rain_probability": rain,
        }
        with self.client.post("/api/core/predict", json=payload, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}: {resp.text}")

    @task(2)
    def predict_weather_transition(self):
        """Simulates prediction payload with rain forecast and mid-race weather transition."""
        driver = random.choice(CANDIDATE_DRIVERS)
        circuit = random.choice(CANDIDATE_CIRCUITS)
        grid = random.randint(1, 20)

        payload = {
            "race_id": circuit,
            "driver_id": driver,
            "grid_position": grid,
            "rain_probability": random.choice([0.25, 0.50, 0.80]),
            "weather_transition": random.choice([True, False]),
        }
        with self.client.post("/api/core/predict", json=payload, catch_response=True) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}: {resp.text}")

    @task(1)
    def health_check(self):
        """Simulates occasional health check ping."""
        self.client.get("/api/health")
