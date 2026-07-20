//! Offline rendering: a Standard MIDI File in, a buffer of audio out.
//!
//! The steps are always the same — [`load`] (or [`parse`]) a MIDI, [`render`] it to
//! samples, then convert those samples to 16-bit PCM with [`normalize_loudness`] and
//! write them with [`write_wav`].
//!
//! [`render`] returns **interleaved stereo `f32`** at [`Options::sample_rate`] Hz. The
//! rate is not carried in the returned buffer, so pass the same `opt.sample_rate()` to
//! every downstream call.

use std::path::Path;

pub use crate::engine::{normalize_loudness, normalize_to_i16, Options, Progress, Stats};
pub use crate::error::{MidiError, MAX_SONG_SECONDS};
pub use crate::loudness::{integrated_lufs, limit_true_peak, momentary_lufs, true_peak_dbtp};
pub use crate::wav::write_wav;

/// A parsed Standard MIDI File: its tempo map, events and markers, ready to render.
pub struct Song(crate::midi::Song);

impl Song {
    /// Playing time in seconds, from the first event to the last note-off. This does
    /// **not** include the reverb tail that [`render`] adds ([`Options::tail`]).
    pub fn seconds(&self) -> f64 {
        self.0.seconds
    }

    /// Number of MIDI events the renderer will play.
    pub fn events_len(&self) -> usize {
        self.0.events.len()
    }

    /// Number of text markers in the conductor track.
    pub fn markers_len(&self) -> usize {
        self.0.markers.len()
    }

    /// The sequence name from the first track, or `""` if the file has none.
    pub fn title(&self) -> &str {
        &self.0.title
    }

    /// Tempo in beats per minute at the first event. Later tempo changes are honoured
    /// by the renderer; this is only the opening value.
    pub fn initial_bpm(&self) -> f64 {
        self.0.initial_bpm
    }
}

/// Read and parse a Standard MIDI File from disk.
///
/// # Errors
///
/// [`MidiError::Io`] if the file cannot be read, or any [`parse`] error if the bytes
/// are not a type-0/1 SMF.
pub fn load(path: &Path) -> Result<Song, MidiError> {
    crate::midi::load(path).map(Song)
}

/// Parse a Standard MIDI File already in memory.
///
/// Supports SMF type 0 and 1 with ticks-per-quarter-note division. Sysex and
/// unmodeled meta events are skipped rather than rejected.
///
/// # Errors
///
/// [`MidiError::NotMidi`] if there is no `MThd` header,
/// [`MidiError::UnsupportedFormat`] for SMF type 2,
/// [`MidiError::UnsupportedTimeDivision`] for SMPTE timecode, or
/// [`MidiError::UnexpectedEof`] if the data is truncated.
pub fn parse(data: &[u8]) -> Result<Song, MidiError> {
    crate::midi::parse(data).map(Song)
}

/// Render a song to audio.
///
/// Returns **interleaved stereo `f32`** at `opt.sample_rate()` Hz — `samples.len() / 2`
/// frames, covering the song plus [`Options::tail`] seconds of reverb decay — together
/// with the [`Stats`] for the render.
///
/// The samples are **not** normalized and `stats.peak` may exceed 1.0. Pass the buffer
/// through [`normalize_loudness`] before writing it.
///
/// # Allocation
///
/// This allocates `(song.seconds() + opt.tail()) * opt.sample_rate() * 8` bytes up front.
/// [`parse`] already refuses a tempo map implying a song longer than 24 hours
/// ([`MidiError::TooLong`]), so untrusted input cannot turn this into an unbounded
/// allocation — but a legitimately long song is still a large buffer, and
/// [`Song::seconds`] lets you check before committing to it.
pub fn render(song: &Song, opt: &Options) -> (Vec<f32>, Stats) {
    crate::engine::render(&song.0, opt)
}

/// Render a song, reporting progress roughly ten times over the render.
///
/// Identical to [`render`] in every respect but the callback — the audio is
/// bit-for-bit the same. The library itself never writes to stdout or stderr, so this
/// is how you drive a progress bar.
///
/// ```no_run
/// use ferrosintesis::offline::{self, Options};
///
/// # fn main() -> Result<(), Box<dyn std::error::Error>> {
/// let song = offline::load(std::path::Path::new("song.mid"))?;
/// let (samples, _stats) = offline::render_with_progress(&song, &Options::default(), &mut |p| {
///     eprintln!("{:.0}% ({} voices)", p.fraction() * 100.0, p.active_voices);
/// });
/// # let _ = samples;
/// # Ok(())
/// # }
/// ```
pub fn render_with_progress(
    song: &Song,
    opt: &Options,
    on_progress: &mut dyn FnMut(Progress),
) -> (Vec<f32>, Stats) {
    crate::engine::render_with_progress(&song.0, opt, on_progress)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn file_from_track(events: &[u8]) -> Vec<u8> {
        let mut data = Vec::new();
        data.extend(b"MThd");
        data.extend(6u32.to_be_bytes());
        data.extend(0u16.to_be_bytes());
        data.extend(1u16.to_be_bytes());
        data.extend(480u16.to_be_bytes());

        let mut track = Vec::from(events);
        track.extend([0x00, 0xFF, 0x2F, 0x00]);
        data.extend(b"MTrk");
        data.extend((track.len() as u32).to_be_bytes());
        data.extend(track);
        data
    }

    #[test]
    fn malformed_note_keys_render_as_their_seven_bit_values() {
        let opt = Options::default().with_samples(false).with_tail(0.2);
        let cases: [(&str, &[u8], &[u8]); 2] = [
            (
                "melodic note and poly-aftertouch",
                &[
                    0x00, 0x90, 200, 100, 0x00, 0xA0, 200, 64, 0x60, 0x80, 200, 0,
                ],
                &[0x00, 0x90, 72, 100, 0x00, 0xA0, 72, 64, 0x60, 0x80, 72, 0],
            ),
            (
                "channel-10 drum note",
                &[0x00, 0x99, 163, 100, 0x60, 0x89, 163, 0],
                &[0x00, 0x99, 35, 100, 0x60, 0x89, 35, 0],
            ),
        ];

        for (name, malformed, canonical) in cases {
            let malformed = parse(&file_from_track(malformed)).unwrap();
            let canonical = parse(&file_from_track(canonical)).unwrap();
            let (malformed_audio, malformed_stats) = render(&malformed, &opt);
            let (canonical_audio, canonical_stats) = render(&canonical, &opt);

            assert!(
                malformed_audio.iter().any(|sample| sample.abs() > 1e-6),
                "{name} rendered silence"
            );
            assert_eq!(malformed_audio, canonical_audio, "{name}");
            assert_eq!(
                malformed_stats.voices_spawned, canonical_stats.voices_spawned,
                "{name}"
            );
        }
    }
}
