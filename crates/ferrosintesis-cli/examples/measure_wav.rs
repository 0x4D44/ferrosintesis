//! measure_wav — DEV-ONLY. Read a 16-bit PCM stereo WAV and print our meter's
//! integrated LUFS and true peak (dBTP), to compare against ffmpeg ebur128 and
//! to bisect limiter-ceiling issues (is the limiter failing, or is our meter
//! under-reading vs ffmpeg?).
//!
//!     cargo run --release -p ferrosintesis-cli --example measure_wav -- in.wav

use ferrosintesis::offline;

#[path = "support/wav.rs"]
mod wav;

fn main() -> Result<(), String> {
    let path = std::env::args()
        .nth(1)
        .ok_or_else(|| "usage: measure_wav <in.wav>".to_owned())?;
    let wav = wav::read_wav(&path, true)?;
    let lufs = offline::integrated_lufs(&wav.samples, wav.sr);
    let tp = offline::true_peak_dbtp(&wav.samples, wav.sr);
    println!("{lufs:.2},{tp:.2}");
    Ok(())
}
