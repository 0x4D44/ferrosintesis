use std::fs;

const MIN_SAMPLE_RATE: u32 = 8_000;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SampleFormat {
    Pcm16,
    Float32,
}

#[derive(Debug)]
pub struct Wav {
    pub samples: Vec<f32>,
    pub sr: u32,
}

pub fn read_wav(path: &str, require_pcm16_stereo: bool) -> Result<Wav, String> {
    let bytes = fs::read(path).map_err(|error| format!("{path}: {error}"))?;
    decode_wav(path, &bytes, require_pcm16_stereo)
}

pub(crate) fn decode_wav(
    path: &str,
    bytes: &[u8],
    require_pcm16_stereo: bool,
) -> Result<Wav, String> {
    if bytes.len() < 12 || &bytes[0..4] != b"RIFF" || &bytes[8..12] != b"WAVE" {
        return Err(format!("{path}: not a RIFF/WAVE file"));
    }
    let riff_size = little_u32(&bytes[4..8]) as usize;
    let riff_end = 8usize
        .checked_add(riff_size)
        .ok_or_else(|| format!("{path}: RIFF size overflows this platform"))?;
    if riff_end > bytes.len() {
        return Err(format!(
            "{path}: truncated RIFF body (declares {riff_size} bytes, file has {})",
            bytes.len().saturating_sub(8)
        ));
    }

    let mut format = None;
    let mut data = None;
    let mut position = 12usize;
    while position < riff_end {
        let header_end = position
            .checked_add(8)
            .ok_or_else(|| format!("{path}: chunk header offset overflow"))?;
        if header_end > riff_end {
            return Err(format!("{path}: truncated WAV chunk header"));
        }
        let id = &bytes[position..position + 4];
        let size = little_u32(&bytes[position + 4..header_end]) as usize;
        let body_start = header_end;
        let body_end = body_start
            .checked_add(size)
            .ok_or_else(|| format!("{path}: WAV chunk size overflow"))?;
        if body_end > riff_end {
            return Err(format!(
                "{path}: truncated {} chunk (declares {size} bytes)",
                chunk_name(id)
            ));
        }
        let body = &bytes[body_start..body_end];
        match id {
            b"fmt " if format.is_none() => {
                if body.len() < 16 {
                    return Err(format!(
                        "{path}: truncated fmt chunk (need 16 bytes, got {})",
                        body.len()
                    ));
                }
                format = Some(Format {
                    tag: little_u16(&body[0..2]),
                    channels: little_u16(&body[2..4]),
                    sample_rate: little_u32(&body[4..8]),
                    byte_rate: little_u32(&body[8..12]),
                    block_align: little_u16(&body[12..14]),
                    bits: little_u16(&body[14..16]),
                });
            }
            b"data" if data.is_none() => data = Some(body),
            _ => {}
        }
        position = body_end
            .checked_add(size & 1)
            .ok_or_else(|| format!("{path}: WAV padding offset overflow"))?;
        if position > riff_end {
            return Err(format!("{path}: truncated padding after WAV chunk"));
        }
    }

    let format = format.ok_or_else(|| format!("{path}: missing fmt chunk"))?;
    let data = data.ok_or_else(|| format!("{path}: missing data chunk"))?;
    let sample_format = match (format.tag, format.bits) {
        (1, 16) => SampleFormat::Pcm16,
        (3, 32) => SampleFormat::Float32,
        _ => {
            return Err(format!(
                "{path}: need 16-bit PCM or 32-bit IEEE float, got {}-bit format {}",
                format.bits, format.tag
            ));
        }
    };
    if !(1..=2).contains(&format.channels) {
        return Err(format!(
            "{path}: need mono or stereo, got {} channels",
            format.channels
        ));
    }
    if require_pcm16_stereo && (sample_format != SampleFormat::Pcm16 || format.channels != 2) {
        return Err(format!(
            "{path}: need 16-bit stereo PCM, got {} x{}",
            sample_format.description(),
            format.channels
        ));
    }
    if format.sample_rate < MIN_SAMPLE_RATE {
        return Err(format!(
            "{path}: unsupported sample rate {} Hz; need at least {MIN_SAMPLE_RATE} Hz",
            format.sample_rate
        ));
    }

    let bytes_per_sample = (format.bits / 8) as usize;
    let expected_align = format.channels as usize * bytes_per_sample;
    if format.block_align as usize != expected_align {
        return Err(format!(
            "{path}: inconsistent block alignment {} (expected {expected_align})",
            format.block_align
        ));
    }
    let expected_byte_rate = format.sample_rate as u64 * expected_align as u64;
    if format.byte_rate as u64 != expected_byte_rate {
        return Err(format!(
            "{path}: inconsistent byte rate {} (expected {expected_byte_rate})",
            format.byte_rate
        ));
    }
    if data.len() % expected_align != 0 {
        return Err(format!(
            "{path}: incomplete data frame ({} bytes is not a multiple of {expected_align})",
            data.len()
        ));
    }

    let frames = data.len() / expected_align;
    let mut samples = Vec::with_capacity(frames * 2);
    for frame in data.chunks_exact(expected_align) {
        let sample = |channel: usize| {
            let offset = channel * bytes_per_sample;
            match sample_format {
                SampleFormat::Pcm16 => {
                    i16::from_le_bytes([frame[offset], frame[offset + 1]]) as f32 / 32768.0
                }
                SampleFormat::Float32 => f32::from_le_bytes([
                    frame[offset],
                    frame[offset + 1],
                    frame[offset + 2],
                    frame[offset + 3],
                ]),
            }
        };
        let left = sample(0);
        let right = if format.channels == 2 {
            sample(1)
        } else {
            left
        };
        samples.extend_from_slice(&[left, right]);
    }

    Ok(Wav {
        samples,
        sr: format.sample_rate,
    })
}

impl SampleFormat {
    fn description(self) -> &'static str {
        match self {
            Self::Pcm16 => "16-bit PCM",
            Self::Float32 => "32-bit IEEE float",
        }
    }
}

#[derive(Clone, Copy)]
struct Format {
    tag: u16,
    channels: u16,
    sample_rate: u32,
    byte_rate: u32,
    block_align: u16,
    bits: u16,
}

fn little_u16(bytes: &[u8]) -> u16 {
    u16::from_le_bytes([bytes[0], bytes[1]])
}

fn little_u32(bytes: &[u8]) -> u32 {
    u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]])
}

fn chunk_name(id: &[u8]) -> String {
    String::from_utf8_lossy(id).into_owned()
}
