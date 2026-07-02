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
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dsp::OnePole;
    use crate::voices;

    #[test]
    fn banks_parse() {
        for z in violin_f().iter().chain(violin_p()).chain(flute()) {
            assert!(z.data.len() > 20_000, "zone too short: {}", z.data.len());
            assert!((100.0..2500.0).contains(&z.root), "odd root {}", z.root);
            let peak = z.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(peak > 0.5, "zone not normalised: peak {peak}");
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

    /// The sampled attack must hand over to the model without a level jump.
    #[test]
    fn la_level_continuity() {
        let sr = 44100.0;
        for (program, name) in [(40u8, "fiddle"), (73u8, "flute")] {
            let mut v = voices::make(program, 69, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100]; // 1 s, note held
            v.render(&mut buf);
            let rms = |a: usize, b: usize| {
                (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
            };
            // 100 ms windows from 50 ms to 950 ms
            let w: Vec<f32> = (0..9)
                .map(|k| rms(2205 + k * 4410, 2205 + (k + 1) * 4410))
                .collect();
            let hi = w.iter().cloned().fold(0.0f32, f32::max);
            let lo = w.iter().cloned().fold(f32::INFINITY, f32::min);
            assert!(
                hi / lo < 3.0,
                "{name}: level jump across the crossfade: {w:?}"
            );
        }
    }
}
