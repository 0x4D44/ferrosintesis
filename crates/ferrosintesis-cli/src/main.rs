//! ferrosintesis — render a General MIDI file to WAV with synthesized
//! modeled instruments.
//!
//!     ferrosintesis input.mid [-o out.wav] [--rate 44100] [--wet 0.32]
//!                 [--delay MS] [--tail 6] [--solo CH[,CH...]] [-q]
//!
//! The echo bus defaults to a dotted quaver at the song's opening tempo;
//! pass `--delay 0` to disable it, or `--delay <ms>` to set it directly.
//! `--solo 11` (or `--solo 12,13`) renders only the listed 0-based
//! channels — verification stems — keeping the tempo map intact.

#![forbid(unsafe_code)]

use ferrosintesis::offline::{self, Options};
use std::path::PathBuf;
use std::time::Instant;

fn usage() -> ! {
    eprintln!(
        "usage: ferrosintesis <input.mid> [-o out.wav] [--rate N] [--wet X] [--delay MS] [--tail S] [--no-samples] [--solo CH[,CH...]] [--lufs LUFS] [--tp-ceiling dBTP] [--peak-normalize] [-q]\n  default: loudness-normalize to -18 LUFS with a -1 dBTP true-peak limit;\n  --peak-normalize uses the legacy per-track peak normalization (-1 dBFS)."
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
    let mut solo = 0xFFFFu16; // all channels
    let mut verbose = true;
    let mut peak_normalize = false; // legacy per-track peak normalization
    let mut target_lufs = -18.0f32; // BS.1770 integrated-loudness target
    let mut tp_ceiling = -1.0f32; // true-peak ceiling (dBTP)

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
            "--peak-normalize" => peak_normalize = true,
            "--lufs" => {
                target_lufs = args
                    .next()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or_else(|| usage())
            }
            "--tp-ceiling" => {
                tp_ceiling = args
                    .next()
                    .and_then(|v| v.parse().ok())
                    .unwrap_or_else(|| usage())
            }
            "--solo" => {
                // render only the listed 0-based channels (e.g. "11" or "12,13")
                let list = args.next().unwrap_or_else(|| usage());
                solo = 0;
                for part in list.split(',') {
                    let ch: u8 = part
                        .trim()
                        .parse()
                        .ok()
                        .filter(|&c| c < 16)
                        .unwrap_or_else(|| usage());
                    solo |= 1 << ch;
                }
            }
            "-q" | "--quiet" => verbose = false,
            "-h" | "--help" => usage(),
            _ if input.is_none() => input = Some(PathBuf::from(a)),
            _ => usage(),
        }
    }
    let input = input.unwrap_or_else(|| usage());
    let output = output.unwrap_or_else(|| input.with_extension("wav"));

    let song = match offline::load(&input) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("error: {e}");
            std::process::exit(1);
        }
    };
    // echo time: a dotted quaver at the opening tempo, unless overridden
    let delay_s = match delay_ms {
        Some(ms) => ms / 1000.0,
        None => (0.75 * 60.0 / song.initial_bpm() as f32).clamp(0.20, 0.62),
    };
    if verbose {
        eprintln!(
            "{}: {:.2} min, {} events, {} markers, {:.0} bpm at open (echo {:.0} ms)",
            if song.title().is_empty() {
                input.display().to_string()
            } else {
                song.title().to_owned()
            },
            song.seconds() / 60.0,
            song.events_len(),
            song.markers_len(),
            song.initial_bpm(),
            delay_s * 1000.0
        );
    }

    let started = Instant::now();
    let opt = Options::default()
        .with_sample_rate(rate)
        .with_reverb(wet)
        .with_tail(tail)
        .with_echo(delay_s)
        .with_samples(samples)
        .with_solo(solo);
    // The library never writes to stderr; progress reporting is the caller's job.
    let (samples, stats) = if verbose {
        offline::render_with_progress(&song, &opt, &mut |p| {
            eprintln!(
                "  rendered {:>3.0}%  ({:.1} s, {} live voices)",
                p.fraction() * 100.0,
                p.rendered_seconds,
                p.active_voices
            );
        })
    } else {
        offline::render(&song, &opt)
    };
    let pcm = if peak_normalize {
        offline::normalize_to_i16(&samples, stats.peak, 0.891) // legacy: peak to -1 dBFS
    } else {
        // Default: per-track loudness normalization to `target_lufs` with a
        // `tp_ceiling` true-peak limit (see the loudness overhaul PLN/CR docs).
        offline::normalize_loudness(&samples, rate, target_lufs, tp_ceiling)
    };
    if let Err(e) = offline::write_wav(&output, rate, &pcm) {
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
