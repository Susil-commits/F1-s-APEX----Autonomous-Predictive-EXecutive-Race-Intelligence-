/**
 * Spatial Trackside Soundscape & Audio FX Procedural Synthesizer (Web Audio API).
 *
 * Implements:
 * 1. Grandstand Crowd Roar on overtakes / pole laps.
 * 2. High-G Kerb Strike rumble vibrations.
 * 3. Pit Lane Speed Limiter oscillating exhaust pops.
 */

class SpatialAudioEffectsEngine {
  private static instance: SpatialAudioEffectsEngine;
  private ctx: AudioContext | null = null;
  private isMuted: boolean = false;

  private constructor() {}

  public static getInstance(): SpatialAudioEffectsEngine {
    if (!SpatialAudioEffectsEngine.instance) {
      SpatialAudioEffectsEngine.instance = new SpatialAudioEffectsEngine();
    }
    return SpatialAudioEffectsEngine.instance;
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
  }

  /**
   * Procedurally generates realistic grandstand crowd cheer on exciting events.
   */
  public playCrowdRoar(durationSeconds: number = 2.5) {
    if (this.isMuted) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      const bufferSize = ctx.sampleRate * durationSeconds;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);

      // Generate pink/white noise with smooth cheering swell
      for (let i = 0; i < bufferSize; i++) {
        const white = Math.random() * 2 - 1;
        const swell = Math.sin((i / bufferSize) * Math.PI);
        data[i] = white * swell * 0.18;
      }

      const noiseSource = ctx.createBufferSource();
      noiseSource.buffer = buffer;

      // Bandpass filter for crowd acoustic resonance (400Hz - 2200Hz)
      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(850, ctx.currentTime);
      filter.Q.setValueAtTime(1.8, ctx.currentTime);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.01, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + durationSeconds * 0.4);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + durationSeconds);

      noiseSource.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      noiseSource.start();
      noiseSource.stop(ctx.currentTime + durationSeconds);
    } catch (e) {
      // Audio context ignore
    }
  }

  /**
   * Generates low-frequency kerb strike rumble.
   */
  public playKerbRumble(durationSeconds: number = 0.4) {
    if (this.isMuted) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(65, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(35, ctx.currentTime + durationSeconds);

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + durationSeconds);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + durationSeconds);
    } catch (e) {
      // Audio context ignore
    }
  }

  /**
   * Generates rapid stuttering pit lane limiter exhaust rev pops.
   */
  public playPitLimiterPop() {
    if (this.isMuted) return;
    const ctx = this.getAudioContext();
    if (!ctx) return;

    try {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(420, ctx.currentTime);

      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      osc.stop(ctx.currentTime + 0.06);
    } catch (e) {
      // Audio context ignore
    }
  }
}

export const spatialAudio = SpatialAudioEffectsEngine.getInstance();
