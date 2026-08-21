/**
 * Hands-Free Voice AI Pit Wall Speech Recognition Engine (Web Speech API).
 *
 * Implements:
 * 1. Push-To-Talk (PTT) speech recognition listener.
 * 2. Natural language intent extraction for race strategy, pit stops, and queries.
 * 3. Autonomous command execution and spoken verbal response via Neural Pit Radio.
 */

import { neuralPitRadio } from './neuralRadioSynth';
import { useRaceStore } from '../store/raceStore';

export interface VoiceCommandResult {
  transcript: string;
  intent: string;
  actionTaken?: string;
  verbalResponse: string;
  confidence: number;
}

type VoiceStatusListener = (isListening: boolean, interimText: string) => void;

class VoiceRadioRecognitionEngine {
  private static instance: VoiceRadioRecognitionEngine;
  private recognition: any = null;
  private isListening: boolean = false;
  private statusListeners: Set<VoiceStatusListener> = new Set();
  private interimTranscript: string = '';

  private constructor() {
    this.initRecognition();
  }

  public static getInstance(): VoiceRadioRecognitionEngine {
    if (!VoiceRadioRecognitionEngine.instance) {
      VoiceRadioRecognitionEngine.instance = new VoiceRadioRecognitionEngine();
    }
    return VoiceRadioRecognitionEngine.instance;
  }

  private initRecognition() {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn('[APEX Voice] Web Speech Recognition API not supported in this browser.');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';

    this.recognition.onstart = () => {
      this.isListening = true;
      neuralPitRadio.playRadioChirp(true);
      this.notifyListeners();
    };

    this.recognition.onresult = (event: any) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      this.interimTranscript = interim || final;
      this.notifyListeners();

      if (final.trim()) {
        this.processVoiceIntent(final.trim());
      }
    };

    this.recognition.onerror = (event: any) => {
      console.warn('[APEX Voice] Speech recognition error:', event.error);
      this.isListening = false;
      this.interimTranscript = '';
      this.notifyListeners();
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.interimTranscript = '';
      neuralPitRadio.playRadioChirp(false);
      this.notifyListeners();
    };
  }

  public subscribeStatus(listener: VoiceStatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.isListening, this.interimTranscript);
    return () => this.statusListeners.delete(listener);
  }

  private notifyListeners() {
    this.statusListeners.forEach((fn) => fn(this.isListening, this.interimTranscript));
  }

  public startListening() {
    if (!this.recognition || this.isListening) return;
    try {
      this.recognition.start();
    } catch (e) {
      console.warn('[APEX Voice] Could not start recognition:', e);
    }
  }

  public stopListening() {
    if (!this.recognition || !this.isListening) return;
    try {
      this.recognition.stop();
    } catch (e) {
      console.warn('[APEX Voice] Could not stop recognition:', e);
    }
  }

  public toggleListening(): boolean {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
    return !this.isListening;
  }

  /**
   * Parses spoken natural language and executes the strategy intent.
   */
  public async processVoiceIntent(spokenText: string): Promise<VoiceCommandResult> {
    const lower = spokenText.toLowerCase();
    const store = useRaceStore.getState();
    const raceState = store.raceState;
    const player = raceState?.cars.find((c) => c.is_player) || raceState?.cars[0];

    let intent = 'UNKNOWN';
    let verbalResponse = "Understood driver, standing by.";
    let actionTaken = undefined;

    const sendBackendEvent = async (endpoint: string, body?: any) => {
      try {
        await fetch(`http://localhost:8000/api/${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body ? JSON.stringify(body) : undefined,
        });
      } catch (e) {
        console.warn('[APEX Voice] Backend event dispatch error:', e);
      }
    };

    // 1. Pit Stop Intents
    if (lower.includes('box') || lower.includes('pit') || lower.includes('tyre') || lower.includes('tire')) {
      if (lower.includes('soft') || lower.includes('red')) {
        intent = 'PIT_SOFT';
        actionTaken = 'PIT_SOFT';
        verbalResponse = 'Copy that, box this lap for Soft tyres. Confirm pit lane in.';
        await sendBackendEvent('strategy/override', { action: 'PIT_SOFT' });
      } else if (lower.includes('hard') || lower.includes('white')) {
        intent = 'PIT_HARD';
        actionTaken = 'PIT_HARD';
        verbalResponse = 'Copy box this lap, swapping to Hard compound.';
        await sendBackendEvent('strategy/override', { action: 'PIT_HARD' });
      } else if (lower.includes('inter') || lower.includes('green')) {
        intent = 'PIT_INTER';
        actionTaken = 'PIT_INTER';
        verbalResponse = 'Understood, box for Intermediate tyres. Pit crew ready.';
        await sendBackendEvent('strategy/override', { action: 'PIT_INTER' });
      } else if (lower.includes('wet') || lower.includes('blue')) {
        intent = 'PIT_WET';
        actionTaken = 'PIT_WET';
        verbalResponse = 'Box for Full Wets, track is drenched.';
        await sendBackendEvent('strategy/override', { action: 'PIT_WET' });
      } else {
        intent = 'PIT_MEDIUM';
        actionTaken = 'PIT_MEDIUM';
        verbalResponse = 'Box box box, confirm Medium tyres this lap.';
        await sendBackendEvent('strategy/override', { action: 'PIT_MEDIUM' });
      }
    }

    // 2. Engine & Driving Mode Intents
    else if (lower.includes('push') || lower.includes('attack') || lower.includes('fast')) {
      intent = 'MODE_PUSH';
      actionTaken = 'PUSH';
      verbalResponse = 'Strat 3 Push mode engaged. Give it everything.';
      await sendBackendEvent('strategy/override', { action: 'PUSH' });
    } else if (lower.includes('conserve') || lower.includes('save') || lower.includes('manage')) {
      intent = 'MODE_CONSERVE';
      actionTaken = 'CONSERVE';
      verbalResponse = 'Switching to conserve mode. Protect the rear tyres.';
      await sendBackendEvent('strategy/override', { action: 'CONSERVE' });
    }

    // 3. ERS & Battery Tactics
    else if (lower.includes('ers') || lower.includes('deploy') || lower.includes('overtake') || lower.includes('battery')) {
      if (lower.includes('harvest') || lower.includes('charge')) {
        intent = 'ERS_HARVEST';
        verbalResponse = 'MGU-K set to harvest mode. Recharging battery SoC.';
      } else {
        intent = 'ERS_OVERTAKE';
        verbalResponse = 'Full ERS deployment available. Press overtake button on exit.';
      }
    }

    // 4. Gap & Strategy Queries
    else if (lower.includes('gap') || lower.includes('ahead') || lower.includes('behind') || lower.includes('position')) {
      intent = 'QUERY_GAP';
      const gapAhead = player ? player.gap_to_car_ahead_s : 1.2;
      const pos = player ? player.position : 1;
      verbalResponse = `You are currently P${pos}. Gap to car ahead is ${gapAhead.toFixed(1)} seconds.`;
    }

    // 5. Weather & Rain Queries
    else if (lower.includes('rain') || lower.includes('weather') || lower.includes('cloud') || lower.includes('track')) {
      intent = 'QUERY_WEATHER';
      const rainProb = raceState ? Math.round(raceState.weather.rain_probability_next_5_laps * 100) : 15;
      const isRaining = raceState && raceState.weather.rain_intensity > 0.15;
      verbalResponse = isRaining
        ? `Track is currently damp with ${Math.round(raceState.weather.rain_intensity * 100)}% rain intensity.`
        : `Weather is currently clear. Rain probability over next 5 laps is ${rainProb}%.`;
    }

    // 6. Tyre Life & Degradation Query
    else if (lower.includes('tyre life') || lower.includes('wear') || lower.includes('cliff') || lower.includes('degradation')) {
      intent = 'QUERY_TYRE';
      const wear = player ? Math.round(player.tyre_wear_pct) : 35;
      verbalResponse = `Tyre wear is at ${wear}%. Degradation is within optimal window.`;
    }

    // Broadcast verbal response
    neuralPitRadio.broadcastTransmission(verbalResponse, 'Race Engineer', 'TACTICAL', raceState?.current_lap || 1);

    return {
      transcript: spokenText,
      intent,
      actionTaken,
      verbalResponse,
      confidence: 0.95,
    };
  }
}

export const voiceRadio = VoiceRadioRecognitionEngine.getInstance();
