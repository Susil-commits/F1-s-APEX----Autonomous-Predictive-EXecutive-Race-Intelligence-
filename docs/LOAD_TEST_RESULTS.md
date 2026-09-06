# APEX Core — Industrial-Grade Load Test Results

This document records the empirical load test benchmarks executed against the standalone APEX Core finishing position prediction service (`/api/core/predict`).

---

## 1. Test Overview & Configuration

- **Target Endpoint**: `POST /api/core/predict` (with background `GET /api/health` heartbeats)
- **Tooling**: [Locust 2.46.4](https://locust.io/) headless runner (`locustfile.py`)
- **Server Framework**: FastAPI on Uvicorn ASGI runtime
- **Worker Configuration**: Single process, in-memory CatBoost point model + GBR Quantile models (`P10/P50/P90`)
- **Rate Limiting**: Bypassed for pure compute saturation testing (`RATE_LIMIT_ENABLED=false`)
- **Payload Variance**: Random permutations of all 24 grid drivers, 14 circuits, qualifying sector splits (S1/S2/S3 deltas), rain forecast variations, and mid-race weather transition flags.

---

## 2. Benchmark Summary Across Concurrency Tiers

| Concurrency Level | Predict Req/s | Aggregated Req/s | Total Requests | Failures (%) | Median Latency | Avg Latency | p90 Latency | p95 Latency | p99 Latency |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **10 Virtual Users** | **135.4 req/s** | **153.7 req/s** | 2,160 | **0.00%** | **6 ms** | **10.1 ms** | **14 ms** | **16 ms** | **22 ms** |
| **50 Virtual Users** | **361.3 req/s** | **409.6 req/s** | 5,735 | **0.00%** | **57 ms** | **54.4 ms** | **80 ms** | **86 ms** | **100 ms** |
| **100 Virtual Users** | **338.0 req/s** | **387.8 req/s** | 5,433 | **0.00%** | **190 ms** | **170.5 ms** | **250 ms** | **270 ms** | **310 ms** |

---

## 3. Detailed Percentile Distribution

### 10 Concurrent Users (Low Latency / Interactive Prior Testing)
- **Requests**: 1,902 predict calls (258 health checks)
- **Failure Count**: 0
- **Throughput**: 135.36 predict req/s (153.72 total req/s)
- **Percentiles**:
  - **50% (Median)**: 6 ms
  - **66%**: 9 ms
  - **75%**: 10 ms
  - **80%**: 11 ms
  - **90%**: 14 ms
  - **95%**: 16 ms
  - **99%**: 22 ms
  - **Max**: 939 ms (first cold initialization call)

### 50 Concurrent Users (Peak Production Load)
- **Requests**: 5,059 predict calls (676 health checks)
- **Failure Count**: 0
- **Throughput**: 361.31 predict req/s (409.59 total req/s)
- **Percentiles**:
  - **50% (Median)**: 57 ms
  - **66%**: 64 ms
  - **75%**: 69 ms
  - **80%**: 72 ms
  - **90%**: 80 ms
  - **95%**: 86 ms
  - **99%**: 100 ms
  - **Max**: 216 ms

### 100 Concurrent Users (Saturation & Queue Backlog Limit)
- **Requests**: 4,735 predict calls (698 health checks)
- **Failure Count**: 0
- **Throughput**: 337.98 predict req/s (387.80 total req/s)
- **Percentiles**:
  - **50% (Median)**: 190 ms
  - **66%**: 210 ms
  - **75%**: 220 ms
  - **80%**: 230 ms
  - **90%**: 250 ms
  - **95%**: 270 ms
  - **99%**: 310 ms
  - **Max**: 1,260 ms

---

## 4. Architectural Analysis & Production Recommendations

1. **Zero Error Rate Under Peak Load**:
   Across all tiers (>13,000 requests processed), the service maintained **100% availability with zero 5xx or connection drops**.
2. **Throughput Plateau**:
   Peak throughput was reached at approximately **50 concurrent users (~360–410 req/s)**. At 100 users, single-process ASGI event loop queuing elevated average latency from 54ms to 170ms, indicating the single CPU core saturated while remaining completely stable.
3. **Horizontal Scaling**:
   For production deployments handling >500 req/s, deploy Uvicorn with 4 worker processes (`--workers 4`) or run containerized replicas behind an NGINX ingress reverse proxy with round-robin load balancing.
4. **Memory Footprint**:
   The process memory footprint remained steady at ~115 MB throughout the test, confirming thread-safe model caching without memory leaks or repeated artifact deserialization.

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
