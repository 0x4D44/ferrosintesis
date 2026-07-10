//! Hall reverb: pre-delay + a handful of early reflections feeding a
//! Freeverb-style tank (8 parallel damped combs + 4 series allpasses per
//! side, the right side delay-offset for width). The pre-delay keeps note
//! attacks clear of the wash; the early taps give the room its walls.

use crate::dsp::{Biquad, DelayLine};

const COMBS: [usize; 8] = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617];
const ALLPASSES: [usize; 4] = [556, 441, 341, 225];
const STEREO_SPREAD: usize = 23;
const PREDELAY_S: f32 = 0.024;
// (seconds after the pre-delay tap, gain, +1 = left / -1 = right emphasis)
const EARLY: [(f32, f32, f32); 5] = [
    (0.0093, 0.50, 1.0),
    (0.0141, 0.42, -1.0),
    (0.0197, 0.34, -1.0),
    (0.0253, 0.26, 1.0),
    (0.0331, 0.18, -1.0),
];

struct Comb {
    buf: Vec<f32>,
    idx: usize,
    feedback: f32,
    damp: f32,
    store: f32,
}

impl Comb {
    fn new(len: usize, feedback: f32, damp: f32) -> Self {
        Comb {
            buf: vec![0.0; len],
            idx: 0,
            feedback,
            damp,
            store: 0.0,
        }
    }

    #[inline]
    fn process(&mut self, x: f32) -> f32 {
        let out = self.buf[self.idx];
        self.store = out * (1.0 - self.damp) + self.store * self.damp;
        self.buf[self.idx] = x + self.store * self.feedback;
        self.idx = (self.idx + 1) % self.buf.len();
        out
    }
}

struct Allpass {
    buf: Vec<f32>,
    idx: usize,
}

impl Allpass {
    fn new(len: usize) -> Self {
        Allpass {
            buf: vec![0.0; len],
            idx: 0,
        }
    }

    #[inline]
    fn process(&mut self, x: f32) -> f32 {
        let b = self.buf[self.idx];
        let out = b - x;
        self.buf[self.idx] = x + b * 0.5;
        self.idx = (self.idx + 1) % self.buf.len();
        out
    }
}

pub struct Reverb {
    pre: DelayLine,
    pre_samples: f32,
    early: Vec<(f32, f32, f32)>, // (samples past the pre-delay, gain, side)
    combs_l: Vec<Comb>,
    combs_r: Vec<Comb>,
    aps_l: Vec<Allpass>,
    aps_r: Vec<Allpass>,
    wet: f32,
}

impl Reverb {
    pub fn new(sr: f32, room: f32, damp: f32, wet: f32) -> Self {
        // the hall keeps its 24 ms predelay (oracle 39 pins this)
        Self::with_predelay(sr, room, damp, wet, PREDELAY_S)
    }

    /// D10: predelay as a parameter — a tight drum room wants ~2-4 ms
    /// first reflections, not the hall's 24 ms (V4/CORR-3).
    pub fn with_predelay(sr: f32, room: f32, damp: f32, wet: f32, predelay_s: f32) -> Self {
        let scale = sr / 44100.0;
        let sz = |n: usize| ((n as f32 * scale) as usize).max(8);
        let pre_samples = predelay_s * sr;
        Reverb {
            pre: DelayLine::new((pre_samples + 0.04 * sr) as usize + 8),
            pre_samples,
            early: EARLY
                .iter()
                .map(|&(t, g, side)| (pre_samples + t * sr, g, side))
                .collect(),
            combs_l: COMBS
                .iter()
                .map(|&n| Comb::new(sz(n), room, damp))
                .collect(),
            combs_r: COMBS
                .iter()
                .map(|&n| Comb::new(sz(n + STEREO_SPREAD), room, damp))
                .collect(),
            aps_l: ALLPASSES.iter().map(|&n| Allpass::new(sz(n))).collect(),
            aps_r: ALLPASSES
                .iter()
                .map(|&n| Allpass::new(sz(n + STEREO_SPREAD)))
                .collect(),
            wet,
        }
    }

    /// Feed a mono send block; add wet stereo into (l, r).
    pub fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        for i in 0..send.len() {
            self.pre.push(send[i]);
            let x = self.pre.tap(self.pre_samples) * 0.015;
            let mut el = 0.0;
            let mut er = 0.0;
            for &(d, g, side) in &self.early {
                let tap = self.pre.tap(d) * g;
                if side > 0.0 {
                    el += tap;
                    er += tap * 0.55;
                } else {
                    er += tap;
                    el += tap * 0.55;
                }
            }
            let mut wl = 0.0;
            let mut wr = 0.0;
            for c in &mut self.combs_l {
                wl += c.process(x);
            }
            for c in &mut self.combs_r {
                wr += c.process(x);
            }
            for a in &mut self.aps_l {
                wl = a.process(wl);
            }
            for a in &mut self.aps_r {
                wr = a.process(wr);
            }
            l[i] += (wl + el * 0.011) * self.wet;
            r[i] += (wr + er * 0.011) * self.wet;
        }
    }
}

const CATHEDRAL_PREDELAY_S: f32 = 0.040;
const CATHEDRAL_LINES_44K: [usize; 8] = [2087, 2609, 3169, 3691, 4241, 4751, 5261, 5813];
const CATHEDRAL_EARLY: [(f32, f32); 5] = [
    (0.048, 0.40),
    (0.057, 0.31),
    (0.071, 0.25),
    (0.091, 0.18),
    (0.117, 0.13),
];
const CATHEDRAL_INPUT: [f32; 8] = [1.0, 1.0, -1.0, 1.0, -1.0, -1.0, 1.0, -1.0];
const CATHEDRAL_LEFT: [f32; 8] = [1.0, -1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0];
const CATHEDRAL_RIGHT: [f32; 8] = [1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0];
const INV_SQRT_8: f32 = 0.353_553_38;

/// One delay and its frequency-dependent decay filter in the cathedral FDN.
struct CathedralLine {
    buf: Vec<f32>,
    idx: usize,
    low_state: f32,
    high_state: f32,
    low_gain: f32,
    mid_gain: f32,
    high_gain: f32,
}

impl CathedralLine {
    fn new(len: usize, sr: f32) -> Self {
        let delay_s = len as f32 / sr;
        let gain = |rt60: f32| 10f32.powf(-3.0 * delay_s / rt60);
        Self {
            buf: vec![0.0; len],
            idx: 0,
            low_state: 0.0,
            high_state: 0.0,
            low_gain: gain(6.2),
            mid_gain: gain(6.25),
            high_gain: gain(3.5),
        }
    }

    #[inline]
    fn output(&self) -> f32 {
        self.buf[self.idx]
    }

    #[inline]
    fn decay_filter(&mut self, x: f32, low_k: f32, high_k: f32) -> f32 {
        self.low_state += low_k * (x - self.low_state);
        self.high_state += high_k * (x - self.high_state);
        let low = self.low_state;
        let mid = self.high_state - low;
        let high = x - self.high_state;
        low * self.low_gain + mid * self.mid_gain + high * self.high_gain
    }

    #[inline]
    fn write(&mut self, x: f32) {
        self.buf[self.idx] = x;
        self.idx += 1;
        if self.idx == self.buf.len() {
            self.idx = 0;
        }
    }
}

/// Normalized Walsh-Hadamard feedback. The butterfly form is the exact H8
/// sign matrix while avoiding a per-sample 8x8 multiply.
#[inline]
fn cathedral_hadamard(mut x: [f32; 8]) -> [f32; 8] {
    let mut stride = 1;
    while stride < 8 {
        let mut base = 0;
        while base < 8 {
            for offset in 0..stride {
                let a = x[base + offset];
                let b = x[base + offset + stride];
                x[base + offset] = a + b;
                x[base + offset + stride] = a - b;
            }
            base += stride * 2;
        }
        stride *= 2;
    }
    for value in &mut x {
        *value *= INV_SQRT_8;
    }
    x
}

/// Long, low-frequency-capable room used only by the default cathedral organ.
/// It is intentionally isolated from `Reverb`, whose layout and render remain
/// unchanged for every existing instrument.
pub(crate) struct CathedralReverb {
    input_delay: DelayLine,
    predelay_samples: f32,
    early: [(f32, f32, bool); 5],
    lines: [CathedralLine; 8],
    low_k: f32,
    high_k: f32,
    return_hp_l: Biquad,
    return_hp_r: Biquad,
    wet: f32,
    active: bool,
    #[cfg(test)]
    return_peak: f32,
}

impl CathedralReverb {
    pub(crate) fn new(sr: f32, wet: f32) -> Self {
        let scale = sr / 44_100.0;
        let line_lengths =
            CATHEDRAL_LINES_44K.map(|len| ((len as f32 * scale).round() as usize).max(8));
        let max_early = CATHEDRAL_EARLY
            .last()
            .map_or(CATHEDRAL_PREDELAY_S, |tap| tap.0);
        let one_pole = |hz: f32| 1.0 - (-std::f32::consts::TAU * hz / sr).exp();
        Self {
            input_delay: DelayLine::new((max_early * sr).ceil() as usize + 8),
            predelay_samples: CATHEDRAL_PREDELAY_S * sr,
            early: std::array::from_fn(|index| {
                let (time, gain) = CATHEDRAL_EARLY[index];
                (time * sr, gain, index % 2 == 0)
            }),
            lines: std::array::from_fn(|index| CathedralLine::new(line_lengths[index], sr)),
            low_k: one_pole(180.0),
            high_k: one_pole(3_500.0),
            return_hp_l: Biquad::highpass(10.0, std::f32::consts::FRAC_1_SQRT_2, sr),
            return_hp_r: Biquad::highpass(10.0, std::f32::consts::FRAC_1_SQRT_2, sr),
            wet,
            active: false,
            #[cfg(test)]
            return_peak: 0.0,
        }
    }

    #[cfg(test)]
    pub(crate) fn debug_return_peak(&self) -> f32 {
        self.return_peak
    }

    /// Feed one mono cathedral send and add its wet stereo return to `left`
    /// and `right`. The room stays dormant until its first non-zero send, and
    /// a fixed zero wet level is an exact, allocation-free render bypass.
    pub(crate) fn process(&mut self, send: &[f32], left: &mut [f32], right: &mut [f32]) {
        assert_eq!(send.len(), left.len());
        assert_eq!(send.len(), right.len());

        #[cfg(test)]
        {
            self.return_peak = 0.0;
        }
        if self.wet == 0.0 {
            return;
        }
        if !self.active {
            if send.iter().all(|sample| *sample == 0.0) {
                return;
            }
            self.active = true;
        }

        #[cfg(test)]
        let mut return_peak = 0.0f32;
        for i in 0..send.len() {
            self.input_delay.push(send[i]);
            let input = self.input_delay.tap(self.predelay_samples);

            let mut early_l = 0.0;
            let mut early_r = 0.0;
            for &(delay, gain, to_left) in &self.early {
                let reflection = self.input_delay.tap(delay) * gain;
                if to_left {
                    early_l += reflection;
                } else {
                    early_r += reflection;
                }
            }

            let outputs: [f32; 8] = std::array::from_fn(|index| self.lines[index].output());
            let mut decayed = [0.0; 8];
            for index in 0..8 {
                decayed[index] =
                    self.lines[index].decay_filter(outputs[index], self.low_k, self.high_k);
            }
            let feedback = cathedral_hadamard(decayed);
            for index in 0..8 {
                let injection = input * CATHEDRAL_INPUT[index] * INV_SQRT_8;
                self.lines[index].write(injection + feedback[index]);
            }

            let late_l = outputs
                .iter()
                .zip(CATHEDRAL_LEFT)
                .map(|(sample, sign)| sample * sign)
                .sum::<f32>()
                * INV_SQRT_8;
            let late_r = outputs
                .iter()
                .zip(CATHEDRAL_RIGHT)
                .map(|(sample, sign)| sample * sign)
                .sum::<f32>()
                * INV_SQRT_8;
            let wet_l = self.return_hp_l.process(early_l + late_l);
            let wet_r = self.return_hp_r.process(early_r + late_r);
            if self.wet != 0.0 {
                left[i] += wet_l * self.wet;
                right[i] += wet_r * self.wet;
                #[cfg(test)]
                {
                    return_peak = return_peak.max((wet_l * self.wet).abs());
                    return_peak = return_peak.max((wet_r * self.wet).abs());
                }
            }
        }
        #[cfg(test)]
        {
            self.return_peak = return_peak;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f32::consts::TAU;

    const SR: f32 = 44_100.0;

    fn rms(xs: &[f32]) -> f32 {
        (xs.iter().map(|x| x * x).sum::<f32>() / xs.len().max(1) as f32).sqrt()
    }

    fn impulse_response(seconds: f32, wet: f32) -> (Vec<f32>, Vec<f32>) {
        let n = (seconds * SR) as usize;
        let mut send = vec![0.0; n];
        send[0] = 1.0;
        let mut left = vec![0.0; n];
        let mut right = vec![0.0; n];
        CathedralReverb::new(SR, wet).process(&send, &mut left, &mut right);
        (left, right)
    }

    fn tone_tail(freq: f32, seconds: f32) -> (Vec<f32>, Vec<f32>) {
        let n = (seconds * SR) as usize;
        let burst_n = (0.75 * SR) as usize;
        let ramp_n = (0.03 * SR) as usize;
        let mut send = vec![0.0; n];
        for (i, x) in send[..burst_n].iter_mut().enumerate() {
            let edge = i.min(burst_n - 1 - i).min(ramp_n) as f32 / ramp_n as f32;
            let taper = 0.5 - 0.5 * (std::f32::consts::PI * edge).cos();
            *x = (TAU * freq * i as f32 / SR).sin() * taper;
        }
        let mut left = vec![0.0; n];
        let mut right = vec![0.0; n];
        CathedralReverb::new(SR, 1.0).process(&send, &mut left, &mut right);
        (left, right)
    }

    fn hall_tone_tail(freq: f32, seconds: f32) -> (Vec<f32>, Vec<f32>) {
        let n = (seconds * SR) as usize;
        let burst_n = (0.75 * SR) as usize;
        let ramp_n = (0.03 * SR) as usize;
        let mut highpass = Biquad::highpass(150.0, 0.7, SR);
        let mut send = vec![0.0; n];
        for (i, x) in send[..burst_n].iter_mut().enumerate() {
            let edge = i.min(burst_n - 1 - i).min(ramp_n) as f32 / ramp_n as f32;
            let taper = 0.5 - 0.5 * (std::f32::consts::PI * edge).cos();
            *x = highpass.process((TAU * freq * i as f32 / SR).sin() * taper);
        }
        let mut left = vec![0.0; n];
        let mut right = vec![0.0; n];
        Reverb::new(SR, 0.86, 0.35, 1.0).process(&send, &mut left, &mut right);
        (left, right)
    }

    fn stereo_rms(left: &[f32], right: &[f32], from_s: f32, to_s: f32) -> f32 {
        let from = (from_s * SR) as usize;
        let to = (to_s * SR) as usize;
        let energy = left[from..to]
            .iter()
            .zip(&right[from..to])
            .map(|(l, r)| 0.5 * (l * l + r * r))
            .sum::<f32>();
        (energy / (to - from) as f32).sqrt()
    }

    fn spectral_flatness(xs: &[f32]) -> f32 {
        let n = xs.len().min(2048);
        let mut sum = 0.0f64;
        let mut log_sum = 0.0f64;
        let mut bins = 0usize;
        for bin in 2..n / 4 {
            let mut re = 0.0f64;
            let mut im = 0.0f64;
            for (index, &sample) in xs[..n].iter().enumerate() {
                let phase = std::f64::consts::TAU * bin as f64 * index as f64 / n as f64;
                let window =
                    0.5 - 0.5 * (std::f64::consts::TAU * index as f64 / (n - 1) as f64).cos();
                re += sample as f64 * window * phase.cos();
                im -= sample as f64 * window * phase.sin();
            }
            let power = (re * re + im * im).max(1e-30);
            sum += power;
            log_sum += power.ln();
            bins += 1;
        }
        (log_sum / bins as f64).exp() as f32 / (sum / bins as f64) as f32
    }

    fn estimated_octave_rt60(center: f32) -> f32 {
        let mut early_energy = 0.0;
        let mut late_energy = 0.0;
        for step in 0..7 {
            let ratio = 2f32.powf(-0.5 + step as f32 / 6.0);
            let (left, right) = tone_tail(center * ratio, 4.5);
            early_energy += stereo_rms(&left, &right, 1.35, 1.85).powi(2);
            late_energy += stereo_rms(&left, &right, 2.95, 3.45).powi(2);
        }
        let early = (early_energy / 7.0).sqrt().max(1e-20);
        let late = (late_energy / 7.0).sqrt().max(1e-20);
        let drop_db = 20.0 * (late / early).log10();
        -60.0 * 1.6 / drop_db
    }

    #[test]
    fn cathedral_predelay_and_first_reflection_are_pinned() {
        let (left, right) = impulse_response(0.14, 1.0);
        let first = left
            .iter()
            .zip(&right)
            .position(|(l, r)| l.abs().max(r.abs()) > 1e-7)
            .expect("cathedral impulse response should become audible");
        let first_s = first as f32 / SR;
        assert!(first_s >= 0.035, "wet output began at {first_s:.6}s");
        assert!(
            (0.047..=0.049).contains(&first_s),
            "first early reflection was at {first_s:.6}s, expected about 48ms"
        );
    }

    #[test]
    fn cathedral_wet_zero_is_an_exact_output_bypass() {
        let n = 4096;
        let mut send = vec![0.0; n];
        send[0] = 1.0;
        let mut left: Vec<f32> = (0..n).map(|i| i as f32 * 1e-5 - 0.02).collect();
        let mut right: Vec<f32> = left.iter().map(|x| -*x).collect();
        let before_left = left.clone();
        let before_right = right.clone();
        CathedralReverb::new(SR, 0.0).process(&send, &mut left, &mut right);
        assert_eq!(left, before_left);
        assert_eq!(right, before_right);
    }

    #[test]
    fn cathedral_silence_stays_silent_and_impulse_stays_finite() {
        let n = SR as usize;
        let silence = vec![0.0; n];
        let mut left = vec![0.0; n];
        let mut right = vec![0.0; n];
        CathedralReverb::new(SR, 1.0).process(&silence, &mut left, &mut right);
        assert!(left.iter().chain(&right).all(|x| *x == 0.0));

        let (left, right) = impulse_response(8.0, 1.0);
        assert!(left.iter().chain(&right).all(|x| x.is_finite()));
        assert!(
            left.iter()
                .chain(&right)
                .fold(0.0f32, |peak, x| peak.max(x.abs()))
                < 2.0
        );
    }

    #[test]
    fn cathedral_retains_real_31_hz_energy() {
        let (low_l, low_r) = tone_tail(31.0, 3.0);
        let (mid_l, mid_r) = tone_tail(500.0, 3.0);
        let low = stereo_rms(&low_l, &low_r, 1.1, 2.1);
        let mid = stereo_rms(&mid_l, &mid_r, 1.1, 2.1);
        assert!(low > mid * 0.30, "31Hz/500Hz tail ratio = {:.3}", low / mid);
    }

    #[test]
    fn cathedral_decay_is_long_but_treble_clears_sooner() {
        let rt31 = estimated_octave_rt60(31.5);
        let rt63 = estimated_octave_rt60(63.0);
        let rt125 = estimated_octave_rt60(125.0);
        let rt500 = estimated_octave_rt60(500.0);
        let rt2k = estimated_octave_rt60(2_000.0);
        let rt8k = estimated_octave_rt60(8_000.0);
        assert!((5.0..=6.5).contains(&rt31), "31.5Hz RT60 {rt31:.2}s");
        assert!((5.5..=7.0).contains(&rt63), "63Hz RT60 {rt63:.2}s");
        assert!((5.5..=7.2).contains(&rt125), "125Hz RT60 {rt125:.2}s");
        assert!((5.5..=7.2).contains(&rt500), "500Hz RT60 {rt500:.2}s");
        assert!((4.5..=6.5).contains(&rt2k), "2kHz RT60 {rt2k:.2}s");
        assert!((2.5..=4.5).contains(&rt8k), "8kHz RT60 {rt8k:.2}s");
        assert!(rt500 > rt8k + 1.0, "500Hz {rt500:.2}s, 8kHz {rt8k:.2}s");
    }

    #[test]
    fn cathedral_late_tail_is_dense_without_a_dominant_pulse() {
        let (left, right) = impulse_response(2.1, 1.0);
        let from = (0.8 * SR) as usize;
        let to = (2.0 * SR) as usize;
        let mono: Vec<f32> = left[from..to]
            .iter()
            .zip(&right[from..to])
            .map(|(l, r)| 0.5 * (l + r))
            .collect();
        let level = rms(&mono);
        let occupied =
            mono.iter().filter(|x| x.abs() > level * 0.01).count() as f32 / mono.len() as f32;
        let crest = mono.iter().fold(0.0f32, |peak, x| peak.max(x.abs())) / level;
        let flatness = spectral_flatness(&mono);
        assert!(occupied > 0.85, "late-tail occupancy {occupied:.3}");
        assert!(
            flatness >= 0.18,
            "late-tail spectral flatness {flatness:.3}"
        );
        // A sparse FDN leaves long exact-zero runs and very large isolated
        // pulses. Once the loop is mixed, this broad crest guard complements
        // the occupancy check without pretending to be the HLD's later
        // 1/6-octave modal measurement.
        assert!(crest < 30.0, "late-tail crest factor {crest:.2}");

        let mut windowed = mono;
        let window_len = windowed.len();
        for (index, sample) in windowed.iter_mut().enumerate() {
            let window =
                0.5 - 0.5 * (TAU * index as f32 / (window_len.saturating_sub(1)) as f32).cos();
            *sample *= window;
        }
        let mut bands = Vec::new();
        let mut freq = 31.5;
        while freq <= 8_000.0 {
            bands.push(crate::testutil::mag_at(&windowed, SR, freq).max(1e-12));
            freq *= 2f32.powf(1.0 / 6.0);
        }
        bands.sort_by(f32::total_cmp);
        let median = bands[bands.len() / 2];
        let modal_peak_db = 20.0 * (bands.last().copied().unwrap_or(0.0) / median).log10();
        assert!(
            modal_peak_db < 12.0,
            "largest 1/6-octave band is {modal_peak_db:.1}dB over median"
        );
    }

    #[test]
    fn cathedral_low_frequency_route_beats_highpassed_hall() {
        let tail_ratio = |render: fn(f32, f32) -> (Vec<f32>, Vec<f32>)| {
            let (low_l, low_r) = render(31.5, 3.0);
            let (mid_l, mid_r) = render(500.0, 3.0);
            stereo_rms(&low_l, &low_r, 1.1, 2.1) / stereo_rms(&mid_l, &mid_r, 1.1, 2.1).max(1e-20)
        };
        let cathedral = tail_ratio(tone_tail);
        let hall = tail_ratio(hall_tone_tail);
        let advantage_db = 20.0 * (cathedral / hall.max(1e-20)).log10();
        assert!(
            advantage_db >= 18.0,
            "cathedral 31.5/500Hz advantage over hall {advantage_db:.1}dB"
        );
    }

    #[test]
    fn cathedral_stereo_tail_has_width_and_safe_mono_collapse() {
        let (left, right) = impulse_response(2.1, 1.0);
        let from = (0.8 * SR) as usize;
        let to = (2.0 * SR) as usize;
        let (left, right) = (&left[from..to], &right[from..to]);
        let lr = left.iter().zip(right).map(|(l, r)| l * r).sum::<f32>();
        let ll = left.iter().map(|x| x * x).sum::<f32>();
        let rr = right.iter().map(|x| x * x).sum::<f32>();
        let corr = lr / (ll * rr).sqrt().max(1e-20);
        let mid: Vec<f32> = left.iter().zip(right).map(|(l, r)| 0.5 * (l + r)).collect();
        let side: Vec<f32> = left.iter().zip(right).map(|(l, r)| 0.5 * (l - r)).collect();
        let stereo = ((ll + rr) / (2 * left.len()) as f32).sqrt();
        let mono_loss_db = 20.0 * (rms(&mid) / stereo.max(1e-20)).log10();
        assert!(
            (0.05..=0.85).contains(&corr),
            "stereo correlation {corr:.3}"
        );
        assert!(
            rms(&side) >= 0.08 * rms(&mid),
            "cathedral return too narrow"
        );
        assert!(
            mono_loss_db >= -3.0,
            "mono collapse lost {mono_loss_db:.2}dB"
        );
    }
}
