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
        // D8 strike-position dither: one shared "how far off centre" draw
        // tilts the partial balance anti-correlated (edge hits starve the
        // fundamental and feed the overtones), plus small independent
        // per-partial and per-band jitter — no two hits balance identically
        let edge = rng.white();
        // per-strike variation: nothing repeats exactly
        let jf = 1.0 + 0.03 * rng.white();
        let jd = 1.0 + 0.10 * rng.white();
        let n_tones = tones.len();
        let tones = tones
            .iter()
            .enumerate()
            .map(|(i, &(f, a, t, glide_oct_per_s))| {
                let modal = if n_tones > 1 {
                    i as f32 / (n_tones - 1) as f32
                } else {
                    0.5
                };
                let tilt = 0.20 * edge * (2.0 * modal - 1.0);
                Tone {
                    phase: rng.white() * TAU,
                    freq: f * jf,
                    glide: if glide_oct_per_s > 0.0 {
                        2f32.powf(-glide_oct_per_s / sr)
                    } else {
                        1.0
                    },
                    min_freq: f * jf * 0.3,
                    amp: (a * (1.0 + tilt + 0.12 * rng.white())).max(0.0),
                    decay: dmul(t * jd, sr),
                }
            })
            .collect();
        let noise = noise
            .iter()
            .map(|&(amp, t, filt)| NoiseBand {
                amp: (amp * (1.0 + 0.15 * edge + 0.10 * rng.white())).max(0.0),
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

/// D2 tom tone table: the fundamental plus the first two membrane modes at
/// the circular-membrane ratios 1.59×/2.14×, all sharing the strike's
/// down-glide so the inharmonic ratios hold while the pitch settles.
/// A shared fn so the oracle-20 structural test drives the exact shipped
/// table with the glide disabled (the glide smears any spectral read).
fn tom_tones(f0: f32, t60: f32, glide: f32) -> [(f32, f32, f32, f32); 3] {
    [
        (f0, 1.0, t60, glide),
        (f0 * 1.59, 0.40, t60 * 0.7, glide),
        (f0 * 2.14, 0.18, t60 * 0.5, glide),
    ]
}

/// D2 snare head modes (DRM-4): four partials with a small shared down-glide
/// — the 186 Hz fundamental plus the 280/330/430 Hz cluster a real head
/// carries. Shared with the oracle-21 structural test.
const SNARE_TONES: [(f32, f32, f32, f32); 4] = [
    (186.0, 0.8, 0.10, 4.0),
    (280.0, 0.35, 0.08, 2.0),
    (330.0, 0.30, 0.07, 2.0),
    (430.0, 0.18, 0.05, 2.0),
];

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
            // beater knock over a sub drop (86 -> ~45 Hz): the chest thump,
            // plus a knuckle-of-the-beater tone (D3)
            &[
                (165.0, 0.8, 0.16, 28.0),
                (86.0, 1.1 + 0.4 * velnorm, 0.42, 3.0),
                (130.0, 0.4 * velnorm, 0.01, 0.0),
            ],
            // D3: the ~3.5 kHz beater "point" is a real bandpass band, not a
            // second flat highpass correlated with band 1 — with the dm
            // click curve on top its energy grows super-linearly with
            // velocity (oracle 22)
            &[
                (0.5, 0.005, Biquad::highpass(2500.0, 0.7, sr)),
                (0.3, 0.005, Biquad::bandpass(3500.0, 0.9, sr)),
            ],
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
            // snare: four head modes (D2) + shell body and wire rattle,
            // brighter when hit harder
            &SNARE_TONES,
            &[
                (0.55, 0.09, Biquad::bandpass(1300.0, 0.7, sr)),
                (
                    0.75,
                    0.19,
                    Biquad::highpass(2800.0 * (0.85 + 0.35 * velnorm), 0.7, sr),
                ),
            ],
            0.5,
            0.68,
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
            &tom_tones(100.0, 0.32, 10.0),
            &one(0.25, 0.05, Biquad::bandpass(900.0, 0.8, sr)),
            0.55,
            0.78,
        ),
        43 => dm(
            &tom_tones(140.0, 0.30, 10.0),
            &one(0.25, 0.05, Biquad::bandpass(1100.0, 0.8, sr)),
            0.5,
            0.74,
        ),
        45 => dm(
            &tom_tones(190.0, 0.28, 10.0),
            &one(0.25, 0.05, Biquad::bandpass(1300.0, 0.8, sr)),
            0.45,
            0.69,
        ),
        47 | 48 | 50 => dm(
            &tom_tones(240.0, 0.24, 10.0),
            &one(0.2, 0.04, Biquad::bandpass(1500.0, 0.8, sr)),
            0.4,
            0.64,
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
        49 => cymbal(
            // crash: rings out the way a real 16" crash does (oracle 29
            // pins the audible tail > 3 s, china ~1 s, splash < 0.7 s)
            sr,
            seed,
            vel,
            950.0,
            0.13,
            2.6,
            1.0,
            (1.0, 1.9, 4200.0),
            4.2,
            0.50,
        ),
        52 => cymbal(
            // china (D7/CYM-7): trashy — compressed decay, aggressive bright
            // wash, short life; until now this key fell to the generic tick
            sr,
            seed,
            vel,
            1400.0,
            0.09,
            0.62,
            0.26,
            (1.7, 0.45, 7500.0),
            1.0,
            0.50,
        ),
        55 => cymbal(
            // splash (D7/CYM-7): small and quick, split from the crash
            sr,
            seed,
            vel,
            1600.0,
            0.12,
            0.4,
            0.2,
            (0.9, 0.25, 5000.0),
            0.6,
            0.45,
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
            // ride bell (D7/CYM-6): a dense inharmonic METAL_RATIOS stack on
            // a 1650 Hz base — not two pure sines — plus a sharp stick click
            // and a light sustaining wash
            &[
                (1650.0, 0.50, 0.60, 0.0),
                (1650.0 * 1.483, 0.38, 0.55, 0.0),
                (1650.0 * 1.932, 0.30, 0.50, 0.0),
                (1650.0 * 2.546, 0.24, 0.42, 0.0),
                (1650.0 * 3.363, 0.18, 0.34, 0.0),
                (1650.0 * 4.365, 0.13, 0.26, 0.0),
            ],
            &[
                (1.6 * velnorm, 0.005, Biquad::highpass(7000.0, 0.7, sr)),
                (0.05, 0.4, Biquad::highpass(6000.0, 0.7, sr)),
            ],
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

    /// Oracle 20 (structural, §5.3): the shipped tom table carries the
    /// 1:1.59:2.14 membrane modes — verified on a glide-disabled build of
    /// the exact same table (the glide smears any spectral read).
    #[test]
    fn tom_membrane_modes_present() {
        let sr = 44100.0;
        let tones = tom_tones(100.0, 0.32, 0.0); // shipped table, glide off
        let mut v = Drum::new(sr, 7, &tones, &[], 0.6, 0.8);
        let mut buf = vec![0f32; (0.4 * sr) as usize];
        Voice::render(&mut v, &mut buf);
        // jf jitters all mode freqs ±3% together; search ±8% windows
        let floor = testutil::mag_at(&buf, sr, 100.0) * 0.05;
        for f0 in [100.0f32, 159.0, 214.0] {
            let p = testutil::peak_locate(&buf, sr, f0 * 0.92, f0 * 1.08);
            let m = testutil::mag_at(&buf, sr, p);
            assert!(m > floor, "mode near {f0} Hz missing (mag {m})");
        }
    }

    /// Oracle 21 (structural, §5.3): all four snare head modes speak.
    #[test]
    fn snare_head_modes_present() {
        let sr = 44100.0;
        let mut tones = SNARE_TONES;
        for t in &mut tones {
            t.3 = 0.0; // disable the shared down-glide for the read
        }
        let mut v = Drum::new(sr, 7, &tones, &[], 0.5, 0.7);
        let mut buf = vec![0f32; (0.3 * sr) as usize];
        Voice::render(&mut v, &mut buf);
        let floor = testutil::mag_at(&buf, sr, 186.0) * 0.05;
        for f0 in [186.0f32, 280.0, 330.0, 430.0] {
            let p = testutil::peak_locate(&buf, sr, f0 * 0.92, f0 * 1.08);
            let m = testutil::mag_at(&buf, sr, p);
            assert!(m > floor, "head mode near {f0} Hz missing (mag {m})");
        }
    }

    /// Oracle 22 (§5.1 corrected): the kick's >3.5 kHz beater point grows
    /// SUPER-linearly with velocity — faster than the amplitude curve.
    #[test]
    fn kick_beater_point_superlinear() {
        let sr = 44100.0;
        let hard = render_drum(36, 120, 0.5);
        let soft = render_drum(36, 30, 0.5);
        let early = (0.004 * sr) as usize;
        let point = |s: &[f32]| testutil::hp_rms(&s[..early], sr, 3500.0);
        let gain_ratio = crate::dsp::vel_amp(120) / crate::dsp::vel_amp(30);
        let point_ratio = point(&hard) / point(&soft).max(1e-9);
        assert!(
            point_ratio > 1.3 * gain_ratio,
            "beater ratio {point_ratio} vs amplitude ratio {gain_ratio}"
        );
    }

    /// Oracle 28: the ride bell is a dense inharmonic stack (≥5 partials)
    /// with a >7 kHz stick click on the front.
    #[test]
    fn ride_bell_dense_and_clicky() {
        let sr = 44100.0;
        let buf = render_drum(53, 110, 1.0);
        let floor = testutil::mag_at(&buf, sr, 1650.0) * 0.04;
        let mut found = 0;
        for r in METAL_RATIOS {
            let f0 = 1650.0 * r;
            let p = testutil::peak_locate(&buf, sr, f0 * 0.92, f0 * 1.08);
            if testutil::mag_at(&buf, sr, p) > floor {
                found += 1;
            }
        }
        assert!(found >= 5, "only {found} bell partials found");
        // stick click: >7 kHz energy concentrated at the very front
        let early = testutil::hp_rms(&buf[..(0.006 * sr) as usize], sr, 7000.0);
        let late = testutil::hp_rms(
            &buf[(0.010 * sr) as usize..(0.030 * sr) as usize],
            sr,
            7000.0,
        );
        assert!(
            early > 2.0 * late,
            "no stick click: early {early} late {late}"
        );
    }

    fn last_audible(s: &[f32]) -> f32 {
        let sr = 44100.0;
        let peak = s.iter().fold(0f32, |m, &x| m.max(x.abs())).max(1e-12);
        let idx = s.iter().rposition(|&x| x.abs() > 1e-4 * peak).unwrap_or(0);
        idx as f32 / sr
    }

    /// Oracle 29 (+ §5.2/§5.3 clauses): china and splash are genuinely
    /// distinct voices — bounded lives and the china measurably trashier
    /// (brighter wash) than the crash.
    #[test]
    fn china_splash_crash_are_distinct() {
        let sr = 44100.0;
        let china = render_drum(52, 110, 1.6);
        let splash = render_drum(55, 110, 1.2);
        let crash = render_drum(49, 110, 4.2);
        let (lc, ls, lx) = (
            last_audible(&china),
            last_audible(&splash),
            last_audible(&crash),
        );
        assert!((0.6..=1.2).contains(&lc), "china life {lc}");
        assert!(ls < 0.7, "splash life {ls}");
        assert!(lx > 3.0, "crash life {lx}");
        // spectral distinctness: china's >8 kHz : 2-4 kHz balance exceeds
        // the crash's by a clear margin at matched velocity
        let trash = |s: &[f32]| {
            testutil::hp_rms(s, sr, 8000.0) / testutil::band_rms(s, sr, 3000.0, 0.8).max(1e-9)
        };
        let (tc, tx) = (
            trash(&china[..(0.5 * sr) as usize]),
            trash(&crash[..(0.5 * sr) as usize]),
        );
        assert!(tc > 1.5 * tx, "china trash {tc} vs crash {tx}");
    }

    /// Oracle 31 (§5.3 calibrated): D8's anti-correlated strike dither makes
    /// the fundamental:overtone balance vary hit-to-hit far beyond what the
    /// old uniform jf jitter produced (which moved all modes together and
    /// left the RATIO nearly constant) — and stays bounded.
    #[test]
    fn strike_variation_is_real_and_bounded() {
        let sr = 44100.0;
        let mut ratios = Vec::new();
        for seed in 1..=8u32 {
            let tones = tom_tones(100.0, 0.32, 0.0);
            let mut v = Drum::new(sr, seed * 977, &tones, &[], 0.6, 0.8);
            let mut buf = vec![0f32; (0.3 * sr) as usize];
            Voice::render(&mut v, &mut buf);
            let f = testutil::peak_locate(&buf, sr, 92.0, 108.0);
            let m = testutil::peak_locate(&buf, sr, 146.0, 172.0);
            ratios.push(testutil::mag_at(&buf, sr, f) / testutil::mag_at(&buf, sr, m).max(1e-9));
        }
        let hi = ratios.iter().fold(f32::MIN, |m, &x| m.max(x));
        let lo = ratios.iter().fold(f32::MAX, |m, &x| m.min(x));
        assert!(hi / lo > 1.3, "ratio spread {} .. {} too uniform", lo, hi);
        assert!(hi / lo < 6.0, "ratio spread {} .. {} unbounded", lo, hi);
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
