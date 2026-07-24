//! The audio thread: it owns the synth, the sequencer and all playback state.
//!
//! `RealtimeSynth::write_byte` buffers into a `Vec` that `render_add` drains, so
//! the synth must be owned by exactly one thread. Sharing it with the UI behind a
//! `Mutex` is the textbook way to get dropouts (a repaint holding the lock is a
//! priority inversion), so the UI only ever pushes commands into a lock-free ring
//! and this thread drains them.

use std::sync::atomic::{AtomicU32, AtomicUsize, Ordering};
use std::sync::Arc;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use ferrosintesis::live::{RealtimeOptions, RealtimeSynth};

use crate::ring::{Cmd, Consumer};
use crate::seq::{Loop, Player};

/// Read-only telemetry the UI polls. Atomics so neither side ever waits.
#[derive(Default)]
pub struct Meters {
    pub voices: AtomicUsize,
    /// Peak output since the last read, as a fixed-point 0..10000 of full scale.
    pub peak_x1e4: AtomicU32,
    pub xruns: AtomicUsize,
}

pub struct Engine {
    _stream: cpal::Stream,
    pub meters: Arc<Meters>,
    pub sample_rate: u32,
    pub device_name: String,
}

/// The channel carrying the guitar we are auditioning. Solo mutes everything else.
pub const GUITAR_CHANNELS: [u8; 2] = [0, 1];

/// How many scheduled events one callback can hold before we stop honouring offsets.
///
/// Sized far above anything a real block produces (the shipped 8-bar loop is 614 events
/// across ~19 s, so a 1024-frame callback sees a handful). It exists only so `process`
/// can be allocation-free: pushing within capacity never allocates, and overflowing is
/// counted as an xrun rather than growing the `Vec` on the audio thread.
const MAX_EVENTS_PER_BLOCK: usize = 256;

/// Everything one audio callback does, with no cpal in sight.
///
/// Factored out of the stream closure because the closure captures a device and can only
/// run on real hardware, which left the whole scheduling path untestable — the reason
/// MM-BUG-KILN-00078 reached `Must` severity with no failing test to show for it. A test
/// can drive this with any block size and inspect the samples.
pub struct Core {
    synth: RealtimeSynth,
    player: Player,
    lp: Loop,
    playing: bool,
    solo: bool,
    scratch: Vec<f32>,
    /// Pre-allocated so the callback never allocates. `(offset_in_block, bytes, len)`.
    pending: Vec<(u64, [u8; 3], u8)>,
    pub xruns: usize,
}

impl Core {
    pub fn new(synth: RealtimeSynth, lp: Loop, max_frames: usize) -> Self {
        Core {
            synth,
            player: Player::new(),
            lp,
            playing: true,
            solo: false,
            scratch: vec![0f32; max_frames.max(4096) * 2],
            pending: Vec::with_capacity(MAX_EVENTS_PER_BLOCK),
            xruns: 0,
        }
    }

    pub fn command(&mut self, c: Cmd) {
        match c {
            Cmd::Midi(b) => self.synth.write_byte(b),
            Cmd::Play(p) => {
                self.playing = p;
                if !p {
                    all_notes_off(&mut self.synth);
                }
            }
            Cmd::Solo(s) => {
                self.solo = s;
                // Muting mid-note would strand its note-off and leave the voice
                // stuck, so silence the channels we stop feeding rather than just
                // skipping their events.
                all_notes_off(&mut self.synth);
            }
            Cmd::Panic => {
                all_notes_off(&mut self.synth);
                self.player.rewind();
            }
        }
    }

    /// Render `frames` of interleaved stereo into `buf`, applying each scheduled event at
    /// its own offset.
    ///
    /// The block is rendered in SPANS: audio up to the next event, then that event's
    /// bytes, then on. Submitting every event up front (as this used to) collapses the
    /// whole callback onto its first sample — at a 1024-frame block that is 23 ms of
    /// quantization, and an on/off pair due in the same callback never sounds at all
    /// because both are applied before any audio exists (MM-BUG-KILN-00078).
    ///
    /// Residual quantization is `RealtimeSynth`'s own 64-frame internal block, ~1.5 ms at
    /// 44.1 kHz, which is a full order of magnitude tighter than the host callback and
    /// does not depend on the device's buffer size.
    ///
    /// Returns the peak sample, or `Err` if the block could not be rendered.
    pub fn process(&mut self, buf: &mut [f32], frames: usize) -> Result<f32, ()> {
        if buf.len() < frames * 2 {
            self.xruns += 1;
            return Err(());
        }
        buf[..frames * 2].fill(0.0);

        self.pending.clear();
        if self.playing {
            let (solo, pending, xruns) = (self.solo, &mut self.pending, &mut self.xruns);
            self.player.advance(&self.lp, frames as u64, |off, msg| {
                if solo && msg[0] < 0xF0 && !GUITAR_CHANNELS.contains(&(msg[0] & 0x0F)) {
                    return;
                }
                if pending.len() == pending.capacity() {
                    // Full: keep playing rather than dropping the event, but say so.
                    *xruns += 1;
                    return;
                }
                let mut b = [0u8; 3];
                b[..msg.len()].copy_from_slice(msg);
                pending.push((off, b, msg.len() as u8));
            });
        }

        let mut done = 0usize;
        for i in 0..self.pending.len() {
            let (off, bytes, len) = self.pending[i];
            let target = (off as usize).min(frames);
            if target > done {
                if self
                    .synth
                    .render_add(target - done, &mut buf[done * 2..target * 2])
                    .is_err()
                {
                    self.xruns += 1;
                    return Err(());
                }
                done = target;
            }
            for &b in &bytes[..len as usize] {
                self.synth.write_byte(b);
            }
        }
        if done < frames
            && self
                .synth
                .render_add(frames - done, &mut buf[done * 2..frames * 2])
                .is_err()
        {
            self.xruns += 1;
            return Err(());
        }

        let mut peak = 0f32;
        for &s in &buf[..frames * 2] {
            peak = peak.max(s.abs());
        }
        Ok(peak)
    }

    pub fn active_voice_count(&self) -> usize {
        self.synth.active_voice_count()
    }

    /// [`Self::process`] plus the fan-out to a device that may not be stereo.
    ///
    /// The scratch is moved out and back rather than borrowed, because `process` takes
    /// `&mut self`. `mem::take` on a `Vec` swaps a pointer — no allocation, so this stays
    /// realtime-safe.
    pub fn fill_device(&mut self, out: &mut [f32], channels: usize) -> Result<f32, ()> {
        let frames = out.len() / channels.max(1);
        out.fill(0.0);
        let mut scratch = std::mem::take(&mut self.scratch);
        if scratch.len() < frames * 2 {
            // Should not happen after construction, and growing here would be a
            // realtime violation — count it and bail.
            self.scratch = scratch;
            self.xruns += 1;
            return Err(());
        }
        let r = self.process(&mut scratch, frames);
        if r.is_ok() {
            for f in 0..frames {
                let (l, rr) = (scratch[f * 2], scratch[f * 2 + 1]);
                match channels {
                    1 => out[f] = 0.5 * (l + rr),
                    _ => {
                        out[f * channels] = l;
                        out[f * channels + 1] = rr;
                    }
                }
            }
        }
        self.scratch = scratch;
        r
    }
}

pub fn start(rx: Consumer, midi: &[u8]) -> Result<Engine, String> {
    let host = cpal::default_host();
    let device = host
        .default_output_device()
        .ok_or_else(|| "no default output device".to_string())?;
    let device_name = device.name().unwrap_or_else(|_| "<unnamed>".into());
    let config = device
        .default_output_config()
        .map_err(|e| format!("no default output config: {e}"))?;
    let sample_rate = config.sample_rate().0;
    let channels = config.channels() as usize;

    let lp = Loop::parse(midi, f64::from(sample_rate))?;
    let synth = RealtimeSynth::new(
        RealtimeOptions::default()
            .with_sample_rate(sample_rate)
            .with_master_gain(0.8),
    );
    // Decode the embedded banks HERE, not lazily inside the callback — that is
    // what this call exists for.
    synth.prewarm_samples();

    let meters = Arc::new(Meters::default());
    let m = meters.clone();

    let mut core = Core::new(synth, lp, 4096);
    let mut last_xruns = 0usize;

    let err_meters = meters.clone();
    let stream = device
        .build_output_stream(
            &config.into(),
            move |out: &mut [f32], _| {
                // 1. Drain the UI's commands.
                while let Some(c) = rx.pop() {
                    core.command(c);
                }

                // 2. Advance the loop and render it, event by event at its own
                //    offset. All of that lives in `Core` so it is testable without a
                //    device — see `audio::tests`.
                let peak = core.fill_device(out, channels).unwrap_or(0.0);

                // 3. Telemetry. `Core` counts its own xruns; publish the delta.
                if core.xruns != last_xruns {
                    m.xruns
                        .fetch_add(core.xruns - last_xruns, Ordering::Relaxed);
                    last_xruns = core.xruns;
                }
                m.voices.store(core.active_voice_count(), Ordering::Relaxed);
                m.peak_x1e4
                    .store((peak.min(9.999) * 1e4) as u32, Ordering::Relaxed);
            },
            move |e| {
                eprintln!("audio stream error: {e}");
                err_meters.xruns.fetch_add(1, Ordering::Relaxed);
            },
            None,
        )
        .map_err(|e| format!("could not build output stream: {e}"))?;

    stream
        .play()
        .map_err(|e| format!("could not start stream: {e}"))?;
    Ok(Engine {
        _stream: stream,
        meters,
        sample_rate,
        device_name,
    })
}

fn all_notes_off(synth: &mut RealtimeSynth) {
    for ch in 0..16u8 {
        for cc in [123u8, 120] {
            synth.write_byte(0xB0 | ch);
            synth.write_byte(cc);
            synth.write_byte(0);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SR: u32 = 44_100;
    /// `RealtimeSynth`'s internal block — the residual quantization a span-splitting
    /// caller cannot beat without a timestamped command surface in the synth itself.
    const SYNTH_BLOCK: usize = 64;

    /// A one-track SMF with the given (tick, bytes) events at 480 ppq / 120 bpm, so one
    /// tick is 1/960 s and tick 1000 lands on frame 45937.
    fn smf(events: &[(u32, &[u8])]) -> Vec<u8> {
        let mut trk = vec![0x00, 0xFF, 0x51, 0x03, 0x07, 0xA1, 0x20]; // tempo 500000
        let mut last = 0u32;
        for (tick, bytes) in events {
            let mut d = tick - last;
            last = *tick;
            let mut vl = vec![d as u8 & 0x7F];
            d >>= 7;
            while d > 0 {
                vl.insert(0, (d as u8 & 0x7F) | 0x80);
                d >>= 7;
            }
            trk.extend_from_slice(&vl);
            trk.extend_from_slice(bytes);
        }
        trk.extend_from_slice(&[0x00, 0xFF, 0x2F, 0x00]);
        let mut out = b"MThd".to_vec();
        out.extend_from_slice(&[0, 0, 0, 6, 0, 0, 0, 1, 0x01, 0xE0]); // ppq 480
        out.extend_from_slice(b"MTrk");
        out.extend_from_slice(&(trk.len() as u32).to_be_bytes());
        out.extend_from_slice(&trk);
        out
    }

    fn core_for(midi: &[u8]) -> Core {
        let lp = Loop::parse(midi, f64::from(SR)).expect("parse");
        let synth = RealtimeSynth::new(RealtimeOptions::default().with_sample_rate(SR));
        Core::new(synth, lp, 4096)
    }

    /// Render `frames` total in `block`-sized callbacks; return interleaved stereo.
    fn render(core: &mut Core, frames: usize, block: usize) -> Vec<f32> {
        let mut out = vec![0f32; frames * 2];
        let mut done = 0;
        while done < frames {
            let n = block.min(frames - done);
            let mut buf = vec![0f32; n * 2];
            core.process(&mut buf, n).expect("render");
            out[done * 2..(done + n) * 2].copy_from_slice(&buf);
            done += n;
        }
        out
    }

    /// First frame whose sample exceeds `eps`.
    fn first_sound(buf: &[f32], eps: f32) -> Option<usize> {
        (0..buf.len() / 2).find(|&f| buf[f * 2].abs() > eps || buf[f * 2 + 1].abs() > eps)
    }

    /// MM-BUG-KILN-00078: a scheduled note must start at its own frame, not at the start
    /// of whatever host callback happens to contain it.
    ///
    /// Pins the FIRST CHANGED OUTPUT FRAME rather than counting emitted events — the old
    /// tests counted, which is exactly why a sequencer that dumped every event onto the
    /// block boundary passed them.
    ///
    /// Swept over host block sizes because the defect's size IS the block size: at 1024
    /// frames the note used to start 23 ms early, at 64 it would have looked almost
    /// correct. A single block size would have measured the device, not the code.
    ///
    /// The bound is `SYNTH_BLOCK`: `RealtimeSynth` applies buffered commands on its own
    /// 64-frame boundary, so that residual is not amp-lab's to remove (the report says as
    /// much). What the fix guarantees is that the error no longer scales with the host
    /// buffer.
    #[test]
    fn note_starts_at_its_own_frame_not_the_block_boundary() {
        // Tick 480 = one quarter = 0.5 s = frame 22050.
        let midi = smf(&[(480, &[0x90, 60, 100])]);
        let want = 22_050usize;
        for block in [64usize, 128, 256, 512, 1024] {
            let mut core = core_for(&midi);
            let buf = render(&mut core, want + 4096, block);
            let got = first_sound(&buf, 1e-6).unwrap_or_else(|| {
                panic!("block {block}: the note never sounded at all");
            });
            let early = want.saturating_sub(got);
            assert!(
                early <= SYNTH_BLOCK,
                "block {block}: note started at frame {got}, {early} frames before its \
                 scheduled {want} — more than the synth's own {SYNTH_BLOCK}-frame \
                 quantum, so the host block size is still leaking into the timing"
            );
            assert!(
                got <= want + SYNTH_BLOCK,
                "block {block}: note started at frame {got}, late against {want}"
            );
        }
    }

    /// An on/off pair inside ONE callback must still produce audio between them.
    ///
    /// Before the fix both bytes were submitted before any of that callback's audio was
    /// rendered, so the note was over before it began — a whole drum hit could vanish
    /// depending only on where the block boundary fell.
    #[test]
    fn an_on_off_pair_inside_one_callback_still_sounds() {
        // On at tick 480 (frame 22050), off 60 ticks later (~2756 frames) — comfortably
        // inside a single 4096-frame callback.
        let midi = smf(&[(480, &[0x90, 60, 100]), (540, &[0x80, 60, 0])]);
        let mut core = core_for(&midi);
        let buf = render(&mut core, 40_000, 4096);
        let sounded = first_sound(&buf, 1e-6);
        assert!(
            sounded.is_some(),
            "the note never sounded: both its on and off were applied before any audio \
             of that callback existed"
        );
        let got = sounded.unwrap();
        assert!(
            got + SYNTH_BLOCK >= 22_050,
            "the note started at frame {got}, far before its scheduled 22050 — the pair \
             collapsed onto the block boundary"
        );
    }
}
