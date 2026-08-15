import { useEffect, useRef, useCallback } from 'react';
import { useRaceStore } from '../store/raceStore';
import { StrategyAction } from '../types/race';

export function useRaceSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const {
    setRaceState,
    setRunning,
    setSpeed,
    setConnected,
    resetHistory,
  } = useRaceStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[APEX WS] Connected to race digital twin stream');
      setConnected(true);
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
      console.log('[APEX WS] Disconnected. Attempting reconnect in 2s...');
      setConnected(false);
      setRunning(false);
      reconnectTimeoutRef.current = window.setTimeout(connect, 2000);
    };

    ws.onerror = (err) => {
      console.warn('[APEX WS] Socket error:', err);
      ws.close();
    };

    wsRef.current = ws;
  }, [setRaceState, setRunning, setSpeed, setConnected]);

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
    send({ type: 'PLAY' });
    try {
      await fetch('/api/race/play', { method: 'POST' });
    } catch {}
  }, [send]);

  const pause = useCallback(async () => {
    send({ type: 'PAUSE' });
    try {
      await fetch('/api/race/pause', { method: 'POST' });
    } catch {}
  }, [send]);

  const step = useCallback(async () => {
    send({ type: 'STEP' });
    try {
      await fetch('/api/race/step', { method: 'POST' });
    } catch {}
  }, [send]);

  const setSimulationSpeed = useCallback(async (speed: number) => {
    send({ type: 'SET_SPEED', speed });
    try {
      await fetch('/api/race/speed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speed }),
      });
    } catch {}
  }, [send]);

  const applyAction = useCallback(async (action: StrategyAction) => {
    send({ type: 'ACTION', action });
    try {
      await fetch('/api/race/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
    } catch {}
  }, [send]);

  const injectIncident = useCallback(async (event: 'SAFETY_CAR' | 'VSC' | 'RAIN') => {
    send({ type: 'INJECT_EVENT', event });
    try {
      await fetch('/api/race/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event }),
      });
    } catch {}
  }, [send]);

  const initRace = useCallback(async (trackName: string = 'silverstone', seed: number = 42) => {
    resetHistory();
    try {
      const res = await fetch('/api/race/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ track_name: trackName, seed }),
      });
      const data = await res.json();
      if (data.state) setRaceState(data.state);
    } catch (e) {
      console.error('Failed to init race', e);
    }
  }, [resetHistory, setRaceState]);

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
