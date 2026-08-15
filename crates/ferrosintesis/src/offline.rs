//! Offline rendering: a Standard MIDI File in, an atomically completed WAV out.
//!
//! The normal path is [`load`] (or [`parse`]), then [`render_to_wav`] with a
//! [`Normalization`] policy. It uses bounded audio buffers and disk-backed passes.
//!
//! [`render`] remains available when a caller deliberately wants **interleaved stereo
//! `f32`** in memory. Its rate is not carried in the returned buffer, so pass the same
//! [`Options::sample_rate`] to every downstream call.

use std::path::Path;

pub use crate::engine::{normalize_loudness, normalize_to_i16, Options, Progress, Stats};
pub use crate::error::{MidiError, MAX_MIDI_FILE_BYTES, MAX_SONG_SECONDS};
pub use crate::loudness::{integrated_lufs, limit_true_peak, momentary_lufs, true_peak_dbtp};
pub use crate::wav::write_wav;

/// Normalization applied by [`render_to_wav`].
///
/// Construct a value with [`Normalization::loudness`] for programme loudness plus
/// true-peak limiting, or [`Normalization::peak`] for the legacy scalar peak mode.
/// The fields are private so future releases can extend the policy without exposing
/// implementation details.
#[derive(Debug, Clone, Copy, PartialEq)]
#[non_exhaustive]
pub struct Normalization {
    kind: NormalizationKind,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum NormalizationKind {
    Loudness { target_lufs: f32, ceiling_dbtp: f32 },
    Peak { target: f32 },
}

impl Normalization {
    /// Normalize integrated BS.1770 loudness to `target_lufs` and constrain
    /// transients to `ceiling_dbtp`.
    ///
    /// Both must be finite, `target_lufs` in `-70..=0` LUFS and `ceiling_dbtp` in
    /// `-60..=0` dBTP. The constructor itself accepts anything — validation happens in
    /// [`render_to_wav`], which is fallible and so can tell you what was wrong; it
    /// returns [`std::io::ErrorKind::InvalidInput`] before creating any file.
    pub fn loudness(target_lufs: f32, ceiling_dbtp: f32) -> Self {
        Self {
            kind: NormalizationKind::Loudness {
                target_lufs,
                ceiling_dbtp,
            },
        }
    }

    /// Apply the legacy scalar normalization from the measured render peak to `target`.
    ///
    /// Most callers should use [`Normalization::loudness`]. This constructor exists
    /// for workflows that deliberately retain the CLI's old peak-normalized sound.
    ///
    /// `target` must be finite and in `0..=1`; as with [`Normalization::loudness`],
    /// [`render_to_wav`] is where that is checked and reported.
    pub fn peak(target: f32) -> Self {
        Self {
            kind: NormalizationKind::Peak { target },
        }
    }
}

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
/// Treats the path as untrusted: the file's size is checked against
/// [`MAX_MIDI_FILE_BYTES`] *before* any of it is read, and the read is bounded as
/// well, so a hostile path cannot exhaust memory ahead of the parser's own checks. If
/// you genuinely have a larger file, read the bytes yourself and call [`parse`], which
/// has no size limit.
///
/// # Errors
///
/// [`MidiError::Io`] if the file cannot be read, [`MidiError::TooLarge`] if it exceeds
/// [`MAX_MIDI_FILE_BYTES`], or any [`parse`] error if the bytes are not a type-0/1 SMF.
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

/// Render, normalize, and atomically write a stereo 16-bit PCM WAV.
///
/// Unlike [`render`], this path keeps audio working memory effectively independent
/// of song duration. It streams the synthesizer into sibling scratch files, applies
/// the selected normalization in disk-backed passes, then incrementally writes the
/// final WAV. The requested output is replaced only after the completed temporary
/// WAV has been flushed and synchronized.
///
/// # Errors
///
/// Returns [`std::io::ErrorKind::InvalidInput`] before creating any file if
/// `normalization` is not finite and within its documented range (see
/// [`Normalization::loudness`] and [`Normalization::peak`]), and before rendering if
/// the result would exceed classic RIFF's 4 GiB size limit. Otherwise returns the
/// underlying scratch, output, flush, synchronization, or rename error. A failed call
/// preserves any existing output and removes its owned temporary files during normal
/// unwinding.
pub fn render_to_wav(
    song: &Song,
    opt: &Options,
    output: &Path,
    normalization: Normalization,
) -> std::io::Result<Stats> {
    render_to_wav_with_progress(song, opt, output, normalization, &mut |_| {})
}

/// The progress-reporting form of [`render_to_wav`].
///
/// The callback reports synthesizer progress roughly ten times. Disk-backed
/// normalization and WAV writing happen after the callback reaches the end.
///
/// # Errors
///
/// Returns the same errors as [`render_to_wav`].
pub fn render_to_wav_with_progress(
    song: &Song,
    opt: &Options,
    output: &Path,
    normalization: Normalization,
    on_progress: &mut dyn FnMut(Progress),
) -> std::io::Result<Stats> {
    crate::scratch::render_to_wav(&song.0, opt, output, normalization.kind, on_progress)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;
    use std::time::{SystemTime, UNIX_EPOCH};

    struct TestDir(PathBuf);

    impl TestDir {
        fn new(label: &str) -> Self {
            let nonce = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let path = std::env::temp_dir().join(format!(
                "ferrosintesis-offline-{label}-{}-{nonce}",
                std::process::id()
            ));
            fs::create_dir(&path).unwrap();
            Self(path)
        }

        fn join(&self, name: &str) -> PathBuf {
            self.0.join(name)
        }
    }

    impl Drop for TestDir {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

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

    fn one_note_song() -> Song {
        parse(&file_from_track(&[
            0x00, 0xC0, 46, // harp
            0x00, 0x90, 60, 100, // note on
            0x83, 0x60, 0x80, 60, 0, // note off after one beat
        ]))
        .unwrap()
    }

    #[test]
    fn render_to_wav_matches_buffered_loudness_and_peak_paths() {
        let dir = TestDir::new("differential");
        let song = one_note_song();
        let opt = Options::default()
            .with_sample_rate(8_000)
            .with_samples(false)
            .with_tail(0.5);
        let (samples, expected_stats) = render(&song, &opt);

        let cases = [
            (
                "loudness",
                Normalization::loudness(-18.0, -1.0),
                normalize_loudness(&samples, opt.sample_rate(), -18.0, -1.0),
            ),
            (
                "peak",
                Normalization::peak(0.891),
                normalize_to_i16(&samples, expected_stats.peak, 0.891),
            ),
        ];
        for (name, normalization, expected_pcm) in cases {
            let expected = dir.join(&format!("{name}-expected.wav"));
            let actual = dir.join(&format!("{name}-actual.wav"));
            write_wav(&expected, opt.sample_rate(), &expected_pcm).unwrap();
            fs::write(&actual, b"prior output").unwrap();

            let actual_stats = render_to_wav(&song, &opt, &actual, normalization).unwrap();

            assert_eq!(actual_stats, expected_stats);
            assert_eq!(fs::read(&actual).unwrap(), fs::read(&expected).unwrap());
        }
    }

    /// MM-BUG-CRUCIBLE-00027: `load` refuses an oversized file instead of
    /// materializing it.
    ///
    /// The discriminator is the error, not merely the failure: the file is
    /// `MAX_MIDI_FILE_BYTES + 1` zero bytes, so a `load` with no limit at all reads it
    /// and returns `NotMidi` — which is what this asserted against before the fix.
    ///
    /// What this test does NOT prove is the ORDER of the two bounds. An earlier
    /// version of this comment claimed it did. It cannot: `read_bounded` checks the
    /// advertised size before reading *and* the byte count after, so removing the
    /// preflight alone still yields `TooLarge` here. The preflight is a cost
    /// optimization — it is what makes a multi-gigabyte file free to reject — and the
    /// property that actually bounds memory is the `take`. Proving the ordering would
    /// need a genuinely multi-gigabyte fixture, which would make the test cost more
    /// when passing than the bug costs when present.
    #[test]
    fn load_rejects_an_oversized_file() {
        let dir = TestDir::new("oversized");
        let path = dir.join("huge.mid");
        let file = fs::File::create(&path).unwrap();
        file.set_len(MAX_MIDI_FILE_BYTES + 1).unwrap();
        drop(file);

        match load(&path).err() {
            Some(MidiError::TooLarge { bytes, .. }) => {
                assert_eq!(bytes, MAX_MIDI_FILE_BYTES + 1)
            }
            Some(MidiError::NotMidi) => {
                panic!("`load` has no size limit: it read the whole file and parsed it")
            }
            other => panic!("expected TooLarge, got {other:?}"),
        }
    }

    /// The boundary is inclusive: a file exactly at the limit is read, not refused.
    /// Without this, a limit off by one in the refusing direction would go unnoticed.
    #[test]
    fn load_accepts_a_file_exactly_at_the_limit() {
        let dir = TestDir::new("at-limit");
        let path = dir.join("limit.mid");
        let file = fs::File::create(&path).unwrap();
        file.set_len(MAX_MIDI_FILE_BYTES).unwrap();
        drop(file);

        // Zeros are not an SMF, so reaching `NotMidi` is exactly the proof that the
        // size check let it through to the parser.
        assert!(
            matches!(load(&path), Err(MidiError::NotMidi)),
            "a file at the limit was refused"
        );
    }

    /// MM-BUG-CRUCIBLE-00027, the other half: a track chunk may DECLARE a near-4-GiB
    /// length in 8 bytes. `parse` must reject that from the declared length alone,
    /// without allocating anything proportional to it.
    ///
    /// This already held — `Cursor::bytes` slices the buffer it was given rather than
    /// reserving from the declared length — but nothing pinned it, and the bug named
    /// it as the case to cover.
    #[test]
    fn parse_rejects_a_track_declaring_almost_four_gibibytes() {
        let mut data = Vec::new();
        data.extend_from_slice(b"MThd");
        data.extend_from_slice(&6u32.to_be_bytes());
        data.extend_from_slice(&0u16.to_be_bytes()); // format 0
        data.extend_from_slice(&1u16.to_be_bytes()); // one track
        data.extend_from_slice(&480u16.to_be_bytes()); // ticks per quarter
        data.extend_from_slice(b"MTrk");
        data.extend_from_slice(&0xFFFF_FF00u32.to_be_bytes()); // ~4 GiB declared
        data.extend_from_slice(&[0x00, 0xFF, 0x2F, 0x00]); // four bytes actually present

        assert!(
            matches!(parse(&data), Err(MidiError::UnexpectedEof)),
            "a track declaring 4 GiB was not rejected from its declared length"
        );
    }

    /// MM-BUG-CRUCIBLE-00026: the buffered render path survives the extreme request
    /// that used to abort in the allocator.
    ///
    /// `with_echo(100_000.0)` reached `PingPong::new`, which at 44.1 kHz asked
    /// `DelayLine::new` for two power-of-two buffers of about 32 GiB each. This
    /// renders for real rather than only checking the accessors, so it covers the
    /// whole chain from a typed public call to the sized buffer.
    #[test]
    fn render_survives_extreme_option_requests() {
        let song = one_note_song();
        let opt = Options::default()
            .with_sample_rate(u32::MAX)
            .with_echo(f32::MAX)
            .with_reverb(f32::NAN)
            .with_samples(false)
            .with_tail(0.5);

        let (samples, _stats) = render(&song, &opt);

        assert!(!samples.is_empty(), "extreme options rendered nothing");
        assert!(
            samples.iter().all(|x| x.is_finite()),
            "extreme options produced non-finite audio"
        );
    }

    /// MM-BUG-CRUCIBLE-00032: a non-finite or absurd normalization setting is a
    /// diagnostic, not silent audio — and it is caught before anything is written.
    ///
    /// Every case previously SUCCEEDED. A NaN loudness target produced a NaN gain that
    /// the i16 quantizer cast to zero, writing a near-silent WAV and reporting success.
    /// A NaN ceiling was quieter still in its failure: every comparison against NaN is
    /// false, so the limiter simply stopped limiting while the call still said it had
    /// worked. Both are checked here on all three knobs, for NaN and both infinities,
    /// plus the finite-but-absurd values the range check exists for.
    ///
    /// The destination and its directory are asserted untouched, so this also proves
    /// the check runs before any file is created — which is the part a caller relies
    /// on when overwriting an existing render.
    #[test]
    fn non_finite_normalization_is_rejected_before_anything_is_written() {
        let dir = TestDir::new("bad-normalization");
        let output = dir.join("song.wav");
        fs::write(&output, b"prior output").unwrap();
        let song = one_note_song();
        let opt = Options::default()
            .with_sample_rate(8_000)
            .with_samples(false)
            .with_tail(0.0);

        let bad = [
            (
                "loudness target NaN",
                Normalization::loudness(f32::NAN, -1.0),
            ),
            (
                "loudness target +Inf",
                Normalization::loudness(f32::INFINITY, -1.0),
            ),
            (
                "loudness target -Inf",
                Normalization::loudness(f32::NEG_INFINITY, -1.0),
            ),
            ("ceiling NaN", Normalization::loudness(-18.0, f32::NAN)),
            (
                "ceiling +Inf",
                Normalization::loudness(-18.0, f32::INFINITY),
            ),
            (
                "ceiling -Inf",
                Normalization::loudness(-18.0, f32::NEG_INFINITY),
            ),
            ("peak NaN", Normalization::peak(f32::NAN)),
            ("peak +Inf", Normalization::peak(f32::INFINITY)),
            ("peak -Inf", Normalization::peak(f32::NEG_INFINITY)),
            // Finite but outside the documented range.
            (
                "loudness target above 0",
                Normalization::loudness(3.0, -1.0),
            ),
            ("ceiling above 0", Normalization::loudness(-18.0, 6.0)),
            ("peak above 1", Normalization::peak(2.0)),
            ("peak below 0", Normalization::peak(-0.5)),
        ];

        for (label, normalization) in bad {
            let error = render_to_wav(&song, &opt, &output, normalization)
                .expect_err(&format!("{label} was accepted"));
            assert_eq!(
                error.kind(),
                std::io::ErrorKind::InvalidInput,
                "{label}: wrong error kind ({error})"
            );
            assert_eq!(
                fs::read(&output).unwrap(),
                b"prior output",
                "{label}: the existing output was modified"
            );
            assert_eq!(
                fs::read_dir(&dir.0).unwrap().count(),
                1,
                "{label}: scratch files were created before validation"
            );
        }

        // The floor: a good setting on the same inputs must still succeed, or the
        // assertions above would pass for a renderer that rejected everything.
        render_to_wav(&song, &opt, &output, Normalization::loudness(-18.0, -1.0))
            .expect("a valid normalization must still render");
        assert_ne!(fs::read(&output).unwrap(), b"prior output");
    }

    /// The infallible in-memory helper cannot report a bad setting, so its documented
    /// answer is to leave the audio alone rather than return the silence a NaN gain
    /// used to produce.
    #[test]
    fn buffered_normalization_passes_non_finite_settings_through_ungained() {
        let sr = 44_100u32;
        // Three seconds, not a fraction of one. BS.1770 integrated loudness is gated
        // over 400 ms blocks, so a short signal measures as non-finite and
        // `normalize_loudness` takes its silence path — breaking out before it could
        // ever compute a gain. An earlier version of this test used 0.1 s and passed
        // with the guard REMOVED, because it never reached the code it was testing.
        let samples: Vec<f32> = (0..sr as usize * 3)
            .flat_map(|i| {
                let s = 0.5 * (2.0 * std::f32::consts::PI * 440.0 * i as f32 / sr as f32).sin();
                [s, s]
            })
            .collect();
        assert!(
            crate::loudness::integrated_lufs(&samples, sr).is_finite(),
            "the fixture must be long enough to measure, or the NaN path is unreachable"
        );
        let reference = crate::engine::normalize_loudness(&samples, sr, -18.0, -1.0);
        assert!(
            reference.iter().any(|&s| s != 0),
            "the reference render is silent, so this test cannot detect silence"
        );

        for (label, target, ceiling) in [
            ("target NaN", f32::NAN, -1.0f32),
            ("ceiling NaN", -18.0f32, f32::NAN),
            ("target +Inf", f32::INFINITY, -1.0),
            ("ceiling -Inf", -18.0, f32::NEG_INFINITY),
        ] {
            let out = crate::engine::normalize_loudness(&samples, sr, target, ceiling);
            assert!(
                out.iter().any(|&s| s != 0),
                "{label}: a non-finite setting produced silence"
            );
        }
    }

    #[test]
    fn riff_preflight_preserves_existing_output_and_creates_no_scratch() {
        let dir = TestDir::new("preflight");
        let output = dir.join("song.wav");
        fs::write(&output, b"prior output").unwrap();
        let song = one_note_song();
        // Oversized through SUPPORTED values, not an absurd one: since
        // MM-BUG-CRUCIBLE-00026 the builders clamp, so `with_sample_rate(u32::MAX)`
        // no longer produces an oversized result and would have quietly stopped
        // exercising the preflight. The top supported rate with a long-but-supported
        // tail still passes RIFF's 4 GiB ceiling — 384 kHz stereo 16-bit is 4 bytes a
        // frame, so 4 GiB is 2796 s and 2800 s clears it.
        let opt = Options::default()
            .with_sample_rate(384_000)
            .with_tail(2_800.0);
        assert_eq!(opt.sample_rate(), 384_000, "the rate was clamped away");
        assert_eq!(opt.tail(), 2_800.0, "the tail was clamped away");

        let error =
            render_to_wav(&song, &opt, &output, Normalization::loudness(-18.0, -1.0)).unwrap_err();

        assert_eq!(error.kind(), std::io::ErrorKind::InvalidInput);
        assert_eq!(fs::read(&output).unwrap(), b"prior output");
        assert_eq!(fs::read_dir(&dir.0).unwrap().count(), 1);
    }

    #[test]
    fn failed_final_rename_cleans_scratch_and_preserves_destination() {
        let dir = TestDir::new("rename-failure");
        let output = dir.join("song.wav");
        fs::create_dir(&output).unwrap();
        let song = parse(&file_from_track(&[])).unwrap();
        let opt = Options::default()
            .with_sample_rate(8_000)
            .with_samples(false)
            .with_tail(0.0);

        render_to_wav(&song, &opt, &output, Normalization::loudness(-18.0, -1.0))
            .expect_err("a completed WAV cannot rename over a directory");

        assert!(output.is_dir(), "failed render replaced the destination");
        assert_eq!(
            fs::read_dir(&dir.0).unwrap().count(),
            1,
            "failed render leaked sibling scratch"
        );
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

    #[test]
    fn malformed_program_change_renders_as_its_seven_bit_value() {
        let malformed = parse(&file_from_track(&[
            0x00, 0xC0, 0xFF, // malformed program 255
            0x00, 0x90, 60, 100, // note on
            0x60, 0x80, 60, 0, // note off
        ]))
        .unwrap();
        let canonical = parse(&file_from_track(&[
            0x00, 0xC0, 0x7F, // canonical program 127
            0x00, 0x90, 60, 100, // note on
            0x60, 0x80, 60, 0, // note off
        ]))
        .unwrap();
        let opt = Options::default().with_samples(false).with_tail(0.2);

        let (malformed_audio, malformed_stats) = render(&malformed, &opt);
        let (canonical_audio, canonical_stats) = render(&canonical, &opt);

        assert!(malformed_audio.iter().any(|sample| sample.abs() > 1e-6));
        assert_eq!(malformed_audio, canonical_audio);
        assert_eq!(malformed_stats, canonical_stats);
    }

    /// MM-BUG-KILN-00035: a mid-file GM On stops the old voice before the next
    /// one, while Stats retain both allocations and the pre-reset audio peak.
    #[test]
    fn parsed_mid_file_gm_reset_preserves_whole_render_stats() {
        let events = [
            0x00, 0xC0, 30, // non-default program
            0x00, 0x90, 60, 110, // held across the reset unless GM On is full
            0x60, 0xF0, 0x05, 0x7E, 0x7F, 0x09, 0x01, 0xF7, // GM System On
            0x00, 0x90, 64, 100, // fresh default-program voice
            0x60, 0x80, 64, 0,
        ];
        let song = parse(&file_from_track(&events)).unwrap();
        let opt = Options::default().with_samples(false).with_tail(0.1);
        let (audio, stats) = render(&song, &opt);

        assert!(audio.iter().any(|sample| sample.abs() > 1e-6));
        assert_eq!(
            stats.voices_spawned, 2,
            "pre-reset voice vanished from Stats"
        );
        assert_eq!(
            stats.max_polyphony, 1,
            "pre-reset voice overlapped the post-reset voice"
        );
        let measured_peak = audio.iter().fold(0.0f32, |peak, &x| peak.max(x.abs()));
        assert_eq!(stats.peak, measured_peak);
    }
}
