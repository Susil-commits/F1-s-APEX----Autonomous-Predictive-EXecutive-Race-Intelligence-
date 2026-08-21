import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Custom k6 Metrics
const monteCarloLatency = new Trend('apex_monte_carlo_duration_ms');
const decisionLatency = new Trend('apex_decision_duration_ms');
const httpErrors = new Counter('apex_http_errors_total');
const rateLimitHits = new Counter('apex_rate_limit_hits_total');
const successRate = new Rate('apex_api_success_rate');

export const options = {
  stages: [
    { duration: '15s', target: 50 },  // Warmup
    { duration: '30s', target: 200 }, // Sustained standard traffic
    { duration: '30s', target: 500 }, // Peak 500 RPS compute traffic
    { duration: '15s', target: 0 },   // Cooldown
  ],
  thresholds: {
    http_req_duration: ['p(95)<250'], // 95% of requests must complete under 250ms
    apex_api_success_rate: ['rate>0.95'],
  },
};

const BASE_URL = __ENV.APEX_BASE_URL || 'http://localhost:8000';

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Client-Role': 'strategist',
    },
  };

  // 1. Benchmark Health Check & Metrics
  let resHealth = http.get(`${BASE_URL}/api/health`, params);
  check(resHealth, { 'Health status 200': (r) => r.status === 200 });

  // 2. Benchmark Monte Carlo Strategy Rollout Compute
  const mcPayload = JSON.stringify({
    action: 'PIT_NOW',
    current_lap: 28,
    total_laps: 52,
    current_compound: 'MEDIUM',
    current_tyre_age: 18,
    current_position: 2,
    n_simulations: 500,
  });

  const mcStart = Date.now();
  let resMC = http.post(`${BASE_URL}/api/strategy/monte-carlo`, mcPayload, params);
  monteCarloLatency.add(Date.now() - mcStart);

  if (resMC.status === 200) {
    successRate.add(1);
  } else if (resMC.status === 429) {
    rateLimitHits.add(1);
  } else {
    httpErrors.add(1);
    successRate.add(0);
  }

  // 3. Benchmark Fast Race State Fetch
  let resState = http.get(`${BASE_URL}/api/race/state/default`, params);
  check(resState, { 'Race state status 200': (r) => r.status === 200 });

  // 4. Benchmark Decision Engine
  const decStart = Date.now();
  let resDecision = http.get(`${BASE_URL}/api/strategy/recommendation/default`, params);
  decisionLatency.add(Date.now() - decStart);

  sleep(0.5);
}
