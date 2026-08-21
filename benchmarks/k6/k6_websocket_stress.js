import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom k6 Observability Metrics
const wsConnectDuration = new Trend('apex_ws_connect_duration_ms');
const wsMessagesReceived = new Counter('apex_ws_messages_received_total');
const wsErrors = new Counter('apex_ws_errors_total');
const wsSuccessRate = new Rate('apex_ws_success_rate');

export const options = {
  stages: [
    { duration: '10s', target: 100 },  // Ramp-up to 100 concurrent clients
    { duration: '30s', target: 500 },  // Ramp-up to 500 clients
    { duration: '30s', target: 1000 }, // Peak sustained 1000 concurrent pit wall cockpits
    { duration: '10s', target: 0 },    // Ramp-down
  ],
  thresholds: {
    apex_ws_connect_duration_ms: ['p(95)<500'], // 95% connections establish under 500ms
    apex_ws_success_rate: ['rate>0.98'],        // >98% message reception success
  },
};

export default function () {
  const url = __ENV.APEX_WS_URL || 'ws://localhost:8000/ws/default';
  const startTime = Date.now();

  const res = ws.connect(url, {}, function (socket) {
    wsConnectDuration.add(Date.now() - startTime);

    socket.on('open', function () {
      wsSuccessRate.add(1);
      // Send PLAY command to ensure simulation loop is active
      socket.send(JSON.stringify({ type: 'PLAY', session_id: 'default' }));
    });

    socket.on('message', function (data) {
      try {
        const msg = JSON.parse(data);
        if (msg.type === 'TICK' || msg.type === 'RACE_STATE') {
          wsMessagesReceived.add(1);
          wsSuccessRate.add(1);
        }
      } catch (e) {
        wsErrors.add(1);
      }
    });

    socket.on('error', function (e) {
      wsErrors.add(1);
      wsSuccessRate.add(0);
    });

    socket.on('close', function () {
      // Clean disconnect
    });

    // Keep connection open for 15 seconds streaming telemetry
    socket.setTimeout(function () {
      socket.close();
    }, 15000);
  });

  check(res, { 'WebSocket handshake status 101': (r) => r && r.status === 101 });
  sleep(1);
}
