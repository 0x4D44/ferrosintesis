#!/usr/bin/env python3
"""render_opus.py — render every album's MIDI to tagged Ogg Opus.

For each MIDI in the repo: render to a temporary WAV with **ferrosintesis**
(our synth, built at target/release), then encode to
`listening/<artist>/<album>/<name>.opus` with **ropusenc**, writing Vorbis-comment tags
(TITLE / ARTIST / ALBUM / ALBUMARTIST / COMPOSER / GENRE / DATE /
TRACKNUMBER / TRACKTOTAL, plus optional multiline LYRICS listening notes). The
`.opus` files are reproducible **build output** (git-ignored), not source: they
are regenerated from the committed MIDI + synth by re-running this script (or,
more simply, `python build.py`, which builds the CLI first).

    python render_opus.py            # render everything (parallel)
    python render_opus.py --album "Winter Guests"   # one album, by name
    python render_opus.py --jobs 4   # limit parallelism

Note: ferrosintesis is *voiced* for the fable5 albums (Oldfield idiom). The
other models' albums are valid General MIDI rendered through the same synth
as a general GM player — faithful, but not specially voiced.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
SYNTH = REPO / "target" / "release" / (
    "ferrosintesis.exe" if sys.platform == "win32" else "ferrosintesis")
LISTENING = REPO / "listening"
BITRATE = "96000"         # VBR; Opus at 96k ≈ 160-192 kbps MP3, near-transparent
DATE = "2026"
# ferrosintesis (>= 0.16) loudness-normalizes every render to this integrated
# loudness (BS.1770-4) with a -1 dBTP true-peak limit. Keep in lockstep with the
# CLI default (crates/ferrosintesis-cli/src/main.rs).
TARGET_LUFS = -18.0
# WAV true-peak ceiling we ask the synth to limit to before encoding. It is more
# conservative than the -1 dBTP delivery target because ropusenc's lossy 96k encode
# + 44.1->48 kHz resample adds inter-sample true peak. The overshoot is content-
# dependent and worst on bright/dense material: up to ~2.9 dB on Bright Matter
# "Six-Five-Two-One" (measured WAV -3.6 -> opus -0.7). At -4.5 dBTP that same track
# encodes to about -2.7 dBTP, and every other track was already compliant at -3.5,
# so -4.5 keeps the whole catalog safely under -1 dBTP. Loudness is unaffected
# (peaks only) and -18 LUFS content at ~-4 dBTP is a normal ~14 dB PLR, so the
# headroom is free.
OPUS_TP_CEILING = -4.5
# R128 replay-gain tags (RFC 7845 §5.2): Q7.8 fixed-point dB to reach the -23 LUFS
# reference. The audio is baked to TARGET_LUFS and the album arc is flattened, so
# the track and album gains are equal — track- and album-mode players then produce
# the identical, arc-preserving result.
R128_GAIN_Q78 = round(256 * (-23.0 - TARGET_LUFS))

# Album metadata by the directory that holds the `midi/` folder.
# (album title, artist == composer == album-artist, genre)
ALBUMS: dict[str, tuple[str, str, str]] = {
    "albums/fable5/Hollow Hill":      ("Hollow Hill",      "Claude Fable 5",   "Progressive Rock / Instrumental"),
    "albums/fable5/Heliopause":       ("Heliopause",       "Claude Fable 5",   "Electronic / Synth"),
    "albums/fable5/The Burning Meridian":
                               ("The Burning Meridian", "Claude Fable 5", "Orchestral / Cinematic"),
    "albums/fable5/Tuxedo Noir":      ("Tuxedo Noir",      "Claude Fable 5",   "Spy Jazz / Instrumental"),
    "albums/fable5/Seven Kinds of Sunlight":
                               ("Seven Kinds of Sunlight", "Claude Fable 5", "Pop-Prog / Instrumental"),
    "albums/fable5/Sub Rosa":         ("Sub Rosa",         "Claude Fable 5",   "Electronic / Downtempo"),
    "albums/fable5/The Ninth Bell":   ("The Ninth Bell",   "Claude Fable 5",   "Gothic Orchestral / Instrumental"),
    "albums/fable5/The Signal Fire":  ("The Signal Fire",  "Claude Fable 5",   "Progressive Rock / Instrumental"),
    "albums/fable5/Winter Guests":    ("Winter Guests",    "Claude Fable 5",   "Progressive Rock / Instrumental"),
    "albums/fable5":                  ("The Iron Tide",    "Claude Fable 5",   "Cinematic / Instrumental"),
    "albums/fable5/Through Lines":    ("Through Lines",    "Claude Fable 5",   "Progressive Eclectic / Instrumental"),
    "albums/fable5/Big Weather":      ("Big Weather",      "Claude Fable 5",   "Rock-Pop / Instrumental"),
    "albums/gpt5-3-spark":            ("The Spark",        "GPT-5.3 Spark",    "Instrumental"),
    "albums/gpt5-5/Hours After Rain": ("Hours After Rain", "GPT-5.5",          "Instrumental"),
    "albums/gpt5-5/The Long Turning": ("The Long Turning", "GPT-5.5",          "Instrumental"),
    "albums/gpt5-6/Atlas of Becoming": ("Atlas of Becoming", "GPT-5.6",      "Cinematic / Progressive / Instrumental"),
    "albums/gpt5-6/The Architecture of Air":
                               ("The Architecture of Air", "GPT-5.6", "Cathedral Organ / Cinematic / Instrumental"),
    "albums/gpt5-6/Bright Matter":    ("Bright Matter",    "GPT-5.6",          "Progressive Electronic / Instrumental"),
    "albums/opus4-8":                 ("VIGIL",            "Claude Opus 4.8",  "Neo-Classical / Instrumental"),
    "albums/opus4-8/amarok":          ("RIVERWAKE",        "Claude Opus 4.8",  "Progressive Folk / Instrumental"),
    "demos/synth_feature_showcase":    ("Synth Feature Showcase", "OpenAI Codex", "Synth Demo / Instrumental"),
    "demos/ferrosintesis_reference":   ("ferrosintesis Reference Audition", "ferrosintesis", "Reference / Instrument Audition"),
}

_NUM = re.compile(r"^\s*(\d+)\s*[-.]\s*(.+)$")


def title_and_number(midi: Path) -> tuple[str, str]:
    """(title, tracknumber) from a filename like '03 - Foo.mid' or 'Foo.mid'."""
    stem = midi.stem
    m = _NUM.match(stem)
    if m:
        return m.group(2).strip(), str(int(m.group(1)))
    return stem, "1"


def album_for(midi: Path) -> str:
    """The ALBUMS key owning this MIDI (the longest matching prefix)."""
    rel = midi.relative_to(REPO).as_posix()
    # midi lives at <key>/midi/... ; strip the '/midi/<file>' tail.
    parent = midi.parent.parent.relative_to(REPO).as_posix()
    if parent in ALBUMS:
        return parent
    raise SystemExit(f"no album metadata for {rel} (parent {parent})")


def all_midis() -> list[Path]:
    out: list[Path] = []
    for key in ALBUMS:
        midis = sorted((REPO / key / "midi").glob("*.mid"))
        if not midis:
            raise SystemExit(f"album {key!r} has no MIDI files")
        out += midis
    unclaimed = sorted(set((REPO / "albums").glob("**/*.mid")) - set(out))
    if unclaimed:
        rel = ", ".join(str(p.relative_to(REPO)) for p in unclaimed[:5])
        raise SystemExit(f"unclaimed MIDI files under albums/: {rel}")
    return out


def opus_path_for(midi: Path) -> Path:
    key = album_for(midi)
    album, artist, _genre = ALBUMS[key]
    return LISTENING / artist / album / (midi.stem + ".opus")


def lyrics_path_for(midi: Path) -> Path:
    """The optional UTF-8 listening-note sidecar for a MIDI file."""
    return midi.parent.parent / "lyrics" / f"{midi.stem}.txt"


def lyrics_for(midi: Path) -> str | None:
    """Read an optional multiline LYRICS value without losing its formatting."""
    path = lyrics_path_for(midi)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: lyrics sidecar is not valid UTF-8") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    if not text.strip():
        raise ValueError(f"{path}: lyrics sidecar is blank")
    if "\x00" in text:
        raise ValueError(f"{path}: lyrics sidecar contains a NUL byte")
    return text


def validate_lyrics_sidecars(midis: list[Path]) -> None:
    """Reject sidecars whose exact MIDI stem is absent from the render set."""
    stems_by_album: dict[Path, set[str]] = {}
    for midi in midis:
        stems_by_album.setdefault(midi.parent.parent, set()).add(midi.stem)
    for album_dir, midi_stems in stems_by_album.items():
        lyrics_dir = album_dir / "lyrics"
        if not lyrics_dir.exists():
            continue
        sidecar_stems = {path.stem for path in lyrics_dir.glob("*.txt")}
        orphans = sorted(sidecar_stems - midi_stems)
        if orphans:
            names = ", ".join(f"{stem}.txt" for stem in orphans)
            raise ValueError(f"{lyrics_dir}: no matching MIDI for {names}")


def encoder_comments(artist: str, track_total: int, lyrics: str | None) -> list[str]:
    comments = [
        f"ALBUMARTIST={artist}",
        f"COMPOSER={artist}",
        f"TRACKTOTAL={track_total}",
        "ENCODER_SETTINGS=ferrosintesis(-18 LUFS)->ropusenc 96k VBR",
        f"R128_TRACK_GAIN={R128_GAIN_Q78}",
        f"R128_ALBUM_GAIN={R128_GAIN_Q78}",
    ]
    if lyrics is not None:
        comments.append(f"LYRICS={lyrics}")
    return comments


def render_one(
    midi: Path,
    total_by_album: dict[str, int],
    lyrics: str | None,
) -> tuple[Path, bool, str]:
    key = album_for(midi)
    album, artist, genre = ALBUMS[key]
    title, tracknum = title_and_number(midi)
    opus = opus_path_for(midi)
    opus.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / (midi.stem + ".wav")
        r = subprocess.run([str(SYNTH), str(midi), "-o", str(wav), "-q",
                            "--tp-ceiling", str(OPUS_TP_CEILING)],
                           capture_output=True, text=True)
        if r.returncode != 0 or not wav.exists():
            return opus, False, f"ferrosintesis failed: {r.stderr.strip()[:200]}"
        cmd = [
            "ropusenc", "--bitrate", BITRATE, "--music", "--vbr",
            "--comp", "10",
            "--title", title, "--artist", artist, "--album", album,
            "--genre", genre, "--date", DATE, "--tracknumber", tracknum,
        ]
        for comment in encoder_comments(artist, total_by_album[key], lyrics):
            cmd.extend(("--comment", comment))
        cmd.extend(("-o", str(opus), str(wav)))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not opus.exists():
            return opus, False, f"ropusenc failed: {r.stderr.strip()[:200]}"
    return opus, True, f"{album} / {title} (#{tracknum})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--album", help="only render this album (by title)")
    ap.add_argument(
        "--only-list",
        help="path to a file of repo-relative MIDI paths (one per line); render "
        "only those. For surgical asset refreshes that touch just the tracks a "
        "synth change actually altered (avoids sweeping in unrelated stale opus).",
    )
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args()

    if not SYNTH.exists():
        raise SystemExit(f"synth not built: {SYNTH}\n"
                         f"run: cargo build --release -p ferrosintesis-cli")

    all_m = all_midis()
    midis = all_m
    if args.album:
        midis = [m for m in midis if ALBUMS[album_for(m)][0] == args.album]
        if not midis:
            raise SystemExit(f"no album titled {args.album!r}")
    if args.only_list:
        with open(args.only_list, encoding="utf-8") as fh:
            wanted = {line.strip() for line in fh if line.strip()}
        midis = [m for m in midis if m.relative_to(REPO).as_posix() in wanted]
        found = {m.relative_to(REPO).as_posix() for m in midis}
        missing = wanted - found
        if missing:
            raise SystemExit(
                f"--only-list has {len(missing)} unmatched path(s): "
                f"{sorted(missing)[:5]}"
            )
        if not midis:
            raise SystemExit("no MIDIs matched --only-list")
    try:
        # Sidecar consistency is a repo-wide invariant: validate against the full
        # MIDI set, not the (possibly track-level) render subset, so a partial
        # refresh doesn't mistake a not-selected track's sidecar for an orphan.
        validate_lyrics_sidecars(all_m)
        lyrics_by_midi = {midi: lyrics_for(midi) for midi in midis}
    except (OSError, ValueError) as exc:
        raise SystemExit(f"invalid lyrics sidecar: {exc}") from exc
    total_by_album = {k: 0 for k in ALBUMS}
    for m in midis:
        total_by_album[album_for(m)] += 1

    print(f"rendering {len(midis)} track(s) with {SYNTH.name} -> opus "
          f"({args.jobs} workers)")
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {
            ex.submit(render_one, m, total_by_album, lyrics_by_midi[m]): m
            for m in midis
        }
        for fut in concurrent.futures.as_completed(futs):
            opus, good, msg = fut.result()
            size = opus.stat().st_size / 1e6 if good and opus.exists() else 0
            print(f"  [{'ok' if good else 'FAIL'}] {msg}"
                  f"{f'  ({size:.1f} MB)' if good else ''}")
            ok += good
    print(f"done: {ok}/{len(midis)} rendered")
    return 0 if ok == len(midis) else 1


if __name__ == "__main__":
    raise SystemExit(main())
