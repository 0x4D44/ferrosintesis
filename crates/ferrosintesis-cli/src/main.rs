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

mod output;

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
    // The shipping renderer's defaults ARE the library's defaults, so read them
    // rather than restate them (MM-REQ-KILN-00032). `impl Default for Options` in
    // `ferrosintesis::offline` is the one definition; a copy here could drift from
    // it silently, which is exactly what happened across the three entry points.
    let d = Options::default();
    let mut rate = d.sample_rate();
    let mut wet = d.reverb();
    let mut tail = d.tail();
    let mut delay_ms: Option<f32> = None;
    let mut samples = d.samples();
    let mut solo = d.solo(); // all channels
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

    if let Err(e) = output::reject_input_alias(&input, &output) {
        eprintln!("error: {e}");
        std::process::exit(1);
    }

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
    let normalization = if peak_normalize {
        offline::Normalization::peak(0.891) // legacy: peak to -1 dBFS
    } else {
        offline::Normalization::loudness(target_lufs, tp_ceiling)
    };
    // The library never writes to stderr; progress reporting is the caller's job.
    let rendered = if verbose {
        offline::render_to_wav_with_progress(&song, &opt, &output, normalization, &mut |p| {
            eprintln!(
                "  rendered {:>3.0}%  ({:.1} s, {} live voices)",
                p.fraction() * 100.0,
                p.rendered_seconds,
                p.active_voices
            );
        })
    } else {
        offline::render_to_wav(&song, &opt, &output, normalization)
    };
    let stats = rendered.unwrap_or_else(|e| {
        eprintln!("error rendering {}: {e}", output.display());
        std::process::exit(1);
    });
    if verbose {
        let output_bytes = std::fs::metadata(&output)
            .map(|metadata| metadata.len())
            .unwrap_or(0);
        eprintln!(
            "wrote {} ({:.1} MB) in {:.1} s — {} voices, peak {:.2}, max polyphony {}",
            output.display(),
            output_bytes as f64 / 1e6,
            started.elapsed().as_secs_f64(),
            stats.voices_spawned,
            stats.peak,
            stats.max_polyphony
        );
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn embedded_samples_feature_is_forwarded_to_the_library() {
        assert_eq!(
            ferrosintesis::embedded_samples_available(),
            cfg!(feature = "embedded-samples")
        );
    }
}
