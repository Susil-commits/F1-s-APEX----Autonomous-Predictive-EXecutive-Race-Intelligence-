# APEX Core — Industrial-Grade Load Test Results

This document records the empirical load test benchmarks executed against the standalone APEX Core finishing position prediction service (`/api/core/predict`).

---

## 1. Test Overview & Configuration

- **Target Endpoint**: `POST /api/core/predict` (with concurrent `GET /api/health` heartbeats)
- **Tooling**: [Locust 2.46.4](https://locust.io/) headless runner (`locustfile.py`)
- **Server Framework**: FastAPI on Uvicorn ASGI runtime
- **Execution Model**: Non-blocking asynchronous event loop; CPU-bound inference (`model.predict` + quantile regression) dispatched to worker threads via `fastapi.concurrency.run_in_threadpool`
- **Worker Configuration**: Single process benchmark runtime; production container configured with `--workers 2` in `Dockerfile.core`
- **Rate Limiting**: Bypassed for pure compute saturation testing (`RATE_LIMIT_ENABLED=false`). In standard production operation, SlowAPI enforces a token-bucket rate limit of **30 requests/minute per client IP** on `/api/core/predict` (429 returned on overflow)
- **Payload Variance**: Random permutations of 16 grid drivers, 14 circuits, qualifying sector splits (S1/S2/S3 deltas), rain forecast variations, and mid-race weather transition flags.

> [!IMPORTANT]
> **Rate Limiting Bypass Disclosure:**
> In live production, the API strictly enforces a **30 req/min per client IP** limit (~0.5 req/s). For this benchmark, rate limiting was disabled to measure the maximum theoretical throughput and latency profile of the underlying inference pipeline under sustained concurrency. Real single-client production throughput will be capped by the 30 req/min policy unless whitelisted or elevated.

---

## 2. Benchmark Summary Across Concurrency Tiers

| Concurrency Level | Predict Req/s | Aggregated Req/s | Total Requests | Failures (%) | Median Latency | Avg Latency | p90 Latency | p95 Latency | p99 Latency |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **10 Virtual Users** | **144.2 req/s** | **164.2 req/s** | 2,308 | **0.00%** | **5 ms** | **7.0 ms** | **8 ms** | **9 ms** | **14 ms** |
| **50 Virtual Users** | **407.1 req/s** | **469.8 req/s** | 6,586 | **0.00%** | **48 ms** | **41.0 ms** | **63 ms** | **68 ms** | **96 ms** |
| **100 Virtual Users** | **438.9 req/s** | **505.1 req/s** | 7,087 | **0.00%** | **150 ms** | **118.9 ms** | **170 ms** | **180 ms** | **200 ms** |

---

## 3. Detailed Percentile Distribution

### 10 Concurrent Users (Low Contention Baseline)
- **Requests**: 2,026 predict calls (282 health checks)
- **Failure Count**: 0 (0.00% error rate)
- **Throughput**: 144.2 predict req/s (164.2 total req/s)
- **Predict Percentiles**:
  - **50% (Median)**: 5 ms
  - **90%**: 8 ms
  - **95%**: 10 ms
  - **99%**: 14 ms
  - **Max**: 961.1 ms (cold start JIT / initial tree loading)

### 50 Concurrent Users (High Telemetry Ingestion)
- **Requests**: 5,707 predict calls (879 health checks)
- **Failure Count**: 0 (0.00% error rate)
- **Throughput**: 407.1 predict req/s (469.8 total req/s)
- **Predict Percentiles**:
  - **50% (Median)**: 50 ms
  - **90%**: 64 ms
  - **95%**: 69 ms
  - **99%**: 100 ms
  - **Max**: 138.0 ms

### 100 Concurrent Users (Saturation & Concurrency Stress)
- **Requests**: 6,158 predict calls (929 health checks)
- **Failure Count**: 0 (0.00% error rate)
- **Throughput**: 438.9 predict req/s (505.1 total req/s)
- **Predict Percentiles**:
  - **50% (Median)**: 150 ms
  - **90%**: 180 ms
  - **95%**: 190 ms
  - **99%**: 200 ms
  - **Max**: 295.7 ms

---

## 4. Architectural Analysis & Production Recommendations

1. **Zero Error Rate Under Concurrency**:
   Across all three tiers (**15,981 total requests** processed), the service maintained **100% availability with 0.00% failure rate** and zero socket disconnects or 5xx exceptions.
2. **Asynchronous Event Loop Unblocking (`run_in_threadpool`)**:
   Offloading `model.predict()` and quantile inference to `run_in_threadpool` prevents synchronous NumPy/CatBoost calculations from blocking the single-threaded asyncio event loop.
   - *Trade-off Context*: Threadpool handoff incurs a fractional microsecond context switch overhead per request. For very light, sub-millisecond tree predictions, this trade-off prioritizes event-loop concurrency and I/O responsiveness (e.g. `/api/health` p50 remains 1–23 ms) over single-request microsecond minimization.
3. **Multi-Worker Scaling (`--workers 2`)**:
   `Dockerfile.core` is configured with `--workers 2`. Since `get_core_model()` caches the model as a module-level singleton, each worker process loads its own in-memory copy upon fork/spawn. This doubles CPU core utilization without inter-process lock contention.
4. **Horizontal Scaling**:
   For production clusters requiring >1,000 req/s, deploy containerized replicas behind an NGINX ingress or AWS ALB reverse proxy with round-robin balancing.

---

## 5. How to Reproduce

```bash
# 1. Start the API server with rate limiting disabled
RATE_LIMIT_ENABLED=false uv run uvicorn core.api.main:app --port 8000

# 2. In another terminal, run Locust in headless mode
uv run locust -f locustfile.py --headless -u 10 -r 5 --run-time 15s --host http://127.0.0.1:8000
uv run locust -f locustfile.py --headless -u 50 -r 10 --run-time 15s --host http://127.0.0.1:8000
uv run locust -f locustfile.py --headless -u 100 -r 20 --run-time 15s --host http://127.0.0.1:8000
```
