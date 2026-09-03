# How to Run F1 APEX

A plain-English guide to exploring, developing, and running the single-tier APEX V1 predictor.

---

## What this project actually does

> Pick a real Formula 1 Grand Prix and a driver. Click one button.
> The service takes verified facts known **strictly before lights out** (Qualifying grid position, 5-race driver rolling average, constructor points share, track downforce index, and rain forecast) and projects the driver's finishing position.
> 
> It provides:
> 1. **Projected Finish Position** (P1–P20)
> 2. **Split-Conformal 90% Confidence Interval** (guaranteed empirical coverage calibrated on held-out data)
> 3. **Win & Podium Probabilities**
> 4. **Feature Importance Breakdown** (transparent attribution of what drove the prediction)

---

## Option A — Run Locally with Python & Node (~2 minutes)

### 1. Install & Start Backend
```bash
# Clone the repository
git clone https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-.git
cd F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-

# Start FastAPI backend with uv (or standard virtualenv):
uv run uvicorn core.api.main:app --port 8000 --reload
```
Interactive OpenAPI documentation will be live at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Start Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173). The console connects to the local prediction endpoint.

---

## Option B — Run with Lean Docker Container

Build and run the entire self-contained predictive runtime in a single lightweight container (~250MB):

```bash
# Build the lean container
docker build -t f1-apex-core .

# Run container on port 8000
docker run -p 8000:8000 f1-apex-core
```

Verify service health:
```bash
curl http://localhost:8000/api/health
```

---

## Running the Automated Test Suite

To run the full unit and integration test suite:
```bash
uv run pytest tests/ -v
```

To re-run the 3-model benchmark (GradientBoosting vs. XGBoost vs. CatBoost) on the temporal holdout:
```bash
uv run python -m core.training.train
```

To evaluate the calibrated model on the temporal holdout:
```bash
uv run python -m core.training.evaluate
```
