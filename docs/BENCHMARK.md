# APEX Benchmark Guide
## Gate J: One-Command Reproducibility

**Document Version:** 1.0
**Last Updated:** 2026-08-19

---

## Quick Start (Gate J)

 Run the full benchmark suite with a single command:

.venv\Scripts\python.exe -m backend.eval.benchmark_runner

Or for a quick smoke test (1-2 min):

.venv\Scripts\python.exe -m backend.eval.benchmark_runner --quick

The command exits with code 0 if Gate J passes, 1 if it fails.

---

## What the Benchmark Measures

| Benchmark | What | Acceptance |
|-----------|------|-----------|
| simulator_speed | Full race laps/second | > 1000 laps/s |
| monte_carlo | ms/rollout at N=100/1k/5k | N=100 < 500ms |
| state_hash_determinism | Identical seed -> identical hashes | True |
| championship | 20-race APEX vs 4 baselines | APEX in top 3 |
| ablation | 9 configs x 10 races | FULL config wins |
| safe_rl_coverage | All scenario masks applied | 0 violations |

---

## Gate Status

| Gate | Benchmark | Pass Condition |
|------|-----------|---------------|
| E (Determinism) | state_hash_determinism | deterministic=True |
| G (Safety) | safe_rl_coverage | violations=0 |
| J (Reproducibility) | All 6 benchmarks | No errors, E + G pass |

---

## Output

The full benchmark report is saved to:

backend/eval/latest_benchmark_report.json

Format:
{ apex_benchmark_version, timestamp, seed, mode, total_elapsed_s,
  gate_j_passed, gate_e_passed, gate_g_passed, errors[], benchmarks[] }

---

## CI Integration

Add to .github/workflows/ci.yml:

    - name: Gate J Benchmark
      run: .venv/Scripts/python.exe -m backend.eval.benchmark_runner --quick

