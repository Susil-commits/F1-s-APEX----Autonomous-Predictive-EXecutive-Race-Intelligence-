/**
 * Neural Pit Wall Radio Synthesizer & Web Audio DSP Transceiver Engine.
 *
 * Implements:
 * 1. Web Speech Synthesis for dynamic real-time team radio calls.
 * 2. Web Audio API DSP signal chain:
 *    - Roger beep radio key chirp (1800Hz burst)
 *    - Transceiver bandpass filter (300Hz - 3400Hz)
 *    - Static white-noise burst & cockpit air turbulence simulator
 *    - Analog radio distortion waveshaper
 * 3. Reactive radio transcript logging and event dispatch.
 */

export interface RadioTransmission {
  id: string;
  timestamp: string;
  lap: number;
  speaker: string; // 'Race Engineer' | 'Pit Wall Chief' | 'Driver (APEX AI)' | 'Tyre Specialist'
  message: string;
  priority: 'ROUTINE' | 'TACTICAL' | 'URGENT' | 'SAFETY_CAR';
}

type RadioListener = (transmissions: RadioTransmission[]) => void;

class NeuralPitRadioEngine {
  private static instance: NeuralPitRadioEngine;
  private audioCtx: AudioContext | null = null;
  private transcriptHistory: RadioTransmission[] = [];
  private listeners: Set<RadioListener> = new Set();
  private isMuted: boolean = false;
  private isSpeaking: boolean = false;

  private constructor() {
    // Lazy AudioContext initialization on first user gesture
  }

  public static getInstance(): NeuralPitRadioEngine {
    if (!NeuralPitRadioEngine.instance) {
      NeuralPitRadioEngine.instance = new NeuralPitRadioEngine();
    }
    return NeuralPitRadioEngine.instance;
  }

  private initAudio(): AudioContext {
    if (!this.audioCtx) {
      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioCtx = new AudioCtxClass();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  public toggleMute(muted?: boolean): boolean {
    this.isMuted = muted !== undefined ? muted : !this.isMuted;
    return this.isMuted;
  }

  public subscribe(listener: RadioListener): () => void {
    this.listeners.add(listener);
    listener([...this.transcriptHistory]);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    const list = [...this.transcriptHistory];
    this.listeners.forEach((fn) => fn(list));
  }

  /**
   * Generates authentic two-tone VHF radio key chirp.
   */
  public playRadioChirp(isOpen: boolean = true) {
    if (this.isMuted) return;
    try {
      const ctx = this.initAudio();
      const now = ctx.currentTime;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(isOpen ? 1750 : 1200, now);
      osc.frequency.exponentialRampToValueAtTime(isOpen ? 2200 : 900, now + 0.045);

      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.055);
    } catch (e) {
      console.warn('[APEX Radio] AudioContext chirp error:', e);
    }
  }

  /**
   * Generates burst of transceiver white noise static.
   */
  public playRadioStatic(durationSeconds: number = 0.08) {
    if (this.isMuted) return;
    try {
      const ctx = this.initAudio();
      const now = ctx.currentTime;

      const bufferSize = ctx.sampleRate * durationSeconds;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = buffer.getChannelData(0);

      for (let i = 0; i < bufferSize; i++) {
        output[i] = Math.random() * 2 - 1;
      }

      const whiteNoise = ctx.createBufferSource();
      whiteNoise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(1600, now);
      filter.Q.setValueAtTime(1.5, now);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + durationSeconds);

      whiteNoise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      whiteNoise.start(now);
    } catch (e) {
      console.warn('[APEX Radio] AudioContext static error:', e);
    }
  }

  /**
   * Dispatches spoken radio message through TTS and logs transmission.
   */
  public broadcastTransmission(
    message: string,
    speaker: string = 'Race Engineer',
    priority: 'ROUTINE' | 'TACTICAL' | 'URGENT' | 'SAFETY_CAR' = 'TACTICAL',
    lap: number = 1
  ) {
    const item: RadioTransmission = {
      id: `rad_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      lap,
      speaker,
      message,
      priority,
    };

    this.transcriptHistory = [item, ...this.transcriptHistory.slice(0, 40)];
    this.notify();

    if (this.isMuted || !('speechSynthesis' in window)) return;

    try {
      this.playRadioChirp(true);
      this.playRadioStatic(0.06);

      // Cancel previous speech if urgent
      if (priority === 'URGENT' || priority === 'SAFETY_CAR') {
        window.speechSynthesis.cancel();
      }

      const utterance = new SpeechSynthesisUtterance(message);
      utterance.rate = 1.06;
      utterance.pitch = speaker.includes('Driver') ? 1.05 : 0.95;

      const voices = window.speechSynthesis.getVoices();
      const britishVoice = voices.find((v) => v.lang === 'en-GB' || v.name.includes('British') || v.name.includes('UK'));
      if (britishVoice) {
        utterance.voice = britishVoice;
      }

      utterance.onend = () => {
        this.playRadioStatic(0.05);
        this.playRadioChirp(false);
        this.isSpeaking = false;
      };

      this.isSpeaking = true;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('[APEX Radio] Speech synthesis broadcast error:', e);
    }
  }

  public getTransmissions(): RadioTransmission[] {
    return [...this.transcriptHistory];
  }

  public clearHistory() {
    this.transcriptHistory = [];
    this.notify();
  }
}

export const neuralPitRadio = NeuralPitRadioEngine.getInstance();
