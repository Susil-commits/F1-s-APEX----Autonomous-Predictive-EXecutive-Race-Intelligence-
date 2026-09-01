# How to Run F1 APEX

A plain-English guide to exploring and running the project.

---

## What this project actually does (no jargon)

> Pick a real Formula 1 race and a real driver. Click one button. The app looks at real facts known *before* that race started — where the driver qualified, how they've been performing recently, how their team has been doing — and predicts where they'll finish. It also shows its work: which facts mattered most, and how confident it is.
>
> There's a second, deeper mode that behaves like a real Formula 1 pit wall: it tracks tyre wear, simulates "what if we pit now vs. two laps later" scenarios, and explains every strategy call it makes.

---

## Option A — Just look at it (zero setup)

- Check out the screenshots and video demonstrations in [README.md](../README.md).
- Access the hosted live demo link (when deployed). This is the version to send in a job application — a recruiter does not need to clone a repository.

---

## Option B — Run it on your own computer (needs Docker, ~5–10 minutes)

1. **Install Docker Desktop**: Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (available for Windows, macOS, and Linux). This is the only developer tool required.
2. **Download or Clone the Project**:
   ```bash
   git clone https://github.com/Susil-commits/F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-.git
   cd F1-s-APEX----Autonomous-Predictive-EXecutive-Race-Intelligence-
   ```
3. **Start the Stack**:
   ```bash
   docker compose up
   ```
   This single command starts the entire system: PostgreSQL, Redis, Kafka event broker, backend API server, and Vite frontend.
4. **Open the Web Application**:
   Navigate to [http://localhost:5173](http://localhost:5173) in your browser.
5. **Try it**:
   - In **Simple Mode**: Pick a Grand Prix and driver, then click **ANALYZE PREDICTION**.
   - Click **Pit-Wall Mode** in the header to view 60Hz live race simulations, tyre physics, and Monte Carlo strategy rollouts.
6. **Stop Everything**:
   Press `Ctrl+C` in your terminal, then run:
   ```bash
   docker compose down
   ```

---

## Option C — Just the core predictor (fastest, lightweight, ~2 minutes)

If someone only wants to see the V1 prediction flow (not the full pit-wall stack with Kafka/Redis/Grafana), use the lightweight `core/` service: one backend process, one frontend, no heavy infrastructure required. This is the version ideal for live interview demonstrations because you can explain 100% of the running components.

### 1. Start Core Backend
```bash
# Using uv (fast package manager) or standard python:
uv run uvicorn core.api.main:app --port 8000 --reload
```
The Core FastAPI documentation will be live at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173). Simple Mode will connect directly to `http://localhost:8000/api/core/predict`.

---

## Running the Automated Test Suite

To verify all 254 test invariants and evaluation checks:
```bash
uv run pytest backend/tests
```
All 254 tests pass out of the box with zero external dependencies required.
