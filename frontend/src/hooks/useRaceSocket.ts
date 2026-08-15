import { useEffect, useRef, useCallback } from 'react';
import { useRaceStore } from '../store/raceStore';
import { StrategyAction } from '../types/race';
import { ClientRaceSimulator } from '../utils/clientSimulator';

export function useRaceSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const simTimerRef = useRef<number | null>(null);
  const localSimRef = useRef<ClientRaceSimulator>(new ClientRaceSimulator('silverstone', 42));

  const {
    setRaceState,
    setRunning,
    setSpeed,
    setConnected,
    setIsLocalTwin,
    resetHistory,
    raceState,
    isRunning,
    simSpeed,
  } = useRaceStore();

  // Initialize initial local state if empty
  useEffect(() => {
    if (!raceState) {
      setRaceState(localSimRef.current.getState());
      setIsLocalTwin(true);
    }
  }, [raceState, setRaceState, setIsLocalTwin]);

  // Local simulation tick loop when running in local twin mode
  useEffect(() => {
    if (isRunning && !wsRef.current?.readyState) {
      const intervalMs = Math.max(100, Math.floor(1000 / simSpeed));
      simTimerRef.current = window.setInterval(() => {
        const nextState = localSimRef.current.step();
        setRaceState(nextState);
        if (nextState.is_finished) {
          setRunning(false);
        }
      }, intervalMs);
    } else {
      if (simTimerRef.current) clearInterval(simTimerRef.current);
    }

    return () => {
      if (simTimerRef.current) clearInterval(simTimerRef.current);
    };
  }, [isRunning, simSpeed, setRaceState, setRunning]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[APEX WS] Connected to backend live twin stream');
        setConnected(true);
        setIsLocalTwin(false);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'STATE_UPDATE') {
            setRaceState(data.state);
            if (data.is_running !== undefined) setRunning(data.is_running);
            if (data.sim_speed !== undefined) setSpeed(data.sim_speed);
          } else if (data.type === 'SPEED_CHANGED') {
            if (data.sim_speed !== undefined) setSpeed(data.sim_speed);
          } else if (data.type === 'RACE_FINISHED') {
            setRaceState(data.state);
            setRunning(false);
          }
        } catch (err) {
          console.error('[APEX WS] Failed to parse message', err);
        }
      };

      ws.onclose = () => {
        console.log('[APEX WS] Backend offline. Operating on high-fidelity client digital twin.');
        setConnected(false);
        setIsLocalTwin(true);
        reconnectTimeoutRef.current = window.setTimeout(connect, 5000);
      };

      ws.onerror = () => {
        ws.close();
      };

      wsRef.current = ws;
    } catch {
      setIsLocalTwin(true);
    }
  }, [setRaceState, setRunning, setSpeed, setConnected, setIsLocalTwin]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  const play = useCallback(async () => {
    setRunning(true);
    send({ type: 'PLAY' });
    try {
      await fetch('/api/race/play', { method: 'POST' });
    } catch {}
  }, [send, setRunning]);

  const pause = useCallback(async () => {
    setRunning(false);
    send({ type: 'PAUSE' });
    try {
      await fetch('/api/race/pause', { method: 'POST' });
    } catch {}
  }, [send, setRunning]);

  const step = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      send({ type: 'STEP' });
      try {
        await fetch('/api/race/step', { method: 'POST' });
      } catch {}
    } else {
      // Local step
      const nextState = localSimRef.current.step();
      setRaceState(nextState);
    }
  }, [send, setRaceState]);

  const setSimulationSpeed = useCallback(
    async (speed: number) => {
      setSpeed(speed);
      send({ type: 'SET_SPEED', speed });
      try {
        await fetch('/api/race/speed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ speed }),
        });
      } catch {}
    },
    [send, setSpeed]
  );

  const applyAction = useCallback(
    async (action: StrategyAction) => {
      localSimRef.current.setAction(action);
      send({ type: 'ACTION', action });
      try {
        await fetch('/api/race/action', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action }),
        });
      } catch {}
    },
    [send]
  );

  const injectIncident = useCallback(
    async (event: 'SAFETY_CAR' | 'VSC' | 'RAIN') => {
      localSimRef.current.injectIncident(event);
      setRaceState(localSimRef.current.getState());
      send({ type: 'INJECT_EVENT', event });
      try {
        await fetch('/api/race/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ event }),
        });
      } catch {}
    },
    [send, setRaceState]
  );

  const initRace = useCallback(
    async (trackName: string = 'silverstone', seed: number = 42) => {
      resetHistory();
      const fresh = localSimRef.current.reset(trackName, seed);
      setRaceState(fresh);
      try {
        const res = await fetch('/api/race/init', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ track_name: trackName, seed }),
        });
        const data = await res.json();
        if (data.state) setRaceState(data.state);
      } catch {
        // Fallback to local reset
      }
    },
    [resetHistory, setRaceState]
  );

  return {
    play,
    pause,
    step,
    setSimulationSpeed,
    applyAction,
    injectIncident,
    initRace,
  };
}
