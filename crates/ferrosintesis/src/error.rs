//! The crate's public error type.

use std::fmt;
use std::path::PathBuf;

/// Longest song [`parse`](crate::offline::parse) will accept, in seconds (24 hours).
///
/// The tempo map of a Standard MIDI File is entirely attacker-controlled: a few dozen
/// bytes can declare a tempo of 16 s/quarter and a tick delta near `u32::MAX`, yielding
/// a nominal length of ~10^10 seconds. [`render`](crate::offline::render) allocates
/// `(seconds + tail) * sr * 8` bytes up front, so such a file would request a petabyte
/// and abort the process in the allocator — not a catchable panic, so a caller cannot
/// even defend with `catch_unwind`. `parse` therefore refuses it, returning
/// [`MidiError::TooLong`].
pub const MAX_SONG_SECONDS: f64 = 24.0 * 3600.0;

/// Why a Standard MIDI File could not be read.
///
/// This enum is `#[non_exhaustive]`, and so is every variant that carries data: match
/// with a `_` arm, and match variants with `..` (e.g. `MidiError::Io { path, .. }`).
/// New variants — and new fields on existing ones — may be added in a minor release.
#[derive(Debug)]
#[non_exhaustive]
pub enum MidiError {
    /// The file could not be read from disk. Only [`load`](crate::offline::load)
    /// produces this; [`parse`](crate::offline::parse) works from bytes and cannot.
    #[non_exhaustive]
    Io {
        /// The path that could not be read.
        path: PathBuf,
        /// The underlying I/O failure.
        source: std::io::Error,
    },
    /// The data does not begin with the `MThd` header chunk, so it is not an SMF.
    NotMidi,
    /// The SMF format field is not 0 or 1. Format 2 (independent patterns) is not modeled.
    #[non_exhaustive]
    UnsupportedFormat {
        /// The format field found in the header.
        format: u16,
    },
    /// The header requests SMPTE timecode division rather than ticks-per-quarter-note.
    UnsupportedTimeDivision,
    /// A track chunk did not begin with the expected `MTrk` header.
    #[non_exhaustive]
    MissingTrack {
        /// The 0-based index of the offending track.
        index: u16,
    },
    /// A status byte in a track chunk is not a MIDI message this reader understands.
    #[non_exhaustive]
    BadStatusByte {
        /// The offending status byte.
        status: u8,
    },
    /// The data ended in the middle of a header, chunk, or event.
    UnexpectedEof,
    /// The tempo map declares a song longer than this reader will render.
    ///
    /// Rendering allocates in proportion to the song's length, so an absurd length from
    /// a malformed or hostile file is refused rather than turned into a huge allocation.
    /// See [`MAX_SONG_SECONDS`].
    #[non_exhaustive]
    TooLong {
        /// The nominal length the tempo map implies, in seconds.
        seconds: f64,
    },
}

impl fmt::Display for MidiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MidiError::Io { path, source } => write!(f, "{}: {source}", path.display()),
            MidiError::NotMidi => f.write_str("not a MIDI file (no MThd header)"),
            MidiError::UnsupportedFormat { format } => {
                write!(
                    f,
                    "unsupported SMF format {format} (only 0 and 1 are supported)"
                )
            }
            MidiError::UnsupportedTimeDivision => {
                f.write_str("SMPTE time division is not supported")
            }
            MidiError::MissingTrack { index } => write!(f, "track {index}: missing MTrk header"),
            MidiError::BadStatusByte { status } => write!(f, "bad status byte {status:#04x}"),
            MidiError::UnexpectedEof => f.write_str("unexpected end of file"),
            MidiError::TooLong { seconds } => write!(
                f,
                "song is {seconds:.0} s long, which exceeds the {MAX_SONG_SECONDS:.0} s limit \
                 (the tempo map is probably malformed)"
            ),
        }
    }
}

impl std::error::Error for MidiError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            MidiError::Io { source, .. } => Some(source),
            _ => None,
        }
    }
}

/// `MidiError` must stay `Send + Sync + 'static` so downstream users can `?` it across an
/// `.await` and box it as `Box<dyn Error + Send + Sync>`. The enum is `#[non_exhaustive]`
/// and designed to grow, so pin the property at compile time: a future variant carrying an
/// `Rc` or a raw pointer would silently break every async caller, and this makes it a
/// build error here instead.
const _: () = {
    const fn assert_send_sync<T: Send + Sync + 'static>() {}
    assert_send_sync::<MidiError>();
    assert_send_sync::<crate::live::RealtimeError>();
};

#[cfg(test)]
mod tests {
    use super::*;

    /// The public error type must be a well-behaved `std::error::Error`: a downstream
    /// user has to be able to `?` it into a `Box<dyn Error>` and read a cause chain.
    #[test]
    fn midi_error_is_a_std_error_with_a_source_chain() {
        let io = MidiError::Io {
            path: PathBuf::from("song.mid"),
            source: std::io::Error::new(std::io::ErrorKind::NotFound, "no such file"),
        };
        // Display keeps the path, which is what the CLI prints.
        assert_eq!(io.to_string(), "song.mid: no such file");
        // The io::Error is reachable as a source.
        assert!(std::error::Error::source(&io).is_some());
        // It boxes into the universal error type — including the Send + Sync form that
        // async callers need.
        let boxed: Box<dyn std::error::Error + Send + Sync> = Box::new(io);
        assert!(boxed.to_string().contains("song.mid"));

        // Parse errors carry no source but must still Display usefully.
        assert!(std::error::Error::source(&MidiError::NotMidi).is_none());
        assert_eq!(
            MidiError::UnsupportedFormat { format: 2 }.to_string(),
            "unsupported SMF format 2 (only 0 and 1 are supported)"
        );
        assert_eq!(
            MidiError::BadStatusByte { status: 0xF7 }.to_string(),
            "bad status byte 0xf7"
        );
        assert_eq!(
            MidiError::MissingTrack { index: 3 }.to_string(),
            "track 3: missing MTrk header"
        );
    }
}
