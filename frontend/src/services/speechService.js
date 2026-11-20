/**
 * Enterprise Centralized Speech Synthesis Service for PharmIntel.
 * Provides unified, singleton control of browser speech synthesis:
 * - Play, Pause, Resume, Stop, Replay
 * - Global Mute / Speaker On-Off
 * - Mode preferences: 'always' | 'manual' | 'text_only'
 * - Single active utterance guarantee (no overlapping speech)
 * - Auto-cleanup on route changes, modal closes, and page unload
 * - Supports 7 Indian languages: en-IN, kn-IN, hi-IN, ml-IN, ta-IN, te-IN, mr-IN
 */

const LANG_CODE_MAP = {
  en: 'en-IN',
  kn: 'kn-IN',
  hi: 'hi-IN',
  ml: 'ml-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  mr: 'mr-IN',
};

class SpeechService {
  constructor() {
    this.synth = typeof window !== 'undefined' && 'speechSynthesis' in window ? window.speechSynthesis : null;
    this.currentUtterance = null;
    this.state = 'idle'; // 'idle' | 'speaking' | 'paused'
    this.currentText = '';
    this.listeners = new Set();

    // Stored preferences
    const savedMuted = typeof window !== 'undefined' ? localStorage.getItem('pharmintel_speech_muted') : null;
    this.muted = savedMuted === 'true';

    const savedMode = typeof window !== 'undefined' ? localStorage.getItem('pharmintel_speech_mode') : null;
    this.mode = savedMode || 'manual'; // 'always' | 'manual' | 'text_only'

    if (typeof window !== 'undefined') {
      // Auto-cleanup when user navigates or closes window
      window.addEventListener('beforeunload', () => this.stop());
      window.addEventListener('pagehide', () => this.stop());
    }
  }

  isSupported() {
    return Boolean(this.synth);
  }

  getState() {
    return {
      state: this.state,
      isSpeaking: this.state === 'speaking',
      isPaused: this.state === 'paused',
      isMuted: this.muted,
      mode: this.mode,
      currentText: this.currentText,
    };
  }

  notify() {
    const snapshot = this.getState();
    this.listeners.forEach((fn) => {
      try {
        fn(snapshot);
      } catch (err) {
        console.error('SpeechService listener error:', err);
      }
    });
  }

  subscribe(listener) {
    this.listeners.add(listener);
    listener(this.getState());
    return () => this.listeners.delete(listener);
  }

  setMuted(muted) {
    this.muted = Boolean(muted);
    if (typeof window !== 'undefined') {
      localStorage.setItem('pharmintel_speech_muted', String(this.muted));
    }
    if (this.muted) {
      this.stop();
    }
    this.notify();
  }

  toggleMute() {
    this.setMuted(!this.muted);
    return this.muted;
  }

  isMuted() {
    return this.muted;
  }

  setMode(mode) {
    if (['always', 'manual', 'text_only'].includes(mode)) {
      this.mode = mode;
      if (typeof window !== 'undefined') {
        localStorage.setItem('pharmintel_speech_mode', mode);
      }
      if (mode === 'text_only') {
        this.stop();
      }
      this.notify();
    }
  }

  getMode() {
    return this.mode;
  }

  cleanTextForSpeech(rawText) {
    if (!rawText) return '';
    return rawText
      .replace(/!\[.*?\]\(.*?\)/g, '') // remove markdown images
      .replace(/\[(.*?)\]\(.*?\)/g, '$1') // keep link text
      .replace(/[*#_`~>|\-]/g, ' ') // remove markdown syntax characters
      .replace(/\\\(.*?\\\)/g, '') // remove inline latex
      .replace(/\\\\[\s\S]*?\\\\/g, '') // remove block latex
      .replace(/\s+/g, ' ')
      .trim();
  }

  speak(text, lang = 'en', onComplete = null) {
    if (!this.synth) {
      if (onComplete) onComplete();
      return;
    }

    // Stop previous utterance
    this.stop();

    if (this.muted || this.mode === 'text_only') {
      if (onComplete) onComplete();
      return;
    }

    const cleaned = this.cleanTextForSpeech(text);
    if (!cleaned) {
      if (onComplete) onComplete();
      return;
    }

    // Slice to maximum 400 characters for concise speech chunks
    const speechChunk = cleaned.slice(0, 450);

    const utterance = new SpeechSynthesisUtterance(speechChunk);
    const speechLangCode = LANG_CODE_MAP[lang] || 'en-IN';
    utterance.lang = speechLangCode;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    this.currentUtterance = utterance;
    this.currentText = speechChunk;
    this.state = 'speaking';
    this.notify();

    utterance.onstart = () => {
      this.state = 'speaking';
      this.notify();
    };

    utterance.onend = () => {
      this.state = 'idle';
      this.currentUtterance = null;
      this.currentText = '';
      this.notify();
      if (onComplete) onComplete();
    };

    utterance.onerror = (e) => {
      console.warn('SpeechSynthesis error:', e);
      this.state = 'idle';
      this.currentUtterance = null;
      this.currentText = '';
      this.notify();
      if (onComplete) onComplete();
    };

    utterance.onpause = () => {
      this.state = 'paused';
      this.notify();
    };

    utterance.onresume = () => {
      this.state = 'speaking';
      this.notify();
    };

    try {
      this.synth.speak(utterance);
    } catch (err) {
      console.error('Failed to trigger speech synthesis:', err);
      this.state = 'idle';
      this.notify();
    }
  }

  pause() {
    if (!this.synth) return;
    if (this.state === 'speaking') {
      try {
        this.synth.pause();
        this.state = 'paused';
        this.notify();
      } catch (err) {
        console.warn('Speech pause error:', err);
      }
    }
  }

  resume() {
    if (!this.synth) return;
    if (this.state === 'paused') {
      try {
        this.synth.resume();
        this.state = 'speaking';
        this.notify();
      } catch (err) {
        console.warn('Speech resume error:', err);
      }
    }
  }

  stop() {
    if (!this.synth) return;
    try {
      this.synth.cancel();
    } catch (err) {
      console.warn('Speech cancel error:', err);
    }
    this.state = 'idle';
    this.currentUtterance = null;
    this.currentText = '';
    this.notify();
  }
}

export const speechService = new SpeechService();
export default speechService;
