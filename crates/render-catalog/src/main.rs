//! render-catalog — render every album's MIDI to a tagged Ogg Opus listening copy.
//!
//! Replaces the retired `render_opus.py` / `build.py`: it discovers the album MIDIs,
//! renders each one to a loudness-normalized WAV **in-process** with ferrosintesis,
//! then encodes it with `ropusenc` (on PATH) into
//! `listening/<artist>/<album>/<name>.opus` with full Vorbis-comment tags.
//!
//!     cargo run --release -p render-catalog                          # everything
//!     cargo run --release -p render-catalog -- --album "Sub Rosa"    # one album
//!     cargo run --release -p render-catalog -- --jobs 4              # parallelism
//!     cargo run --release -p render-catalog -- --only-list paths.txt # surgical refresh
//!
//! The `.opus` files are reproducible **build output** (git-ignored), not source:
//! the committed inputs are the album MIDIs plus the synth. Requires `ropusenc`
//! (from the sibling `ropus` repo) on PATH.

#![forbid(unsafe_code)]

use ferrosintesis::offline::{self, Options, Song};
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicUsize, Ordering};

// ---------------------------------------------------------------------------
// Constants — kept in lockstep with ferrosintesis-cli's defaults, because the
// retired render_opus.py drove the CLI with only `-q --tp-ceiling -4.5` and took
// every other value from the CLI's own defaults. Changing one here silently
// changes the whole catalog's sound: see the parameter-parity test below.
// ---------------------------------------------------------------------------

const BITRATE: &str = "96000"; // VBR; Opus at 96k is near-transparent for music
const DATE: &str = "2026";
const SR: u32 = 44100;
const WET: f32 = 0.32;
const TAIL: f32 = 6.0;

/// BS.1770-4 integrated-loudness target (the ferrosintesis-cli default).
const TARGET_LUFS: f32 = -18.0;

/// True-peak ceiling for the WAV handed to `ropusenc`. Deliberately more
/// conservative than the −1 dBTP delivery target: the lossy 96k encode plus the
/// 44.1→48 kHz resample *adds* inter-sample true peak — up to ~2.9 dB on the
/// brightest material — so limiting the WAV here keeps the encoded `.opus` under
/// −1 dBTP. Loudness is unaffected (peaks only).
const TP_CEILING: f32 = -4.5;

/// R128 replay-gain reference (RFC 7845 §5.2).
const R128_REFERENCE_LUFS: f32 = -23.0;

const DEFAULT_JOBS: usize = 6;

/// Album metadata, keyed by the directory that holds the `midi/` folder.
/// `(dir key, album title, artist == composer == album-artist, genre)`
///
/// Order matters: it is the render order, and it is the order the "album has no
/// MIDI files" guard reports in.
const ALBUMS: &[(&str, &str, &str, &str)] = &[
    (
        "albums/fable5/Hollow Hill",
        "Hollow Hill",
        "Claude Fable 5",
        "Progressive Rock / Instrumental",
    ),
    (
        "albums/fable5/Heliopause",
        "Heliopause",
        "Claude Fable 5",
        "Electronic / Synth",
    ),
    (
        "albums/fable5/The Burning Meridian",
        "The Burning Meridian",
        "Claude Fable 5",
        "Orchestral / Cinematic",
    ),
    (
        "albums/fable5/Tuxedo Noir",
        "Tuxedo Noir",
        "Claude Fable 5",
        "Spy Jazz / Instrumental",
    ),
    (
        "albums/fable5/Seven Kinds of Sunlight",
        "Seven Kinds of Sunlight",
        "Claude Fable 5",
        "Pop-Prog / Instrumental",
    ),
    (
        "albums/fable5/Sub Rosa",
        "Sub Rosa",
        "Claude Fable 5",
        "Electronic / Downtempo",
    ),
    (
        "albums/fable5/The Ninth Bell",
        "The Ninth Bell",
        "Claude Fable 5",
        "Gothic Orchestral / Instrumental",
    ),
    (
        "albums/fable5/The Signal Fire",
        "The Signal Fire",
        "Claude Fable 5",
        "Progressive Rock / Instrumental",
    ),
    (
        "albums/fable5/Winter Guests",
        "Winter Guests",
        "Claude Fable 5",
        "Progressive Rock / Instrumental",
    ),
    (
        "albums/fable5",
        "The Iron Tide",
        "Claude Fable 5",
        "Cinematic / Instrumental",
    ),
    (
        "albums/fable5/Through Lines",
        "Through Lines",
        "Claude Fable 5",
        "Progressive Eclectic / Instrumental",
    ),
    (
        "albums/fable5/Big Weather",
        "Big Weather",
        "Claude Fable 5",
        "Rock-Pop / Instrumental",
    ),
    (
        "albums/gpt5-3-spark",
        "The Spark",
        "GPT-5.3 Spark",
        "Instrumental",
    ),
    (
        "albums/gpt5-5/Hours After Rain",
        "Hours After Rain",
        "GPT-5.5",
        "Instrumental",
    ),
    (
        "albums/gpt5-5/The Long Turning",
        "The Long Turning",
        "GPT-5.5",
        "Instrumental",
    ),
    (
        "albums/gpt5-6/Atlas of Becoming",
        "Atlas of Becoming",
        "GPT-5.6",
        "Cinematic / Progressive / Instrumental",
    ),
    (
        "albums/gpt5-6/The Architecture of Air",
        "The Architecture of Air",
        "GPT-5.6",
        "Cathedral Organ / Cinematic / Instrumental",
    ),
    (
        "albums/gpt5-6/Bright Matter",
        "Bright Matter",
        "GPT-5.6",
        "Progressive Electronic / Instrumental",
    ),
    (
        "albums/opus4-8",
        "VIGIL",
        "Claude Opus 4.8",
        "Neo-Classical / Instrumental",
    ),
    (
        "albums/opus4-8/amarok",
        "RIVERWAKE",
        "Claude Opus 4.8",
        "Progressive Folk / Instrumental",
    ),
    (
        "demos/synth_feature_showcase",
        "Synth Feature Showcase",
        "OpenAI Codex",
        "Synth Demo / Instrumental",
    ),
    (
        "demos/ferrosintesis_reference",
        "ferrosintesis Reference Audition",
        "ferrosintesis",
        "Reference / Instrument Audition",
    ),
];

const USAGE: &str = "\
usage: render-catalog [--album TITLE] [--only-list FILE] [--jobs N]

  --album TITLE      render only the album with this title
  --only-list FILE   render only the repo-relative MIDI paths listed in FILE
                     (one per line) — for surgical refreshes
  --jobs N           parallel renders (default 6)
  -h, --help         show this help

Renders every album MIDI to listening/<artist>/<album>/<name>.opus.
Requires `ropusenc` on PATH.";

// ---------------------------------------------------------------------------
// Pure helpers (unit-tested below)
// ---------------------------------------------------------------------------

/// `(title, tracknumber)` from a stem like `03 - Foo` (→ `Foo`, `3`) or `Foo`
/// (→ `Foo`, `1`). Mirrors render_opus.py's `^\s*(\d+)\s*[-.]\s*(.+)$` + `int()`.
fn title_and_number(stem: &str) -> (String, String) {
    match split_numbered(stem) {
        Some((num, title)) => (title, num),
        None => (stem.to_string(), "1".to_string()),
    }
}

fn split_numbered(stem: &str) -> Option<(String, String)> {
    let rest = stem.trim_start();
    let digits: String = rest.chars().take_while(|c| c.is_ascii_digit()).collect();
    if digits.is_empty() {
        return None;
    }
    let rest = rest[digits.len()..].trim_start();
    let mut chars = rest.chars();
    match chars.next() {
        Some('-') | Some('.') => {}
        _ => return None,
    }
    let title = chars.as_str().trim();
    if title.is_empty() {
        return None;
    }
    // `int("007")` → 7: drop leading zeros, but keep a lone "0".
    let num = digits.trim_start_matches('0');
    let num = if num.is_empty() { "0" } else { num };
    Some((num.to_string(), title.to_string()))
}

/// The Q7.8 fixed-point gain (dB) that takes `TARGET_LUFS` audio to the −23 LUFS
/// R128 reference. The album arc is already baked in, so track gain == album gain.
fn r128_gain_q78() -> i32 {
    (256.0 * (R128_REFERENCE_LUFS - TARGET_LUFS)).round() as i32
}

/// The echo time ferrosintesis-cli derives when `--delay` is absent: a dotted
/// quaver at the opening tempo. Computed in **f32**, exactly as the CLI does
/// (`main.rs`) — an f64 computation would diverge in the last bits.
fn default_delay_s(bpm: f64) -> f32 {
    (0.75 * 60.0 / bpm as f32).clamp(0.20, 0.62)
}

/// The single source of truth for the synth parameters. Production and the
/// parameter-parity test both read *this*, so the test observes what actually runs.
fn synth_options(song: &Song) -> Options {
    Options {
        sr: SR as f32,
        wet: WET,
        tail: TAIL,
        delay_s: default_delay_s(song.initial_bpm()),
        samples: true,
        solo: 0xFFFF, // all 16 channels
        verbose: false,
    }
}

/// Repo-relative path with forward slashes — Python's `PurePath.as_posix()`.
/// Windows `Path` yields `\`, which would make every `--only-list` entry miss.
fn rel_posix(repo: &Path, path: &Path) -> String {
    path.strip_prefix(repo)
        .unwrap_or(path)
        .components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/")
}

/// Normalize a lyrics sidecar's text exactly as render_opus.py did: fold CRLF
/// *and* lone CR to LF, strip trailing newlines, reject blank / NUL.
fn normalize_lyrics(text: &str) -> Result<String, String> {
    let text = text.replace("\r\n", "\n").replace('\r', "\n");
    let text = text.trim_end_matches('\n').to_string();
    if text.trim().is_empty() {
        return Err("lyrics sidecar is blank".into());
    }
    if text.contains('\0') {
        return Err("lyrics sidecar contains a NUL byte".into());
    }
    Ok(text)
}

/// The Vorbis comments render_opus.py emitted, in its exact order.
fn encoder_comments(artist: &str, track_total: usize, lyrics: Option<&str>) -> Vec<String> {
    let gain = r128_gain_q78();
    let mut c = vec![
        format!("ALBUMARTIST={artist}"),
        format!("COMPOSER={artist}"),
        format!("TRACKTOTAL={track_total}"),
        "ENCODER_SETTINGS=ferrosintesis(-18 LUFS)->ropusenc 96k VBR".to_string(),
        format!("R128_TRACK_GAIN={gain}"),
        format!("R128_ALBUM_GAIN={gain}"),
    ];
    if let Some(l) = lyrics {
        c.push(format!("LYRICS={l}"));
    }
    c
}

/// Everything that ends up in a track's Vorbis comments.
struct Tags<'a> {
    title: &'a str,
    artist: &'a str,
    album: &'a str,
    genre: &'a str,
    tracknum: &'a str,
    /// The count of *selected* tracks in the album — see the note in `main`.
    track_total: usize,
    lyrics: Option<&'a str>,
}

/// The full `ropusenc` argument vector (program name excluded), in render_opus.py's
/// exact order. Pinned against a golden captured from the real Python run.
fn ropusenc_argv(t: &Tags, opus: &str, wav: &str) -> Vec<String> {
    let mut a: Vec<String> = [
        "--bitrate",
        BITRATE,
        "--music",
        "--vbr",
        "--comp",
        "10",
        "--title",
        t.title,
        "--artist",
        t.artist,
        "--album",
        t.album,
        "--genre",
        t.genre,
        "--date",
        DATE,
        "--tracknumber",
        t.tracknum,
    ]
    .iter()
    .map(|s| s.to_string())
    .collect();
    for comment in encoder_comments(t.artist, t.track_total, t.lyrics) {
        a.push("--comment".to_string());
        a.push(comment);
    }
    a.push("-o".to_string());
    a.push(opus.to_string());
    a.push(wav.to_string());
    a
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

#[derive(Debug, PartialEq)]
struct Args {
    album: Option<String>,
    only_list: Option<PathBuf>,
    jobs: usize,
}

#[derive(Debug, PartialEq)]
enum Parsed {
    Run(Args),
    Help,
}

/// Hand-rolled parser (the workspace is deliberately third-party-free). Accepts
/// both `--key value` and `--key=value`, like Python's argparse did.
fn parse_args(argv: &[String]) -> Result<Parsed, String> {
    let mut args = Args {
        album: None,
        only_list: None,
        jobs: DEFAULT_JOBS,
    };
    let mut it = argv.iter();
    while let Some(a) = it.next() {
        // Split `--key=value` into (key, Some(value)).
        let (key, inline) = match a.split_once('=') {
            Some((k, v)) if k.starts_with("--") => (k, Some(v.to_string())),
            _ => (a.as_str(), None),
        };
        let mut value = |what: &str| -> Result<String, String> {
            match inline.clone() {
                Some(v) => Ok(v),
                None => it
                    .next()
                    .cloned()
                    .ok_or_else(|| format!("{what} needs a value")),
            }
        };
        match key {
            "-h" | "--help" => return Ok(Parsed::Help),
            "--album" => args.album = Some(value("--album")?),
            "--only-list" => args.only_list = Some(PathBuf::from(value("--only-list")?)),
            "--jobs" => {
                let raw = value("--jobs")?;
                let n: usize = raw
                    .parse()
                    .map_err(|_| format!("--jobs expects a positive integer, got {raw:?}"))?;
                if n == 0 {
                    return Err("--jobs must be >= 1".into());
                }
                args.jobs = n;
            }
            other => return Err(format!("unknown argument {other:?}")),
        }
    }
    Ok(Parsed::Run(args))
}

// ---------------------------------------------------------------------------
// Discovery
// ---------------------------------------------------------------------------

/// One track to render: its MIDI plus the index of its owning `ALBUMS` entry.
struct Track {
    midi: PathBuf,
    album: usize,
}

/// Walk up from `start` to the repo root (the dir holding `albums/` and the
/// workspace `Cargo.toml`). Anchoring on the cwd rather than a compile-time path
/// keeps a stale binary from rendering into a *different* worktree's tree.
fn find_repo_root(start: &Path) -> Result<PathBuf, String> {
    for dir in start.ancestors() {
        if dir.join("albums").is_dir() && dir.join("Cargo.toml").is_file() {
            return Ok(dir.to_path_buf());
        }
    }
    Err(format!(
        "not inside the midi-music repo (no ancestor of {} has albums/ + Cargo.toml)",
        start.display()
    ))
}

fn sorted_midis(dir: &Path) -> Vec<PathBuf> {
    let mut out: Vec<PathBuf> = std::fs::read_dir(dir)
        .into_iter()
        .flatten()
        .flatten()
        .map(|e| e.path())
        .filter(|p| p.extension().is_some_and(|e| e == "mid"))
        .collect();
    out.sort();
    out
}

fn find_midis_recursive(dir: &Path, out: &mut Vec<PathBuf>) {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            find_midis_recursive(&path, out);
        } else if path.extension().is_some_and(|e| e == "mid") {
            out.push(path);
        }
    }
}

/// Every catalog MIDI, in `ALBUMS` order. Errors if an album has no MIDIs, or if
/// a `.mid` under `albums/` is owned by no album — both guards from the Python.
/// (Like the Python, the unclaimed scan covers `albums/` only, not `demos/`.)
fn discover(repo: &Path) -> Result<Vec<Track>, String> {
    let mut tracks = Vec::new();
    for (i, (key, ..)) in ALBUMS.iter().enumerate() {
        let midis = sorted_midis(&repo.join(key).join("midi"));
        if midis.is_empty() {
            return Err(format!("album {key:?} has no MIDI files"));
        }
        tracks.extend(midis.into_iter().map(|midi| Track { midi, album: i }));
    }

    let claimed: BTreeSet<&Path> = tracks.iter().map(|t| t.midi.as_path()).collect();
    let mut under_albums = Vec::new();
    find_midis_recursive(&repo.join("albums"), &mut under_albums);
    let mut unclaimed: Vec<String> = under_albums
        .iter()
        .filter(|p| !claimed.contains(p.as_path()))
        .map(|p| rel_posix(repo, p))
        .collect();
    if !unclaimed.is_empty() {
        unclaimed.sort();
        unclaimed.truncate(5);
        return Err(format!(
            "unclaimed MIDI files under albums/: {}",
            unclaimed.join(", ")
        ));
    }
    Ok(tracks)
}

fn lyrics_path_for(midi: &Path) -> PathBuf {
    midi.parent()
        .and_then(Path::parent)
        .unwrap_or(Path::new("."))
        .join("lyrics")
        .join(format!(
            "{}.txt",
            midi.file_stem().unwrap_or_default().to_string_lossy()
        ))
}

/// The optional listening-note sidecar for a MIDI, validated.
fn lyrics_for(midi: &Path) -> Result<Option<String>, String> {
    let path = lyrics_path_for(midi);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = std::fs::read(&path).map_err(|e| format!("{}: {e}", path.display()))?;
    let text = String::from_utf8(bytes)
        .map_err(|_| format!("{}: lyrics sidecar is not valid UTF-8", path.display()))?;
    normalize_lyrics(&text)
        .map(Some)
        .map_err(|e| format!("{}: {e}", path.display()))
}

/// Reject sidecars whose exact MIDI stem is absent. Checked against the **full**
/// MIDI set, so a partial `--album`/`--only-list` run cannot mistake a
/// not-selected track's sidecar for an orphan.
fn validate_lyrics_sidecars(all: &[Track]) -> Result<(), String> {
    let mut stems_by_album: BTreeMap<PathBuf, BTreeSet<String>> = BTreeMap::new();
    for t in all {
        let album_dir = t
            .midi
            .parent()
            .and_then(Path::parent)
            .unwrap_or(Path::new("."));
        stems_by_album
            .entry(album_dir.to_path_buf())
            .or_default()
            .insert(
                t.midi
                    .file_stem()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned(),
            );
    }
    for (album_dir, midi_stems) in stems_by_album {
        let lyrics_dir = album_dir.join("lyrics");
        if !lyrics_dir.is_dir() {
            continue;
        }
        let mut orphans: Vec<String> = std::fs::read_dir(&lyrics_dir)
            .map_err(|e| format!("{}: {e}", lyrics_dir.display()))?
            .flatten()
            .map(|e| e.path())
            .filter(|p| p.extension().is_some_and(|e| e == "txt"))
            .filter_map(|p| {
                let stem = p.file_stem()?.to_string_lossy().into_owned();
                (!midi_stems.contains(&stem)).then_some(stem)
            })
            .collect();
        if !orphans.is_empty() {
            orphans.sort();
            let names: Vec<String> = orphans.iter().map(|s| format!("{s}.txt")).collect();
            return Err(format!(
                "{}: no matching MIDI for {}",
                lyrics_dir.display(),
                names.join(", ")
            ));
        }
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

/// A temp WAV that removes itself — the zero-dep stand-in for Python's
/// `TemporaryDirectory`. `Drop` runs on the happy path, on an encode failure, and
/// on a caught panic alike, so a failed render cannot leak hundreds of MB.
struct TempWav(PathBuf);

impl TempWav {
    fn new(idx: usize) -> Self {
        let name = format!("render-catalog-{}-{}.wav", std::process::id(), idx);
        TempWav(std::env::temp_dir().join(name))
    }
    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TempWav {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.0);
    }
}

/// Render one MIDI to a loudness-normalized WAV, in-process. These are exactly the
/// calls ferrosintesis-cli makes under render_opus.py's flags.
fn render_wav(midi: &Path, wav: &Path) -> Result<(), String> {
    let song = offline::load(midi)?;
    let (samples, _stats) = offline::render(&song, &synth_options(&song));
    let pcm = offline::normalize_loudness(&samples, SR as f32, TARGET_LUFS, TP_CEILING);
    offline::write_wav(wav, SR, &pcm).map_err(|e| format!("writing {}: {e}", wav.display()))
}

struct Outcome {
    ok: bool,
    message: String,
}

fn render_one(
    repo: &Path,
    track: &Track,
    track_total: usize,
    lyrics: Option<&str>,
    idx: usize,
) -> Outcome {
    let (_key, album, artist, genre) = ALBUMS[track.album];
    let stem = track
        .midi
        .file_stem()
        .unwrap_or_default()
        .to_string_lossy()
        .into_owned();
    let (title, tracknum) = title_and_number(&stem);
    let label = format!("{album} / {title} (#{tracknum})");

    let fail = |what: String| Outcome {
        ok: false,
        message: format!("{label}: {what}"),
    };

    let opus = repo
        .join("listening")
        .join(artist)
        .join(album)
        .join(format!("{stem}.opus"));
    if let Some(parent) = opus.parent() {
        if let Err(e) = std::fs::create_dir_all(parent) {
            return fail(format!("creating {}: {e}", parent.display()));
        }
    }

    let wav = TempWav::new(idx);
    if let Err(e) = render_wav(&track.midi, wav.path()) {
        return fail(format!("ferrosintesis failed: {e}"));
    }

    let tags = Tags {
        title: &title,
        artist,
        album,
        genre,
        tracknum: &tracknum,
        track_total,
        lyrics,
    };
    let argv = ropusenc_argv(
        &tags,
        &opus.to_string_lossy(),
        &wav.path().to_string_lossy(),
    );
    let out = match Command::new("ropusenc").args(&argv).output() {
        Ok(o) => o,
        Err(e) => return fail(format!("ropusenc failed to start: {e}")),
    };
    if !out.status.success() || !opus.exists() {
        let err = String::from_utf8_lossy(&out.stderr);
        let err: String = err.trim().chars().take(200).collect();
        return fail(format!("ropusenc failed: {err}"));
    }

    let mb = std::fs::metadata(&opus).map(|m| m.len()).unwrap_or(0) as f64 / 1e6;
    Outcome {
        ok: true,
        message: format!("{label}  ({mb:.1} MB)"),
    }
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

fn fatal(msg: impl std::fmt::Display) -> ! {
    eprintln!("render-catalog: {msg}");
    std::process::exit(1)
}

fn usage_error(msg: impl std::fmt::Display) -> ! {
    eprintln!("render-catalog: {msg}\n\n{USAGE}");
    std::process::exit(2)
}

fn main() {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let args = match parse_args(&argv) {
        Ok(Parsed::Help) => {
            println!("{USAGE}");
            return;
        }
        Ok(Parsed::Run(a)) => a,
        Err(e) => usage_error(e),
    };

    let cwd = std::env::current_dir().unwrap_or_else(|e| fatal(e));
    let repo = find_repo_root(&cwd).unwrap_or_else(|e| fatal(e));

    // Pre-flight: fail fast and clearly if the encoder is missing, rather than
    // failing every track mid-run.
    if Command::new("ropusenc").arg("--version").output().is_err() {
        fatal("`ropusenc` not found on PATH (build it from the sibling `ropus` repo)");
    }

    let all = discover(&repo).unwrap_or_else(|e| fatal(e));

    // Filter: --album narrows first, then --only-list intersects (as the Python did).
    let mut selected: Vec<&Track> = all.iter().collect();
    if let Some(title) = &args.album {
        selected.retain(|t| ALBUMS[t.album].1 == title);
        if selected.is_empty() {
            fatal(format!("no album titled {title:?}"));
        }
    }
    if let Some(list) = &args.only_list {
        let text = std::fs::read_to_string(list)
            .unwrap_or_else(|e| fatal(format!("{}: {e}", list.display())));
        let wanted: BTreeSet<&str> = text
            .lines()
            .map(str::trim)
            .filter(|l| !l.is_empty())
            .collect();
        selected.retain(|t| wanted.contains(rel_posix(&repo, &t.midi).as_str()));
        let found: BTreeSet<String> = selected.iter().map(|t| rel_posix(&repo, &t.midi)).collect();
        let missing: Vec<&&str> = wanted
            .iter()
            .filter(|w| !found.contains(**w))
            .take(5)
            .collect();
        if !missing.is_empty() {
            fatal(format!(
                "--only-list has {} unmatched path(s): {missing:?}",
                wanted.len() - found.len()
            ));
        }
        if selected.is_empty() {
            fatal("no MIDIs matched --only-list");
        }
    }

    // Sidecar consistency is a repo-wide invariant: validate against the FULL set.
    validate_lyrics_sidecars(&all)
        .unwrap_or_else(|e| fatal(format!("invalid lyrics sidecar: {e}")));

    // Read every selected track's lyrics BEFORE rendering: an invalid sidecar is a
    // fatal, render-nothing error (as in render_opus.py), not a per-track failure
    // discovered after five minutes of synthesis.
    let lyrics: Vec<Option<String>> = selected
        .iter()
        .map(|t| lyrics_for(&t.midi))
        .collect::<Result<_, _>>()
        .unwrap_or_else(|e| fatal(format!("invalid lyrics sidecar: {e}")));

    // TRACKTOTAL counts the *selected* tracks per album — faithfully reproducing
    // render_opus.py, which summed over the filtered set, so a partial refresh tags
    // the partial count.
    let mut totals = vec![0usize; ALBUMS.len()];
    for t in &selected {
        totals[t.album] += 1;
    }

    let jobs = args.jobs.min(selected.len().max(1));
    println!(
        "rendering {} track(s) -> opus ({jobs} workers)",
        selected.len()
    );

    let cursor = AtomicUsize::new(0);
    let results: Vec<Outcome> = std::thread::scope(|scope| {
        let handles: Vec<_> = (0..jobs)
            .map(|_| {
                let (cursor, repo, selected) = (&cursor, &repo, &selected);
                let (totals, lyrics) = (&totals, &lyrics);
                scope.spawn(move || {
                    let mut mine = Vec::new();
                    loop {
                        let i = cursor.fetch_add(1, Ordering::Relaxed);
                        let Some(track) = selected.get(i) else { break };
                        let total = totals[track.album];
                        let lyric = lyrics[i].as_deref();
                        // Per-track panic isolation: the subprocess boundary the
                        // Python got for free. (Panics only — an abort or stack
                        // overflow still takes the process down.)
                        let outcome =
                            std::panic::catch_unwind(|| render_one(repo, track, total, lyric, i))
                                .unwrap_or_else(|_| Outcome {
                                    ok: false,
                                    message: format!(
                                        "{}: panicked while rendering",
                                        track.midi.display()
                                    ),
                                });
                        println!(
                            "  [{}] {}",
                            if outcome.ok { "ok" } else { "FAIL" },
                            outcome.message
                        );
                        mine.push(outcome);
                    }
                    mine
                })
            })
            .collect();
        handles
            .into_iter()
            .flat_map(|h| h.join().unwrap_or_default())
            .collect()
    });

    let ok = results.iter().filter(|o| o.ok).count();
    println!("done: {ok}/{} rendered", results.len());
    if ok != results.len() {
        std::process::exit(1);
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn repo() -> PathBuf {
        find_repo_root(&std::env::current_dir().unwrap()).expect("repo root")
    }

    // --- filename parsing -------------------------------------------------

    #[test]
    fn title_and_number_parses_the_python_shapes() {
        assert_eq!(title_and_number("03 - Foo"), ("Foo".into(), "3".into()));
        assert_eq!(title_and_number("1. Bar"), ("Bar".into(), "1".into()));
        assert_eq!(
            title_and_number("10 - A - B"),
            ("A - B".into(), "10".into())
        );
        assert_eq!(title_and_number("007 - X"), ("X".into(), "7".into()));
        // No leading number, or digits with no separator → the whole stem, track 1.
        assert_eq!(title_and_number("Foo"), ("Foo".into(), "1".into()));
        assert_eq!(title_and_number("12"), ("12".into(), "1".into()));
        // Degenerate stem "12 - " (a number, a separator, no title): we keep the
        // whole stem rather than emit an EMPTY title. The Python regex backtracked
        // here and produced ("", "12"). A deliberate divergence on a stem that
        // cannot occur in the catalog — an untitled track is never the right answer.
        assert_eq!(title_and_number("12 - "), ("12 - ".into(), "1".into()));
    }

    // --- tags -------------------------------------------------------------

    #[test]
    fn r128_gain_matches_the_python_constant() {
        // round(256 * (-23.0 - -18.0)) == -1280
        assert_eq!(r128_gain_q78(), -1280);
    }

    #[test]
    fn encoder_comments_omit_lyrics_when_absent() {
        let c = encoder_comments("A", 3, None);
        assert_eq!(c.len(), 6);
        assert!(!c.iter().any(|s| s.starts_with("LYRICS=")));
        assert_eq!(c[2], "TRACKTOTAL=3");
        assert_eq!(encoder_comments("A", 3, Some("x")).len(), 7);
    }

    // --- synth parameter parity (the durable AC3 oracle) -------------------

    #[test]
    fn default_delay_matches_the_cli_formula() {
        // Dotted quaver at the opening tempo, clamped — computed in f32 exactly as
        // ferrosintesis-cli does. (An f64 computation would diverge in the last bits.)
        assert_eq!(default_delay_s(120.0), 0.375);
        assert_eq!(default_delay_s(30.0), 0.62); // clamped high
        assert_eq!(default_delay_s(300.0), 0.20); // clamped low
        assert_eq!(
            default_delay_s(96.0),
            (0.75 * 60.0 / 96.0f32).clamp(0.20, 0.62)
        );
    }

    #[test]
    fn synth_options_match_ferrosintesis_cli_defaults() {
        // These are the values render_opus.py caused the CLI to use: it passed only
        // `-q --tp-ceiling -4.5` and inherited every other default. If one of these
        // drifts, the whole catalog silently changes sound.
        assert_eq!(SR, 44100);
        assert_eq!(WET, 0.32);
        assert_eq!(TAIL, 6.0);
        assert_eq!(TARGET_LUFS, -18.0);
        assert_eq!(TP_CEILING, -4.5);

        let midi =
            repo().join("demos/ferrosintesis_reference/midi/06 - Controllers and Effects.mid");
        let song = offline::load(&midi).expect("load fixture midi");
        let opt = synth_options(&song);
        assert_eq!(opt.sr, 44100.0);
        assert_eq!(opt.wet, 0.32);
        assert_eq!(opt.tail, 6.0);
        assert!(opt.samples);
        assert_eq!(opt.solo, 0xFFFF);
        assert!(!opt.verbose);
        assert_eq!(opt.delay_s, default_delay_s(song.initial_bpm()));
    }

    // --- ropusenc argv, pinned to a golden captured from the real Python ----

    /// Parse the length-prefixed capture: `#### argv N`, then per arg
    /// `#<byte-len>\n<raw bytes>\n`.
    fn parse_golden(bytes: &[u8]) -> Vec<String> {
        let mut args = Vec::new();
        // Skip the `#### argv N` header line.
        let mut i = bytes.iter().position(|&b| b == b'\n').unwrap() + 1;
        while i < bytes.len() {
            assert_eq!(bytes[i], b'#', "expected a length prefix");
            let nl = i + bytes[i..].iter().position(|&b| b == b'\n').unwrap();
            let len: usize = std::str::from_utf8(&bytes[i + 1..nl])
                .unwrap()
                .parse()
                .unwrap();
            let start = nl + 1;
            args.push(String::from_utf8(bytes[start..start + len].to_vec()).unwrap());
            i = start + len + 1; // skip the trailing newline
        }
        args
    }

    /// Build the argv for demo track 06 with the volatile path slots replaced by
    /// the same placeholders the capture stub wrote.
    fn argv_for_demo_track06(track_total: usize) -> Vec<String> {
        let midi =
            repo().join("demos/ferrosintesis_reference/midi/06 - Controllers and Effects.mid");
        let (_key, album, artist, genre) = ALBUMS
            .iter()
            .find(|(k, ..)| *k == "demos/ferrosintesis_reference")
            .copied()
            .unwrap();
        let stem = midi.file_stem().unwrap().to_string_lossy().into_owned();
        let (title, tracknum) = title_and_number(&stem);
        let lyrics = lyrics_for(&midi).expect("lyrics readable");
        let tags = Tags {
            title: &title,
            artist,
            album,
            genre,
            tracknum: &tracknum,
            track_total,
            lyrics: lyrics.as_deref(),
        };
        ropusenc_argv(&tags, "<OPUS>", "<WAV>")
    }

    #[test]
    fn ropusenc_argv_matches_the_python_golden_full_album() {
        // Golden captured by running the REAL render_opus.py against a stub ropusenc
        // (see the journal) — so it cannot share a bug with this implementation.
        let golden = parse_golden(include_bytes!("../tests/golden/track06_full_album.argv"));
        assert!(golden.contains(&"TRACKTOTAL=6".to_string()));
        assert_eq!(argv_for_demo_track06(6), golden);
    }

    #[test]
    fn ropusenc_argv_matches_the_python_golden_only_list_subset() {
        // The same track rendered via `--only-list` — the Python tagged TRACKTOTAL=1
        // (it counts the *selected* tracks, not the album's true size). Faithfully
        // reproduced.
        let golden = parse_golden(include_bytes!("../tests/golden/track06_only_list.argv"));
        assert!(golden.contains(&"TRACKTOTAL=1".to_string()));
        assert_eq!(argv_for_demo_track06(1), golden);
    }

    // --- lyrics -----------------------------------------------------------

    #[test]
    fn normalize_lyrics_folds_crlf_and_lone_cr() {
        assert_eq!(normalize_lyrics("a\r\nb").unwrap(), "a\nb");
        assert_eq!(normalize_lyrics("a\rb").unwrap(), "a\nb"); // classic-Mac lone CR
        assert_eq!(normalize_lyrics("a\n\n\n").unwrap(), "a"); // trailing newlines stripped
        assert_eq!(normalize_lyrics("a\r\n\r\n").unwrap(), "a");
    }

    #[test]
    fn normalize_lyrics_rejects_blank_and_nul() {
        assert!(normalize_lyrics("").is_err());
        assert!(normalize_lyrics("   \n  ").is_err());
        assert!(normalize_lyrics("ok\0bad").is_err());
    }

    #[test]
    fn a_bad_sidecar_is_detected_before_rendering_starts() {
        // Regression: lyrics used to be read inside the worker, which turned an
        // invalid sidecar into a per-track [FAIL] *after* minutes of synthesis while
        // every other track still rendered. render_opus.py resolved lyrics up front
        // and rendered NOTHING on a bad sidecar; main() now does the same, so the
        // whole selection is validated by this fallible read before any work starts.
        let bad = Path::new("no-such-album/midi/01 - x.mid");
        assert!(
            lyrics_for(bad).unwrap().is_none(),
            "absent sidecar is not an error"
        );
        // The fatal path is the Err arm of exactly this call, collected over the
        // full selection in main() before the render loop.
        assert!(normalize_lyrics("\0").is_err());
    }

    // --- discovery --------------------------------------------------------

    #[test]
    fn discovery_claims_every_catalog_midi() {
        // Mirrors the Python's all_midis() guards: every album has MIDIs and no
        // .mid under albums/ is left unowned. `discover` errors on either.
        let repo = repo();
        let tracks = discover(&repo).expect("discovery clean");
        assert!(
            tracks.len() > 100,
            "expected the full catalog, got {}",
            tracks.len()
        );
        for t in &tracks {
            assert!(t.album < ALBUMS.len());
            assert!(t.midi.exists());
        }
    }

    #[test]
    fn lyrics_sidecars_are_consistent() {
        let repo = repo();
        let all = discover(&repo).expect("discovery clean");
        validate_lyrics_sidecars(&all).expect("no orphan sidecars");
    }

    #[test]
    fn rel_posix_uses_forward_slashes() {
        let repo = Path::new("/repo");
        let p = Path::new("/repo")
            .join("albums")
            .join("x")
            .join("midi")
            .join("01 - a.mid");
        assert_eq!(rel_posix(repo, &p), "albums/x/midi/01 - a.mid");
    }

    // --- work distribution -------------------------------------------------

    #[test]
    fn cursor_partitions_every_index_exactly_once() {
        // Guards the hand-rolled AtomicUsize work queue against skipping or
        // double-rendering a track.
        for (n, jobs) in [(0, 4), (1, 4), (7, 3), (100, 6), (3, 8)] {
            let cursor = AtomicUsize::new(0);
            let items: Vec<usize> = (0..n).collect();
            let seen: Vec<usize> = std::thread::scope(|scope| {
                let handles: Vec<_> = (0..jobs)
                    .map(|_| {
                        let (cursor, items) = (&cursor, &items);
                        scope.spawn(move || {
                            let mut mine = Vec::new();
                            loop {
                                let i = cursor.fetch_add(1, Ordering::Relaxed);
                                let Some(item) = items.get(i) else { break };
                                mine.push(*item);
                            }
                            mine
                        })
                    })
                    .collect();
                handles
                    .into_iter()
                    .flat_map(|h| h.join().unwrap())
                    .collect()
            });
            let mut sorted = seen.clone();
            sorted.sort_unstable();
            assert_eq!(sorted, items, "n={n} jobs={jobs}: every index exactly once");
        }
    }

    // --- CLI parsing -------------------------------------------------------

    fn parse(args: &[&str]) -> Result<Parsed, String> {
        parse_args(&args.iter().map(|s| s.to_string()).collect::<Vec<_>>())
    }

    #[test]
    fn parse_args_defaults_and_forms() {
        assert_eq!(
            parse(&[]).unwrap(),
            Parsed::Run(Args {
                album: None,
                only_list: None,
                jobs: DEFAULT_JOBS
            })
        );
        // Both `--key value` and `--key=value`, as argparse accepted.
        let space = parse(&["--album", "Sub Rosa", "--jobs", "4"]).unwrap();
        let equals = parse(&["--album=Sub Rosa", "--jobs=4"]).unwrap();
        assert_eq!(space, equals);
        assert_eq!(
            space,
            Parsed::Run(Args {
                album: Some("Sub Rosa".into()),
                only_list: None,
                jobs: 4
            })
        );
        assert_eq!(
            parse(&["--only-list=x.txt"]).unwrap(),
            Parsed::Run(Args {
                album: None,
                only_list: Some("x.txt".into()),
                jobs: DEFAULT_JOBS
            })
        );
        assert_eq!(parse(&["-h"]).unwrap(), Parsed::Help);
        assert_eq!(parse(&["--help"]).unwrap(), Parsed::Help);
    }

    #[test]
    fn parse_args_rejects_bad_input() {
        assert!(parse(&["--jobs", "0"]).is_err()); // Python's ThreadPoolExecutor(0) raised too
        assert!(parse(&["--jobs", "-1"]).is_err());
        assert!(parse(&["--jobs", "abc"]).is_err());
        assert!(parse(&["--jobs"]).is_err()); // missing value
        assert!(parse(&["--album"]).is_err());
        assert!(parse(&["--nope"]).is_err());
        assert!(parse(&["stray"]).is_err());
    }
}
