//! Hall reverb: pre-delay + a handful of early reflections feeding a
//! Freeverb-style tank (8 parallel damped combs + 4 series allpasses per
//! side, the right side delay-offset for width). The pre-delay keeps note
//! attacks clear of the wash; the early taps give the room its walls.

use crate::dsp::DelayLine;

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
        let scale = sr / 44100.0;
        let sz = |n: usize| ((n as f32 * scale) as usize).max(8);
        let pre_samples = PREDELAY_S * sr;
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
