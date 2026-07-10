//! LA-style sample layer — the Roland D-50 trick: a short PCM attack
//! transient supplies the first ~200 ms (the bow bite, the breath chiff —
//! exactly what synthesis fakes worst), then crossfades into the modeled
//! sustain, which keeps all its expressive vibrato, scoop and dynamics.
//!
//! The transients are trimmed from VSCO 2 Community Edition (CC0 / public
//! domain) sustains and embedded in the binary, so the tool remains a
//! single self-contained executable. Each zone's root frequency was
//! measured by autocorrelation, so repitching is cent-accurate.

use crate::dsp::{key_freq, vel_amp};
use crate::voices::Voice;
use std::sync::OnceLock;

pub struct Zone {
    root: f32,
    data: Vec<f32>,
}

pub struct HitSample {
    data: Vec<f32>,
}

/// Minimal RIFF walker for the bank's own files (16-bit mono 44.1 kHz).
fn parse_wav(bytes: &[u8]) -> Vec<f32> {
    assert!(&bytes[0..4] == b"RIFF" && &bytes[8..12] == b"WAVE");
    let mut pos = 12;
    let mut data = Vec::new();
    while pos + 8 <= bytes.len() {
        let id = &bytes[pos..pos + 4];
        let len = u32::from_le_bytes(bytes[pos + 4..pos + 8].try_into().unwrap()) as usize;
        let body = &bytes[pos + 8..(pos + 8 + len).min(bytes.len())];
        if id == b"fmt " {
            let channels = u16::from_le_bytes(body[2..4].try_into().unwrap());
            let sr = u32::from_le_bytes(body[4..8].try_into().unwrap());
            let bits = u16::from_le_bytes(body[14..16].try_into().unwrap());
            assert!(
                channels == 1 && sr == 44100 && bits == 16,
                "sample bank must be 16-bit mono 44.1 kHz"
            );
        } else if id == b"data" {
            data = body
                .chunks_exact(2)
                .map(|c| i16::from_le_bytes([c[0], c[1]]) as f32 / 32768.0)
                .collect();
        }
        pos += 8 + len + (len & 1);
    }
    assert!(!data.is_empty(), "sample bank file has no data chunk");
    data
}

macro_rules! bank {
    ($($file:literal => $root:expr),+ $(,)?) => {
        vec![$(Zone {
            root: $root,
            data: parse_wav(include_bytes!(concat!("../samples/", $file))),
        }),+]
    };
}

macro_rules! hit_bank {
    ($($file:literal),+ $(,)?) => {
        vec![$(HitSample {
            data: parse_wav(include_bytes!(concat!("../samples/", $file))),
        }),+]
    };
}

// Roots measured by autocorrelation in the prep script (see samples/README.md).
fn violin_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "violin_G3_f.wav" => 196.00,
            "violin_E4_f.wav" => 329.33,
            "violin_C5_f.wav" => 519.94,
            "violin_G5_f.wav" => 786.90,
            "violin_C6_f.wav" => 1040.45,
            "violin_E6_f.wav" => 1329.58,
        )
    })
}

fn violin_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "violin_G3_p.wav" => 195.11,
            "violin_E4_p.wav" => 329.51,
            "violin_C5_p.wav" => 521.61,
            "violin_G5_p.wav" => 787.21,
            "violin_C6_p.wav" => 1045.77,
            "violin_E6_p.wav" => 1320.88,
        )
    })
}

fn flute() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "flute_C4.wav" => 523.23,
            "flute_A4.wav" => 879.92,
            "flute_E5.wav" => 1320.47,
            "flute_A5.wav" => 1757.81,
            "flute_C6.wav" => 2091.31,
        )
    })
}

fn piano_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_pp.wav" => 65.05,
            "piano_G2_pp.wav" => 97.77,
            "piano_C3_pp.wav" => 130.68,
            "piano_G3_pp.wav" => 195.31,
            "piano_C4_pp.wav" => 261.04,
            "piano_G4_pp.wav" => 393.15,
            "piano_C5_pp.wav" => 523.65,
            "piano_G5_pp.wav" => 784.41,
            "piano_C6_pp.wav" => 1051.84,
        )
    })
}

fn piano_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_mf.wav" => 65.17,
            "piano_G2_mf.wav" => 98.10,
            "piano_C3_mf.wav" => 130.94,
            "piano_G3_mf.wav" => 196.23,
            "piano_C4_mf.wav" => 261.25,
            "piano_G4_mf.wav" => 393.58,
            "piano_C5_mf.wav" => 524.52,
            "piano_G5_mf.wav" => 785.35,
            "piano_C6_mf.wav" => 1050.22,
        )
    })
}

fn piano_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_f.wav" => 65.52,
            "piano_G2_f.wav" => 98.33,
            "piano_C3_f.wav" => 131.19,
            "piano_G3_f.wav" => 195.73,
            "piano_C4_f.wav" => 261.74,
            "piano_G4_f.wav" => 393.96,
            "piano_C5_f.wav" => 525.21,
            "piano_G5_f.wav" => 786.26,
            "piano_C6_f.wav" => 1050.00,
        )
    })
}

fn piano_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_pp_rr2.wav" => 65.05,
            "piano_G2_pp_rr2.wav" => 97.77,
            "piano_C3_pp_rr2.wav" => 130.60,
            "piano_G3_pp_rr2.wav" => 194.91,
            "piano_C4_pp_rr2.wav" => 261.00,
            "piano_G4_pp_rr2.wav" => 392.77,
            "piano_C5_pp_rr2.wav" => 523.95,
            "piano_G5_pp_rr2.wav" => 784.04,
            "piano_C6_pp_rr2.wav" => 1049.08,
        )
    })
}

fn piano_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_mf_rr2.wav" => 65.51,
            "piano_G2_mf_rr2.wav" => 98.28,
            "piano_C3_mf_rr2.wav" => 131.12,
            "piano_G3_mf_rr2.wav" => 196.23,
            "piano_C4_mf_rr2.wav" => 261.29,
            "piano_G4_mf_rr2.wav" => 393.76,
            "piano_C5_mf_rr2.wav" => 524.92,
            "piano_G5_mf_rr2.wav" => 785.18,
            "piano_C6_mf_rr2.wav" => 1049.43,
        )
    })
}

fn piano_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_f_rr2.wav" => 65.58,
            "piano_G2_f_rr2.wav" => 98.43,
            "piano_C3_f_rr2.wav" => 131.20,
            "piano_G3_f_rr2.wav" => 196.39,
            "piano_C4_f_rr2.wav" => 261.73,
            "piano_G4_f_rr2.wav" => 393.77,
            "piano_C5_f_rr2.wav" => 525.19,
            "piano_G5_f_rr2.wav" => 786.16,
            "piano_C6_f_rr2.wav" => 1050.12,
        )
    })
}

fn trumpet_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trumpet_F2_p.wav" => 174.88,
            "trumpet_C3_p.wav" => 259.21,
            "trumpet_G3_p.wav" => 392.78,
            "trumpet_D4_p.wav" => 586.53,
            "trumpet_A4_p.wav" => 877.64,
        )
    })
}

fn trumpet_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trumpet_F2_f.wav" => 172.61,
            "trumpet_C3_f.wav" => 261.15,
            "trumpet_G3_f.wav" => 393.83,
            "trumpet_D4_f.wav" => 588.04,
            "trumpet_A4_f.wav" => 886.84,
        )
    })
}

fn mutetpt_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "mutetpt_A#2_p.wav" => 232.97,
            "mutetpt_D3_p.wav" => 293.86,
            "mutetpt_G3_p.wav" => 392.99,
            "mutetpt_D4_p.wav" => 586.63,
            "mutetpt_A4_p.wav" => 880.37,
        )
    })
}

fn mutetpt_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "mutetpt_A#2_f.wav" => 233.07,
            "mutetpt_D3_f.wav" => 293.30,
            "mutetpt_G3_f.wav" => 392.47,
            "mutetpt_D4_f.wav" => 586.39,
            "mutetpt_A4_f.wav" => 880.34,
        )
    })
}

fn trombone_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trombone_F1_p.wav" => 87.34,
            "trombone_A#1_p.wav" => 116.31,
            "trombone_D2_p.wav" => 146.73,
            "trombone_F2_p.wav" => 174.45,
            "trombone_C3_p.wav" => 261.43,
            "trombone_F3_p.wav" => 349.09,
        )
    })
}

fn trombone_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trombone_F1_f.wav" => 87.21,
            "trombone_A#1_f.wav" => 116.56,
            "trombone_D2_f.wav" => 146.73,
            "trombone_F2_f.wav" => 174.53,
            "trombone_C3_f.wav" => 261.56,
            "trombone_F3_f.wav" => 349.05,
        )
    })
}

fn tuba_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "tuba_A#0_p.wav" => 58.01,
            "tuba_D#1_p.wav" => 78.25,
            "tuba_A#1_p.wav" => 116.03,
            "tuba_D2_p.wav" => 146.34,
            "tuba_F2_p.wav" => 174.46,
            "tuba_A#2_p.wav" => 231.99,
        )
    })
}

fn tuba_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "tuba_A#0_f.wav" => 58.35,
            "tuba_D#1_f.wav" => 77.78,
            "tuba_A#1_f.wav" => 116.34,
            "tuba_D2_f.wav" => 145.88,
            "tuba_F2_f.wav" => 174.42,
            "tuba_A#2_f.wav" => 233.19,
        )
    })
}

fn horn_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "horn_A#1_p.wav" => 116.90,
            "horn_D2_p.wav" => 148.36,
            "horn_F2_p.wav" => 173.95,
            "horn_A2_p.wav" => 219.46,
            "horn_C3_p.wav" => 260.59,
            "horn_D4_p.wav" => 604.11,
        )
    })
}

fn horn_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "horn_A#1_f.wav" => 116.81,
            "horn_D2_f.wav" => 146.41,
            "horn_F2_f.wav" => 173.93,
            "horn_A2_f.wav" => 219.08,
            "horn_C3_f.wav" => 260.84,
            "horn_D4_f.wav" => 604.11,
        )
    })
}

fn drum_crash() -> &'static [HitSample] {
    static B: OnceLock<Vec<HitSample>> = OnceLock::new();
    B.get_or_init(|| {
        hit_bank!(
            "drum_sus_cymb1_mp_rr1.wav",
            "drum_sus_cymb1_mp_rr2.wav",
            "drum_crash1_ff_rr1.wav",
            "drum_crash1_ff_rr2.wav",
        )
    })
}

fn drum_kick() -> &'static [HitSample] {
    static B: OnceLock<Vec<HitSample>> = OnceLock::new();
    B.get_or_init(|| hit_bank!("drum_kick_v3_rr1.wav", "drum_kick_v3_rr2.wav"))
}

fn drum_snare() -> &'static [HitSample] {
    static B: OnceLock<Vec<HitSample>> = OnceLock::new();
    B.get_or_init(|| hit_bank!("drum_snare2_v5_rr1.wav", "drum_snare2_v5_rr2.wav"))
}

/// Velocity picks the dynamic layer; alternating round robins keep
/// repeated notes from being byte-identical (the machine-gun tell).
pub fn piano_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => piano_pp(),
        (0..=51, true) => piano_pp_rr2(),
        (52..=95, false) => piano_mf(),
        (52..=95, true) => piano_mf_rr2(),
        (_, false) => piano_f(),
        (_, true) => piano_f_rr2(),
    }
}

pub fn violin_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        violin_f()
    } else {
        violin_p()
    }
}

pub fn flute_bank() -> &'static [Zone] {
    flute()
}

/// Bank for the layered brass programs (GM 56–61). Velocity picks the
/// dynamic layer (VSCO v1 → p, v3 → f, threshold as `violin_bank`);
/// 61 (section) shares the trumpet bank at reduced wrap gain.
pub fn brass_bank(program: u8, vel: u8) -> &'static [Zone] {
    let f = vel >= 80;
    match program {
        57 => {
            if f {
                trombone_f()
            } else {
                trombone_p()
            }
        }
        58 => {
            if f {
                tuba_f()
            } else {
                tuba_p()
            }
        }
        59 => {
            if f {
                mutetpt_f()
            } else {
                mutetpt_p()
            }
        }
        60 => {
            if f {
                horn_f()
            } else {
                horn_p()
            }
        }
        _ => {
            if f {
                trumpet_f()
            } else {
                trumpet_p()
            }
        }
    }
}

pub fn drum_crash_bank() -> &'static [HitSample] {
    drum_crash()
}

pub fn drum_kick_bank() -> &'static [HitSample] {
    drum_kick()
}

pub fn drum_snare_bank() -> &'static [HitSample] {
    drum_snare()
}

pub fn prewarm() {
    let _ = piano_bank(1, false);
    let _ = piano_bank(1, true);
    let _ = piano_bank(80, false);
    let _ = piano_bank(80, true);
    let _ = piano_bank(127, false);
    let _ = piano_bank(127, true);
    let _ = violin_bank(1);
    let _ = violin_bank(127);
    let _ = flute_bank();
    for program in 56..=60 {
        let _ = brass_bank(program, 1);
        let _ = brass_bank(program, 127);
    }
    let _ = drum_crash_bank();
    let _ = drum_kick_bank();
    let _ = drum_snare_bank();
}

fn nearest(zones: &'static [Zone], f: f32) -> &'static Zone {
    zones
        .iter()
        .min_by(|a, b| {
            let da = (a.root / f).ln().abs();
            let db = (b.root / f).ln().abs();
            da.partial_cmp(&db).unwrap()
        })
        .unwrap()
}

#[inline]
fn smooth(x: f32) -> f32 {
    let x = x.clamp(0.0, 1.0);
    x * x * (3.0 - 2.0 * x)
}

/// Sampled attack + modeled sustain. The sustain fades in over
/// `[0, fade_end]` while the transient fades out over `[fade_start,
/// fade_end]`, so the model's own (weaker) onset is masked by the real one.
pub struct LaVoice {
    sustain: Box<dyn Voice>,
    zone: &'static Zone,
    pos: f32,
    step: f32,
    base_step: f32,
    gain: f32,
    rel_gain: f32,
    rel_mul: f32,
    rel_t60_mul: f32,
    t: usize,
    fade_start: usize,
    fade_end: usize,
    buf: Vec<f32>,
}

impl LaVoice {
    /// Wrap `sustain`; falls back to the bare model when the target is too
    /// far outside the sampled range for a credible repitch.
    pub fn wrap(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
    ) -> Box<dyn Voice> {
        let f = key_freq(key);
        let zone = nearest(zones, f);
        let step = f / zone.root * 44100.0 / sr;
        if !(0.5..=2.05).contains(&step) {
            return sustain;
        }
        Box::new(LaVoice {
            sustain,
            zone,
            pos: 0.0,
            step,
            base_step: step,
            gain: gain * (0.35 + 0.65 * vel_amp(vel)),
            rel_gain: 1.0,
            rel_mul: 1.0,
            rel_t60_mul: 10f32.powf(-3.0 / (0.06 * sr)),
            t: 0,
            fade_start: (fade.0 * sr) as usize,
            fade_end: (fade.1 * sr) as usize,
            buf: Vec::new(),
        })
    }
}

impl Voice for LaVoice {
    fn render(&mut self, out: &mut [f32]) -> bool {
        self.buf.resize(out.len(), 0.0);
        self.buf.fill(0.0);
        let sustain_alive = self.sustain.render(&mut self.buf);
        let n = self.zone.data.len();
        let fade_len = (self.fade_end - self.fade_start).max(1) as f32;
        let mut sample_live = false;
        for (i, o) in out.iter_mut().enumerate() {
            let t = self.t + i;
            let mut s = self.buf[i] * smooth(t as f32 / self.fade_end as f32);
            let j = self.pos as usize;
            if j + 1 < n && self.rel_gain > 0.0005 {
                sample_live = true;
                let frac = self.pos - j as f32;
                let v = self.zone.data[j] * (1.0 - frac) + self.zone.data[j + 1] * frac;
                let ag = 1.0 - smooth((t as f32 - self.fade_start as f32) / fade_len);
                s += v * ag * self.gain * self.rel_gain;
                self.rel_gain *= self.rel_mul;
                self.pos += self.step;
            }
            *o += s;
        }
        self.t += out.len();
        sustain_alive || sample_live
    }

    fn note_off(&mut self) {
        self.sustain.note_off();
        // let the transient die quickly (~60 ms T60) on early releases
        self.rel_mul = self.rel_t60_mul;
    }

    fn released(&self) -> bool {
        self.sustain.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        // bend the transient with the note, and the model underneath
        self.step = self.base_step * mult;
        self.sustain.set_pitch(mult);
    }

    fn legato_to(&mut self, key: u8, vel: u8) -> bool {
        // a slur has no fresh attack: retire the transient, glide the model
        if self.sustain.legato_to(key, vel) {
            self.rel_mul = self.rel_t60_mul;
            true
        } else {
            false
        }
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        // the LA wrapper is transparent for routing: report the model inside
        self.sustain.kind()
    }

    fn set_trem(&mut self, rate_hz: f32, depth: f32) {
        self.sustain.set_trem(rate_hz, depth);
    }
}

/// Unpitched drum sample overlay. The model remains the sustaining voice; the
/// sample contributes only a short attack/body cue and obeys the same routing
/// controls as the wrapped model.
pub struct SampleOverlay {
    model: Box<dyn Voice>,
    sample: &'static HitSample,
    pos: f32,
    step: f32,
    gain: f32,
    rel_gain: f32,
    rel_mul: f32,
    rel_t60_mul: f32,
    buf: Vec<f32>,
}

impl SampleOverlay {
    pub fn wrap(
        model: Box<dyn Voice>,
        bank: &'static [HitSample],
        vel: u8,
        seed: u32,
        sr: f32,
        gain: f32,
    ) -> Box<dyn Voice> {
        let sample = &bank[(seed as usize) % bank.len()];
        Box::new(Self {
            model,
            sample,
            pos: 0.0,
            step: 44100.0 / sr,
            gain: gain * (0.35 + 0.65 * vel_amp(vel)),
            rel_gain: 1.0,
            rel_mul: 1.0,
            rel_t60_mul: 10f32.powf(-3.0 / (0.018 * sr)),
            buf: Vec::new(),
        })
    }
}

impl Voice for SampleOverlay {
    fn render(&mut self, out: &mut [f32]) -> bool {
        self.buf.resize(out.len(), 0.0);
        self.buf.fill(0.0);
        let model_alive = self.model.render(&mut self.buf);
        let mut sample_live = false;
        let n = self.sample.data.len();
        for (i, o) in out.iter_mut().enumerate() {
            let mut s = self.buf[i];
            let j = self.pos as usize;
            if j + 1 < n && self.rel_gain > 0.0005 {
                sample_live = true;
                let frac = self.pos - j as f32;
                let v = self.sample.data[j] * (1.0 - frac) + self.sample.data[j + 1] * frac;
                s += v * self.gain * self.rel_gain;
                self.rel_gain *= self.rel_mul;
                self.pos += self.step;
            }
            *o += s;
        }
        model_alive || sample_live
    }

    fn note_off(&mut self) {
        self.model.note_off();
        self.rel_mul = self.rel_t60_mul;
    }

    fn released(&self) -> bool {
        self.model.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        self.model.set_pitch(mult);
    }

    fn legato_to(&mut self, key: u8, vel: u8) -> bool {
        if self.model.legato_to(key, vel) {
            self.rel_mul = self.rel_t60_mul;
            true
        } else {
            false
        }
    }

    fn choke(&mut self) {
        self.model.choke();
        self.rel_mul = self.rel_t60_mul;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        self.model.kind()
    }

    fn set_trem(&mut self, rate_hz: f32, depth: f32) {
        self.model.set_trem(rate_hz, depth);
    }

    fn set_vowel(&mut self, freqs: [f32; 3], qs: [f32; 3], gains: [f32; 3]) {
        self.model.set_vowel(freqs, qs, gains);
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        self.model.set_breath(pressure, growl);
    }

    fn set_vib(&mut self, depth: f32) {
        self.model.set_vib(depth);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dsp::OnePole;
    use crate::voices;

    #[test]
    fn banks_parse() {
        for z in violin_f()
            .iter()
            .chain(violin_p())
            .chain(flute())
            .chain(piano_pp())
            .chain(piano_mf())
            .chain(piano_f())
            .chain(piano_pp_rr2())
            .chain(piano_mf_rr2())
            .chain(piano_f_rr2())
            .chain(trumpet_p())
            .chain(trumpet_f())
            .chain(mutetpt_p())
            .chain(mutetpt_f())
            .chain(trombone_p())
            .chain(trombone_f())
            .chain(tuba_p())
            .chain(tuba_f())
            .chain(horn_p())
            .chain(horn_f())
        {
            assert!(z.data.len() > 20_000, "zone too short: {}", z.data.len());
            // the tuba bank reaches A#0 (~29 Hz), hence the low floor
            assert!((25.0..2500.0).contains(&z.root), "odd root {}", z.root);
            let peak = z.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(peak > 0.5, "zone not normalised: peak {peak}");
        }
        for h in drum_crash().iter().chain(drum_kick()).chain(drum_snare()) {
            assert!(
                h.data.len() > 8_000,
                "drum sample too short: {}",
                h.data.len()
            );
            let peak = h.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(peak > 0.5, "drum sample not normalised: peak {peak}");
        }
    }

    fn pitch_of(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(600.0, sr);
        let mut lp2 = OnePole::lowpass(600.0, sr);
        let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        let mut c = 0;
        for w in f.windows(2) {
            if w[0] <= 0.0 && w[1] > 0.0 {
                c += 1;
            }
        }
        c as f32 / (seg.len() as f32 / sr)
    }

    /// The LA fiddle at A4 must sound at 440 Hz straight through the
    /// crossfade — the repitched sample and the model have to agree.
    #[test]
    fn la_pitch_a4() {
        let sr = 44100.0;
        let mut v = voices::make(40, 69, 100, sr, 5, true);
        let mut buf = vec![0f32; 44100];
        v.render(&mut buf);
        let hz = pitch_of(&buf[6615..24255], sr); // 0.15 s – 0.55 s
        assert!((hz - 440.0).abs() < 12.0, "measured {hz} Hz");
    }

    /// The brass sample layer must not shift perceived pitch: Goertzel peak
    /// through the crossfade window (zero-crossing counters lie when a layer
    /// brightens a voice — lessons_learnt 2026.07.07).
    #[test]
    fn la_brass_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (56u8, 69u8, "trumpet"),
            (57, 55, "trombone"),
            (58, 40, "tuba"),
            (59, 69, "muted-trumpet"),
            (60, 62, "french-horn"),
            (61, 69, "brass-section"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15–0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The layer must be audible, not just present (lessons_learnt
    /// 2026.07.06): samples-on vs samples-off of the same note must differ
    /// materially in the first 50 ms, and for the bright programs the real
    /// attack must raise the high-band fraction (the sampled bite) over the
    /// model's synthetic chiff. The french horn is exempt from the HF check:
    /// its hand-in-bell attack is genuinely dark (measured on ≈ off).
    #[test]
    fn la_brass_attack_sharpness() {
        let sr = 44100.0;
        for (program, key, hf_gain, name) in [
            (56u8, 69u8, 1.5f32, "trumpet"),
            (57, 55, 1.3, "trombone"),
            (58, 40, 2.0, "tuba"),
            (59, 69, 1.3, "muted-trumpet"),
            (60, 62, 0.0, "french-horn"),
            (61, 69, 1.05, "brass-section"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on > r_off * hf_gain,
                "{name}: attack not sharper: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The sampled attack must hand over to the model without a level jump.
    #[test]
    fn la_level_continuity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (40u8, 69u8, "fiddle"),
            (110u8, 69, "fiddle-110"),
            (73u8, 69, "flute"),
            (0u8, 69, "piano"),
            (56u8, 69, "trumpet"),
            (57u8, 55, "trombone"),
            (58u8, 40, "tuba"),
            (59u8, 69, "muted-trumpet"),
            (60u8, 62, "french-horn"),
            (61u8, 69, "brass-section"),
        ] {
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100]; // 1 s, note held
            v.render(&mut buf);
            let rms = |a: usize, b: usize| {
                (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
            };
            // 100 ms windows from 50 ms to 950 ms; a natural decay is fine,
            // but no adjacent pair may jump (a bad handover is a step)
            let w: Vec<f32> = (0..9)
                .map(|k| rms(2205 + k * 4410, 2205 + (k + 1) * 4410))
                .collect();
            for pair in w.windows(2) {
                let ratio = (pair[0] / pair[1]).max(pair[1] / pair[0]);
                assert!(
                    ratio < 2.4,
                    "{name}: level jump across the crossfade: {w:?}"
                );
            }
        }
    }

    #[test]
    fn drum_sample_overlay_is_finite_and_forwards_controls() {
        let sr = 44100.0;
        let model = voices::make(0, 60, 100, sr, 5, false);
        let want_kind = model.kind();
        let mut v = SampleOverlay::wrap(model, drum_kick_bank(), 110, 5, sr, 0.05);
        v.set_pitch(1.01);
        assert_eq!(v.kind(), want_kind);
        v.choke();
        let mut buf = vec![0f32; (0.1 * sr) as usize];
        v.render(&mut buf);
        assert!(buf.iter().all(|x| x.is_finite()));
        assert!(buf.iter().any(|&x| x.abs() > 1e-5));
    }
}
