use crate::engine::{self, DitherQuantizer, Options, Progress, Stats};
use crate::loudness::{self, StreamLoudness, StreamTruePeak};
use crate::midi::Song;
use crate::offline::NormalizationKind;
use crate::wav::WavWriter;
use std::ffi::OsString;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufReader, BufWriter, Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

const IO_FRAMES: usize = 4096;
const IO_SAMPLES: usize = IO_FRAMES * 2;
const AUDIO_BYTES: usize = IO_SAMPLES * 4;
const GAIN_BYTES: usize = IO_FRAMES * 4;

static NEXT_TEMP_FILE: AtomicU64 = AtomicU64::new(0);

pub(crate) fn render_to_wav(
    song: &Song,
    opt: &Options,
    output: &Path,
    normalization: NormalizationKind,
    on_progress: &mut dyn FnMut(Progress),
) -> io::Result<Stats> {
    let frames = engine::render_sample_count(song, opt) as u64;
    let sample_count = frames
        .checked_mul(2)
        .ok_or_else(|| invalid_input("render length exceeds addressable stereo samples"))?;
    crate::wav::checked_header(opt.sample_rate(), sample_count)?;

    let (audio_temp, audio_file) = TempFile::reserve(output, "audio")?;
    let gain_temp = match normalization {
        NormalizationKind::Loudness { .. } => Some(TempFile::reserve(output, "gain")?.0),
        NormalizationKind::Peak { .. } => None,
    };

    let (stats, measured_loudness) = render_float_scratch(
        song,
        opt,
        audio_file,
        matches!(normalization, NormalizationKind::Loudness { .. }),
        on_progress,
    )?;

    normalize_audio(
        audio_temp.path(),
        gain_temp.as_ref().map(TempFile::path),
        frames,
        opt.sample_rate(),
        normalization,
        stats.peak,
        measured_loudness,
    )?;

    let (final_temp, final_file) = TempFile::reserve(output, "wav")?;
    write_pcm_wav(
        audio_temp.path(),
        final_file,
        opt.sample_rate(),
        sample_count,
    )?
    .sync_all()?;
    fs::rename(final_temp.path(), output)?;
    Ok(stats)
}

fn render_float_scratch(
    song: &Song,
    opt: &Options,
    file: File,
    measure_loudness: bool,
    on_progress: &mut dyn FnMut(Progress),
) -> io::Result<(Stats, Option<f32>)> {
    let mut writer = BufWriter::new(file);
    let mut meter = measure_loudness.then(|| StreamLoudness::new(opt.sample_rate()));
    let mut bytes = [0u8; 64 * 2 * 4];
    let stats = engine::render_stream_with_progress(song, opt, on_progress, &mut |block| {
        if let Some(meter) = meter.as_mut() {
            meter.push(block);
        }
        encode_f32s(block, &mut bytes);
        writer.write_all(&bytes[..block.len() * 4])
    })?;
    writer.flush()?;
    writer.into_inner().map_err(|error| error.into_error())?;
    Ok((stats, meter.map(StreamLoudness::finish)))
}

fn normalize_audio(
    audio: &Path,
    gain: Option<&Path>,
    frames: u64,
    sample_rate: u32,
    normalization: NormalizationKind,
    render_peak: f32,
    measured_loudness: Option<f32>,
) -> io::Result<(usize, usize, usize)> {
    match normalization {
        NormalizationKind::Peak { target } => {
            let scale = if render_peak > 1e-9 {
                target / render_peak
            } else {
                1.0
            };
            scale_audio(audio, frames * 2, scale)?;
            Ok((0, 0, 0))
        }
        NormalizationKind::Loudness {
            target_lufs,
            ceiling_dbtp,
        } => {
            let gain = gain.expect("loudness normalization reserves gain scratch");
            let mut measured = measured_loudness
                .ok_or_else(|| io::Error::other("loudness meter was not initialized"))?;
            let mut iterations = 0;
            let mut limiter_passes = 0;
            let mut max_limiter_passes = 0;
            for _ in 0..engine::LOUDNESS_MAX_ITERS {
                if !measured.is_finite() {
                    break;
                }
                let delta = target_lufs - measured;
                // The ceiling applies whether or not the loudness needed gain — the
                // same control-flow fix as the buffered normalizer, and for the same
                // reason (MM-BUG-CRUCIBLE-00031). This `break` sat above the limiter,
                // so a signal already on target was written out unlimited. The scratch
                // parity test could not catch it: it compares against the buffered
                // implementation, which carried the identical bug.
                let on_target = delta.abs() < engine::LOUDNESS_TOL_DB;
                if !on_target {
                    scale_audio(audio, frames * 2, 10f32.powf(delta / 20.0))?;
                    iterations += 1;
                }
                let passes = limit_audio(audio, gain, frames, sample_rate, ceiling_dbtp)?;
                limiter_passes += passes;
                max_limiter_passes = max_limiter_passes.max(passes);
                if on_target {
                    break;
                }
                measured = measure_loudness_file(audio, frames, sample_rate)?;
            }
            Ok((iterations, limiter_passes, max_limiter_passes))
        }
    }
}

fn scale_audio(path: &Path, sample_count: u64, scale: f32) -> io::Result<()> {
    let mut file = OpenOptions::new().read(true).write(true).open(path)?;
    let mut bytes = [0u8; AUDIO_BYTES];
    let mut sample = 0u64;
    while sample < sample_count {
        let count = usize::try_from((sample_count - sample).min(IO_SAMPLES as u64))
            .expect("bounded chunk fits usize");
        let offset = sample * 4;
        file.seek(SeekFrom::Start(offset))?;
        file.read_exact(&mut bytes[..count * 4])?;
        for encoded in bytes[..count * 4].chunks_exact_mut(4) {
            let value = f32::from_le_bytes(encoded.try_into().expect("four-byte sample"));
            encoded.copy_from_slice(&(value * scale).to_le_bytes());
        }
        file.seek(SeekFrom::Start(offset))?;
        file.write_all(&bytes[..count * 4])?;
        sample += count as u64;
    }
    Ok(())
}

fn measure_loudness_file(path: &Path, frames: u64, sample_rate: u32) -> io::Result<f32> {
    let mut reader = BufReader::new(File::open(path)?);
    let mut meter = StreamLoudness::new(sample_rate);
    for_chunks(&mut reader, frames * 2, |samples| {
        meter.push(samples);
        Ok(())
    })?;
    Ok(meter.finish())
}

fn limit_audio(
    audio: &Path,
    gain: &Path,
    frames: u64,
    sample_rate: u32,
    ceiling_dbtp: f32,
) -> io::Result<usize> {
    let (ceiling, attack, release) = loudness::limiter_config(sample_rate, ceiling_dbtp);
    let mut passes = 0;
    for _ in 0..loudness::TP_MAX_PASSES {
        if !write_raw_gain(audio, gain, frames, ceiling)? {
            break;
        }
        passes += 1;
        ramp_gain_backward(gain, frames, attack)?;
        ramp_gain_forward(gain, frames, release)?;
        apply_gain(audio, gain, frames)?;
    }
    Ok(passes)
}

fn write_raw_gain(audio: &Path, gain: &Path, frames: u64, ceiling: f32) -> io::Result<bool> {
    let mut audio = BufReader::new(File::open(audio)?);
    let gain_file = OpenOptions::new().write(true).truncate(true).open(gain)?;
    let mut gain = BufWriter::new(gain_file);
    let mut meter = StreamTruePeak::new();
    let mut gain_bytes = [0u8; GAIN_BYTES];
    let mut reduced = false;
    for_chunks(&mut audio, frames * 2, |samples| {
        let count = samples.len() / 2;
        for (i, frame) in samples.chunks_exact(2).enumerate() {
            let envelope = meter.push_frame(frame[0], frame[1]);
            let value = if envelope > ceiling {
                reduced = true;
                ceiling / envelope
            } else {
                1.0
            };
            gain_bytes[i * 4..i * 4 + 4].copy_from_slice(&value.to_le_bytes());
        }
        gain.write_all(&gain_bytes[..count * 4])?;
        Ok(())
    })?;
    gain.flush()?;
    gain.into_inner().map_err(|error| error.into_error())?;
    Ok(reduced)
}

fn ramp_gain_backward(path: &Path, frames: u64, step: f32) -> io::Result<()> {
    let mut file = OpenOptions::new().read(true).write(true).open(path)?;
    let mut bytes = [0u8; GAIN_BYTES];
    let mut values = [0.0f32; IO_FRAMES];
    let mut end = frames;
    let mut next = None;
    while end > 0 {
        let start = end.saturating_sub(IO_FRAMES as u64);
        let count = usize::try_from(end - start).expect("bounded chunk fits usize");
        read_gain_chunk(&mut file, start, count, &mut bytes, &mut values)?;
        for value in values[..count].iter_mut().rev() {
            if let Some(next) = next {
                let ramp = next * step;
                if ramp < *value {
                    *value = ramp;
                }
            }
            next = Some(*value);
        }
        write_gain_chunk(&mut file, start, &values[..count], &mut bytes)?;
        end = start;
    }
    Ok(())
}

fn ramp_gain_forward(path: &Path, frames: u64, step: f32) -> io::Result<()> {
    let mut file = OpenOptions::new().read(true).write(true).open(path)?;
    let mut bytes = [0u8; GAIN_BYTES];
    let mut values = [0.0f32; IO_FRAMES];
    let mut start = 0u64;
    let mut previous = None;
    while start < frames {
        let count =
            usize::try_from((frames - start).min(IO_FRAMES as u64)).expect("chunk fits usize");
        read_gain_chunk(&mut file, start, count, &mut bytes, &mut values)?;
        for value in &mut values[..count] {
            if let Some(previous) = previous {
                let ramp = previous * step;
                if ramp < *value {
                    *value = ramp;
                }
            }
            previous = Some(*value);
        }
        write_gain_chunk(&mut file, start, &values[..count], &mut bytes)?;
        start += count as u64;
    }
    Ok(())
}

fn read_gain_chunk(
    file: &mut File,
    start: u64,
    count: usize,
    bytes: &mut [u8; GAIN_BYTES],
    values: &mut [f32; IO_FRAMES],
) -> io::Result<()> {
    file.seek(SeekFrom::Start(start * 4))?;
    file.read_exact(&mut bytes[..count * 4])?;
    for (dst, encoded) in values[..count]
        .iter_mut()
        .zip(bytes[..count * 4].chunks_exact(4))
    {
        *dst = f32::from_le_bytes(encoded.try_into().expect("four-byte gain"));
    }
    Ok(())
}

fn write_gain_chunk(
    file: &mut File,
    start: u64,
    values: &[f32],
    bytes: &mut [u8; GAIN_BYTES],
) -> io::Result<()> {
    encode_f32s(values, bytes);
    file.seek(SeekFrom::Start(start * 4))?;
    file.write_all(&bytes[..values.len() * 4])
}

fn apply_gain(audio_path: &Path, gain_path: &Path, frames: u64) -> io::Result<()> {
    let mut audio = OpenOptions::new().read(true).write(true).open(audio_path)?;
    let mut gain = BufReader::new(File::open(gain_path)?);
    let mut audio_bytes = [0u8; AUDIO_BYTES];
    let mut gain_bytes = [0u8; GAIN_BYTES];
    let mut frame = 0u64;
    while frame < frames {
        let count =
            usize::try_from((frames - frame).min(IO_FRAMES as u64)).expect("chunk fits usize");
        let audio_offset = frame * 8;
        audio.seek(SeekFrom::Start(audio_offset))?;
        audio.read_exact(&mut audio_bytes[..count * 8])?;
        gain.read_exact(&mut gain_bytes[..count * 4])?;
        for i in 0..count {
            let gain_value = f32::from_le_bytes(gain_bytes[i * 4..i * 4 + 4].try_into().unwrap());
            for channel in 0..2 {
                let at = (i * 2 + channel) * 4;
                let value =
                    f32::from_le_bytes(audio_bytes[at..at + 4].try_into().unwrap()) * gain_value;
                audio_bytes[at..at + 4].copy_from_slice(&value.to_le_bytes());
            }
        }
        audio.seek(SeekFrom::Start(audio_offset))?;
        audio.write_all(&audio_bytes[..count * 8])?;
        frame += count as u64;
    }
    Ok(())
}

fn write_pcm_wav(
    audio_path: &Path,
    wav_file: File,
    sample_rate: u32,
    sample_count: u64,
) -> io::Result<File> {
    let mut reader = BufReader::new(File::open(audio_path)?);
    let mut writer = WavWriter::from_file(wav_file, sample_rate, sample_count)?;
    let mut quantizer = DitherQuantizer::new();
    let mut pcm = [0i16; IO_SAMPLES];
    for_chunks(&mut reader, sample_count, |samples| {
        for (dst, &sample) in pcm.iter_mut().zip(samples) {
            *dst = quantizer.quantize(sample, 1.0);
        }
        writer.write_samples(&pcm[..samples.len()])
    })?;
    writer.finish()
}

fn for_chunks(
    reader: &mut impl Read,
    sample_count: u64,
    mut consume: impl FnMut(&[f32]) -> io::Result<()>,
) -> io::Result<()> {
    let mut bytes = [0u8; AUDIO_BYTES];
    let mut samples = [0.0f32; IO_SAMPLES];
    let mut offset = 0u64;
    while offset < sample_count {
        let count = usize::try_from((sample_count - offset).min(IO_SAMPLES as u64))
            .expect("bounded chunk fits usize");
        reader.read_exact(&mut bytes[..count * 4])?;
        for (dst, encoded) in samples[..count]
            .iter_mut()
            .zip(bytes[..count * 4].chunks_exact(4))
        {
            *dst = f32::from_le_bytes(encoded.try_into().expect("four-byte sample"));
        }
        consume(&samples[..count])?;
        offset += count as u64;
    }
    Ok(())
}

fn encode_f32s(samples: &[f32], bytes: &mut [u8]) {
    for (&sample, encoded) in samples.iter().zip(bytes.chunks_exact_mut(4)) {
        encoded.copy_from_slice(&sample.to_le_bytes());
    }
}

struct TempFile {
    path: PathBuf,
}

impl TempFile {
    fn reserve(output: &Path, role: &str) -> io::Result<(Self, File)> {
        let parent = output
            .parent()
            .filter(|path| !path.as_os_str().is_empty())
            .unwrap_or_else(|| Path::new("."));
        let file_name = output
            .file_name()
            .ok_or_else(|| invalid_input("render output path must contain a file name"))?;
        for _ in 0..100 {
            let sequence = NEXT_TEMP_FILE.fetch_add(1, Ordering::Relaxed);
            let mut temporary_name = OsString::from(".");
            temporary_name.push(file_name);
            temporary_name.push(format!(".{}.{}.{role}.tmp", std::process::id(), sequence));
            let path = parent.join(temporary_name);
            match OpenOptions::new()
                .read(true)
                .write(true)
                .create_new(true)
                .open(&path)
            {
                Ok(file) => return Ok((Self { path }, file)),
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {}
                Err(error) => return Err(error),
            }
        }
        Err(io::Error::new(
            io::ErrorKind::AlreadyExists,
            format!(
                "could not reserve temporary render storage beside {}",
                output.display()
            ),
        ))
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for TempFile {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

fn invalid_input(message: &'static str) -> io::Error {
    io::Error::new(io::ErrorKind::InvalidInput, message)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    struct FixturePaths {
        audio: PathBuf,
        gain: PathBuf,
        wav: PathBuf,
    }

    impl FixturePaths {
        fn new(label: &str) -> Self {
            let nonce = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let stem = format!(
                "ferrosintesis-scratch-{label}-{}-{nonce}",
                std::process::id()
            );
            let parent = std::env::temp_dir();
            Self {
                audio: parent.join(format!("{stem}.audio")),
                gain: parent.join(format!("{stem}.gain")),
                wav: parent.join(format!("{stem}.wav")),
            }
        }
    }

    impl Drop for FixturePaths {
        fn drop(&mut self) {
            let _ = fs::remove_file(&self.audio);
            let _ = fs::remove_file(&self.gain);
            let _ = fs::remove_file(&self.wav);
        }
    }

    fn write_audio(path: &Path, samples: &[f32]) {
        let mut writer = BufWriter::new(File::create(path).unwrap());
        let mut bytes = [0u8; AUDIO_BYTES];
        for chunk in samples.chunks(IO_SAMPLES) {
            encode_f32s(chunk, &mut bytes);
            writer.write_all(&bytes[..chunk.len() * 4]).unwrap();
        }
        writer.flush().unwrap();
    }

    fn scratch_pcm(
        label: &str,
        samples: &[f32],
        sample_rate: u32,
        normalization: NormalizationKind,
        peak: f32,
    ) -> (Vec<u8>, (usize, usize, usize)) {
        let paths = FixturePaths::new(label);
        write_audio(&paths.audio, samples);
        File::create(&paths.gain).unwrap();
        let measured = match normalization {
            NormalizationKind::Loudness { .. } => {
                Some(loudness::integrated_lufs(samples, sample_rate))
            }
            NormalizationKind::Peak { .. } => None,
        };
        let work = normalize_audio(
            &paths.audio,
            Some(&paths.gain),
            (samples.len() / 2) as u64,
            sample_rate,
            normalization,
            peak,
            measured,
        )
        .unwrap();
        let wav = File::create(&paths.wav).unwrap();
        write_pcm_wav(&paths.audio, wav, sample_rate, samples.len() as u64)
            .unwrap()
            .sync_all()
            .unwrap();
        (fs::read(&paths.wav).unwrap()[44..].to_vec(), work)
    }

    fn pcm_bytes(samples: &[i16]) -> Vec<u8> {
        samples
            .iter()
            .flat_map(|sample| sample.to_le_bytes())
            .collect()
    }

    #[test]
    fn peak_normalization_is_byte_identical_across_disk_chunks() {
        let samples: Vec<f32> = (0..IO_FRAMES * 3 + 17)
            .flat_map(|i| {
                let sample = (i as f32 * 0.017).sin() * 0.37;
                [sample, -sample * 0.73]
            })
            .collect();
        let peak = samples.iter().fold(0.0f32, |m, &x| m.max(x.abs()));
        let expected = engine::normalize_to_i16(&samples, peak, 0.891);
        let (actual, work) = scratch_pcm(
            "peak",
            &samples,
            44_100,
            NormalizationKind::Peak { target: 0.891 },
            peak,
        );
        assert_eq!(actual, pcm_bytes(&expected));
        assert_eq!(work, (0, 0, 0));
    }

    /// MM-BUG-CRUCIBLE-00031, the scratch half — and deliberately NOT a parity test.
    ///
    /// The existing parity oracle compares this implementation against the buffered
    /// one, which carried the identical control-flow bug, so it agreed with it and
    /// proved nothing. This one measures the WRITTEN PCM against the ceiling directly.
    #[test]
    fn scratch_loudness_applies_the_ceiling_when_already_on_target() {
        let sample_rate = 44_100u32;
        let ceiling = -6.0f32;
        let samples: Vec<f32> = (0..sample_rate as usize * 2)
            .flat_map(|i| {
                let s = 0.9
                    * (2.0 * std::f32::consts::PI * 997.0 * i as f32 / sample_rate as f32).sin();
                [s, s]
            })
            .collect();

        let target = loudness::integrated_lufs(&samples, sample_rate);
        let peak_in = loudness::true_peak_dbtp(&samples, sample_rate);
        assert!(
            peak_in > ceiling + 1.0,
            "premise: the input must exceed the ceiling, but it is {peak_in:.2} dBTP"
        );

        let (pcm, _work) = scratch_pcm(
            "ceiling-on-target",
            &samples,
            sample_rate,
            NormalizationKind::Loudness {
                target_lufs: target,
                ceiling_dbtp: ceiling,
            },
            samples.iter().fold(0.0f32, |m, &x| m.max(x.abs())),
        );

        let back: Vec<f32> = pcm
            .chunks_exact(2)
            .map(|b| i16::from_le_bytes([b[0], b[1]]) as f32 / 32768.0)
            .collect();
        let peak_out = loudness::true_peak_dbtp(&back, sample_rate);
        assert!(
            peak_out <= ceiling + 0.3,
            "already-on-target signal was written unlimited: {peak_out:.2} dBTP \
             against a {ceiling:.1} dBTP ceiling"
        );
        let loudness_out = loudness::integrated_lufs(&back, sample_rate);
        assert!(
            loudness_out <= target + 0.3,
            "loudness overshot the target: {loudness_out:.2} LUFS against {target:.2}"
        );
    }

    #[test]
    fn high_crest_loudness_normalization_is_byte_identical() {
        let sample_rate = 8_000u32;
        let frames = sample_rate as usize * 6;
        let burst_period = sample_rate as usize / 3;
        let burst_len = sample_rate as usize / 200;
        let samples: Vec<f32> = (0..frames)
            .flat_map(|i| {
                let t = i as f32 / sample_rate as f32;
                let mut sample = 0.05 * (2.0 * std::f32::consts::PI * 180.0 * t).sin();
                if i % burst_period < burst_len {
                    sample += 0.55 * (2.0 * std::f32::consts::PI * 1200.0 * t).sin();
                }
                [sample, sample]
            })
            .collect();
        let expected = engine::normalize_loudness(&samples, sample_rate, -18.0, -6.0);
        let peak = samples.iter().fold(0.0f32, |m, &x| m.max(x.abs()));
        let (actual, (iterations, _, max_limiter_passes)) = scratch_pcm(
            "high-crest",
            &samples,
            sample_rate,
            NormalizationKind::Loudness {
                target_lufs: -18.0,
                ceiling_dbtp: -6.0,
            },
            peak,
        );
        assert_eq!(actual, pcm_bytes(&expected));
        assert!(iterations > 1, "fixture did not exercise loudness recovery");
        assert!(
            max_limiter_passes > 1,
            "fixture did not exercise limiter convergence"
        );
    }

    #[test]
    fn empty_loudness_render_is_a_header_only_wav() {
        let (actual, work) = scratch_pcm(
            "empty",
            &[],
            44_100,
            NormalizationKind::Loudness {
                target_lufs: -18.0,
                ceiling_dbtp: -1.0,
            },
            0.0,
        );
        assert!(actual.is_empty());
        assert_eq!(work, (0, 0, 0));
    }

    #[test]
    fn truncated_audio_scratch_is_an_error() {
        let paths = FixturePaths::new("truncated");
        write_audio(&paths.audio, &[0.1, -0.1]);
        let error = measure_loudness_file(&paths.audio, 2, 44_100).unwrap_err();
        assert_eq!(error.kind(), io::ErrorKind::UnexpectedEof);
    }
}
