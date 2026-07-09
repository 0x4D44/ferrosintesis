#!/usr/bin/env python3
"""render_opus.py — render every committed album to tagged Ogg Opus.

For each MIDI in the repo: render to a temporary WAV with **ferrosintesis**
(our synth, built at target/release), then encode to
`listening/<artist>/<album>/<name>.opus` with **ropusenc**, writing Vorbis-comment tags
(TITLE / ARTIST / ALBUM / ALBUMARTIST / COMPOSER / GENRE / DATE /
TRACKNUMBER / TRACKTOTAL). The committed `.opus` files are the shareable,
tagged listening copies; they are reproducible from the committed MIDI +
synth by re-running this script.

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
    "albums/gpt5-3-spark":            ("The Spark",        "GPT-5.3 Spark",    "Instrumental"),
    "albums/gpt5-5/Hours After Rain": ("Hours After Rain", "GPT-5.5",          "Instrumental"),
    "albums/gpt5-5/The Long Turning": ("The Long Turning", "GPT-5.5",          "Instrumental"),
    "albums/opus4-8":                 ("VIGIL",            "Claude Opus 4.8",  "Neo-Classical / Instrumental"),
    "albums/opus4-8/amarok":          ("RIVERWAKE",        "Claude Opus 4.8",  "Progressive Folk / Instrumental"),
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


def render_one(midi: Path, total_by_album: dict[str, int]) -> tuple[Path, bool, str]:
    key = album_for(midi)
    album, artist, genre = ALBUMS[key]
    title, tracknum = title_and_number(midi)
    opus = opus_path_for(midi)
    opus.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / (midi.stem + ".wav")
        r = subprocess.run([str(SYNTH), str(midi), "-o", str(wav), "-q"],
                           capture_output=True, text=True)
        if r.returncode != 0 or not wav.exists():
            return opus, False, f"ferrosintesis failed: {r.stderr.strip()[:200]}"
        cmd = [
            "ropusenc", "--bitrate", BITRATE, "--music", "--vbr",
            "--comp", "10",
            "--title", title, "--artist", artist, "--album", album,
            "--genre", genre, "--date", DATE, "--tracknumber", tracknum,
            "--comment", f"ALBUMARTIST={artist}",
            "--comment", f"COMPOSER={artist}",
            "--comment", f"TRACKTOTAL={total_by_album[key]}",
            "--comment", "ENCODER_SETTINGS=ferrosintesis->ropusenc 96k VBR",
            "-o", str(opus), str(wav),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not opus.exists():
            return opus, False, f"ropusenc failed: {r.stderr.strip()[:200]}"
    return opus, True, f"{album} / {title} (#{tracknum})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--album", help="only render this album (by title)")
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args()

    if not SYNTH.exists():
        raise SystemExit(f"synth not built: {SYNTH}\n"
                         f"run: cargo build --release -p ferrosintesis-cli")

    midis = all_midis()
    if args.album:
        midis = [m for m in midis if ALBUMS[album_for(m)][0] == args.album]
        if not midis:
            raise SystemExit(f"no album titled {args.album!r}")
    total_by_album = {k: 0 for k in ALBUMS}
    for m in midis:
        total_by_album[album_for(m)] += 1

    print(f"rendering {len(midis)} track(s) with {SYNTH.name} -> opus "
          f"({args.jobs} workers)")
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(render_one, m, total_by_album): m for m in midis}
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
