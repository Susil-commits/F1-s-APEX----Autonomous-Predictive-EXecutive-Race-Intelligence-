# APEX — Enterprise Distributed System Design & Architecture Deep-Dive

This document details the high-scale distributed systems design, asynchronous event processing, caching topologies, and trade-off analyses behind **APEX (Autonomous Predictive & EXecutive Race Intelligence)**.

---

## 1. System Overview & Core Requirements

Formula 1 live telemetry and tactical decision systems operate under strict real-time constraints:
- **Telemetry Frequency**: 60 Hz per vehicle across 20 cars = 1,200 telemetry packets/sec.
- **Decision Latency SLA**: P95 $< 100\text{ ms}$, P99 $< 250\text{ ms}$ for real-time pit orders during active race incidents.
- **Compute Offload**: High-iteration Monte Carlo rollouts ($10,000\times$ stochastic simulations) and TreeSHAP explainability must never block the primary event ingestion or WebSocket broadcasting loops.

---

## 2. Event-Driven Architecture vs Traditional Polling

```
                                 ┌─────────────────────────┐
                                 │ Real-Time FastF1 / Track │
                                 └────────────┬────────────┘
                                              │ 60Hz Telemetry
                                              ▼
                                 ┌─────────────────────────┐
                                 │  Kafka Ingestion Layer  │
                                 └───────┬─────────┬───────┘
                     Partition by Car ID │         │ Partition by Session ID
                                         ▼         ▼
          ┌────────────────────────────────┐     ┌────────────────────────────────┐
          │  Telemetry Consumer Group      │     │  Race Control Consumer Group   │
          │  • Physics-Informed Validation │     │  • SC/VSC Incident Trigger     │
          │  • L1 Memory Ring Buffer       │     │  • Emergency Brain Interrupt   │
          └────────────────────────────────┘     └────────────────────────────────┘
```

### Why Event-Driven with Kafka?
1. **Decoupling Producers and Consumers**: The simulation loop and external data providers (FastF1/Jolpica) publish events at high velocity without coupling to downstream consumers (ML models, historical recorders, pit wall UI).
2. **Backpressure Buffer**: During high-intensity events (e.g. 5 cars entering pit lane under Safety Car), Kafka buffers burst traffic without dropping packets or exhausting FastAPI worker memory.
3. **Partitioning & Ordering Guarantees**:
   - Telemetry partitioned by `session_id:car_id` guarantees **strict in-order packet processing** per car.
   - Race Control partitioned by `session_id` guarantees deterministic global race order timeline.
4. **Replayability & At-Least-Once Delivery**: Consumers commit offsets manually after successful processing. If a processing pod crashes, the replacement pod resumes from the last uncommitted offset.

---

## 3. Asynchronous Worker Queue (BullMQ / Redis Streams)

Heavy computational workloads are decoupled from the synchronous HTTP/WebSocket API:

```
[REST / WS Request] ──► [ApexJobManager] ──► [Redis Job Queue] ──► [ApexWorkerPool (N Pods)]
                                │                                         │
                                └──◄─── [Idempotency Deduplication Key] ──┘
```

### Job Queue Types & Idempotency
- **`STRATEGY_MONTE_CARLO`**: Parallelized 10,000-rollout stochastic simulations evaluating 9 candidate actions.
- **`HISTORICAL_REPLAY`**: Parsing multi-gigabyte session archives from FastF1.
- **`ML_RETRAIN_BATCH`**: Physics-Informed Neural Network (PINN) residual fitting and TreeSHAP global matrix generation.
- **`ALERT_DISPATCH`**: High-priority speech synthesis and radio dispatch notifications.

### Idempotency Strategy
```
idempotency_key = "apex:job:" + job_type + ":" + SHA256(canonical_json(params))[:16]
```
If multiple strategists trigger identical simulations within the same lap window, the existing job handle is returned immediately, eliminating redundant compute.

---

## 4. Multi-Tier Cache & Storage Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│ L1: In-Memory Ring Buffer (<0.1ms)                                     │
│     • Hot vehicle state dictionary                                     │
│     • Zero serialization overhead                                      │
├────────────────────────────────────────────────────────────────────────┤
│ L2: Distributed Redis Cluster (1-3ms)                                  │
│     • Distributed Session State & Token-Bucket Rate Limiter            │
│     • Write-behind queue buffer                                        │
├────────────────────────────────────────────────────────────────────────┤
│ L3: Relational Persistence: PostgreSQL + AsyncPG (10-50ms)             │
│     • Persistent Session Histories & Stint Data                        │
│     • Audit Journals & Tournament Standings                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security & Role-Based Access Control (RBAC)

| Role | Telemetry Streaming | Sandbox Simulation | Live Strategy Override | Incident Injection | Model Retraining / Admin |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **VIEWER** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **ANALYST** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **STRATEGIST** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **ADMIN** | ✅ | ✅ | ✅ | ✅ | ✅ |

Stateless HMAC-SHA256 JWT tokens contain claims (`sub`, `role`, `permissions`, `exp`) allowing horizontal scaling of backend pods without shared session state lookups.

---

## 6. Observability & Chaos Engineering

- **Prometheus Metric Registry**: Custom gauges for active sessions, connected WebSockets, Kafka consumer lag, BullMQ queue depth, and ML drift status.
- **OpenTelemetry Distributed Spans**: W3C `traceparent` headers propagate end-to-end across Kafka, workers, and WebSocket ticks.
- **Dead-Letter Queue (DLQ)**: Corrupted or poisoned payloads are routed to `f1.dlq.failed_events` without halting active telemetry ingestion.
