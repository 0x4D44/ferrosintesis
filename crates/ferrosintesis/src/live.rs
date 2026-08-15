//! Realtime raw-MIDI byte input and block-render API.

use crate::engine::{CoreOptions, EngineCore};
use crate::midi::{decode_sysex_payload, EvKind};
use crate::sampler;

const LIVE_BLOCK: usize = 64;
/// Longest modeled SysEx payload, excluding F0/F7 (GS DT1 reset/rhythm).
const SYSEX_CAPTURE_LEN: usize = 9;

/// Global polyphony ceiling for the realtime path. A dense live stream can stack
/// hundreds of un-released voices, and rendering them all per block would blow
/// the audio-callback deadline; capping bounds that worst case. Generous enough
/// that real playing never hits it (a full ensemble plus pedal tails sits well
/// under it) while still bounding the pathological case. Tunable — raise for more
/// headroom, lower to protect a tighter deadline. Offline rendering ignores this
/// entirely (no deadline → unbounded polyphony).
const LIVE_MAX_VOICES: usize = 128;

/// How many completed MIDI commands the queue between [`RealtimeSynth::write_byte`]
/// and the next [`RealtimeSynth::render_add`] block can hold.
///
/// MM-BUG-CRUCIBLE-00025: this queue used to be a growable `Vec`, so a caller feeding
/// valid messages without rendering grew memory without limit, and the next audio
/// callback then applied the whole backlog — an unbounded stall on a deadline-bearing
/// thread. A fixed budget makes both bounded, and because the block drains the whole
/// queue, one constant bounds storage *and* per-block work.
///
/// Sized against real traffic, not guesswork: a 31 250-baud MIDI port delivers roughly
/// one message per millisecond and a block is 64 frames (1.45 ms at 44.1 kHz), so a
/// block's honest worst case is a handful of commands. A host that buffers a scheduling
/// hiccup and delivers 100 ms in one go still lands around 300. 1024 clears that with
/// margin while costing a few KB of inline storage.
const LIVE_MAX_PENDING: usize = 1024;

/// The fixed-capacity command queue between `write_byte` and `render_add`.
///
/// Overflow policy is **drop the newest and count it**: the queue never allocates,
/// never reorders what it does keep, and the loss is observable through
/// [`RealtimeSynth::dropped_command_count`]. Dropping the newest rather than the
/// oldest keeps the applied prefix a contiguous, in-order piece of the caller's
/// stream, which is what makes the behaviour deterministic to reason about.
#[derive(Debug, Clone)]
pub(crate) struct PendingQueue {
    commands: [LiveCommand; LIVE_MAX_PENDING],
    len: usize,
    dropped: u64,
}

impl PendingQueue {
    pub(crate) fn new() -> Self {
        Self {
            commands: [LiveCommand::SystemReset; LIVE_MAX_PENDING],
            len: 0,
            dropped: 0,
        }
    }

    /// Queue one command, or count it as dropped if the budget is spent.
    pub(crate) fn push(&mut self, command: LiveCommand) {
        if self.len < LIVE_MAX_PENDING {
            self.commands[self.len] = command;
            self.len += 1;
        } else {
            self.dropped = self.dropped.saturating_add(1);
        }
    }

    pub(crate) fn as_slice(&self) -> &[LiveCommand] {
        &self.commands[..self.len]
    }

    pub(crate) fn len(&self) -> usize {
        self.len
    }

    #[cfg(test)]
    pub(crate) fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Forget the queued commands. Does NOT reset the dropped counter, which is
    /// cumulative for the synth's lifetime.
    pub(crate) fn clear(&mut self) {
        self.len = 0;
    }

    pub(crate) fn dropped(&self) -> u64 {
        self.dropped
    }
}

/// How to configure a [`RealtimeSynth`].
///
/// Start from [`RealtimeOptions::default`] and refine with the `with_*` builders. As
/// with [`Options`](crate::offline::Options), the fields are private so that a future
/// minor release can add or rename a knob without breaking you.
///
/// ```
/// use ferrosintesis::live::RealtimeOptions;
///
/// let opt = RealtimeOptions::default()
///     .with_sample_rate(48_000)
///     .with_master_gain(0.5);
///
/// assert_eq!(opt.sample_rate(), 48_000);
/// ```
#[derive(Debug, Clone, Copy, PartialEq)]
#[non_exhaustive]
pub struct RealtimeOptions {
    pub(crate) sample_rate: u32,
    pub(crate) wet: f32,
    pub(crate) delay_s: f32,
    pub(crate) samples: bool,
    pub(crate) master_gain: f32,
}

impl Default for RealtimeOptions {
    fn default() -> Self {
        Self {
            sample_rate: 44_100,
            wet: 0.32,
            delay_s: 0.375,
            samples: true,
            master_gain: 0.70,
        }
    }
}

impl RealtimeOptions {
    /// Set the output sample rate in Hz. Default 44100.
    pub fn with_sample_rate(mut self, sample_rate: u32) -> Self {
        self.sample_rate = sample_rate;
        self
    }

    /// Set the reverb send, 0.0 (dry) to 1.0. Default 0.32.
    pub fn with_reverb(mut self, wet: f32) -> Self {
        self.wet = wet;
        self
    }

    /// Set the echo time in seconds. Pass 0.0 to disable the echo bus. Default 0.375.
    pub fn with_echo(mut self, delay_s: f32) -> Self {
        self.delay_s = delay_s;
        self
    }

    /// Enable or disable the embedded PCM attack-sample layer. Default true.
    pub fn with_samples(mut self, samples: bool) -> Self {
        self.samples = samples;
        self
    }

    /// Set the master output gain applied to the mix. Default 0.70.
    pub fn with_master_gain(mut self, master_gain: f32) -> Self {
        self.master_gain = master_gain;
        self
    }

    /// The output sample rate in Hz.
    pub fn sample_rate(&self) -> u32 {
        self.sample_rate
    }

    /// The reverb send, 0.0 (dry) to 1.0.
    pub fn reverb(&self) -> f32 {
        self.wet
    }

    /// The echo time in seconds; 0.0 means the echo bus is disabled.
    pub fn echo(&self) -> f32 {
        self.delay_s
    }

    /// Whether the embedded PCM attack-sample layer is enabled.
    pub fn samples(&self) -> bool {
        self.samples
    }

    /// The master output gain applied to the mix.
    pub fn master_gain(&self) -> f32 {
        self.master_gain
    }
}

/// Why a realtime block render failed.
///
/// Both the enum and its data-carrying variants are `#[non_exhaustive]`: match with a
/// `_` arm, and match variants with `..`. New variants — and new fields on existing
/// ones — may be added in a minor release.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum RealtimeError {
    /// The output slice passed to [`RealtimeSynth::render_add`] is too short for the
    /// requested frame count. It needs `frames * 2` samples (interleaved stereo).
    #[non_exhaustive]
    OutputTooSmall {
        /// Samples required: `frames * 2` (saturating).
        needed: usize,
        /// Samples actually supplied.
        got: usize,
        /// Frames requested, as passed to [`RealtimeSynth::render_add`].
        frames: usize,
    },
}

impl std::fmt::Display for RealtimeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RealtimeError::OutputTooSmall {
                needed,
                got,
                frames,
            } => write!(
                f,
                "output buffer too small: {frames} frames need {needed} samples \
                 (interleaved stereo), got {got}"
            ),
        }
    }
}

impl std::error::Error for RealtimeError {}

/// A realtime General MIDI synthesizer: raw MIDI bytes in, stereo audio blocks out.
///
/// Feed it the bytes of a live MIDI stream with [`write_byte`](Self::write_byte) — it
/// parses running status and interleaved realtime bytes itself — then pull audio with
/// [`render_add`](Self::render_add) from your audio callback.
///
/// This is the same engine and the same voices as [`offline`](crate::offline); the crate
/// is offline-first, and this is the secondary surface.
pub struct RealtimeSynth {
    core: EngineCore,
    parser: MidiByteParser,
    pending: PendingQueue,
    ring: [f32; LIVE_BLOCK * 2],
    ring_pos: usize,
    ring_len: usize,
    master_gain: f32,
}

impl RealtimeSynth {
    /// Create a synth. Voices, buses and reverb are sized for `options.sample_rate`,
    /// so the rate cannot change afterwards — build a new synth instead.
    pub fn new(options: RealtimeOptions) -> Self {
        let core = EngineCore::new(CoreOptions {
            sr: options.sample_rate as f32,
            wet: options.wet,
            delay_s: options.delay_s,
            samples: options.samples,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        });
        Self {
            core,
            parser: MidiByteParser::new(),
            // Inline fixed storage: a completed MIDI message pushes here from the audio
            // thread, so it must neither allocate (MM-BUG-KILN-00082) nor grow without
            // limit (MM-BUG-CRUCIBLE-00025).
            pending: PendingQueue::new(),
            ring: [0.0; LIVE_BLOCK * 2],
            ring_pos: 0,
            ring_len: 0,
            master_gain: options.master_gain,
        }
    }

    /// Silence every voice, clear the effect tanks, and reset the MIDI parser to a
    /// clean running-status state. Equivalent to a panic / all-notes-off button.
    pub fn reset(&mut self) {
        self.core.hard_reset();
        self.parser.reset();
        self.pending.clear();
        self.ring.fill(0.0);
        self.ring_pos = 0;
        self.ring_len = 0;
    }

    /// Decode the embedded attack-sample banks now, on this thread.
    ///
    /// The banks decode lazily on first use, which would otherwise happen inside your
    /// audio callback and blow the deadline. Call this once during setup, off the
    /// realtime thread. A no-op without the `embedded-samples` feature.
    ///
    /// This decodes **every** bank, not just the ones a default program set reaches —
    /// a live stream can select any program or alternate bank at any moment, so a
    /// partial prewarm leaves exactly the dropout this call exists to prevent. That is
    /// the trade you are opting into: it costs setup time and holds the decoded PCM
    /// resident for the process lifetime. Ordinary PCM16 banks expand to roughly twice
    /// their embedded bytes. The B1's 3.35 MB byte-companded natural tails expand to
    /// about 13.4 MB. If you would rather pay in occasional first-use stalls, simply do
    /// not call it.
    pub fn prewarm_samples(&self) {
        sampler::prewarm();
    }

    /// Reserve the voice and per-channel index storage a live session can need, so a
    /// NoteOn or the following bucket rebuild does not grow a `Vec` on the audio thread
    /// (MM-BUG-KILN-00082, MM-BUG-CRUCIBLE-00006).
    ///
    /// Separate from [`prewarm_samples`](Self::prewarm_samples) because it is not about
    /// samples: a `--no-samples` build needs this just as much. Call both at setup.
    pub fn reserve_realtime_storage(&mut self) {
        self.core.reserve_voices(LIVE_MAX_VOICES);
    }

    /// Feed one byte of a live MIDI stream.
    ///
    /// The parser tracks running status and tolerates realtime bytes (clock, active
    /// sensing) interleaved mid-message, so you can hand it a raw port's bytes verbatim.
    /// Bytes are buffered and take effect at the start of the next
    /// [`render_add`](Self::render_add) block.
    ///
    /// The buffer between the two calls is **fixed-size**, so neither its memory nor
    /// the work the next block does can grow without limit. Completing more than 1024
    /// commands before a block drops the excess — the newest — and counts it in
    /// [`dropped_command_count`](Self::dropped_command_count). Real traffic does not
    /// come close: that is roughly 700 times what a 1.45 ms block can carry at MIDI
    /// wire rate.
    pub fn write_byte(&mut self, byte: u8) {
        self.parser.push(byte, &mut self.pending);
    }

    /// How many MIDI commands have been dropped because the queue between
    /// [`write_byte`](Self::write_byte) and [`render_add`](Self::render_add) was full.
    ///
    /// Cumulative for the life of the synth, and **not** cleared by
    /// [`reset`](Self::reset) — a caller polling it wants to notice that it once
    /// overran, not just that it is not overrunning now. A nonzero value means you are
    /// feeding faster than you render; render more often, or feed less.
    pub fn dropped_command_count(&self) -> u64 {
        self.pending.dropped()
    }

    /// Render `frames` frames and **add** them into `output`.
    ///
    /// `output` is interleaved stereo, so it must hold at least `frames * 2` samples.
    /// This call is **additive**: it sums into whatever is already there rather than
    /// overwriting, so zero the buffer first if you want the synth alone.
    ///
    /// # Errors
    ///
    /// [`RealtimeError::OutputTooSmall`] if `output.len() < frames * 2`. Nothing is
    /// written and no MIDI state is consumed, so the call is safe to retry.
    pub fn render_add(&mut self, frames: usize, output: &mut [f32]) -> Result<(), RealtimeError> {
        let needed = frames.saturating_mul(2);
        if output.len() < needed {
            return Err(RealtimeError::OutputTooSmall {
                needed,
                got: output.len(),
                frames,
            });
        }

        let mut written = 0usize;
        while written < frames {
            if self.ring_len == 0 {
                self.fill_ring();
            }
            let take = (frames - written).min(self.ring_len);
            let src = self.ring_pos * 2;
            let dst = written * 2;
            for i in 0..take * 2 {
                output[dst + i] += self.ring[src + i];
            }
            self.ring_pos += take;
            self.ring_len -= take;
            written += take;
            if self.ring_len == 0 {
                self.ring_pos = 0;
            }
        }
        Ok(())
    }

    /// How many voices are sounding right now. Useful as a load meter.
    pub fn active_voice_count(&self) -> usize {
        self.core.active_voice_count()
    }

    fn fill_ring(&mut self) {
        // Bounded by LIVE_MAX_PENDING: the queue cannot hold more, so the block
        // cannot apply more (MM-BUG-CRUCIBLE-00025). Indexed rather than iterated
        // so the queue and the core can be borrowed as the disjoint fields they are.
        for i in 0..self.pending.len() {
            let command = self.pending.as_slice()[i];
            match command {
                LiveCommand::Channel(kind) => self.core.handle_event(kind),
                LiveCommand::SystemReset => self.core.hard_reset(),
            }
        }
        self.pending.clear();
        // Bound polyphony before the (deadline-bearing) block render — this is
        // the ONLY caller of enforce_voice_cap, so offline stays unbounded and
        // bit-identical (MM-BUG-KILN-00013).
        self.core.enforce_voice_cap(LIVE_MAX_VOICES);
        self.ring.fill(0.0);
        self.core.render_block_add(LIVE_BLOCK, &mut self.ring);
        for x in &mut self.ring {
            *x = realtime_limit(*x * self.master_gain);
        }
        self.ring_pos = 0;
        self.ring_len = LIVE_BLOCK;
    }
}

#[inline]
fn realtime_limit(x: f32) -> f32 {
    if x.abs() <= 0.95 {
        x
    } else {
        0.95 * (x / 0.95).tanh()
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum LiveCommand {
    Channel(EvKind),
    SystemReset,
}

#[derive(Debug, Clone)]
pub(crate) struct MidiByteParser {
    running: Option<u8>,
    status: Option<u8>,
    data: [u8; 2],
    len: usize,
    needed: usize,
    in_sysex: bool,
    sysex: [u8; SYSEX_CAPTURE_LEN],
    sysex_len: usize,
    sysex_overflow: bool,
}

impl MidiByteParser {
    fn new() -> Self {
        Self {
            running: None,
            status: None,
            data: [0; 2],
            len: 0,
            needed: 0,
            in_sysex: false,
            sysex: [0; SYSEX_CAPTURE_LEN],
            sysex_len: 0,
            sysex_overflow: false,
        }
    }

    pub(crate) fn reset(&mut self) {
        self.running = None;
        self.status = None;
        self.len = 0;
        self.needed = 0;
        self.in_sysex = false;
        self.sysex_len = 0;
        self.sysex_overflow = false;
    }

    pub(crate) fn push(&mut self, byte: u8, out: &mut PendingQueue) {
        if self.in_sysex {
            self.push_sysex(byte, out);
            return;
        }

        if byte >= 0x80 {
            self.push_status(byte, out);
            return;
        }

        let Some(status) = self.status.or(self.running) else {
            return;
        };
        if self.status.is_none() {
            self.status = Some(status);
            self.needed = data_len(status).unwrap_or(0);
            self.len = 0;
        }
        self.push_data(byte, out);
    }

    fn push_sysex(&mut self, byte: u8, out: &mut PendingQueue) {
        match byte {
            0xF8..=0xFE => {}
            0xFF => {
                out.push(LiveCommand::SystemReset);
                self.reset();
            }
            0xF7 => {
                if !self.sysex_overflow {
                    if let Some(kind) = decode_sysex_payload(&self.sysex[..self.sysex_len]) {
                        out.push(LiveCommand::Channel(kind));
                    }
                }
                self.reset();
            }
            0xF0 => {
                // A nested F0 restarts the partial message.
                self.reset();
                self.push_status(0xF0, out);
            }
            b @ 0x00..=0x7F => {
                if self.sysex_len < self.sysex.len() {
                    self.sysex[self.sysex_len] = b;
                    self.sysex_len += 1;
                } else {
                    self.sysex_overflow = true;
                }
            }
            status @ 0x80..=0xEF | status @ 0xF1..=0xF6 => {
                // Any non-realtime status terminates malformed SysEx. Reprocess
                // it so a missing F7 cannot swallow channel/system traffic.
                self.reset();
                self.push_status(status, out);
            }
        }
    }

    fn push_status(&mut self, status: u8, out: &mut PendingQueue) {
        match status {
            0x80..=0xEF => {
                self.running = Some(status);
                self.status = Some(status);
                self.needed = data_len(status).unwrap();
                self.len = 0;
            }
            0xF0 => {
                self.running = None;
                self.status = None;
                self.len = 0;
                self.needed = 0;
                self.in_sysex = true;
                self.sysex_len = 0;
                self.sysex_overflow = false;
            }
            0xF1 | 0xF3 => {
                self.running = None;
                self.status = Some(status);
                self.needed = 1;
                self.len = 0;
            }
            0xF2 => {
                self.running = None;
                self.status = Some(status);
                self.needed = 2;
                self.len = 0;
            }
            0xF4..=0xF7 => {
                self.running = None;
                self.status = None;
                self.len = 0;
                self.needed = 0;
            }
            0xF8..=0xFE => {}
            0xFF => {
                out.push(LiveCommand::SystemReset);
                self.reset();
            }
            _ => {}
        }
    }

    fn push_data(&mut self, byte: u8, out: &mut PendingQueue) {
        if self.len < self.data.len() {
            self.data[self.len] = byte;
        }
        self.len += 1;
        if self.len < self.needed {
            return;
        }

        let status = self.status.unwrap();
        if status < 0xF0 {
            if let Some(kind) = channel_event(status, &self.data[..self.needed]) {
                out.push(LiveCommand::Channel(kind));
            }
            self.status = None;
        } else {
            self.status = None;
        }
        self.len = 0;
        self.needed = 0;
    }
}

fn data_len(status: u8) -> Option<usize> {
    match status & 0xF0 {
        0x80 | 0x90 | 0xA0 | 0xB0 | 0xE0 => Some(2),
        0xC0 | 0xD0 => Some(1),
        _ => None,
    }
}

fn channel_event(status: u8, data: &[u8]) -> Option<EvKind> {
    let ch = status & 0x0F;
    match status & 0xF0 {
        0x80 => Some(EvKind::NoteOff { ch, key: data[0] }),
        0x90 => {
            let key = data[0];
            let vel = data[1];
            Some(if vel == 0 {
                EvKind::NoteOff { ch, key }
            } else {
                EvKind::NoteOn { ch, key, vel }
            })
        }
        0xA0 => Some(EvKind::PolyAftertouch {
            ch,
            key: data[0],
            val: data[1],
        }),
        0xB0 => Some(EvKind::Cc {
            ch,
            num: data[0],
            val: data[1],
        }),
        0xC0 => Some(EvKind::Prog { ch, prog: data[0] }),
        0xD0 => Some(EvKind::Aftertouch { ch, val: data[0] }),
        0xE0 => {
            let raw = ((data[1] as i32) << 7) | data[0] as i32;
            Some(EvKind::Bend {
                ch,
                semis: (raw - 8192) as f32 / 8192.0 * 2.0,
            })
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn opts() -> RealtimeOptions {
        RealtimeOptions {
            sample_rate: 44_100,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            master_gain: 1.0,
        }
    }

    /// Spawn `n` distinct (channel, key) melodic voices with no note-offs, then
    /// render one block so the pending note-ons are applied. Distinct pairs (and
    /// skipping the drum channel 9) keep every note a fresh voice rather than a
    /// same-key retrigger. Returns the live voice count after the block.
    fn spawn_voices_and_render(synth: &mut RealtimeSynth, n: usize) -> usize {
        let mut spawned = 0usize;
        'outer: for ch in 0u8..9 {
            for key in 21u8..=108 {
                synth.write_byte(0x90 | ch);
                synth.write_byte(key);
                synth.write_byte(80);
                spawned += 1;
                if spawned >= n {
                    break 'outer;
                }
            }
        }
        let mut out = vec![0f32; LIVE_BLOCK * 2];
        synth.render_add(LIVE_BLOCK, &mut out).unwrap();
        synth.active_voice_count()
    }

    /// MM-BUG-KILN-00013: the realtime path caps total polyphony. A stream that
    /// stacks far more un-released voices than the cap must be stolen back down
    /// to `LIVE_MAX_VOICES`, not left unbounded to blow the callback deadline.
    #[test]
    fn live_polyphony_is_capped() {
        let mut synth = RealtimeSynth::new(opts());
        let count = spawn_voices_and_render(&mut synth, LIVE_MAX_VOICES + 40);
        assert_eq!(
            count, LIVE_MAX_VOICES,
            "live polyphony not capped at {LIVE_MAX_VOICES}: got {count}"
        );
    }

    /// The cap must not fire spuriously: a normal voice count well under the
    /// ceiling keeps every voice.
    #[test]
    fn live_under_cap_steals_nothing() {
        let mut synth = RealtimeSynth::new(opts());
        let n = 40;
        let count = spawn_voices_and_render(&mut synth, n);
        assert_eq!(count, n, "voices stolen below the cap");
    }

    /// Feed `count` complete, perfectly valid non-voice messages (CC 7 volume on
    /// channel 0) without rendering. Returns the last value sent.
    fn flood_controllers(synth: &mut RealtimeSynth, count: usize) -> u8 {
        let mut last = 0u8;
        for i in 0..count {
            last = (i % 128) as u8;
            synth.write_byte(0xB0);
            synth.write_byte(7);
            synth.write_byte(last);
        }
        last
    }

    /// MM-BUG-CRUCIBLE-00025: storage between `write_byte` and `render_add` is
    /// bounded, and the overflow is counted rather than silent.
    ///
    /// The old `Vec` grew with the burst: three times the budget in valid CC
    /// messages meant three times the memory and three times the work in the next
    /// audio callback. Non-voice messages on purpose — they spawn nothing, so the
    /// only thing under test is the queue itself.
    ///
    /// Deliberately NOT asserted against `LIVE_MAX_PENDING`: the queue derives its
    /// own length from that same constant, so such an assertion could only agree
    /// with itself and would still pass if the budget were raised to infinity. The
    /// claims here are independent of its value — the queue kept strictly fewer
    /// commands than were fed (so it is bounded at all), it sits under an absolute
    /// ceiling (so the budget is a realtime-sane size), and kept + dropped equals
    /// fed (so nothing was lost silently, which is the property the counter is for).
    #[test]
    fn pending_queue_is_bounded_and_counts_drops() {
        let fed = 30_000usize;
        let mut synth = RealtimeSynth::new(opts());
        flood_controllers(&mut synth, fed);

        let kept = synth.pending.len();
        let dropped = synth.dropped_command_count();
        assert!(
            kept < fed,
            "queue absorbed the whole flood: {kept} of {fed}"
        );
        assert!(
            kept <= 4096,
            "realtime queue budget is implausibly large: {kept}"
        );
        assert_eq!(
            kept as u64 + dropped,
            fed as u64,
            "commands vanished without being counted: kept {kept}, dropped {dropped}"
        );
    }

    /// The budget bounds per-block work too: one block applies at most the budget
    /// and leaves the queue empty, so a burst cannot stall a second callback.
    #[test]
    fn one_block_applies_at_most_the_budget_and_drains_the_queue() {
        let mut synth = RealtimeSynth::new(opts());
        flood_controllers(&mut synth, LIVE_MAX_PENDING * 3);
        let queued = synth.pending.len();
        assert!(queued <= LIVE_MAX_PENDING);

        let mut out = vec![0f32; LIVE_BLOCK * 2];
        synth.render_add(LIVE_BLOCK, &mut out).unwrap();

        assert!(synth.pending.is_empty(), "queue not drained by the block");
    }

    /// Overflow drops the NEWEST, so what survives is the caller's stream prefix.
    ///
    /// Both ends are checked, and the values are chosen so the two candidate
    /// policies disagree at both. An earlier version of this test used `i % 128`
    /// for the flood and 127 for the overflow command — under which drop-newest
    /// and drop-oldest BOTH leave 127 last, so it passed against either policy
    /// and proved nothing. The flood now steps mod 100, so the last accepted
    /// value is 23 and the dropped one is 127.
    #[test]
    fn overflow_drops_the_newest_and_keeps_the_prefix() {
        let mut synth = RealtimeSynth::new(opts());
        for i in 0..LIVE_MAX_PENDING {
            synth.write_byte(0xB0);
            synth.write_byte(7);
            synth.write_byte((i % 100) as u8);
        }
        let first_sent = 0u8;
        let last_accepted = ((LIVE_MAX_PENDING - 1) % 100) as u8;
        assert_ne!(
            last_accepted, 127,
            "the fixture must distinguish the policies"
        );
        // One command past the budget, carrying a value none of the accepted
        // commands ends on.
        synth.write_byte(0xB0);
        synth.write_byte(7);
        synth.write_byte(127);

        assert_eq!(synth.dropped_command_count(), 1);
        let queued = synth.pending.as_slice();
        let cc = |val| LiveCommand::Channel(EvKind::Cc { ch: 0, num: 7, val });
        assert_eq!(
            queued[0],
            cc(first_sent),
            "overflow discarded the head of the stream instead of the tail"
        );
        assert_eq!(
            *queued.last().unwrap(),
            cc(last_accepted),
            "the dropped command displaced an accepted one"
        );
    }

    /// A NoteOn burst is bounded by the same budget, so the block spawns a bounded
    /// number of voices and the cap trims them in one pass — the case that used to
    /// mean an unbounded spawn followed by quadratic stealing.
    #[test]
    fn noteon_burst_is_bounded_and_capped() {
        let mut synth = RealtimeSynth::new(opts());
        // Far more note-ons than either budget, all distinct (channel, key) pairs
        // so each is a fresh voice rather than a retrigger.
        let mut spawned = 0usize;
        'outer: for ch in 0u8..9 {
            for key in 21u8..=108 {
                synth.write_byte(0x90 | ch);
                synth.write_byte(key);
                synth.write_byte(80);
                spawned += 1;
                if spawned >= LIVE_MAX_PENDING * 2 {
                    break 'outer;
                }
            }
        }
        assert!(
            synth.pending.len() <= LIVE_MAX_PENDING,
            "note-on burst grew the queue past its budget"
        );

        let mut out = vec![0f32; LIVE_BLOCK * 2];
        synth.render_add(LIVE_BLOCK, &mut out).unwrap();

        assert_eq!(
            synth.active_voice_count(),
            LIVE_MAX_VOICES,
            "burst left polyphony above the cap"
        );
        assert!(synth.pending.is_empty());
    }

    /// `reset` clears queued commands but keeps the cumulative drop count — a
    /// caller polling it must still learn that it once overran.
    #[test]
    fn reset_clears_the_queue_but_keeps_the_drop_count() {
        let mut synth = RealtimeSynth::new(opts());
        flood_controllers(&mut synth, LIVE_MAX_PENDING + 5);
        assert_eq!(synth.dropped_command_count(), 5);

        synth.reset();

        assert!(synth.pending.is_empty(), "reset left commands queued");
        assert_eq!(
            synth.dropped_command_count(),
            5,
            "reset erased the overflow evidence"
        );
    }

    fn assert_send<T: Send>() {}

    #[test]
    fn realtime_synth_is_send() {
        assert_send::<RealtimeSynth>();
    }

    #[test]
    fn parser_handles_running_status_and_realtime_interleave() {
        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        for b in [0x90, 60, 100, 0xF8, 64, 0, 67, 80] {
            parser.push(b, &mut out);
        }
        assert_eq!(
            out.as_slice(),
            [
                LiveCommand::Channel(EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                }),
                LiveCommand::Channel(EvKind::NoteOff { ch: 0, key: 64 }),
                LiveCommand::Channel(EvKind::NoteOn {
                    ch: 0,
                    key: 67,
                    vel: 80,
                }),
            ]
        );
    }

    #[test]
    fn parser_emits_poly_aftertouch_and_consumes_system_common() {
        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        // 0xA0 poly-aftertouch is now forwarded (the engine acts on it); the 0xF2
        // system-common message and its data bytes are still consumed and ignored.
        for b in [0xA0, 60, 12, 0x90, 60, 100, 0xF2, 1, 2, 64, 100] {
            parser.push(b, &mut out);
        }
        assert_eq!(
            out.as_slice(),
            [
                LiveCommand::Channel(EvKind::PolyAftertouch {
                    ch: 0,
                    key: 60,
                    val: 12,
                }),
                LiveCommand::Channel(EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                }),
            ]
        );
    }

    #[test]
    fn parser_emits_gm_and_system_resets() {
        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        for b in [0xF0, 0x7E, 0x7F, 0x09, 0x01, 0xF7, 0xFF] {
            parser.push(b, &mut out);
        }
        assert_eq!(
            out.as_slice(),
            [
                LiveCommand::Channel(EvKind::GmReset),
                LiveCommand::SystemReset,
            ]
        );
    }

    #[test]
    fn live_gm_system_on_uses_the_full_engine_reset() {
        let mut synth = RealtimeSynth::new(opts());
        assert_eq!(spawn_voices_and_render(&mut synth, 2), 2);
        for byte in [0xF0, 0x7E, 0x7F, 0x09, 0x01, 0xF7] {
            synth.write_byte(byte);
        }
        let mut out = [0.0; LIVE_BLOCK * 2];
        synth.render_add(LIVE_BLOCK, &mut out).unwrap();
        assert_eq!(synth.active_voice_count(), 0);
    }

    /// MM-BUG-KILN-00035: every fixed SysEx shape modeled by the SMF parser is
    /// recognized from the raw live wire too.
    #[test]
    fn parser_emits_all_modeled_system_sysex() {
        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        let bytes = [
            // XG System On, with transparent timing clock interleaved.
            0xF0, 0x43, 0x10, 0xF8, 0x4C, 0x00, 0x00, 0x7E, 0x00, 0xF7,
            // XG Effect1 one-byte parameter.
            0xF0, 0x43, 0x10, 0x4C, 0x02, 0x01, 0x5A, 0x00, 0xF7, // GS Reset.
            0xF0, 0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00, 0x41, 0xF7,
            // GS Use for Rhythm Part, block A => channel index 10.
            0xF0, 0x41, 0x10, 0x42, 0x12, 0x40, 0x1A, 0x15, 0x01, 0x00, 0xF7,
        ];
        for byte in bytes {
            parser.push(byte, &mut out);
        }
        assert_eq!(
            out.as_slice(),
            [
                LiveCommand::Channel(EvKind::XgReset),
                LiveCommand::Channel(EvKind::XgEffectParam {
                    addr_lo: 0x5A,
                    data: [0, 0],
                    len: 1,
                }),
                LiveCommand::Channel(EvKind::GsReset),
                LiveCommand::Channel(EvKind::DrumMode { ch: 10, on: true }),
            ]
        );
    }

    /// A non-realtime status terminates malformed SysEx and must itself be
    /// processed; dropping it can both swallow notes and create a false GM reset.
    #[test]
    fn parser_recovers_channel_status_from_malformed_sysex() {
        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        for byte in [0xF0, 0x7E, 0x7F, 0x90, 60, 100] {
            parser.push(byte, &mut out);
        }
        assert_eq!(
            out.as_slice(),
            [LiveCommand::Channel(EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100,
            })]
        );
    }

    #[test]
    fn parser_recovers_after_sysex_overflow_and_system_reset() {
        let note = LiveCommand::Channel(EvKind::NoteOn {
            ch: 0,
            key: 60,
            vel: 100,
        });

        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        // A valid GM prefix extended past the fixed capture cannot become a reset.
        for byte in [
            0xF0, 0x7E, 0x7F, 0x09, 0x01, 0, 0, 0, 0, 0, 0, 0xF7, 0x90, 60, 100,
        ] {
            parser.push(byte, &mut out);
        }
        assert_eq!(out.as_slice(), [note]);

        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        // FF acts immediately and clears the partial GM prefix. Its remaining
        // bytes cannot later complete a second reset; normal traffic recovers.
        for byte in [0xF0, 0x7E, 0x7F, 0x09, 0xFF, 0x01, 0xF7, 0x90, 60, 100] {
            parser.push(byte, &mut out);
        }
        assert_eq!(out.as_slice(), [LiveCommand::SystemReset, note]);
    }

    #[test]
    fn parser_does_not_false_reset_on_extended_sysex_prefix() {
        let mut parser = MidiByteParser::new();
        let mut out = PendingQueue::new();
        for b in [0xF0, 0x7E, 0x7F, 0x09, 0x01, 0x00, 0xF7] {
            parser.push(b, &mut out);
        }
        assert!(out.is_empty());
    }

    #[test]
    fn render_add_rejects_short_output_without_modifying_it() {
        let mut synth = RealtimeSynth::new(opts());
        let mut out = [0.25f32; 3];
        let err = synth.render_add(2, &mut out).unwrap_err();
        assert_eq!(
            err,
            RealtimeError::OutputTooSmall {
                needed: 4,
                got: 3,
                frames: 2,
            }
        );
        assert_eq!(out, [0.25; 3]);

        let err = synth.render_add(usize::MAX, &mut []).unwrap_err();
        assert_eq!(
            err,
            RealtimeError::OutputTooSmall {
                needed: usize::MAX,
                got: 0,
                frames: usize::MAX,
            }
        );
    }

    #[test]
    fn render_add_is_additive_and_chunk_stable() {
        let bytes = [0x90, 60, 100, 0x80, 60, 0];

        let mut one = RealtimeSynth::new(opts());
        for &b in &bytes[..3] {
            one.write_byte(b);
        }
        let mut whole = vec![0.5f32; 256 * 2];
        one.render_add(128, &mut whole[..256]).unwrap();
        for &b in &bytes[3..] {
            one.write_byte(b);
        }
        one.render_add(128, &mut whole[256..]).unwrap();

        let mut split = RealtimeSynth::new(opts());
        for &b in &bytes[..3] {
            split.write_byte(b);
        }
        let mut chunks = vec![0.5f32; 256 * 2];
        for i in 0..4 {
            split
                .render_add(32, &mut chunks[i * 64..(i + 1) * 64])
                .unwrap();
        }
        for &b in &bytes[3..] {
            split.write_byte(b);
        }
        for i in 4..8 {
            split
                .render_add(32, &mut chunks[i * 64..(i + 1) * 64])
                .unwrap();
        }

        let signal = whole.iter().any(|&x| (x - 0.5).abs() > 1e-5);
        assert!(signal, "note stream produced no audible output");
        for (a, b) in whole.iter().zip(chunks.iter()) {
            assert!((a - b).abs() < 1e-6, "chunk drift {a} vs {b}");
        }
    }

    #[test]
    fn reset_stops_voice_and_clears_partial_message() {
        let mut synth = RealtimeSynth::new(opts());
        for b in [0x90, 60, 100] {
            synth.write_byte(b);
        }
        synth.render_add(64, &mut vec![0.0; 128]).unwrap();
        assert!(synth.active_voice_count() > 0);

        synth.write_byte(0x90);
        synth.reset();
        synth.write_byte(64);
        synth.write_byte(100);
        let mut out = vec![0.0f32; 128];
        synth.render_add(64, &mut out).unwrap();
        assert_eq!(synth.active_voice_count(), 0);
        assert!(out.iter().all(|x| x.abs() < 1e-9));
    }

    #[test]
    fn gm_reset_and_all_sound_off_clear_active_voice() {
        let mut gm = RealtimeSynth::new(opts());
        for b in [0x90, 60, 100] {
            gm.write_byte(b);
        }
        gm.render_add(64, &mut vec![0.0; 128]).unwrap();
        assert!(gm.active_voice_count() > 0);
        for b in [0xF0, 0x7E, 0x7F, 0x09, 0x01, 0xF7] {
            gm.write_byte(b);
        }
        let mut out = vec![0.0f32; 128];
        gm.render_add(64, &mut out).unwrap();
        assert_eq!(gm.active_voice_count(), 0);
        assert!(out.iter().all(|x| x.abs() < 1e-9));

        let mut cc120 = RealtimeSynth::new(opts());
        for b in [0x90, 60, 100] {
            cc120.write_byte(b);
        }
        cc120.render_add(64, &mut vec![0.0; 128]).unwrap();
        assert!(cc120.active_voice_count() > 0);
        for b in [0xB0, 120, 0] {
            cc120.write_byte(b);
        }
        let mut off = vec![0.0f32; 128];
        cc120.render_add(64, &mut off).unwrap();
        assert_eq!(cc120.active_voice_count(), 0);
    }

    #[test]
    fn all_notes_off_releases_sustained_voice() {
        let mut synth = RealtimeSynth::new(opts());
        for b in [0xB0, 64, 127, 0x90, 60, 100, 0x80, 60, 0] {
            synth.write_byte(b);
        }
        synth.render_add(64, &mut vec![0.0; 128]).unwrap();
        assert!(synth.active_voice_count() > 0);

        for b in [0xB0, 123, 0, 64, 0] {
            synth.write_byte(b);
        }
        let frames = 44_100 * 2;
        let mut out = vec![0.0f32; frames * 2];
        synth.render_add(frames, &mut out).unwrap();
        assert_eq!(synth.active_voice_count(), 0);
    }

    #[test]
    fn sample_prewarm_is_available() {
        RealtimeSynth::new(opts()).prewarm_samples();
    }

    /// MM-BUG-KILN-00064: after `prewarm_samples()`, real GM 76 and B1 NoteOns driven
    /// through the realtime path must decode no bank or B1 tail and search no loop.
    ///
    /// `sample_prewarm_is_available` above only proves the call does not panic. This one
    /// proves the contract the call actually makes — that nothing is left to do inside
    /// `fill_ring()`'s deadline-bearing block. Every voice is constructed there, *before*
    /// the voice cap is applied, so a NoteOn burst multiplies any per-note setup cost even
    /// when stealing is about to discard the voices.
    ///
    /// The out-of-window keys are deliberate: they fall back to the modeled Wind bottle,
    /// and the pre-fix constructor still ran the full 67-million-operation loop search
    /// before the pitch-ratio check could reject the sample. Testing only in-window keys
    /// would let the fallback hide that cost.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn realtime_note_on_after_prewarm_does_no_decode_or_loop_search() {
        use std::sync::atomic::Ordering;

        let mut synth = RealtimeSynth::new(RealtimeOptions {
            samples: true,
            ..opts()
        });
        synth.prewarm_samples();
        let banks_before = crate::sampler::BANK_INITS.load(Ordering::SeqCst);
        let searches_before = crate::sampler::LOOP_SEARCHES.load(Ordering::SeqCst);
        let tails_before = crate::sampler::TAIL_DECODES.load(Ordering::SeqCst);
        assert!(
            searches_before > 0,
            "prewarm_samples() resolved no sustain loop — this oracle would pass vacuously"
        );

        // Program change to GM 76 on channel 0, then NoteOns spanning the sample's
        // ~keys 44..68 repitch window and both sides of it.
        synth.write_byte(0xC0);
        synth.write_byte(76);
        for key in [30u8, 40, 44, 48, 55, 60, 67, 68, 70, 100] {
            synth.write_byte(0x90);
            synth.write_byte(key);
            synth.write_byte(100);
        }
        // Return to GM0 and cross the B1's real normal/hard velocity split. Both
        // compact-tail caches must already have decoded on the setup thread.
        synth.write_byte(0xC0);
        synth.write_byte(0);
        for velocity in [59u8, 60] {
            synth.write_byte(0x90);
            synth.write_byte(69);
            synth.write_byte(velocity);
        }
        let mut out = vec![0f32; LIVE_BLOCK * 2];
        synth.render_add(LIVE_BLOCK, &mut out).unwrap();
        assert!(
            synth.active_voice_count() > 0,
            "no voice sounded — the NoteOns never reached voice construction, so this \
             oracle measured nothing"
        );

        let searched = crate::sampler::LOOP_SEARCHES.load(Ordering::SeqCst) - searches_before;
        let decoded = crate::sampler::BANK_INITS.load(Ordering::SeqCst) - banks_before;
        let tails = crate::sampler::TAIL_DECODES.load(Ordering::SeqCst) - tails_before;
        assert_eq!(
            searched, 0,
            "{searched} sustain-loop search(es) ran inside the realtime render block \
             after prewarm_samples(). Each scans static PCM (67.4 M multiply-accumulates \
             for the blown bottle) under the audio deadline."
        );
        assert_eq!(
            decoded, 0,
            "{decoded} sample bank(s) decoded inside the realtime render block after \
             prewarm_samples() promised they would not."
        );
        assert_eq!(
            tails, 0,
            "{tails} B1 natural tail(s) decoded inside the realtime render block after \
             prewarm_samples() promised they would not."
        );
    }

    /// MM-BUG-KILN-00125: the accent-cymbal package has its own PCM cache, separate
    /// from the core drum-kit crate. Prewarm it before a channel-10 NoteOn reaches
    /// `fill_ring()`, then exercise every routed companion articulation.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn realtime_accent_cymbals_are_prewarmed_before_the_audio_block() {
        let mut synth = RealtimeSynth::new(RealtimeOptions {
            samples: true,
            ..opts()
        });
        synth.prewarm_samples();
        let before = ferrosintesis_samples_drumkit2::pcm_cache_initializations();
        assert_eq!(
            before, 1,
            "prewarm_samples() returned while the companion drum cache was still cold"
        );

        // Channel 10 crash, china and splash routes. Key 57 aliases crash, but is
        // included because it is a separately reachable GM NoteOn path.
        for key in [49u8, 52, 55, 57] {
            synth.write_byte(0x99);
            synth.write_byte(key);
            synth.write_byte(100);
        }
        let mut out = vec![0f32; LIVE_BLOCK * 2];
        synth.render_add(LIVE_BLOCK, &mut out).unwrap();
        assert!(
            synth.active_voice_count() >= 4,
            "accent NoteOns did not reach realtime voice construction"
        );
        assert_eq!(
            ferrosintesis_samples_drumkit2::pcm_cache_initializations(),
            before,
            "the companion drum cache initialized inside the realtime audio block"
        );
    }
}
