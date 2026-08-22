import { useEffect, useCallback } from 'react';
import { useRaceStore } from '../store/raceStore';
import { StrategyAction } from '../types/race';
import { ClientRaceSimulator } from '../utils/clientSimulator';

// Module-level singleton state across all component hook subscribers
let globalWs: WebSocket | null = null;
let globalReconnectTimer: number | null = null;
let globalSimTimer: number | null = null;
const globalLocalSim = new ClientRaceSimulator('silverstone', 42);
let subscriberCount = 0;

export function useRaceSocket() {
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

  // Initialize initial state if empty
  useEffect(() => {
    if (!raceState) {
      setRaceState(globalLocalSim.getState());
      setIsLocalTwin(true);
    }
  }, [raceState, setRaceState, setIsLocalTwin]);

  // Local simulation tick loop when offline or in client twin mode
  useEffect(() => {
    if (isRunning && (!globalWs || globalWs.readyState !== WebSocket.OPEN)) {
      if (globalSimTimer) clearInterval(globalSimTimer);
      const intervalMs = Math.max(100, Math.floor(1000 / simSpeed));
      globalSimTimer = window.setInterval(() => {
        const nextState = globalLocalSim.step();
        setRaceState(nextState);
        if (nextState.is_finished) {
          setRunning(false);
        }
      }, intervalMs);
    } else {
      if (globalSimTimer) {
        clearInterval(globalSimTimer);
        globalSimTimer = null;
      }
    }

    return () => {
      if (globalSimTimer) {
        clearInterval(globalSimTimer);
        globalSimTimer = null;
      }
    };
  }, [isRunning, simSpeed, setRaceState, setRunning]);

  const connect = useCallback(() => {
    if (globalWs && (globalWs.readyState === WebSocket.OPEN || globalWs.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const defaultHost = isLocal ? window.location.host : 'f1-s-apex-autonomous-predictive-executive-rac-production.up.railway.app';
      const wsUrl = (import.meta as any).env?.VITE_WS_URL || `${protocol}//${defaultHost}/ws`;

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
        setConnected(false);
        setIsLocalTwin(true);
        if (!globalReconnectTimer) {
          globalReconnectTimer = window.setTimeout(() => {
            globalReconnectTimer = null;
            connect();
          }, 5000);
        }
      };

      ws.onerror = () => {
        try {
          ws.close();
        } catch {}
      };

      globalWs = ws;
    } catch {
      setIsLocalTwin(true);
    }
  }, [setRaceState, setRunning, setSpeed, setConnected, setIsLocalTwin]);

  useEffect(() => {
    subscriberCount += 1;
    connect();

    return () => {
      subscriberCount -= 1;
      if (subscriberCount <= 0) {
        subscriberCount = 0;
        if (globalReconnectTimer) {
          clearTimeout(globalReconnectTimer);
          globalReconnectTimer = null;
        }
        if (globalWs) {
          try {
            globalWs.close();
          } catch {}
          globalWs = null;
        }
      }
    };
  }, [connect]);

  const send = useCallback((payload: object) => {
    if (globalWs && globalWs.readyState === WebSocket.OPEN) {
      globalWs.send(JSON.stringify(payload));
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
    if (globalWs && globalWs.readyState === WebSocket.OPEN) {
      send({ type: 'STEP' });
      try {
        await fetch('/api/race/step', { method: 'POST' });
      } catch {}
    } else {
      const nextState = globalLocalSim.step();
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
      globalLocalSim.setAction(action);
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
      globalLocalSim.injectIncident(event);
      setRaceState(globalLocalSim.getState());
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
      const fresh = globalLocalSim.reset(trackName, seed);
      setRaceState(fresh);
      try {
        const res = await fetch('/api/race/init', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ track_name: trackName, seed }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.state) {
            setRaceState(data.state);
          }
        }
      } catch {}
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
    isRunning,
    simSpeed,
  };
}
