import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Rate } from 'k6/metrics';

const rateLimitHits = new Counter('apex_chaos_429_hits');
const server5xxErrors = new Counter('apex_chaos_5xx_errors');
const completedJobs = new Counter('apex_chaos_jobs_dispatched');

export const options = {
  scenarios: {
    // Spike scenario pushing system past normal rate limits
    spike_traffic: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 1000,
      stages: [
        { duration: '10s', target: 200 },  // Normal load
        { duration: '20s', target: 1200 }, // Chaos spike: 1200 RPS
        { duration: '15s', target: 100 },  // Recovery
      ],
    },
  },
};

const BASE_URL = __ENV.APEX_BASE_URL || 'http://localhost:8000';

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  // Dispatch asynchronous heavy strategy jobs during burst
  const jobPayload = JSON.stringify({
    job_type: 'STRATEGY_MONTE_CARLO',
    params: {
      n_rollouts: 1000,
      current_lap: 30,
      total_laps: 52,
      tyre_compound: 'HARD',
      tyre_age: 22,
      position: 4,
    },
  });

  const res = http.post(`${BASE_URL}/api/jobs/enqueue`, jobPayload, { headers });

  if (res.status === 200 || res.status === 201) {
    completedJobs.add(1);
  } else if (res.status === 429) {
    rateLimitHits.add(1);
    check(res, {
      '429 response contains Retry-After': (r) => r.headers['Retry-After'] !== undefined,
    });
  } else if (res.status >= 500) {
    server5xxErrors.add(1);
  }
}
