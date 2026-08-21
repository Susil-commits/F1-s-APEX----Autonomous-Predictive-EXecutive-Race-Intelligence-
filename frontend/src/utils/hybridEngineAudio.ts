/**
 * Formula 1 Hybrid 1.6L V6 Turbo & MGU-K Power Unit Audio Synthesizer (Web Audio API).
 *
 * Implements:
 * 1. 1.6L V6 ICE harmonics (fundamental firing frequency + 3rd/5th harmonics).
 * 2. Turbocharger compressor spool-up high-frequency sine tone.
 * 3. MGU-K electric motor regenerative whine on deceleration.
 */

class HybridEngineAudioSynthesizer {
  private static instance: HybridEngineAudioSynthesizer;
  private ctx: AudioContext | null = null;
  private isRunning: boolean = false;
  private isMuted: boolean = false;

  // Audio Nodes
  private masterGain: GainNode | null = null;
  private iceOsc1: OscillatorNode | null = null;
  private iceOsc2: OscillatorNode | null = null;
  private iceGain: GainNode | null = null;
  private turboOsc: OscillatorNode | null = null;
  private turboGain: GainNode | null = null;
  private mgukOsc: OscillatorNode | null = null;
  private mgukGain: GainNode | null = null;

  private constructor() {}

  public static getInstance(): HybridEngineAudioSynthesizer {
    if (!HybridEngineAudioSynthesizer.instance) {
      HybridEngineAudioSynthesizer.instance = new HybridEngineAudioSynthesizer();
    }
    return HybridEngineAudioSynthesizer.instance;
  }

  private getAudioContext(): AudioContext | null {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setValueAtTime(muted ? 0 : 0.12, this.ctx.currentTime);
    }
  }

  public start() {
    if (this.isRunning) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      this.masterGain = ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : 0.08, ctx.currentTime);
      this.masterGain.connect(ctx.destination);

      // ICE Oscillator 1 (Sawtooth for raw exhaust roar)
      this.iceOsc1 = ctx.createOscillator();
      this.iceOsc1.type = 'sawtooth';
      this.iceOsc1.frequency.setValueAtTime(220, ctx.currentTime);

      // ICE Oscillator 2 (Triangle for deep engine body rumble)
      this.iceOsc2 = ctx.createOscillator();
      this.iceOsc2.type = 'triangle';
      this.iceOsc2.frequency.setValueAtTime(110, ctx.currentTime);

      this.iceGain = ctx.createGain();
      this.iceGain.gain.setValueAtTime(0.7, ctx.currentTime);

      this.iceOsc1.connect(this.iceGain);
      this.iceOsc2.connect(this.iceGain);
      this.iceGain.connect(this.masterGain);

      // Turbocharger Whistle (High-frequency sine)
      this.turboOsc = ctx.createOscillator();
      this.turboOsc.type = 'sine';
      this.turboOsc.frequency.setValueAtTime(1800, ctx.currentTime);

      this.turboGain = ctx.createGain();
      this.turboGain.gain.setValueAtTime(0.04, ctx.currentTime);

      this.turboOsc.connect(this.turboGain);
      this.turboGain.connect(this.masterGain);

      // MGU-K Electric Whine (High pitched square wave with lowpass)
      this.mgukOsc = ctx.createOscillator();
      this.mgukOsc.type = 'sine';
      this.mgukOsc.frequency.setValueAtTime(950, ctx.currentTime);

      this.mgukGain = ctx.createGain();
      this.mgukGain.gain.setValueAtTime(0.02, ctx.currentTime);

      this.mgukOsc.connect(this.mgukGain);
      this.mgukGain.connect(this.masterGain);

      this.iceOsc1.start();
      this.iceOsc2.start();
      this.turboOsc.start();
      this.mgukOsc.start();

      this.isRunning = true;
    } catch (e) {
      // Audio context error
    }
  }

  public updateEngineTelemetry(rpm: number, throttlePct: number, isBraking: boolean) {
    if (!this.isRunning || !this.ctx) return;

    try {
      const now = this.ctx.currentTime;
      // F1 1.6L 4-stroke V6 firing frequency = (RPM / 60) * 3
      const fundamentalHz = Math.max(80, (rpm / 60) * 3);

      if (this.iceOsc1) this.iceOsc1.frequency.setTargetAtTime(fundamentalHz, now, 0.05);
      if (this.iceOsc2) this.iceOsc2.frequency.setTargetAtTime(fundamentalHz * 0.5, now, 0.05);

      // Turbo frequency scales with throttle
      const turboHz = 1200 + (throttlePct / 100) * 2200;
      if (this.turboOsc) this.turboOsc.frequency.setTargetAtTime(turboHz, now, 0.08);
      if (this.turboGain) {
        this.turboGain.gain.setTargetAtTime((throttlePct / 100) * 0.08, now, 0.05);
      }

      // MGU-K regen whine when braking
      if (this.mgukGain) {
        this.mgukGain.gain.setTargetAtTime(isBraking ? 0.08 : 0.01, now, 0.04);
      }
      if (this.mgukOsc && isBraking) {
        this.mgukOsc.frequency.setTargetAtTime(800 + (rpm / 12000) * 800, now, 0.04);
      }
    } catch (e) {
      // Safe ignore
    }
  }

  public stop() {
    if (!this.isRunning) return;
    try {
      if (this.iceOsc1) this.iceOsc1.stop();
      if (this.iceOsc2) this.iceOsc2.stop();
      if (this.turboOsc) this.turboOsc.stop();
      if (this.mgukOsc) this.mgukOsc.stop();
      this.isRunning = false;
    } catch (e) {
      // Safe ignore
    }
  }
}

export const hybridAudio = HybridEngineAudioSynthesizer.getInstance();
