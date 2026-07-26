//! 16-bit PCM stereo WAV writer.

use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::path::Path;

const HEADER_LEN: u64 = 44;
const PCM_CHUNK_SAMPLES: usize = 4096;

/// Write interleaved stereo 16-bit PCM to a WAV file.
///
/// `interleaved` is left/right/left/right, so its length must be even; `sr` is the
/// sample rate in Hz. This is the last step of the offline pipeline — pass it the
/// `Vec<i16>` from [`normalize_loudness`](crate::offline::normalize_loudness).
///
/// # Errors
///
/// Returns [`io::ErrorKind::InvalidInput`] if the samples are not stereo or the
/// file would exceed the classic RIFF size limit. Otherwise, returns any I/O
/// error from creating or writing the file.
pub fn write_wav(path: &Path, sr: u32, interleaved: &[i16]) -> io::Result<()> {
    let mut writer = WavWriter::create(path, sr, interleaved.len() as u64)?;
    writer.write_samples(interleaved)?;
    writer.finish().map(|_| ())
}

pub(crate) fn checked_data_len(sample_count: u64) -> io::Result<u32> {
    if !sample_count.is_multiple_of(2) {
        return Err(invalid_input("WAV samples must be interleaved stereo"));
    }
    let bytes = sample_count
        .checked_mul(2)
        .ok_or_else(|| invalid_input("WAV sample count exceeds the classic RIFF limit"))?;
    if bytes > u64::from(u32::MAX - 36) {
        return Err(invalid_input(
            "WAV audio exceeds the 4 GiB classic RIFF limit",
        ));
    }
    Ok(bytes as u32)
}

pub(crate) struct WavWriter {
    writer: BufWriter<File>,
    remaining_samples: u64,
}

impl WavWriter {
    pub(crate) fn create(path: &Path, sr: u32, sample_count: u64) -> io::Result<Self> {
        let data_len = checked_data_len(sample_count)?;
        let byte_rate = sr
            .checked_mul(4)
            .ok_or_else(|| invalid_input("WAV sample rate exceeds the header limit"))?;
        let mut writer = BufWriter::new(File::create(path)?);
        write_header(&mut writer, sr, byte_rate, data_len)?;
        Ok(Self {
            writer,
            remaining_samples: sample_count,
        })
    }

    pub(crate) fn write_samples(&mut self, samples: &[i16]) -> io::Result<()> {
        if samples.len() as u64 > self.remaining_samples {
            return Err(invalid_input("more WAV samples written than declared"));
        }
        let mut bytes = [0u8; PCM_CHUNK_SAMPLES * 2];
        for chunk in samples.chunks(PCM_CHUNK_SAMPLES) {
            for (sample, dst) in chunk.iter().zip(bytes.chunks_exact_mut(2)) {
                dst.copy_from_slice(&sample.to_le_bytes());
            }
            self.writer.write_all(&bytes[..chunk.len() * 2])?;
        }
        self.remaining_samples -= samples.len() as u64;
        Ok(())
    }

    pub(crate) fn finish(mut self) -> io::Result<File> {
        if self.remaining_samples != 0 {
            return Err(io::Error::new(
                io::ErrorKind::UnexpectedEof,
                "fewer WAV samples written than declared",
            ));
        }
        self.writer.flush()?;
        self.writer.into_inner().map_err(|error| error.into_error())
    }
}

fn write_header(writer: &mut impl Write, sr: u32, byte_rate: u32, data_len: u32) -> io::Result<()> {
    debug_assert_eq!(HEADER_LEN, 44);
    let w = writer;
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
    Ok(())
}

fn invalid_input(message: &'static str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidInput, message)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn temp_path(label: &str) -> std::path::PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!(
            "ferrosintesis-wav-{label}-{}-{nonce}.wav",
            std::process::id()
        ))
    }

    #[test]
    fn incremental_and_one_shot_writers_are_byte_identical() {
        let samples = [-32768, -1, 0, 1, 32767, 42];
        let one_shot = temp_path("one-shot");
        let incremental = temp_path("incremental");
        write_wav(&one_shot, 44_100, &samples).unwrap();

        let mut writer = WavWriter::create(&incremental, 44_100, samples.len() as u64).unwrap();
        writer.write_samples(&samples[..2]).unwrap();
        writer.write_samples(&samples[2..5]).unwrap();
        writer.write_samples(&samples[5..]).unwrap();
        writer.finish().unwrap();

        assert_eq!(
            fs::read(&one_shot).unwrap(),
            fs::read(&incremental).unwrap()
        );
        fs::remove_file(one_shot).unwrap();
        fs::remove_file(incremental).unwrap();
    }

    #[test]
    fn rejects_invalid_sizes_before_creating_output() {
        let path = temp_path("invalid");
        let error = match WavWriter::create(&path, 44_100, 3) {
            Err(error) => error,
            Ok(_) => panic!("odd sample count unexpectedly accepted"),
        };
        assert_eq!(error.kind(), io::ErrorKind::InvalidInput);
        assert!(!path.exists());
        assert_eq!(
            checked_data_len((u64::from(u32::MAX - 36) / 2) + 2)
                .unwrap_err()
                .kind(),
            io::ErrorKind::InvalidInput
        );
    }

    #[test]
    fn rejects_too_many_or_too_few_samples() {
        let too_many = temp_path("too-many");
        let mut writer = WavWriter::create(&too_many, 44_100, 2).unwrap();
        assert_eq!(
            writer.write_samples(&[0, 0, 0, 0]).unwrap_err().kind(),
            io::ErrorKind::InvalidInput
        );
        drop(writer);
        fs::remove_file(too_many).unwrap();

        let too_few = temp_path("too-few");
        let mut writer = WavWriter::create(&too_few, 44_100, 4).unwrap();
        writer.write_samples(&[0, 0]).unwrap();
        assert_eq!(
            writer.finish().unwrap_err().kind(),
            io::ErrorKind::UnexpectedEof
        );
        fs::remove_file(too_few).unwrap();
    }
}
