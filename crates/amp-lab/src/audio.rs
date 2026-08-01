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

use crate::ring::{Cmd, Consumer, MAX_QUEUED_COMMANDS};
use crate::seq::{Loop, Player};

/// Read-only telemetry the UI polls. Atomics so neither side ever waits.
#[derive(Default)]
pub struct Meters {
    pub voices: AtomicUsize,
    /// Peak output since the last read, as a fixed-point 0..10000 of full scale.
    peak_x1e4: AtomicU32,
    pub xruns: AtomicUsize,
}

impl Meters {
    /// Retain the loudest callback until the UI consumes this polling interval.
    fn publish_peak(&self, peak: f32) {
        let peak_x1e4 = (peak.min(9.999) * 1e4) as u32;
        self.peak_x1e4.fetch_max(peak_x1e4, Ordering::Relaxed);
    }

    /// Consume the peak accumulated since the previous call.
    pub fn take_peak_x1e4(&self) -> u32 {
        self.peak_x1e4.swap(0, Ordering::Relaxed)
    }
}

pub struct Engine {
    _stream: cpal::Stream,
    pub meters: Arc<Meters>,
    pub sample_rate: u32,
    pub device_name: String,
}

/// The channel carrying the guitar we are auditioning. Solo mutes everything else.
pub const GUITAR_CHANNELS: [u8; 2] = [0, 1];

/// How many scheduled events one callback can hold before playback stops and resets.
///
/// Sized far above anything a real block produces (the shipped 8-bar loop is 614 events
/// across ~19 s, so a 1024-frame callback sees a handful). It exists only so `process`
/// can be allocation-free: pushing within capacity never allocates. Overflow is one xrun
/// and a hard reset; applying a partial batch could strand a note when its NoteOff is lost.
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
                if self.playing == p {
                    return;
                }
                self.playing = p;
                if !p {
                    all_notes_off(&mut self.synth);
                }
            }
            Cmd::Solo(s) => {
                if self.solo == s {
                    return;
                }
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
        let mut event_overflow = false;
        if self.playing {
            let (solo, pending) = (self.solo, &mut self.pending);
            self.player.advance(&self.lp, frames as u64, |off, msg| {
                if solo && msg[0] < 0xF0 && !GUITAR_CHANNELS.contains(&(msg[0] & 0x0F)) {
                    return;
                }
                if pending.len() == pending.capacity() {
                    event_overflow = true;
                    return;
                }
                let mut b = [0u8; 3];
                b[..msg.len()].copy_from_slice(msg);
                pending.push((off, b, msg.len() as u8));
            });
        }
        if event_overflow {
            // The player has advanced past events we could not retain. Never apply the
            // prefix and continue from a corrupted note state: stop at a known boundary
            // and silence every channel. Toggle the transport off and on to restart.
            self.pending.clear();
            self.xruns += 1;
            self.playing = false;
            self.player.rewind();
            all_notes_off(&mut self.synth);
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
        let channels = channels.max(1);
        let frames = out.len() / channels;
        out.fill(0.0);
        let mut scratch = std::mem::take(&mut self.scratch);

        // Render in CHUNKS of whatever the scratch holds, rather than demanding the whole
        // callback fit in it. A host is entitled to hand us a buffer larger than the
        // 4096 frames we sized for, and it typically does so on EVERY callback — so
        // bailing out (as this used to) was not a one-off underrun, it was permanent
        // silence with a rising xrun count (MM-BUG-KILN-00081).
        //
        // Chunking keeps the realtime contract: no allocation, and no reliance on the
        // host's buffer size. The sequencer stays sample-accurate because `process`
        // advances the player by exactly the frames it renders.
        let chunk = scratch.len() / 2;
        if chunk == 0 {
            self.scratch = scratch;
            self.xruns += 1;
            return Err(());
        }

        let mut peak = 0f32;
        let mut done = 0usize;
        let mut result = Ok(0.0);
        while done < frames {
            let n = chunk.min(frames - done);
            match self.process(&mut scratch, n) {
                Ok(p) => peak = peak.max(p),
                Err(()) => {
                    result = Err(());
                    break;
                }
            }
            for f in 0..n {
                let (l, rr) = (scratch[f * 2], scratch[f * 2 + 1]);
                let o = (done + f) * channels;
                match channels {
                    1 => out[o] = 0.5 * (l + rr),
                    _ => {
                        out[o] = l;
                        out[o + 1] = rr;
                    }
                }
            }
            done += n;
        }
        self.scratch = scratch;
        result.map(|_: f32| peak)
    }
}

/// Drain the complete bounded UI backlog and coalesce its idempotent controls.
///
/// Panic runs first, then the latest rig bytes, Play and Solo. This preserves recovery's
/// "panic, then restore state" order while applying repeated state only once. The fixed
/// stack buffer and the ring's 63-entry ceiling keep callback work and synth commands
/// within retained capacity.
fn drain_ui_commands(rx: &Consumer, core: &mut Core) -> usize {
    let mut commands = [Cmd::Panic; MAX_QUEUED_COMMANDS];
    let drained = rx.drain_published(&mut commands);
    let mut playing = None;
    let mut solo = None;
    let mut panic = false;

    for &command in &commands[..drained] {
        match command {
            Cmd::Midi(_) => {}
            Cmd::Play(value) => playing = Some(value),
            Cmd::Solo(value) => solo = Some(value),
            Cmd::Panic => panic = true,
        }
    }

    if panic {
        core.command(Cmd::Panic);
    }
    for &command in &commands[..drained] {
        if let Cmd::Midi(byte) = command {
            core.command(Cmd::Midi(byte));
        }
    }
    if let Some(value) = playing {
        core.command(Cmd::Play(value));
    }
    if let Some(value) = solo {
        core.command(Cmd::Solo(value));
    }
    drained
}

fn choose_f32_sample_rate(default_rate: u32, ranges: &[(u32, u32)]) -> Option<u32> {
    let supported = |rate: u32| {
        ranges
            .iter()
            .any(|&(minimum, maximum)| (minimum..=maximum).contains(&rate))
    };
    if supported(default_rate) {
        return Some(default_rate);
    }
    for preferred in [48_000, 44_100] {
        if supported(preferred) {
            return Some(preferred);
        }
    }
    ranges
        .iter()
        .flat_map(|&(minimum, maximum)| [minimum, maximum])
        .min_by_key(|&rate| (rate.abs_diff(default_rate), rate))
}

pub fn start(rx: Consumer, midi: &[u8]) -> Result<Engine, String> {
    let host = cpal::default_host();
    let device = host
        .default_output_device()
        .ok_or_else(|| "no default output device".to_string())?;
    let device_name = device.name().unwrap_or_else(|_| "<unnamed>".into());
    let default_config = device
        .default_output_config()
        .map_err(|e| format!("no default output config: {e}"))?;
    // The callback renders `&mut [f32]`, so the STREAM has to be f32. The default
    // config is not guaranteed to be: a device whose default is i16/u16 previously
    // failed to open with cpal's own error, which says nothing about the real cause
    // (MM-BUG-KILN-00081). Take the default when it is f32, else find a supported f32
    // config, else say exactly what the device offered and why we refused it.
    let config = if default_config.sample_format() == cpal::SampleFormat::F32 {
        default_config
    } else {
        let ranges: Vec<_> = device
            .supported_output_configs()
            .map_err(|e| format!("cannot enumerate output configs: {e}"))?
            .filter(|c| c.sample_format() == cpal::SampleFormat::F32)
            .collect();
        let range_bounds: Vec<_> = ranges
            .iter()
            .map(|range| (range.min_sample_rate().0, range.max_sample_rate().0))
            .collect();
        let chosen_rate = choose_f32_sample_rate(default_config.sample_rate().0, &range_bounds)
            .ok_or_else(|| {
                format!(
                    "{device_name} offers no f32 output configuration (its default is \
                     {:?}); amp-lab renders f32 and does not convert",
                    default_config.sample_format()
                )
            })?;
        ranges
            .into_iter()
            .find(|range| {
                (range.min_sample_rate().0..=range.max_sample_rate().0).contains(&chosen_rate)
            })
            .expect("the chosen rate came from these ranges")
            .with_sample_rate(cpal::SampleRate(chosen_rate))
    };
    let sample_rate = config.sample_rate().0;
    let channels = config.channels() as usize;

    let lp = Loop::parse(midi, f64::from(sample_rate))?;
    let mut synth = RealtimeSynth::new(
        RealtimeOptions::default()
            .with_sample_rate(sample_rate)
            .with_master_gain(0.8),
    );
    // Decode the embedded banks HERE, not lazily inside the callback — that is
    // what this call exists for.
    synth.prewarm_samples();
    // Same reason, different resource: a NoteOn must not grow the voice vector on the
    // audio thread (MM-BUG-KILN-00082).
    synth.reserve_realtime_storage();

    let meters = Arc::new(Meters::default());
    let m = meters.clone();

    let mut core = Core::new(synth, lp, 4096);
    let mut last_xruns = 0usize;

    let err_meters = meters.clone();
    let stream = device
        .build_output_stream(
            &config.into(),
            move |out: &mut [f32], _| {
                // 1. Drain the UI's bounded backlog and coalesce repeated state.
                drain_ui_commands(&rx, &mut core);

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
                m.publish_peak(peak);
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

    #[test]
    fn interval_peak_survives_quieter_callbacks_and_is_consumed_once() {
        let meters = Meters::default();
        meters.publish_peak(0.42);
        meters.publish_peak(1.25);
        meters.publish_peak(0.73);

        assert_eq!(meters.take_peak_x1e4(), 12_500);
        assert_eq!(meters.take_peak_x1e4(), 0);
    }

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

    /// MM-BUG-KILN-00082: the audio callback allocates nothing per BLOCK, and its only
    /// remaining allocation is bounded and attributable.
    ///
    /// The lab's contract is "no allocation on the audio thread after setup". That is not
    /// a source-review question — what allocates depends on retained capacity — so this
    /// counts real allocations through a test-only global allocator (`crate::rtalloc`),
    /// armed only around the measured call.
    ///
    /// Measured on the pre-fix tree: a steady block already allocated 0, and so did a
    /// 64-message CC burst, but PANIC allocated 17. Reserving the voice storage at setup
    /// took panic to 0. What remains is per-NoteOn: `EngineCore` builds each voice as a
    /// `Box<dyn Voice>`, which is one allocation per voice by construction. Making that
    /// allocation-free needs a voice pool in the shared engine — an architectural change
    /// to code the offline renderer uses too, tracked as MM-BUG-KILN-00092.
    ///
    /// So the bound below is a RATCHET, not an endorsement: NoteOn may allocate up to the
    /// voices it creates, and every other callback shape must stay at zero. If a future
    /// change reintroduces a per-block `Vec` growth, this reds.
    #[test]
    fn the_audio_callback_does_not_allocate_per_block() {
        use crate::rtalloc::measure;
        let mut core = core_for(&smf(&[(0, &[0x90, 60, 100]), (240, &[0x80, 60, 0])]));
        core.synth.prewarm_samples();
        core.synth.reserve_realtime_storage();
        let mut buf = vec![0f32; 1024 * 2];
        // Setup includes the first callbacks: one-shot first-use capacity is not the
        // steady-state contract.
        for _ in 0..3 {
            core.process(&mut buf, 1024).expect("warm");
        }

        let (_, steady) = measure(|| core.process(&mut buf, 1024));
        assert_eq!(steady, 0, "a steady render block allocated {steady} times");

        let (_, burst) = measure(|| {
            for i in 0..64u8 {
                core.command(Cmd::Midi(0xB0));
                core.command(Cmd::Midi(74));
                core.command(Cmd::Midi(i));
            }
            core.process(&mut buf, 1024)
        });
        assert_eq!(burst, 0, "a 64-message CC burst allocated {burst} times");

        // Playback stopped first, so this measures PANIC's own cost. With the loop
        // running, the rewind restarts it and the tick-0 NoteOn spawns a voice — the
        // Box below, attributed to the wrong cause.
        core.command(Cmd::Play(false));
        core.process(&mut buf, 1024).expect("settle");
        let (_, panic_) = measure(|| {
            core.command(Cmd::Panic);
            core.process(&mut buf, 1024)
        });
        assert_eq!(panic_, 0, "panic + all-notes-off allocated {panic_} times");

        // Still stopped, so exactly ONE voice spawns and the count is per-voice rather
        // than per-voice times whatever the sequencer happened to play.
        let (_, note) = measure(|| {
            core.command(Cmd::Midi(0x90));
            core.command(Cmd::Midi(60));
            core.command(Cmd::Midi(100));
            core.process(&mut buf, 1024)
        });
        assert!(
            note <= 16,
            "a single NoteOn allocated {note} times — the per-voice Box is ~13; more              than that means something new allocates in the callback (KILN-00092)"
        );
    }

    #[test]
    fn ui_backlog_is_bounded_and_does_not_grow_the_synth_queue() {
        use crate::amp::Rig;
        use crate::outbox::Outbox;
        use crate::ring::Ring;
        use crate::rtalloc::measure;

        let (tx, rx) = Ring::channel();
        let mut outbox = Outbox::new(tx, 1);
        let mut rig = Rig::default();
        let mut core = core_for(&smf(&[]));
        core.synth.prewarm_samples();
        core.synth.reserve_realtime_storage();
        let mut buf = vec![0f32; 1024 * 2];
        // Warm the initial rig outside the measured steady-state callback. Program and
        // insert setup has bounded first-use work unrelated to backlog growth.
        outbox.send_rig(&rig);
        drain_ui_commands(&rx, &mut core);
        core.process(&mut buf, 1024).expect("warm");

        // The old incremental path emitted three completed CC messages per knob. Fifty
        // updates therefore exceeded RealtimeSynth's retained 128-command queue before
        // the next render; the bounded snapshot path must coalesce them instead.
        for value in 0..50u8 {
            rig.vals[0] = value;
            outbox.send_knob(&rig, 0);
        }

        let ((drained, rendered), allocations) = measure(|| {
            let drained = drain_ui_commands(&rx, &mut core);
            (drained, core.process(&mut buf, 1024))
        });
        rendered.expect("backlog render");
        assert!(
            drained <= MAX_QUEUED_COMMANDS && allocations == 0,
            "one callback drained {drained} UI commands and allocated {allocations} times; \
             the command budget is {MAX_QUEUED_COMMANDS} and retained control traffic \
             must allocate zero"
        );
    }

    #[test]
    fn a_full_mixed_ui_ring_is_coalesced_without_allocating() {
        use crate::amp::Rig;
        use crate::outbox::Outbox;
        use crate::ring::Ring;
        use crate::rtalloc::measure;

        let (tx, rx) = Ring::channel();
        let mut outbox = Outbox::new(tx, 1);
        let rig = Rig::default();
        let mut core = core_for(&smf(&[]));
        core.synth.prewarm_samples();
        core.synth.reserve_realtime_storage();
        let mut buf = vec![0f32; 1024 * 2];

        // Warm first-use rig setup, then fill all 63 slots with one 61-command state
        // snapshot and two panic requests. A third panic becomes the held recovery item.
        outbox.send_rig(&rig);
        drain_ui_commands(&rx, &mut core);
        core.process(&mut buf, 1024).expect("warm");
        outbox.send_rig(&rig);
        outbox.request_panic();
        outbox.request_panic();
        outbox.request_panic();
        assert!(
            outbox.saturated(),
            "the full-ring panic was not held for retry"
        );

        let ((drained, rendered), allocations) = measure(|| {
            let drained = drain_ui_commands(&rx, &mut core);
            (drained, core.process(&mut buf, 1024))
        });
        rendered.expect("full mixed backlog render");
        assert_eq!(drained, MAX_QUEUED_COMMANDS, "ring was not actually full");
        assert_eq!(
            allocations, 0,
            "a full mixed UI ring allocated {allocations} times in the callback"
        );

        outbox.pump(&rig, true, false);
        assert!(
            !outbox.saturated(),
            "held panic did not recover after the drain"
        );
    }

    #[test]
    fn realtime_bucket_reservation_covers_the_single_channel_voice_cap() {
        use crate::rtalloc::measure;

        fn allocations_for_next_voice(existing: usize, channels: u8) -> usize {
            let options = RealtimeOptions::default()
                .with_sample_rate(SR)
                .with_reverb(0.0)
                .with_echo(0.0)
                .with_samples(false);
            let mut synth = RealtimeSynth::new(options);
            synth.reserve_realtime_storage();
            let mut buf = vec![0.0f32; SYNTH_BLOCK * 2];

            for key in 0..existing {
                synth.write_byte(0x90 | (key as u8 % channels));
                synth.write_byte(key as u8);
                synth.write_byte(80);
                buf.fill(0.0);
                synth.render_add(SYNTH_BLOCK, &mut buf).unwrap();
            }
            assert_eq!(synth.active_voice_count(), existing);

            let (_, allocations) = measure(|| {
                synth.write_byte(0x90);
                synth.write_byte(existing as u8);
                synth.write_byte(80);
                buf.fill(0.0);
                synth.render_add(SYNTH_BLOCK, &mut buf)
            });
            assert_eq!(synth.active_voice_count(), existing + 1);
            allocations
        }

        // Match each crowded case against the SAME next key and total polyphony with
        // prior voices spread across channels. Voice-model allocation counts vary by
        // key, so comparing key 127 with key 63 would not isolate bucket growth.
        let spread_65 = allocations_for_next_voice(64, 2);
        let crowded_65 = allocations_for_next_voice(64, 1);
        assert_eq!(
            crowded_65, spread_65,
            "same-channel voice 65 allocated {crowded_65} times versus the matched \
             spread-channel control's {spread_65}; \
             the same-channel index bucket grew inside the callback"
        );

        let spread_128 = allocations_for_next_voice(127, 3);
        let crowded_128 = allocations_for_next_voice(127, 1);
        assert_eq!(
            crowded_128, spread_128,
            "same-channel voice 128 allocated {crowded_128} times versus the matched \
             spread-channel control's {spread_128}; \
             setup did not reserve the bucket through the live cap"
        );
    }

    /// MM-BUG-KILN-00127: a prewarmed sampled drum NoteOn allocates only its
    /// engine-owned `Box<dyn Voice>`. Selecting the take itself must use direct
    /// bounded indexing, without formatting a file name or scanning the bank.
    #[test]
    fn sampled_drum_note_on_does_not_allocate_for_take_lookup() {
        use crate::rtalloc::measure;

        let mut core = core_for(&smf(&[]));
        core.synth.prewarm_samples();
        core.synth.reserve_realtime_storage();
        let mut buf = vec![0f32; 1024 * 2];
        core.process(&mut buf, 1024).expect("warm");
        core.command(Cmd::Play(false));
        core.process(&mut buf, 1024).expect("settle");

        let (_, allocations) = measure(|| {
            core.command(Cmd::Midi(0x99));
            core.command(Cmd::Midi(38));
            core.command(Cmd::Midi(100));
            core.process(&mut buf, 1024)
        });
        assert_eq!(
            allocations, 1,
            "a prewarmed sampled snare NoteOn allocated {allocations} times; \
             only its engine-owned Box<dyn Voice> is expected"
        );
    }

    /// MM-BUG-KILN-00081: a callback LARGER than the scratch must still produce audio.
    ///
    /// `fill_device` used to require the whole callback to fit in its 4096-frame scratch
    /// and return `Err` otherwise. A host that picks a bigger buffer does so on every
    /// callback, so that was not a one-off underrun — it was permanent silence with a
    /// rising xrun count, on a configuration cpal considers perfectly valid.
    ///
    /// Sizes below, at and above the scratch, because the boundary is exactly where the
    /// old code changed behaviour.
    #[test]
    fn any_callback_size_produces_audio() {
        for &frames in &[1024usize, 4096, 4097, 8192] {
            let mut core = core_for(&smf(&[(0, &[0x90, 60, 100]), (960, &[0x80, 60, 0])]));
            let mut out = vec![0f32; frames * 2];
            let before = core.xruns;
            let peak = core
                .fill_device(&mut out, 2)
                .unwrap_or_else(|()| panic!("{frames}-frame callback failed to render"));
            assert!(
                peak > 0.0,
                "{frames}-frame callback rendered silence (peak {peak})"
            );
            assert_eq!(
                core.xruns, before,
                "{frames}-frame callback counted an xrun"
            );
        }
    }

    /// The chunked path must not change WHAT is rendered — only how many passes it takes.
    ///
    /// One 8192-frame callback and eight 1024-frame callbacks are the same span of the
    /// same loop, so they must produce the same samples. This is what proves chunking did
    /// not disturb the sequencer's frame accounting.
    #[test]
    fn chunking_does_not_change_the_audio() {
        let midi = smf(&[(0, &[0x90, 60, 100]), (960, &[0x80, 60, 0])]);
        let mut one = core_for(&midi);
        let mut many = core_for(&midi);
        let frames = 8192usize;

        let mut big = vec![0f32; frames * 2];
        one.fill_device(&mut big, 2).expect("one big callback");

        let mut small = vec![0f32; frames * 2];
        for c in 0..8 {
            let mut buf = vec![0f32; 1024 * 2];
            many.fill_device(&mut buf, 2).expect("small callback");
            small[c * 1024 * 2..(c + 1) * 1024 * 2].copy_from_slice(&buf);
        }
        assert_eq!(big, small, "chunked output differs from one-shot output");
    }

    /// Mono and multichannel devices get the stereo render mapped, not dropped.
    #[test]
    fn device_channel_counts_are_mapped() {
        let midi = smf(&[(0, &[0x90, 60, 100]), (960, &[0x80, 60, 0])]);
        for &ch in &[1usize, 2, 4] {
            let mut core = core_for(&midi);
            let mut out = vec![0f32; 5000 * ch];
            let peak = core.fill_device(&mut out, ch).expect("render");
            assert!(peak > 0.0, "{ch}-channel device rendered silence");
            if ch > 2 {
                // Channels beyond the first pair stay silent rather than being fed
                // garbage; the buffer was zeroed and never written there.
                let mut extra = 0f32;
                for f in 0..5000 {
                    for c in 2..ch {
                        extra += out[f * ch + c].abs();
                    }
                }
                assert_eq!(extra, 0.0, "{ch}-channel device got noise on the extras");
            }
        }
    }

    #[test]
    fn event_overflow_stops_and_resets_instead_of_losing_note_offs() {
        let synth = RealtimeSynth::new(
            RealtimeOptions::default()
                .with_sample_rate(SR)
                .with_reverb(0.0)
                .with_echo(0.0)
                .with_samples(false),
        );
        let mut core = Core::new(
            synth,
            Loop {
                events: Vec::new(),
                frames: 64,
            },
            64,
        );
        for byte in [0x90, 60, 100] {
            core.command(Cmd::Midi(byte));
        }
        let mut out = vec![0.0; 128];
        core.process(&mut out, 64).expect("prime one voice");
        assert!(
            core.active_voice_count() > 0,
            "the reset has no live voice to prove"
        );

        let mut events = Vec::new();
        for key in 0..150u64 {
            events.push(crate::seq::Event {
                frame: 0,
                bytes: [0x90, (key % 128) as u8, 100],
                len: 3,
            });
            events.push(crate::seq::Event {
                frame: 1,
                bytes: [0x80, (key % 128) as u8, 0],
                len: 3,
            });
        }
        core.lp = Loop { events, frames: 64 };
        core.player.rewind();
        core.playing = true;

        core.process(&mut out, 64)
            .expect("overflow fallback renders safely");

        assert_eq!(core.xruns, 1, "one dense block is one explicit overflow");
        assert!(
            !core.playing,
            "the corrupted sequence must not keep advancing"
        );
        assert_eq!(
            core.player.pos, 0,
            "resume must start from a known boundary"
        );
        assert_eq!(
            core.active_voice_count(),
            0,
            "the hard reset must prevent a stuck note"
        );
        assert!(
            core.pending.is_empty(),
            "no partial event batch may be applied"
        );
    }

    #[test]
    fn f32_fallback_rate_follows_the_normal_rate_policy() {
        assert_eq!(
            choose_f32_sample_rate(44_100, &[(8_000, 192_000)]),
            Some(44_100),
            "use the device default when f32 supports it"
        );
        assert_eq!(
            choose_f32_sample_rate(32_000, &[(48_000, 192_000)]),
            Some(48_000),
            "prefer 48 kHz over the range maximum"
        );
        assert_eq!(
            choose_f32_sample_rate(32_000, &[(44_100, 44_100), (96_000, 192_000)]),
            Some(44_100),
            "fall back to 44.1 kHz when 48 kHz is unavailable"
        );
        assert_eq!(
            choose_f32_sample_rate(50_000, &[(32_000, 40_000), (60_000, 96_000)]),
            Some(40_000),
            "otherwise clamp to the nearest supported boundary"
        );
        assert_eq!(choose_f32_sample_rate(48_000, &[]), None);
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
