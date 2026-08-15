/**
 * APEX Pit Wall Audio & Multi-Persona Voice Synthesizer
 * Provides authentic F1-style radio beeps, tactical alert chimes,
 * pneumatic wheel gun sound effects, bandpass radio static,
 * V6 Turbo Hybrid engine sound synthesis, and text-to-speech race engineer radio announcements.
 */

export type VoicePersona = 'apex_core' | 'bono' | 'gp' | 'xavi';

class AudioEngine {
  private audioCtx: AudioContext | null = null;
  private isMuted: boolean = false;
  private voiceEnabled: boolean = true;
  private engineSoundEnabled: boolean = false;
  private engineOsc: OscillatorNode | null = null;
  private engineGain: GainNode | null = null;
  private volume: number = 0.6;
  private persona: VoicePersona = 'apex_core';
  private lastSpokenMessage: string = '';
  private lastSpokenTime: number = 0;

  private getContext(): AudioContext | null {
    if (typeof window === 'undefined') return null;
    if (!this.audioCtx) {
      const AudioCtxClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioCtxClass) {
        this.audioCtx = new AudioCtxClass();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
    return this.audioCtx;
  }

  public setMuted(muted: boolean) {
    this.isMuted = muted;
    if (muted && this.engineGain) {
      this.engineGain.gain.setValueAtTime(0, this.audioCtx?.currentTime || 0);
    }
  }

  public setVoiceEnabled(enabled: boolean) {
    this.voiceEnabled = enabled;
  }

  public setVolume(vol: number) {
    this.volume = Math.max(0, Math.min(1, vol));
  }

  public setPersona(persona: VoicePersona) {
    this.persona = persona;
  }

  public getPersona(): VoicePersona {
    return this.persona;
  }

  /**
   * Toggle V6 Turbo Hybrid engine RPM tone synth
   */
  public toggleEngineSound(rpm: number = 11500): boolean {
    const ctx = this.getContext();
    if (!ctx) return false;

    if (this.engineSoundEnabled) {
      this.stopEngineSound();
      this.engineSoundEnabled = false;
      return false;
    } else {
      this.startEngineSound(rpm);
      this.engineSoundEnabled = true;
      return true;
    }
  }

  private startEngineSound(rpm: number) {
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      // V6 frequency calculation: (RPM / 60) * 3 combustion pulses per rev
      const baseFreq = (rpm / 60) * 3;

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(baseFreq, ctx.currentTime);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(baseFreq * 2.2, ctx.currentTime);

      gain.gain.setValueAtTime(0.08 * this.volume, ctx.currentTime);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start();
      this.engineOsc = osc;
      this.engineGain = gain;
    } catch {}
  }

  private stopEngineSound() {
    try {
      if (this.engineOsc) {
        this.engineOsc.stop();
        this.engineOsc.disconnect();
        this.engineOsc = null;
      }
      if (this.engineGain) {
        this.engineGain.disconnect();
        this.engineGain = null;
      }
    } catch {}
  }

  public updateEngineRPM(rpm: number) {
    if (!this.engineSoundEnabled || !this.engineOsc || !this.audioCtx) return;
    const baseFreq = (rpm / 60) * 3;
    this.engineOsc.frequency.linearRampToValueAtTime(baseFreq, this.audioCtx.currentTime + 0.1);
  }

  /**
   * Play classic F1 team radio introductory chirp ("beep-boop") with radio static burst
   */
  public playRadioBleep() {
    if (this.isMuted) return;
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(1600, ctx.currentTime);
      filter.Q.setValueAtTime(1.5, ctx.currentTime);

      const now = ctx.currentTime;

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(1480, now);
      osc1.frequency.setValueAtTime(1860, now + 0.06);

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(740, now);
      osc2.frequency.setValueAtTime(930, now + 0.06);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.25 * this.volume, now + 0.02);
      gain.gain.setValueAtTime(0.25 * this.volume, now + 0.1);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);

      osc1.connect(filter);
      osc2.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 0.18);
      osc2.stop(now + 0.18);

      this.playStaticBurst(0.12);
    } catch {}
  }

  public playStaticBurst(durationS: number = 0.15) {
    if (this.isMuted) return;
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const bufferSize = ctx.sampleRate * durationS;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = Math.random() * 2 - 1;
      }

      const whiteNoise = ctx.createBufferSource();
      whiteNoise.buffer = buffer;

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(2200, ctx.currentTime);

      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.04 * this.volume, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + durationS);

      whiteNoise.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      whiteNoise.start(ctx.currentTime);
    } catch {}
  }

  public playWheelGunSound() {
    if (this.isMuted) return;
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(120, now);
      osc.frequency.linearRampToValueAtTime(320, now + 0.12);

      gain.gain.setValueAtTime(0.3 * this.volume, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.2);
    } catch {}
  }

  public playBoxAlarm() {
    if (this.isMuted) return;
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.25);

      gain.gain.setValueAtTime(0.2 * this.volume, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.3);
    } catch {}
  }

  public playSafetyCarAlert() {
    if (this.isMuted) return;
    try {
      const ctx = this.getContext();
      if (!ctx) return;

      const now = ctx.currentTime;
      for (let i = 0; i < 2; i++) {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const offset = i * 0.18;

        osc.type = 'square';
        osc.frequency.setValueAtTime(520, now + offset);
        osc.frequency.setValueAtTime(780, now + offset + 0.09);

        gain.gain.setValueAtTime(0.15 * this.volume, now + offset);
        gain.gain.exponentialRampToValueAtTime(0.001, now + offset + 0.16);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now + offset);
        osc.stop(now + offset + 0.17);
      }
    } catch {}
  }

  private formatPersonaMessage(rawText: string): string {
    if (this.persona === 'bono') {
      if (rawText.toLowerCase().includes('box')) {
        return `Box box box, box this lap. Hammer time.`;
      }
      return `Okay Lewis, ${rawText}`;
    }

    if (this.persona === 'gp') {
      if (rawText.toLowerCase().includes('box')) {
        return `Pit confirm, Max. Box this lap.`;
      }
      return `Max, ${rawText}. Keep managing the delta.`;
    }

    if (this.persona === 'xavi') {
      if (rawText.toLowerCase().includes('box')) {
        return `Box this lap for tyres, box now.`;
      }
      return `We are checking, ${rawText}. Plan A.`;
    }

    return rawText;
  }

  public speakRadioMessage(text: string) {
    if (this.isMuted || !this.voiceEnabled) return;
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;

    const formatted = this.formatPersonaMessage(text);
    const now = Date.now();
    if (this.lastSpokenMessage === formatted && now - this.lastSpokenTime < 10000) {
      return;
    }
    this.lastSpokenMessage = formatted;
    this.lastSpokenTime = now;

    try {
      this.playRadioBleep();

      setTimeout(() => {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(formatted);
        utterance.rate = 1.1;
        utterance.pitch = this.persona === 'bono' ? 0.95 : this.persona === 'gp' ? 1.05 : 1.0;
        utterance.volume = this.volume;

        const voices = window.speechSynthesis.getVoices();
        const englishVoice = voices.find(
          (v) =>
            v.lang.startsWith('en') &&
            (v.name.includes('Google') ||
              v.name.includes('Natural') ||
              v.name.includes('Samantha') ||
              v.name.includes('Daniel'))
        );
        if (englishVoice) {
          utterance.voice = englishVoice;
        }

        window.speechSynthesis.speak(utterance);
      }, 150);
    } catch {}
  }
}

export const audioEngine = new AudioEngine();
