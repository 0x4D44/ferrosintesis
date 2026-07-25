//! measure_wav — DEV-ONLY. Read a 16-bit PCM stereo WAV and print our meter's
//! integrated LUFS and true peak (dBTP), to compare against ffmpeg ebur128 and
//! to bisect limiter-ceiling issues (is the limiter failing, or is our meter
//! under-reading vs ffmpeg?).
//!
//!     cargo run --release -p ferrosintesis-cli --example measure_wav -- in.wav

use ferrosintesis::offline;

fn main() {
    let path = std::env::args()
        .nth(1)
        .expect("usage: measure_wav <in.wav>");
    let bytes = std::fs::read(&path).expect("read wav");
    // Find the "data" chunk (skip RIFF/WAVE/fmt and any other chunks).
    let mut pos = 12; // past "RIFF"<size>"WAVE"
    let mut data: &[u8] = &[];
    while pos + 8 <= bytes.len() {
        let id = &bytes[pos..pos + 4];
        let sz = u32::from_le_bytes([
            bytes[pos + 4],
            bytes[pos + 5],
            bytes[pos + 6],
            bytes[pos + 7],
        ]) as usize;
        let body_start = pos + 8;
        if id == b"data" {
            let end = (body_start + sz).min(bytes.len());
            data = &bytes[body_start..end];
            break;
        }
        pos = body_start + sz + (sz & 1); // chunks are word-aligned
    }
    // i16 LE interleaved stereo → f32.
    let samples: Vec<f32> = data
        .chunks_exact(2)
        .map(|b| i16::from_le_bytes([b[0], b[1]]) as f32 / 32768.0)
        .collect();
    let lufs = offline::integrated_lufs(&samples, 44100);
    let tp = offline::true_peak_dbtp(&samples, 44100);
    println!("{lufs:.2},{tp:.2}");
}
