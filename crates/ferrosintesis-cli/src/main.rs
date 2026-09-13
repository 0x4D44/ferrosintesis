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

const HELP_TEXT: &str = concat!(
    "usage: ferrosintesis <input.mid> [-o out.wav] [--rate 44100] [--wet 0.32] [--delay MS] [--tail 6] [--no-samples] [--solo CH[,CH...]] [--lufs LUFS] [--tp-ceiling dBTP] [--peak-normalize] [-q] [-h] [-V]\n",
    "  default: loudness-normalize to -18 LUFS with a -1 dBTP true-peak limit;\n",
    "  --peak-normalize uses the legacy per-track peak normalization (-1 dBFS).\n",
    "  -h, --help       print this help text; -V, --version    print the package version;\n",
    "  --               stop option parsing so a filename beginning with '-' can be used."
);

fn help() -> ! {
    println!("{HELP_TEXT}");
    std::process::exit(0);
}

fn usage_error(message: &str) -> ! {
    eprintln!("error: {message}\n{HELP_TEXT}");
    std::process::exit(2);
}

fn version() -> ! {
    println!("ferrosintesis {}", env!("CARGO_PKG_VERSION"));
    std::process::exit(0);
}

fn next_arg(args: &mut impl Iterator<Item = String>, option: &str) -> String {
    args.next()
        .unwrap_or_else(|| usage_error(&format!("missing value for {option}")))
}

fn parse_arg<T>(args: &mut impl Iterator<Item = String>, option: &str) -> T
where
    T: std::str::FromStr,
    T::Err: std::fmt::Display,
{
    let raw = next_arg(args, option);
    raw.parse()
        .unwrap_or_else(|error| usage_error(&format!("invalid value for {option}: {error}")))
}

fn clamp_warnings(
    rate: u32,
    wet: f32,
    tail: f32,
    delay_ms: Option<f32>,
    opt: &Options,
) -> Vec<String> {
    let mut warnings = Vec::new();
    if rate != opt.sample_rate() {
        warnings.push(format!(
            "--rate {rate} is out of range; using {}",
            opt.sample_rate()
        ));
    }
    if wet != opt.reverb() {
        warnings.push(format!(
            "--wet {wet} is out of range; using {}",
            opt.reverb()
        ));
    }
    if tail != opt.tail() {
        warnings.push(format!(
            "--tail {tail} is out of range; using {}",
            opt.tail()
        ));
    }
    if let Some(requested_ms) = delay_ms {
        let requested_s = requested_ms / 1000.0;
        if requested_s != opt.echo() {
            warnings.push(format!(
                "--delay {requested_ms} ms is out of range; using {} ms",
                opt.echo() * 1000.0
            ));
        }
    }
    warnings
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
    let mut options_enabled = true;
    while let Some(a) = args.next() {
        if options_enabled && a == "--" {
            options_enabled = false;
            continue;
        }
        if options_enabled {
            match a.as_str() {
                "-o" | "--out" => output = Some(PathBuf::from(next_arg(&mut args, "--out"))),
                "--rate" => rate = parse_arg(&mut args, "--rate"),
                "--wet" => wet = parse_arg(&mut args, "--wet"),
                "--delay" => delay_ms = Some(parse_arg(&mut args, "--delay")),
                "--tail" => tail = parse_arg(&mut args, "--tail"),
                "--no-samples" => samples = false,
                "--peak-normalize" => peak_normalize = true,
                "--lufs" => target_lufs = parse_arg(&mut args, "--lufs"),
                "--tp-ceiling" => tp_ceiling = parse_arg(&mut args, "--tp-ceiling"),
                "--solo" => {
                    // render only the listed 0-based channels (e.g. "11" or "12,13")
                    let list = next_arg(&mut args, "--solo");
                    solo = 0;
                    for part in list.split(',') {
                        let ch: u8 = part
                            .trim()
                            .parse()
                            .ok()
                            .filter(|&c| c < 16)
                            .unwrap_or_else(|| usage_error("invalid value for --solo"));
                        solo |= 1 << ch;
                    }
                }
                "-q" | "--quiet" => verbose = false,
                "-h" | "--help" => help(),
                "-V" | "--version" => version(),
                _ if a.starts_with('-') => usage_error(&format!("unknown option `{a}`")),
                _ if input.is_none() => input = Some(PathBuf::from(a)),
                _ => usage_error(&format!("unexpected argument `{a}`")),
            }
        } else if input.is_none() {
            input = Some(PathBuf::from(a));
        } else {
            usage_error(&format!("unexpected argument `{a}`"));
        }
    }
    let input = input.unwrap_or_else(|| usage_error("missing input path"));
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
    let opt = Options::default()
        .with_sample_rate(rate)
        .with_reverb(wet)
        .with_tail(tail)
        .with_echo(delay_s)
        .with_samples(samples)
        .with_solo(solo);
    // Clamp warnings are configuration diagnostics, not progress output; keep them visible
    // even when `--quiet` suppresses the render summary and progress callbacks.
    for warning in clamp_warnings(rate, wet, tail, delay_ms, &opt) {
        eprintln!("warning: {warning}");
    }
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
            opt.echo() * 1000.0
        );
    }

    let started = Instant::now();
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
    use super::{clamp_warnings, Options};

    #[test]
    fn reports_each_changed_option_against_the_effective_value() {
        let opt = Options::default()
            .with_sample_rate(500_000)
            .with_reverb(5.0)
            .with_tail(99_999.0)
            .with_echo(60.0);

        assert_eq!(
            clamp_warnings(500_000, 5.0, 99_999.0, Some(60_000.0), &opt),
            vec![
                "--rate 500000 is out of range; using 384000",
                "--wet 5 is out of range; using 1",
                "--tail 99999 is out of range; using 3600",
                "--delay 60000 ms is out of range; using 10000 ms",
            ]
        );
    }

    #[test]
    fn embedded_samples_feature_is_forwarded_to_the_library() {
        assert_eq!(
            ferrosintesis::embedded_samples_available(),
            cfg!(feature = "embedded-samples")
        );
    }
}
