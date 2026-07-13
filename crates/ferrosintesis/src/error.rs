//! The crate's public error type.

use std::fmt;
use std::path::PathBuf;

/// Why a Standard MIDI File could not be read.
///
/// This enum is `#[non_exhaustive]`: match with a `_` arm, as new variants may be
/// added in a minor release.
#[derive(Debug)]
#[non_exhaustive]
pub enum MidiError {
    /// The file could not be read from disk. Only [`load`](crate::offline::load)
    /// produces this; [`parse`](crate::offline::parse) works from bytes and cannot.
    Io {
        /// The path that could not be read.
        path: PathBuf,
        /// The underlying I/O failure.
        source: std::io::Error,
    },
    /// The data does not begin with the `MThd` header chunk, so it is not an SMF.
    NotMidi,
    /// The SMF format field is not 0 or 1. Format 2 (independent patterns) is not modeled.
    UnsupportedFormat(u16),
    /// The header requests SMPTE timecode division rather than ticks-per-quarter-note.
    UnsupportedTimeDivision,
    /// A track chunk did not begin with the expected `MTrk` header.
    MissingTrack {
        /// The 0-based index of the offending track.
        index: u16,
    },
    /// A status byte in a track chunk is not a MIDI message this reader understands.
    BadStatusByte(u8),
    /// The data ended in the middle of a header, chunk, or event.
    UnexpectedEof,
}

impl fmt::Display for MidiError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MidiError::Io { path, source } => write!(f, "{}: {source}", path.display()),
            MidiError::NotMidi => f.write_str("not a MIDI file (no MThd header)"),
            MidiError::UnsupportedFormat(fmt_id) => {
                write!(
                    f,
                    "unsupported SMF format {fmt_id} (only 0 and 1 are supported)"
                )
            }
            MidiError::UnsupportedTimeDivision => {
                f.write_str("SMPTE time division is not supported")
            }
            MidiError::MissingTrack { index } => write!(f, "track {index}: missing MTrk header"),
            MidiError::BadStatusByte(b) => write!(f, "bad status byte {b:#04x}"),
            MidiError::UnexpectedEof => f.write_str("unexpected end of file"),
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
        // It boxes into the universal error type.
        let boxed: Box<dyn std::error::Error> = Box::new(io);
        assert!(boxed.to_string().contains("song.mid"));

        // Parse errors carry no source but must still Display usefully.
        assert!(std::error::Error::source(&MidiError::NotMidi).is_none());
        assert_eq!(
            MidiError::UnsupportedFormat(2).to_string(),
            "unsupported SMF format 2 (only 0 and 1 are supported)"
        );
        assert_eq!(
            MidiError::BadStatusByte(0xF7).to_string(),
            "bad status byte 0xf7"
        );
        assert_eq!(
            MidiError::MissingTrack { index: 3 }.to_string(),
            "track 3: missing MTrk header"
        );
    }
}
