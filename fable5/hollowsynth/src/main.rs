//! hollowsynth — render a General MIDI file to WAV with synthesized
//! (modeled, not sampled) instruments, voiced for the *Hollow Hill* album.
//!
//!     hollowsynth input.mid [-o out.wav] [--rate 44100] [--wet 0.32]
//!                 [--delay MS] [--tail 6] [-q]
//!
//! The echo bus defaults to a dotted quaver at the song's opening tempo;
//! pass `--delay 0` to disable it, or `--delay <ms>` to set it directly.

mod drums;
mod dsp;
mod engine;
mod midi;
mod reverb;
mod sampler;
mod voices;
mod wav;

use std::path::PathBuf;
use std::time::Instant;

fn usage() -> ! {
    eprintln!(
        "usage: hollowsynth <input.mid> [-o out.wav] [--rate N] [--wet X] [--delay MS] [--tail S] [--no-samples] [-q]"
    );
    std::process::exit(2);
}

fn main() {
    let mut input: Option<PathBuf> = None;
    let mut output: Option<PathBuf> = None;
    let mut rate = 44100u32;
    let mut wet = 0.32f32;
    let mut tail = 6.0f32;
    let mut delay_ms: Option<f32> = None;
    let mut samples = true;
    let mut verbose = true;

    let mut args = std::env::args().skip(1);
    while let Some(a) = args.next() {
        match a.as_str() {
            "-o" | "--out" => output = Some(PathBuf::from(args.next().unwrap_or_else(|| usage()))),
            "--rate" => {
                rate = args
                    .next()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or_else(|| usage())
            }
            "--wet" => {
                wet = args
                    .next()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or_else(|| usage())
            }
            "--delay" => {
                delay_ms = Some(
                    args.next()
                        .and_then(|v| v.parse().ok())
                        .unwrap_or_else(|| usage()),
                )
            }
            "--tail" => {
                tail = args
                    .next()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or_else(|| usage())
            }
            "--no-samples" => samples = false,
            "-q" | "--quiet" => verbose = false,
            "-h" | "--help" => usage(),
            _ if input.is_none() => input = Some(PathBuf::from(a)),
            _ => usage(),
        }
    }
    let input = input.unwrap_or_else(|| usage());
    let output = output.unwrap_or_else(|| input.with_extension("wav"));

    let song = match midi::load(&input) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("error: {e}");
            std::process::exit(1);
        }
    };
    // echo time: a dotted quaver at the opening tempo, unless overridden
    let delay_s = match delay_ms {
        Some(ms) => ms / 1000.0,
        None => (0.75 * 60.0 / song.initial_bpm as f32).clamp(0.20, 0.62),
    };
    if verbose {
        eprintln!(
            "{}: {:.2} min, {} events, {} markers, {:.0} bpm at open (echo {:.0} ms)",
            if song.title.is_empty() {
                input.display().to_string()
            } else {
                song.title.clone()
            },
            song.seconds / 60.0,
            song.events.len(),
            song.markers.len(),
            song.initial_bpm,
            delay_s * 1000.0
        );
    }

    let started = Instant::now();
    let opt = engine::Options {
        sr: rate as f32,
        wet,
        tail,
        delay_s,
        samples,
        verbose,
    };
    let (samples, stats) = engine::render(&song, &opt);
    let pcm = engine::normalize_to_i16(&samples, stats.peak, 0.891); // -1 dBFS
    if let Err(e) = wav::write_wav(&output, rate, &pcm) {
        eprintln!("error writing {}: {e}", output.display());
        std::process::exit(1);
    }
    if verbose {
        eprintln!(
            "wrote {} ({:.1} MB) in {:.1} s — {} voices, peak {:.2}, max polyphony {}",
            output.display(),
            (pcm.len() * 2) as f64 / 1e6,
            started.elapsed().as_secs_f64(),
            stats.voices_spawned,
            stats.peak,
            stats.max_polyphony
        );
    }
}
