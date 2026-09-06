// Tactile Mechanical & Hardware Synthesizer for Silicon Test Bench (Zero Dependencies)
let audioCtx = null;
let soundEnabled = false;

// Initialize or resume audio context safely on user gesture
function getAudioContext() {
  if (typeof window === 'undefined') return null;
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

export function isAudioEnabled() {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('sentinel_sound_enabled');
    if (saved !== null) {
      soundEnabled = saved === 'true';
    }
  }
  return soundEnabled;
}

export function setAudioEnabled(enabled) {
  soundEnabled = enabled;
  if (typeof window !== 'undefined') {
    localStorage.setItem('sentinel_sound_enabled', enabled ? 'true' : 'false');
  }
  if (enabled) {
    getAudioContext();
    playMechanicalClick();
  }
}

// 1. Mechanical Relay Click (for socket clicks, buttons, switch toggles)
export function playMechanicalClick() {
  if (!isAudioEnabled()) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    
    // First high-frequency impact micro-click
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(2200, now);
    osc1.frequency.exponentialRampToValueAtTime(600, now + 0.008);
    
    gain1.gain.setValueAtTime(0.04, now);
    gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.009);
    
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    
    osc1.start(now);
    osc1.stop(now + 0.01);

    // Second deeper relay body resonance
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(320, now + 0.004);
    osc2.frequency.exponentialRampToValueAtTime(110, now + 0.016);
    
    gain2.gain.setValueAtTime(0.025, now + 0.004);
    gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.018);
    
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    
    osc2.start(now + 0.004);
    osc2.stop(now + 0.02);
  } catch (e) {
    // Ignore audio errors gracefully
  }
}

// 2. High-Tech Precision Tick (for hover, arrow key stepper)
export function playTick() {
  if (!isAudioEnabled()) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(3400, now);
    osc.frequency.exponentialRampToValueAtTime(1800, now + 0.005);

    gain.gain.setValueAtTime(0.015, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.006);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.007);
  } catch (e) {}
}

// 3. Calibration Sweep Chime (for 168h outcome reveal / mode change)
export function playSweepChime() {
  if (!isAudioEnabled()) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(1760, now + 0.06);

    gain.gain.setValueAtTime(0.03, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + 0.1);
  } catch (e) {}
}
