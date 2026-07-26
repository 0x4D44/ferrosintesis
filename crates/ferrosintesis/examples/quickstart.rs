//! The README's quick-start, as a compiled example.
//!
//! The README is the crate's landing page on crates.io and its code block is the first
//! thing anyone copies. A fenced block in a markdown file is checked by nothing, so this
//! file exists to keep it honest: it is the same program, and `cargo build --examples`
//! (which `clippy --all-targets` already runs in the gate) fails if the API drifts from
//! what the README claims.
//!
//! Keep the two in sync. If you change this, change the README.
//!
//!     cargo run --release --example quickstart -- input.mid output.wav

use ferrosintesis::offline::{self, Normalization, Options};
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let input = args.next().unwrap_or_else(|| "input.mid".into());
    let output = args.next().unwrap_or_else(|| "output.wav".into());

    let song = offline::load(Path::new(&input))?;
    println!(
        "{}: {:.1} s, {} events",
        song.title(),
        song.seconds(),
        song.events_len()
    );

    // `Options` has private fields: build it from Default with the with_* builders.
    let opt = Options::default().with_reverb(0.25);

    // Render with bounded audio memory, normalize to -18 LUFS (BS.1770-4)
    // under a -1 dBTP ceiling, and atomically publish the completed WAV.
    let stats = offline::render_to_wav(
        &song,
        &opt,
        Path::new(&output),
        Normalization::loudness(-18.0, -1.0),
    )?;
    eprintln!("{} voices, peak {:.3}", stats.voices_spawned, stats.peak);
    Ok(())
}
