//! raw_dump — DEV-ONLY measurement tool (not shipped in the product binary).
//!
//! Renders a MIDI exactly as `render_opus.py` does (all CLI defaults) but writes
//! the RAW, UN-normalized float buffer straight from `offline::render` to a
//! 32-bit IEEE-float WAV — bypassing `normalize_to_i16` (the per-track peak
//! normalizer). ffmpeg's ebur128 meter then reads that WAV to report the synth's
//! NATIVE integrated loudness and true peak, before any gain staging.
//!
//!     cargo run --release -p ferrosintesis-cli --example raw_dump -- in.mid out.f32.wav
//!
//! Prints one CSV line to stdout: raw_sample_peak,voices,max_polyphony
//! so a driver script can capture the exact peak at full precision.

use ferrosintesis::offline::{self, Options};
use std::io::Write;

fn write_f32_wav(path: &str, sr: u32, interleaved_stereo: &[f32]) -> std::io::Result<()> {
    // Minimal WAVE_FORMAT_IEEE_FLOAT (format tag 3), 2ch, 32-bit.
    let ch: u16 = 2;
    let bits: u16 = 32;
    let byte_rate = sr * ch as u32 * (bits / 8) as u32;
    let block_align: u16 = ch * (bits / 8);
    let data_bytes = (interleaved_stereo.len() * 4) as u32;
    let mut f = std::io::BufWriter::new(std::fs::File::create(path)?);
    f.write_all(b"RIFF")?;
    f.write_all(&(36 + data_bytes).to_le_bytes())?;
    f.write_all(b"WAVE")?;
    f.write_all(b"fmt ")?;
    f.write_all(&16u32.to_le_bytes())?; // fmt chunk size
    f.write_all(&3u16.to_le_bytes())?; // audio format 3 = IEEE float
    f.write_all(&ch.to_le_bytes())?;
    f.write_all(&sr.to_le_bytes())?;
    f.write_all(&byte_rate.to_le_bytes())?;
    f.write_all(&block_align.to_le_bytes())?;
    f.write_all(&bits.to_le_bytes())?;
    f.write_all(b"data")?;
    f.write_all(&data_bytes.to_le_bytes())?;
    for &s in interleaved_stereo {
        f.write_all(&s.to_le_bytes())?;
    }
    f.flush()
}

fn main() {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    // `--no-samples` disables the LA sample layer. Rendering a probe twice — once with, once
    // without — and diffing per note is an EMPIRICAL sampled-vs-fallback ground truth: a note
    // that renders bit-identically never engaged a sample, so it was measured on the modelled
    // fallback voice. That matters for calibration, because a probe key outside a program's
    // sample bank measures a different voice than real-register content plays. Deriving this
    // by diff avoids replicating the sampler's routing (its repitch cutoff is applied at three
    // separate call sites, so a re-implementation would silently drift).
    let no_samples = argv.iter().any(|a| a == "--no-samples");
    let mut pos = argv.iter().filter(|a| !a.starts_with("--"));
    let input = pos
        .next()
        .expect("usage: raw_dump <in.mid> <out.wav> [--no-samples]")
        .clone();
    let output = pos
        .next()
        .expect("usage: raw_dump <in.mid> <out.wav> [--no-samples]")
        .clone();

    let song = offline::load(std::path::Path::new(&input)).expect("load MIDI");
    // Identical echo-time policy to the CLI (main.rs): dotted quaver at opening
    // tempo, clamped [0.20, 0.62] s.
    let delay_s = (0.75 * 60.0 / song.initial_bpm() as f32).clamp(0.20, 0.62);
    // Identical defaults to render_opus.py's invocation (it passes only -o/-q):
    // rate 44100, wet 0.32, tail 6.0, samples on, all channels.
    let opt = Options::default()
        .with_sample_rate(44100.0)
        .with_reverb(0.32)
        .with_tail(6.0)
        .with_echo(delay_s)
        .with_samples(!no_samples)
        .with_solo(0xFFFF);
    let (samples, stats) = offline::render(&song, &opt);
    let lufs = offline::integrated_lufs(&samples, 44100.0);
    let tp = offline::true_peak_dbtp(&samples, 44100.0);
    write_f32_wav(&output, 44100, &samples).expect("write float WAV");
    // raw_sample_peak, voices, max_polyphony, our_integrated_LUFS, our_true_peak_dBTP
    // (for the differential check vs ffmpeg ebur128 on the same WAV).
    println!(
        "{:.6},{},{},{:.2},{:.2}",
        stats.peak, stats.voices_spawned, stats.max_polyphony, lufs, tp
    );
}
