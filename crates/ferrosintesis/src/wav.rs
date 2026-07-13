//! 16-bit PCM stereo WAV writer.

use std::io::{BufWriter, Write};
use std::path::Path;

/// Write interleaved stereo 16-bit PCM to a WAV file.
///
/// `interleaved` is left/right/left/right, so its length must be even; `sr` is the
/// sample rate in Hz. This is the last step of the offline pipeline — pass it the
/// `Vec<i16>` from [`normalize_loudness`](crate::offline::normalize_loudness).
///
/// # Errors
///
/// Any [`std::io::Error`] from creating or writing the file.
pub fn write_wav(path: &Path, sr: u32, interleaved: &[i16]) -> std::io::Result<()> {
    let mut w = BufWriter::new(std::fs::File::create(path)?);
    let data_len = (interleaved.len() * 2) as u32;
    let byte_rate = sr * 2 * 2;
    w.write_all(b"RIFF")?;
    w.write_all(&(36 + data_len).to_le_bytes())?;
    w.write_all(b"WAVE")?;
    w.write_all(b"fmt ")?;
    w.write_all(&16u32.to_le_bytes())?;
    w.write_all(&1u16.to_le_bytes())?; // PCM
    w.write_all(&2u16.to_le_bytes())?; // stereo
    w.write_all(&sr.to_le_bytes())?;
    w.write_all(&byte_rate.to_le_bytes())?;
    w.write_all(&4u16.to_le_bytes())?; // block align
    w.write_all(&16u16.to_le_bytes())?;
    w.write_all(b"data")?;
    w.write_all(&data_len.to_le_bytes())?;
    let mut buf = Vec::with_capacity(interleaved.len() * 2);
    for &s in interleaved {
        buf.extend_from_slice(&s.to_le_bytes());
    }
    w.write_all(&buf)?;
    w.flush()
}
