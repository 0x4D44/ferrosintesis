//! GM percussion (channel 10). Every hit is a small parametric voice:
//! decaying sine partials (with downward pitch glide for membranes, and
//! dense inharmonic stacks for cymbals) plus up to two filtered noise bands
//! (e.g. snare shell + snare wires). Hits vary: frequencies and decays are
//! jittered per strike, and harder hits are brighter.

use crate::dsp::{vel_amp, Biquad, Rng};
use crate::voices::Voice;
use std::f32::consts::TAU;

struct Tone {
    phase: f32,
    freq: f32,
    glide: f32, // per-sample frequency multiplier (1.0 = none)
    min_freq: f32,
    amp: f32,
    decay: f32,
}

struct NoiseBand {
    amp: f32,
    decay: f32,
    filt: Biquad,
}

pub struct Drum {
    tones: Vec<Tone>,
    noise: Vec<NoiseBand>,
    bursts: Vec<(u32, f32)>, // noise re-triggers (offset samples, amp)
    rng: Rng,
    t: u32,
    life: u32,
    gain: f32,
    sr: f32,
}

fn dmul(t60: f32, sr: f32) -> f32 {
    10f32.powf(-3.0 / (t60.max(0.005) * sr))
}

impl Drum {
    #[allow(clippy::too_many_arguments)]
    fn new(
        sr: f32,
        seed: u32,
        tones: &[(f32, f32, f32, f32)], // (freq, amp, T60, glide octaves/sec down)
        noise: &[(f32, f32, Biquad)],   // (amp, T60, filter)
        life_s: f32,
        gain: f32,
    ) -> Self {
        let mut rng = Rng::new(seed);
        // per-strike variation: nothing repeats exactly
        let jf = 1.0 + 0.03 * rng.white();
        let jd = 1.0 + 0.10 * rng.white();
        let tones = tones
            .iter()
            .map(|&(f, a, t, glide_oct_per_s)| Tone {
                phase: rng.white() * TAU,
                freq: f * jf,
                glide: if glide_oct_per_s > 0.0 {
                    2f32.powf(-glide_oct_per_s / sr)
                } else {
                    1.0
                },
                min_freq: f * jf * 0.3,
                amp: a,
                decay: dmul(t * jd, sr),
            })
            .collect();
        let noise = noise
            .iter()
            .map(|&(amp, t, filt)| NoiseBand {
                amp,
                decay: dmul(t * jd, sr),
                filt,
            })
            .collect();
        Drum {
            tones,
            noise,
            bursts: Vec::new(),
            rng,
            t: 0,
            life: (life_s * sr) as u32,
            gain,
            sr,
        }
    }

    fn with_bursts(mut self, bursts: &[(f32, f32)]) -> Self {
        self.bursts = bursts
            .iter()
            .map(|&(sec, amp)| ((sec * self.sr) as u32, amp))
            .collect();
        self
    }
}

impl Voice for Drum {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t >= self.life {
                return false;
            }
            let mut s = 0.0;
            for tone in &mut self.tones {
                s += tone.amp * tone.phase.sin();
                tone.phase += TAU * tone.freq / self.sr;
                if tone.phase > TAU {
                    tone.phase -= TAU;
                }
                if tone.glide < 1.0 && tone.freq > tone.min_freq {
                    tone.freq *= tone.glide;
                }
                tone.amp *= tone.decay;
            }
            for &(offset, amp) in &self.bursts {
                if self.t == offset {
                    for band in &mut self.noise {
                        band.amp = band.amp.max(amp);
                    }
                }
            }
            let white = self.rng.white();
            for band in &mut self.noise {
                if band.amp > 1e-5 {
                    s += band.filt.process(white) * band.amp;
                    band.amp *= band.decay;
                }
            }
            *o += s * self.gain;
            self.t += 1;
        }
        true
    }

    fn note_off(&mut self) {} // percussion ignores note-off

    fn released(&self) -> bool {
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "drum"
    }
}

/// D1 velocity→timbre for membrane voices (HLD family A, §3.3): a harder hit
/// starts slightly sharper, glides down faster, rings longer, and carries
/// proportionally more click/noise energy (the 0.5 floor preserves ghost
/// notes). Applied ONLY to membrane keys — cymbals keep their own `velnorm`
/// handling (the V4 apply-once rule).
#[allow(clippy::type_complexity)]
fn membrane_velocity(
    tones: &[(f32, f32, f32, f32)],
    noise: &[(f32, f32, Biquad)],
    vn: f32,
) -> (Vec<(f32, f32, f32, f32)>, Vec<(f32, f32, Biquad)>) {
    let tones = tones
        .iter()
        .map(|&(f, a, t, glide)| {
            (
                f * (1.0 + 0.03 * vn),
                a,
                t * (0.85 + 0.30 * vn),
                glide * (0.6 + 0.8 * vn),
            )
        })
        .collect();
    let noise = noise
        .iter()
        .map(|&(a, t, filt)| (a * (0.5 + 0.5 * vn * vn), t, filt))
        .collect();
    (tones, noise)
}

/// Inharmonic cymbal partial stack — the classic bell-plate ratios.
const METAL_RATIOS: [f32; 6] = [1.0, 1.483, 1.932, 2.546, 3.363, 4.365];

#[allow(clippy::too_many_arguments)]
fn cymbal(
    sr: f32,
    seed: u32,
    vel: u8,
    base: f32,
    tone_amp: f32,
    t60_first: f32,
    t60_last: f32,
    noise: (f32, f32, f32), // (amp, T60, highpass cutoff)
    life: f32,
    gain: f32,
) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let mut tones = Vec::with_capacity(6);
    for (i, &r) in METAL_RATIOS.iter().enumerate() {
        let frac = i as f32 / (METAL_RATIOS.len() - 1) as f32;
        let amp = tone_amp * (1.0 - 0.6 * frac) * (0.55 + 0.55 * velnorm.powf(frac + 0.5));
        let t60 = t60_first + (t60_last - t60_first) * frac;
        tones.push((base * r, amp, t60, 0.0));
    }
    // harder hits open the wash up higher
    let hp = noise.2 * (0.85 + 0.35 * velnorm);
    let bands = [(noise.0, noise.1, Biquad::highpass(hp, 0.7, sr))];
    Some(Box::new(Drum::new(
        sr,
        seed,
        &tones,
        &bands,
        life,
        gain * v,
    )))
}

/// Build a drum voice for a GM key, or None for unmapped keys.
pub fn make(key: u8, vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let d = |tones: &[(f32, f32, f32, f32)], noise: &[(f32, f32, Biquad)], life: f32, g: f32| {
        Some(Box::new(Drum::new(sr, seed, tones, noise, life, g * v)) as Box<dyn Voice>)
    };
    // membrane variant: the D1 velocity→timbre transform, then the same build
    let dm = |tones: &[(f32, f32, f32, f32)], noise: &[(f32, f32, Biquad)], life: f32, g: f32| {
        let (tones, noise) = membrane_velocity(tones, noise, velnorm);
        Some(Box::new(Drum::new(sr, seed, &tones, &noise, life, g * v)) as Box<dyn Voice>)
    };
    let one = |amp: f32, t: f32, filt: Biquad| vec![(amp, t, filt)];
    match key {
        35 | 36 => dm(
            // beater knock over a sub drop (86 -> ~45 Hz): the chest thump
            &[
                (165.0, 0.8, 0.16, 28.0),
                (86.0, 1.1 + 0.4 * velnorm, 0.42, 3.0),
            ],
            &one(0.5, 0.005, Biquad::highpass(2500.0, 0.7, sr)),
            0.8,
            1.0,
        ),
        37 => d(
            // side stick
            &[(430.0, 0.5, 0.05, 0.0)],
            &one(0.6, 0.03, Biquad::bandpass(2200.0, 1.5, sr)),
            0.2,
            0.55,
        ),
        38 | 40 => dm(
            // snare: shell body + wire rattle, brighter when hit harder
            &[(186.0, 0.8, 0.10, 4.0), (330.0, 0.4, 0.07, 0.0)],
            &[
                (0.55, 0.09, Biquad::bandpass(1300.0, 0.7, sr)),
                (
                    0.75,
                    0.19,
                    Biquad::highpass(2800.0 * (0.85 + 0.35 * velnorm), 0.7, sr),
                ),
            ],
            0.5,
            0.72,
        ),
        39 => Some(Box::new(
            Drum::new(
                sr,
                seed,
                &[],
                &[(0.9, 0.10, Biquad::bandpass(1100.0, 1.2, sr))],
                0.35,
                0.70 * v,
            )
            .with_bursts(&[(0.010, 0.75), (0.022, 0.6)]),
        ) as Box<dyn Voice>), // hand clap: three quick bursts
        41 => dm(
            &[(100.0, 1.0, 0.32, 10.0)],
            &one(0.25, 0.05, Biquad::bandpass(900.0, 0.8, sr)),
            0.55,
            0.85,
        ),
        43 => dm(
            &[(140.0, 1.0, 0.30, 10.0)],
            &one(0.25, 0.05, Biquad::bandpass(1100.0, 0.8, sr)),
            0.5,
            0.80,
        ),
        45 => dm(
            &[(190.0, 1.0, 0.28, 10.0)],
            &one(0.25, 0.05, Biquad::bandpass(1300.0, 0.8, sr)),
            0.45,
            0.75,
        ),
        47 | 48 | 50 => dm(
            &[(240.0, 1.0, 0.24, 10.0)],
            &one(0.2, 0.04, Biquad::bandpass(1500.0, 0.8, sr)),
            0.4,
            0.7,
        ),
        42 | 44 => cymbal(
            sr,
            seed,
            vel,
            3300.0,
            0.10,
            0.05,
            0.03,
            (0.8, 0.035, 6500.0),
            0.14,
            0.42,
        ),
        46 => cymbal(
            sr,
            seed,
            vel,
            3300.0,
            0.10,
            0.30,
            0.18,
            (0.8, 0.28, 6000.0),
            0.95,
            0.40,
        ),
        49 | 55 => cymbal(
            sr,
            seed,
            vel,
            950.0,
            0.13,
            2.0,
            0.8,
            (1.0, 1.5, 4200.0),
            3.6,
            0.50,
        ),
        57 => cymbal(
            sr,
            seed,
            vel,
            820.0,
            0.13,
            2.4,
            1.0,
            (1.0, 1.9, 3800.0),
            4.6,
            0.52,
        ),
        51 | 59 => cymbal(
            sr,
            seed,
            vel,
            1150.0,
            0.16,
            0.7,
            0.35,
            (0.35, 1.0, 6000.0),
            2.6,
            0.42,
        ),
        53 => d(
            // ride bell
            &[(1700.0, 0.5, 0.6, 0.0), (2600.0, 0.3, 0.5, 0.0)],
            &one(0.1, 0.2, Biquad::highpass(5000.0, 0.7, sr)),
            1.5,
            0.5,
        ),
        54 => d(
            // tambourine
            &[(6100.0, 0.15, 0.10, 0.0), (7900.0, 0.12, 0.09, 0.0)],
            &one(0.9, 0.11, Biquad::highpass(5200.0, 0.8, sr)),
            0.35,
            0.42,
        ),
        56 => d(
            // cowbell
            &[(560.0, 0.8, 0.22, 0.0), (845.0, 0.55, 0.18, 0.0)],
            &one(0.15, 0.02, Biquad::bandpass(700.0, 2.0, sr)),
            0.5,
            0.55,
        ),
        60 => dm(
            &[(400.0, 1.0, 0.11, 3.0)],
            &one(0.35, 0.02, Biquad::bandpass(1400.0, 1.0, sr)),
            0.3,
            0.6,
        ),
        61 => dm(
            &[(300.0, 1.0, 0.13, 3.0)],
            &one(0.35, 0.02, Biquad::bandpass(1100.0, 1.0, sr)),
            0.3,
            0.6,
        ),
        62 => dm(
            &[(230.0, 1.0, 0.05, 0.0)],
            &one(0.3, 0.015, Biquad::bandpass(1200.0, 1.0, sr)),
            0.2,
            0.6,
        ),
        63 => dm(
            &[(190.0, 1.0, 0.24, 3.0)],
            &one(0.3, 0.02, Biquad::bandpass(1000.0, 1.0, sr)),
            0.4,
            0.65,
        ),
        64 => dm(
            &[(145.0, 1.0, 0.28, 3.0)],
            &one(0.3, 0.02, Biquad::bandpass(800.0, 1.0, sr)),
            0.45,
            0.65,
        ),
        65 | 66 => dm(
            &[(430.0, 0.9, 0.15, 4.0)],
            &one(0.3, 0.02, Biquad::bandpass(1600.0, 1.0, sr)),
            0.3,
            0.6,
        ),
        69 | 70 | 82 => d(
            // cabasa / maracas / shaker
            &[],
            &one(1.0, 0.055, Biquad::highpass(4200.0, 0.7, sr)),
            0.18,
            0.40,
        ),
        75 => d(
            &[(2500.0, 1.0, 0.09, 0.0)],
            &one(0.1, 0.01, Biquad::bandpass(2500.0, 3.0, sr)),
            0.25,
            0.55,
        ),
        76 => d(
            &[(850.0, 1.0, 0.09, 0.0)],
            &one(0.25, 0.012, Biquad::bandpass(1700.0, 1.5, sr)),
            0.25,
            0.60,
        ),
        77 => d(
            &[(620.0, 1.0, 0.10, 0.0)],
            &one(0.25, 0.012, Biquad::bandpass(1300.0, 1.5, sr)),
            0.3,
            0.60,
        ),
        81 => d(
            // open triangle
            &[
                (4050.0, 0.7, 1.8, 0.0),
                (6420.0, 0.45, 1.5, 0.0),
                (8900.0, 0.25, 1.2, 0.0),
            ],
            &one(0.08, 0.01, Biquad::highpass(6000.0, 0.7, sr)),
            2.5,
            0.30,
        ),
        80 => d(
            // muted triangle
            &[(4050.0, 0.7, 0.12, 0.0), (6420.0, 0.4, 0.1, 0.0)],
            &one(0.08, 0.01, Biquad::highpass(6000.0, 0.7, sr)),
            0.3,
            0.30,
        ),
        _ => d(
            // gentle generic tick so unmapped keys are audible, not silent
            &[(1000.0, 0.4, 0.05, 0.0)],
            &one(0.3, 0.02, Biquad::bandpass(2000.0, 1.0, sr)),
            0.15,
            0.4,
        ),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::testutil;

    /// Oracle 30 (structural half, §5.3): the D1 membrane transform moves
    /// every table quantity in the designed direction — the audio spectral
    /// form is unwritable under the pitch glide, so the tables are the seam.
    #[test]
    fn membrane_velocity_transform_is_directional() {
        let sr = 44100.0;
        let tones = [(100.0, 1.0, 0.32, 10.0)];
        let noise = [(0.25, 0.05, Biquad::bandpass(900.0, 0.8, sr))];
        let (t_hard, n_hard) = membrane_velocity(&tones, &noise, 1.0);
        let (t_soft, n_soft) = membrane_velocity(&tones, &noise, 0.0);
        assert!(t_hard[0].0 > t_soft[0].0, "start pitch");
        assert!(t_hard[0].2 > t_soft[0].2, "decay t60");
        assert!(t_hard[0].3 > t_soft[0].3, "glide rate");
        assert!(n_hard[0].0 > n_soft[0].0, "click/noise energy");
        // the vn² click curve spans exactly 2x with a 0.5 ghost-note floor
        assert!((n_hard[0].0 / n_soft[0].0 - 2.0).abs() < 1e-4);
    }

    fn render_drum(key: u8, vel: u8, secs: f32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(key, vel, sr, 7).unwrap();
        let mut buf = vec![0f32; (sr * secs) as usize];
        v.render(&mut buf);
        buf
    }

    /// Oracle 30 (audio half): a hard kick carries proportionally more
    /// beater click and rings longer than a soft one.
    #[test]
    fn drum_velocity_shapes_timbre() {
        let sr = 44100.0;
        let hard = render_drum(36, 120, 1.0);
        let soft = render_drum(36, 30, 1.0);
        // beater-click energy normalised by the exact velocity gain the
        // engine applies (gain = g·vel_amp) — on main this ratio is 1.0
        // because the click amp is velocity-independent relative to gain
        let click = |s: &[f32], vel: u8| {
            testutil::hp_rms(&s[..(0.005 * sr) as usize], sr, 2500.0)
                / crate::dsp::vel_amp(vel).max(1e-9)
        };
        let (ch, cs) = (click(&hard, 120), click(&soft, 30));
        assert!(
            ch > 1.3 * cs,
            "click (gain-normalised) hard {ch} vs soft {cs}"
        );
        let (th, ts) = (testutil::t60_of(&hard, sr), testutil::t60_of(&soft, sr));
        assert!(th > ts, "t60 hard {th} vs soft {ts}");
    }
}
