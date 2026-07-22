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
    pending: Vec<LiveCommand>,
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
            pending: Vec::new(),
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
    pub fn prewarm_samples(&self) {
        sampler::prewarm();
    }

    /// Feed one byte of a live MIDI stream.
    ///
    /// The parser tracks running status and tolerates realtime bytes (clock, active
    /// sensing) interleaved mid-message, so you can hand it a raw port's bytes verbatim.
    /// Bytes are buffered and take effect at the start of the next
    /// [`render_add`](Self::render_add) block.
    pub fn write_byte(&mut self, byte: u8) {
        self.parser.push(byte, &mut self.pending);
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
        for command in self.pending.drain(..) {
            match command {
                LiveCommand::Channel(kind) => self.core.handle_event(kind),
                LiveCommand::SystemReset => self.core.hard_reset(),
            }
        }
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

    pub(crate) fn push(&mut self, byte: u8, out: &mut Vec<LiveCommand>) {
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

    fn push_sysex(&mut self, byte: u8, out: &mut Vec<LiveCommand>) {
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

    fn push_status(&mut self, status: u8, out: &mut Vec<LiveCommand>) {
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

    fn push_data(&mut self, byte: u8, out: &mut Vec<LiveCommand>) {
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

    fn assert_send<T: Send>() {}

    #[test]
    fn realtime_synth_is_send() {
        assert_send::<RealtimeSynth>();
    }

    #[test]
    fn parser_handles_running_status_and_realtime_interleave() {
        let mut parser = MidiByteParser::new();
        let mut out = Vec::new();
        for b in [0x90, 60, 100, 0xF8, 64, 0, 67, 80] {
            parser.push(b, &mut out);
        }
        assert_eq!(
            out,
            vec![
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
        let mut out = Vec::new();
        // 0xA0 poly-aftertouch is now forwarded (the engine acts on it); the 0xF2
        // system-common message and its data bytes are still consumed and ignored.
        for b in [0xA0, 60, 12, 0x90, 60, 100, 0xF2, 1, 2, 64, 100] {
            parser.push(b, &mut out);
        }
        assert_eq!(
            out,
            vec![
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
        let mut out = Vec::new();
        for b in [0xF0, 0x7E, 0x7F, 0x09, 0x01, 0xF7, 0xFF] {
            parser.push(b, &mut out);
        }
        assert_eq!(
            out,
            vec![
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
        let mut out = Vec::new();
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
            out,
            vec![
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
        let mut out = Vec::new();
        for byte in [0xF0, 0x7E, 0x7F, 0x90, 60, 100] {
            parser.push(byte, &mut out);
        }
        assert_eq!(
            out,
            vec![LiveCommand::Channel(EvKind::NoteOn {
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
        let mut out = Vec::new();
        // A valid GM prefix extended past the fixed capture cannot become a reset.
        for byte in [
            0xF0, 0x7E, 0x7F, 0x09, 0x01, 0, 0, 0, 0, 0, 0, 0xF7, 0x90, 60, 100,
        ] {
            parser.push(byte, &mut out);
        }
        assert_eq!(out, vec![note]);

        let mut parser = MidiByteParser::new();
        let mut out = Vec::new();
        // FF acts immediately and clears the partial GM prefix. Its remaining
        // bytes cannot later complete a second reset; normal traffic recovers.
        for byte in [0xF0, 0x7E, 0x7F, 0x09, 0xFF, 0x01, 0xF7, 0x90, 60, 100] {
            parser.push(byte, &mut out);
        }
        assert_eq!(out, vec![LiveCommand::SystemReset, note]);
    }

    #[test]
    fn parser_does_not_false_reset_on_extended_sysex_prefix() {
        let mut parser = MidiByteParser::new();
        let mut out = Vec::new();
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
}
