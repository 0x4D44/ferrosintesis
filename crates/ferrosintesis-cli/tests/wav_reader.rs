#[path = "../examples/support/wav.rs"]
mod wav;

use wav::decode_wav;

fn wav_bytes(format: u16, channels: u16, bits: u16, sample_rate: u32, data: &[u8]) -> Vec<u8> {
    let bytes_per_sample = bits / 8;
    let block_align = channels * bytes_per_sample;
    let byte_rate = sample_rate * block_align as u32;
    let mut wav = Vec::new();
    wav.extend_from_slice(b"RIFF");
    wav.extend_from_slice(&(36 + data.len() as u32).to_le_bytes());
    wav.extend_from_slice(b"WAVEfmt ");
    wav.extend_from_slice(&16u32.to_le_bytes());
    wav.extend_from_slice(&format.to_le_bytes());
    wav.extend_from_slice(&channels.to_le_bytes());
    wav.extend_from_slice(&sample_rate.to_le_bytes());
    wav.extend_from_slice(&byte_rate.to_le_bytes());
    wav.extend_from_slice(&block_align.to_le_bytes());
    wav.extend_from_slice(&bits.to_le_bytes());
    wav.extend_from_slice(b"data");
    wav.extend_from_slice(&(data.len() as u32).to_le_bytes());
    wav.extend_from_slice(data);
    wav
}

#[test]
fn file_reader_uses_the_shared_decoder() {
    let unique = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .expect("system clock is after the Unix epoch")
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "ferrosintesis-wav-reader-{}-{unique}.wav",
        std::process::id()
    ));
    std::fs::write(&path, wav_bytes(1, 2, 16, 48_000, &[0; 4])).expect("write WAV fixture");
    let result = wav::read_wav(path.to_str().expect("temporary path is UTF-8"), true);
    std::fs::remove_file(&path).expect("remove WAV fixture");

    assert_eq!(result.expect("read PCM stereo").sr, 48_000);
}

#[test]
fn pcm_stereo_preserves_44k1_and_48k_rates() {
    for sample_rate in [44_100, 48_000] {
        let bytes = wav_bytes(1, 2, 16, sample_rate, &[0, 0, 0xff, 0x7f]);
        let decoded = decode_wav("fixture.wav", &bytes, true).expect("decode PCM stereo");
        assert_eq!(decoded.sr, sample_rate);
        assert_eq!(decoded.samples, [0.0, 32767.0 / 32768.0]);
    }
}

#[test]
fn strict_meter_rejects_mono_and_float_layouts() {
    let mono = wav_bytes(1, 1, 16, 44_100, &[0, 0]);
    assert!(decode_wav("mono.wav", &mono, true)
        .unwrap_err()
        .contains("need 16-bit stereo PCM"));

    let float = wav_bytes(3, 2, 32, 48_000, &[0; 8]);
    assert!(decode_wav("float.wav", &float, true)
        .unwrap_err()
        .contains("need 16-bit stereo PCM"));
}

#[test]
fn shared_reader_still_accepts_calmeter_mono_and_float_inputs() {
    let mono = wav_bytes(1, 1, 16, 8_000, &[0, 64]);
    let decoded = decode_wav("mono.wav", &mono, false).expect("decode mono PCM");
    assert_eq!(decoded.samples, [0.5, 0.5]);

    let mut float_data = Vec::new();
    float_data.extend_from_slice(&0.25f32.to_le_bytes());
    float_data.extend_from_slice(&(-0.5f32).to_le_bytes());
    let float = wav_bytes(3, 2, 32, 48_000, &float_data);
    let decoded = decode_wav("float.wav", &float, false).expect("decode stereo float");
    assert_eq!(decoded.samples, [0.25, -0.5]);
}

#[test]
fn rejects_missing_or_truncated_format_and_missing_data() {
    let missing_format = b"RIFF\x04\0\0\0WAVE";
    assert!(decode_wav("missing-fmt.wav", missing_format, true)
        .unwrap_err()
        .contains("missing fmt chunk"));

    let mut truncated_format = Vec::from(&b"RIFF\x18\0\0\0WAVEfmt \x10\0\0\0"[..]);
    truncated_format.extend_from_slice(&[1, 0, 2, 0]);
    assert!(decode_wav("truncated-fmt.wav", &truncated_format, true)
        .unwrap_err()
        .contains("truncated"));

    let mut missing_data = wav_bytes(1, 2, 16, 44_100, &[]);
    missing_data.truncate(36);
    missing_data[4..8].copy_from_slice(&28u32.to_le_bytes());
    assert!(decode_wav("missing-data.wav", &missing_data, true)
        .unwrap_err()
        .contains("missing data chunk"));
}

#[test]
fn rejects_inconsistent_alignment_and_incomplete_data() {
    let mut bad_alignment = wav_bytes(1, 2, 16, 44_100, &[0; 4]);
    bad_alignment[32..34].copy_from_slice(&2u16.to_le_bytes());
    assert!(decode_wav("bad-align.wav", &bad_alignment, true)
        .unwrap_err()
        .contains("inconsistent block alignment"));

    let incomplete = wav_bytes(1, 2, 16, 44_100, &[0; 2]);
    assert!(decode_wav("incomplete.wav", &incomplete, true)
        .unwrap_err()
        .contains("incomplete data frame"));
}

#[test]
fn rejects_non_pcm_and_unsupported_sample_rates() {
    let non_pcm = wav_bytes(6, 2, 16, 44_100, &[0; 4]);
    assert!(decode_wav("non-pcm.wav", &non_pcm, true)
        .unwrap_err()
        .contains("need 16-bit PCM or 32-bit IEEE float"));

    let too_slow = wav_bytes(1, 2, 16, 1, &[0; 4]);
    assert!(decode_wav("one-hz.wav", &too_slow, true)
        .unwrap_err()
        .contains("unsupported sample rate 1 Hz"));
}
