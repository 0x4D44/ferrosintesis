"""Rebuild the attack-transient sample bank from VSCO 2 Community Edition.

Downloads the pinned source sustains/hits (CC0,
github.com/sgossner/VSCO-2-CE), then
trims each to its onset: ~0.62 s kept, fades applied, peak-normalized,
resampled to 44.1 kHz mono 16-bit. The fundamental is measured by
autocorrelation — smallest near-maximal lag (octave-safe) with parabolic
refinement (cent accuracy) — and printed as the zone's root frequency,
which must match the table in crates/ferrosintesis/src/sampler.rs. Unpitched
drum hits skip root measurement.

Pure stdlib; run from the repository root:
python tools/ferrosintesis-samples/prepare.py
"""

import hashlib
import math
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import wave

VSCO_REV = "440300901dfe9275fd84e0b7763af1f8443ae62e"
BASE = f"https://raw.githubusercontent.com/sgossner/VSCO-2-CE/{VSCO_REV}"
DRUM_SOURCES = {
    "drum_sus_cymb1_mp_rr1.wav": f"{BASE}/Percussion/susCymb1-hit_mp_rr1.wav",
    "drum_sus_cymb1_mp_rr2.wav": f"{BASE}/Percussion/susCymb1-hit_mp_rr2.wav",
    "drum_crash1_ff_rr1.wav": f"{BASE}/Percussion/cymbal-crash1_ff_rr1.wav",
    "drum_crash1_ff_rr2.wav": f"{BASE}/Percussion/cymbal-crash1_ff_rr2.wav",
    "drum_kick_v3_rr1.wav": f"{BASE}/Percussion/BDrumNewhit_v3_rr1_Sum.wav",
    "drum_kick_v3_rr2.wav": f"{BASE}/Percussion/BDrumNewhit_v3_rr2_Sum.wav",
    "drum_snare2_v5_rr1.wav": f"{BASE}/Percussion/Snare2-HitSN_v5_rr1_Sum.wav",
    "drum_snare2_v5_rr2.wav": f"{BASE}/Percussion/Snare2-HitSN_v5_rr2_Sum.wav",
}
SOURCES = {
    f"violin_{n}_{d}.wav": f"{BASE}/Strings/Solo%20Violin/Arco%20Vib/LLVln_ArcoVib_{n}_{d}.wav"
    for n in ("G3", "E4", "C5", "G5", "C6", "E6")
    for d in ("f", "p")
} | {
    f"flute_{n}.wav": f"{BASE}/Woodwinds/Flute/susvib/LDFlute_susvib_{n}_v1_1.wav"
    for n in ("C4", "A4", "E5", "A5", "C6")
} | {
    f"piano_{n}_{d}.wav": f"{BASE}/Keys/Upright%20Nr1/UR1_{n}_{d}_RR1.wav"
    for n in ("C2", "G2", "C3", "G3", "C4", "G4", "C5", "G5", "C6")
    for d in ("pp", "mf", "f")
} | {
    # second round robin (VSCO has no pp RR2 for C2/G2; reuse RR1 there)
    f"piano_{n}_{d}_rr2.wav": f"{BASE}/Keys/Upright%20Nr1/UR1_{n}_{d}_RR{{}}.wav".format(
        1 if (d == "pp" and n in ("C2", "G2")) else 2
    )
    for n in ("C2", "G2", "C3", "G3", "C4", "G4", "C5", "G5", "C6")
    for d in ("pp", "mf", "f")
} | {
    # brass sustain onsets — VSCO dynamic layers: v1 -> p, v3 -> f
    f"trumpet_{n}_{d}.wav":
        f"{BASE}/Brass/Trumpet/sus/Sum_SHTrumpet_sus_{n}_{v}_rr1.wav"
    for n in ("F2", "C3", "G3", "D4", "A4")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    f"mutetpt_{n}_{d}.wav":
        f"{BASE}/Brass/Trumpet/straightM-sus/Sum_SHTrumpet_straightM-sus_"
        f"{n.replace('#', '%23')}_{v}_rr1.wav"
    for n in ("A#2", "D3", "G3", "D4", "A4")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    f"trombone_{n}_{d}.wav":
        f"{BASE}/Brass/Tenor%20Trombone/sus/tenortbn_sus_"
        f"{n.replace('#', '%23')}_{v}_1.wav"
    for n in ("F1", "A#1", "D2", "F2", "C3", "F3")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    f"tuba_{n}_{d}.wav":
        f"{BASE}/Brass/Tuba/sus/Tuba3_sus_{n.replace('#', '%23')}_{v}_rr1_Mid.wav"
    for n in ("A#0", "D#1", "A#1", "D2", "F2", "A#2")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    # F Horn: D4 has only v1 at the pinned rev; reuse it for the f layer
    f"horn_{n}_{d}.wav":
        f"{BASE}/Brass/F%20Horn/sus/MOHorn_sus_{n.replace('#', '%23')}_"
        f"{('v1' if n == 'D4' else v)}_1.wav"
    for n in ("A#1", "D2", "F2", "A2", "C3", "D4")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    # reed sustain onsets — VSCO dynamic layers: v1 -> p, v3 -> f
    f"oboe_{n}_{d}.wav":
        f"{BASE}/Woodwinds/Oboe/Sus/Oboe_Sus_{n.replace('#', '%23')}_{v}_Main.wav"
    for n in ("D3", "F3", "A#3", "D4", "F4", "A#4")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    # bassoon has only v1/v2 at the pinned rev: v1 -> p, v2 -> f
    f"bassoon_{n}_{d}.wav":
        f"{BASE}/Woodwinds/Bassoon/sus/PSBassoon_{n.replace('#', '%23')}_{v}_1.wav"
    for n in ("A#0", "F1", "C2", "G2", "D#3", "C4")
    for d, v in (("p", "v1"), ("f", "v2"))
} | {
    f"clarinet_{n}_{d}.wav":
        f"{BASE}/Woodwinds/Clarinet/susLong/DCClar_susLong_"
        f"{n.replace('#', '%23')}_{v}_rr1_sum.wav"
    for n in ("A#2", "D3", "F3", "A#3", "D4", "F4")
    for d, v in (("p", "v1"), ("f", "v3"))
} | {
    # string-section sustain onsets for GM 48-49 — violin section covers the
    # high split (VSCO dynamic layers: v1 -> p, v2 -> f; no v3 in this set)
    f"vlnens_{n}_{d}.wav":
        f"{BASE}/Strings/Violin%20Section/susVib/VlnEns_susVib_"
        f"{n.replace('#', '%23')}_{v}.wav"
    for n in ("G2", "D3", "A3", "E4", "B4", "D5")
    for d, v in (("p", "v1"), ("f", "v2"))
} | {
    # cello section covers the low split (v1 -> p, v3 -> f)
    f"celens_{n}_{d}.wav":
        f"{BASE}/Strings/Cello%20Section/susvib/susvib_"
        f"{n.replace('#', '%23')}_{v}_1.wav"
    for n in ("C1", "G1", "D2", "A2", "E3", "B3")
    for d, v in (("p", "v1"), ("f", "v3"))
} | DRUM_SOURCES

# FreePats "Spanish classical guitar" (version 2019-06-18), CC0 1.0 public
# domain dedication (readme.txt + cc0.txt inside the archive). One WAV per
# note, no velocity layers, no round robins — so the nylon bank is a single
# dynamic layer / single RR. Pinned by SHA-256 of the versioned archive;
# extraction needs a 7-Zip binary (`7z x`) — the archive uses an LZMA filter
# bsdtar cannot decode.
SCG_ARCHIVE_URL = (
    "https://freepats.zenvoid.org/Guitar/SpanishClassicalGuitar/"
    "SpanishClassicalGuitar-SFZ-20190618.7z"
)
SCG_ARCHIVE_SHA256 = "ef2fb7de0cc0ab561c4ebc28494f3fc2962596e4f32f16d6c96b8a385c7c098b"
SCG_MEMBER_DIR = "SpanishClassicalGuitar-SFZ-20190618/samples"
# nylon zones E2–E5, ~6-semitone spacing (max repitch ±3.5 st); B2 stands in
# for the set's missing A#2
GUITAR_SOURCES = {
    f"nylon_{n}.wav": f"{SCG_MEMBER_DIR}/{n}.wav"
    for n in ("E2", "B2", "E3", "A#3", "E4", "A#4", "E5")
}

# Steel-string acoustic (GM 25) — a 2017 Martin HD28 Vintage Series recorded and
# CC0-dedicated by Jeff Learman, distributed in the Discord SFZ GM Bank. The
# dedication is a header comment in the instrument's own .sfz ("// License:
# Creative Commons CC0"), which that repo's README designates as the
# authoritative per-instrument licence location. The repo is a MIXED CC0/CC-BY
# aggregation with no repo-level LICENSE, so CC0 cannot be inferred repo-wide
# and THE SHA PIN IS LOAD-BEARING: fetch from STEEL_REV only, never master.
# One take per note — no velocity layers, no round robins — so, exactly like
# nylon, the steel bank is a single flat layer and LaVoice's vel_amp does the
# dynamic scaling.
STEEL_REV = "05d5ed8befa042fd9d99a6d159dfc3673d3f8edc"
STEEL_DIR = "Discord GM/Melodic/026-Acoustic Guitar (steel)"
# zones E2–B5, ~6-semitone spacing (max repitch ±3.5 st), mirroring nylon. The
# source labels accidentals as FLATS; our note parser (and NOTE_HZ) speak
# sharps, so the destination names are respelled: Bb2 -> A#2, Bb3 -> A#3.
STEEL_SOURCES = {
    "steel_E2.wav": "MartinGM2_040__E2_1.wav",
    "steel_A#2.wav": "MartinGM2_046_Bb2_1.wav",
    "steel_E3.wav": "MartinGM2_052__E3_1.wav",
    "steel_A#3.wav": "MartinGM2_058_Bb3_1.wav",
    "steel_E4.wav": "MartinGM2_064__E4_1.wav",
    "steel_B4.wav": "MartinGM2_071__B4_1.wav",
    "steel_F5.wav": "MartinGM2_077__F5_1.wav",
    "steel_B5.wav": "MartinGM2_083__B5_1.wav",
}
STEEL_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sfzinstruments/Discord-SFZ-GM-Bank/"
        f"{STEEL_REV}/{urllib.parse.quote(STEEL_DIR)}/{urllib.parse.quote(member)}"
    )
    for dest, member in STEEL_SOURCES.items()
}

# Harpsichord (GM 6) — VCSL "Harpsichord, Unk" (Harpsi4), a 5-octave FF–f''' plucked
# keyboard, CC0 1.0 (github.com/sgossner/VCSL; the root LICENSE is the full CC0 1.0
# Universal text, added in commit c1ea7bcc). Single register (Main), single round
# robin (rr1) — one flat layer exactly like nylon/steel, so LaVoice's vel_amp does
# the dynamic scaling. THE PIN IS LOAD-BEARING: fetch from VCSL_REV only. Note that
# VCSL's octave labels sit ONE OCTAVE BELOW sounding pitch (measured 2026.07.17 —
# label C3 sounds 262 Hz = C4), the same offset the VSCO string sections carry. So
# the destination names use the SOUNDING pitch and map to the octave-down source
# label; the MEASURED root (not the label) is what lands in sampler.rs.
VCSL_REV = "c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e"
_VCSL_HARPSI_DIR = "Chordophones/Zithers/Harpsichord, Unk/Sustains"
# dest (SOUNDING pitch) -> source label (one octave down); ~6-semitone C/F grid
# spanning sounding C2..F6 (max repitch ±3 st, mirroring nylon).
_HARPSI_ZONES = [
    ("harpsi_C2.wav", "C1"),
    ("harpsi_F2.wav", "F1"),
    ("harpsi_C3.wav", "C2"),
    ("harpsi_F3.wav", "F2"),
    ("harpsi_C4.wav", "C3"),
    ("harpsi_F4.wav", "F3"),
    ("harpsi_C5.wav", "C4"),
    ("harpsi_F5.wav", "F4"),
    ("harpsi_C6.wav", "C5"),
    ("harpsi_F6.wav", "F5"),
]
HARPSICHORD_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(_VCSL_HARPSI_DIR)}/"
        f"Harpsi4_Sus_Main_{urllib.parse.quote(label)}_rr1.wav"
    )
    for dest, label in _HARPSI_ZONES
}

# GM 109 bagpipe (HLD 2026.07.17). A CC0 FreePats G-pipe: two separately-recorded
# drones (bass G2, tenor G3) an octave apart, plus a chanter. These are LOOPED
# sustains, not attack transients — `extract_loop` (not `trim_to_onset`) emits a
# seamless loop region, and the whole emitted WAV loops at render time via a plain
# modulo wrap. Take the WAV archive (not the FLAC one — stdlib `wave` reads it).
BAGPIPE_ARCHIVE_URL = (
    "https://freepats.zenvoid.org/Ethnic/Bagpipe/Bagpipe-SFZ-20221204.7z"
)
BAGPIPE_ARCHIVE_SHA256 = (
    "6f25f232065ebc51ab9d3b54aaedc8a29e59e454ec31d3f1b4a03b3d04256066"
)
_BP_MEMBERS = "Bagpipe-SFZ-20221204"
# dest -> member path in the archive. Two drones + six chanter zones (RR1, `_31`),
# ~2.5-semitone spacing F4–G5. The `.sfz` is copied too, for its loop points.
BAGPIPE_SOURCES = {
    "drone_G2.wav": f"{_BP_MEMBERS}/samples/drone_G2_1.wav",
    "drone_G3.wav": f"{_BP_MEMBERS}/samples/drone_G3_3.wav",
    "chanter_F4.wav": f"{_BP_MEMBERS}/samples/F4_31.wav",
    "chanter_G4.wav": f"{_BP_MEMBERS}/samples/G4_31.wav",
    "chanter_A4.wav": f"{_BP_MEMBERS}/samples/A4_31.wav",
    "chanter_C5.wav": f"{_BP_MEMBERS}/samples/C5_31.wav",
    "chanter_D5.wav": f"{_BP_MEMBERS}/samples/D5_31.wav",
    "chanter_G5.wav": f"{_BP_MEMBERS}/samples/G5_31.wav",
}
BAGPIPE_SFZ_MEMBER = f"{_BP_MEMBERS}/Bagpipe-20221204.sfz"
# Target loop lengths: drones long (slow, low), chanter short (masked by the drone).
BAGPIPE_LOOP_S = {"drone": 1.5, "chanter": 0.4}
# Every bagpipe sample is normalized to this RMS at bake; the drone/chanter MIX is
# then set by the per-voice gains in Rust (mirroring the modeled 0.154 : 0.075).
BAGPIPE_TARGET_RMS = 0.18

# f0 search range per family (the default misses the piano's low octaves
# and the low brass/bassoon fundamentals)
F0_RANGE = {
    "piano": (45.0, 2500.0),
    "trumpet": (80.0, 1200.0),
    "mutetpt": (80.0, 1200.0),
    "trombone": (35.0, 600.0),
    "tuba": (40.0, 300.0),
    "horn": (25.0, 600.0),
    # oboe hi capped at 1000: the F4_f take's 2nd harmonic outcorrelates its
    # fundamental (~699 Hz) and a 2000 Hz ceiling lets autocorr pick 1398
    "oboe": (200.0, 1000.0),
    "bassoon": (50.0, 800.0),
    "clarinet": (100.0, 1500.0),
    # guitar E2 (82.4) … E5 (659.3); ceiling 700 keeps autocorr off the
    # 2nd harmonic of the top zones (the brass/oboe lesson)
    "nylon": (70.0, 700.0),
    # steel E2 (82.4) … B5 (987.8); ceiling 1050 clears the top zone's
    # fundamental but stays under its 2nd harmonic (1976) — the brass/oboe
    # lesson. The Martin is tuned ~12 cents flat throughout; harmless, because
    # the MEASURED root is what lands in the zone table.
    "steel": (70.0, 1050.0),
    # harpsichord sounds C2 65 Hz … F6 1396 Hz; ceiling 1500 clears the top
    # zone's fundamental but stays under its 2nd harmonic (2792) — the
    # brass/oboe autocorr lesson. Bright and plucked, but the fundamental
    # dominates: the probe measured every zone correctly even at a 2200 ceiling.
    "harpsi": (55.0, 1500.0),
    # violin section G2-name spans G3 196 Hz … D5-name D6 1175 Hz (VSCO's
    # octave labels sit one below sounding pitch here); ceiling 1300 keeps
    # autocorr off the top zone's 2nd harmonic (the brass/oboe lesson)
    "vlnens": (150.0, 1300.0),
    # cello section C1-name sounds C2 65.4 Hz … B3-name B4 493.9 Hz; ceiling
    # 550 sits just above the top fundamental, below its 2nd harmonic (988)
    "celens": (50.0, 550.0),
}
# the piano has no expressive sustain to preserve: keep much more of the
# real recording and let the model take only the long tail
# plucks decay — keep more real body than the 0.62 s default (HLD §3)
KEEP_FAM = {
    "piano": (1.8, 0.6),
    "nylon": (0.9, 0.30),
    "steel": (0.9, 0.30),
    "harpsi": (0.9, 0.30),
}  # (keep_s, fade_s)
KEEP_FILE = {
    "drum_sus_cymb1_mp_rr1.wav": (2.2, 0.35),
    "drum_sus_cymb1_mp_rr2.wav": (2.2, 0.35),
    "drum_crash1_ff_rr1.wav": (2.2, 0.35),
    "drum_crash1_ff_rr2.wav": (2.2, 0.35),
    "drum_kick_v3_rr1.wav": (0.45, 0.08),
    "drum_kick_v3_rr2.wav": (0.45, 0.08),
    "drum_snare2_v5_rr1.wav": (0.45, 0.08),
    "drum_snare2_v5_rr2.wav": (0.45, 0.08),
}

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(TOOL_DIR, os.pardir, os.pardir))

# Local-file intake — CC BY 3.0 gong pair pre-placed under gong-src/ (there is NO
# auto-fetch: Freesound requires a login to download the originals, so they are
# committed as source and read directly from disk). They run through the SAME
# downmix/resample/normalize chain as the fetched sources, but the FULL RING is
# kept — a gong's multi-second bloom IS the instrument — so only leading silence is
# trimmed and a short squared end fade removes the truncation click (no attack
# trim). Treated as one-shots like DRUM_SOURCES: measure_f0 is skipped, and the
# destination crate is routed explicitly here (NOT via sample_output_path, whose
# family-prefix routing is left untouched for core/orchestral).
GONG_SRC = os.path.join(TOOL_DIR, "gong-src")
# out_name -> (source filename under gong-src/, destination sample crate, end fade s)
LOCAL_SOURCES = {
    "gong_ageng_soft.wav": (
        "gong_ageng_soft_261890.wav", "ferrosintesis-samples-gong", 0.30),
    "gong_ageng_loud.wav": (
        "gong_ageng_loud_261893.wav", "ferrosintesis-samples-gong", 0.30),
}

CORE_FAMILIES = frozenset(("piano", "violin", "flute"))
OUT_SR = 44100
KEEP_S = 0.62      # length kept after the pre-onset pad
PRE_S = 0.008      # pad kept before the onset
FADE_S = 0.20      # fade-out applied to the tail
NOTE_HZ = {}
for octave in range(0, 8):
    for i, name in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G",
                              "G#", "A", "A#", "B"]):
        NOTE_HZ[f"{name}{octave}"] = 440.0 * 2 ** ((12 * (octave + 1) + i - 69) / 12)


def sample_output_path(filename, repo_root=REPO_ROOT):
    """Return the sample-package destination for a generated WAV."""
    family = filename.split("_", 1)[0]
    package = (
        "ferrosintesis-samples-core"
        if family in CORE_FAMILIES
        else "ferrosintesis-samples-orchestral"
    )
    return os.path.join(repo_root, "crates", package, "samples", filename)


def read_wav(path):
    with wave.open(path, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    expected = n * ch * sw
    if len(raw) != expected:
        raise ValueError(f"{path}: truncated WAV data ({len(raw)} bytes, expected {expected})")
    if sw == 2:
        vals = struct.unpack(f"<{n * ch}h", raw)
        norm = [v / 32768.0 for v in vals]
    elif sw == 3:
        norm = []
        for i in range(n * ch):
            v = int.from_bytes(raw[3 * i:3 * i + 3], "little", signed=True)
            norm.append(v / 8388608.0)
    else:
        raise ValueError(f"{path}: unsupported sample width {sw}")
    if ch == 2:
        norm = [(norm[2 * i] + norm[2 * i + 1]) * 0.5 for i in range(n)]
    return norm, sr


def fetch(url, path):
    part = path + ".part"
    if os.path.exists(part):
        os.remove(part)
    try:
        urllib.request.urlretrieve(url, part)
        os.replace(part, path)
    except Exception:
        if os.path.exists(part):
            os.remove(part)
        raise


def ensure_source(fn, url, src):
    path = os.path.join(src, fn)
    if not os.path.exists(path):
        print(f"fetching {fn} ...", file=sys.stderr)
        fetch(url, path)
        return path
    try:
        read_wav(path)
    except (ValueError, wave.Error, EOFError) as e:
        print(f"cached {fn} invalid ({e}); refetching ...", file=sys.stderr)
        os.remove(path)
        fetch(url, path)
    return path


def ensure_archive_sources(src, url, sha256, member_map, extract_subdir):
    """Fetch + sha256-verify + 7z-extract an archive, copying members into `src`.

    Generalizes the FreePats fetch: two callers (Spanish guitar, bagpipe) are
    structurally identical — a `.7z` pinned by SHA-256, extracted with 7z (the
    archives use an LZMA filter bsdtar cannot decode), members copied out by a
    dest -> member-path map. Kept to exactly these four params; if a third caller
    ever needs a post-process hook, copy-paste rather than grow this.
    """
    if all(os.path.exists(os.path.join(src, fn)) for fn in member_map):
        return
    arc = os.path.join(src, os.path.basename(url))
    if not os.path.exists(arc):
        print(f"fetching {os.path.basename(arc)} ...", file=sys.stderr)
        fetch(url, arc)
    digest = hashlib.sha256(open(arc, "rb").read()).hexdigest()
    if digest != sha256:
        raise ValueError(f"{arc}: sha256 {digest} != pinned {sha256}")
    seven = shutil.which("7z") or r"C:\Program Files\7-Zip\7z.exe"
    ext = os.path.join(src, extract_subdir)
    subprocess.run([seven, "x", "-y", f"-o{ext}", arc], check=True,
                   stdout=subprocess.DEVNULL)
    for fn, member in member_map.items():
        shutil.copyfile(os.path.join(ext, *member.split("/")),
                        os.path.join(src, fn))


def ensure_guitar_sources(src):
    """Fetch + verify + extract the pinned FreePats Spanish-guitar archive."""
    ensure_archive_sources(src, SCG_ARCHIVE_URL, SCG_ARCHIVE_SHA256,
                           GUITAR_SOURCES, "scg_extract")


def ensure_bagpipe_sources(src):
    """Fetch + verify + extract the pinned FreePats bagpipe archive (+ its SFZ)."""
    members = dict(BAGPIPE_SOURCES)
    members["bagpipe.sfz"] = BAGPIPE_SFZ_MEMBER
    ensure_archive_sources(src, BAGPIPE_ARCHIVE_URL, BAGPIPE_ARCHIVE_SHA256,
                           members, "bagpipe_extract")


def parse_sfz_loops(sfz_text):
    """Map each region's source basename -> (loop_start, loop_end) from an SFZ.

    Minimal: splits on `<region>`, reads the last `sample=` and any
    `loop_start=`/`loop_end=` in each. Enough for the FreePats bagpipe, whose
    loop points are expertly correlation-placed (rho 0.98-1.00) — far better than
    a self-search on a variable reed, so we seed `extract_loop` from these.
    """
    loops = {}
    for region in re.split(r"<region>", sfz_text)[1:]:
        # sample value runs to the next opcode on the line or the end of line —
        # handles both "own line" (FreePats) and inline `sample=x opcode=y` SFZ
        m_s = re.search(r"sample=(.+?)(?=\s+\w+=|[\r\n]|$)", region)
        m_ls = re.search(r"loop_start=(\d+)", region)
        m_le = re.search(r"loop_end=(\d+)", region)
        if m_s and m_ls and m_le:
            base = os.path.basename(m_s.group(1).strip().replace("\\", "/"))
            loops[base] = (int(m_ls.group(1)), int(m_le.group(1)))
    return loops


def _seam_click(seg):
    """Wrap-seam click for a buffer looped by plain modulo.

    Returns |seg[0] - seg[-1]| (the discontinuity a modulo wrap actually
    produces) as a MULTIPLE of the 95th-percentile of the body's sample-to-
    sample steps. A seamless loop wraps with a step no worse than the signal's
    own normal steps, so this is ~1; a click is an outlier, >> 1.

    This replaces a Pearson-correlation seam metric: Pearson is offset/scale-
    insensitive (Codex review) AND phase-sensitive across a fixed window, so it
    both admits anomalous boundary steps and rejects perfectly-seamless loops.
    The first-difference outlier ratio is what a click physically is.
    """
    n = len(seg)
    diffs = sorted(abs(seg[i + 1] - seg[i]) for i in range(n - 1))
    p95 = diffs[min(len(diffs) - 1, int(0.95 * len(diffs)))] if diffs else 0.0
    wrap = abs(seg[0] - seg[-1])
    return wrap / p95 if p95 > 0 else 0.0


def extract_loop(x, sr, loop_start, f0, target_s, target_rms=None):
    """Emit a SHORT seamless loop region from a sustained sample.

    Unlike `trim_to_onset` (an attack extractor that seeks the onset, fades the
    tail to zero, and peak-normalizes) this keeps the STEADY interior and the
    whole returned buffer loops via a plain modulo wrap.

    `loop_start` is the SFZ's expertly-placed loop entry (a trusted steady-state
    point). The SFZ loop_end, though, spans nearly the whole file (chanter loops
    run 4-6 s), which is far too large to ship — so we cut our OWN endpoint at
    ~`target_s`, searching +/-1 period for the length whose modulo wrap has the
    smallest seam step. Then DC-remove (the drones carry -35/-41 dB DC) and
    normalize to a COMMON RMS (not per-file peak) so a `nearest()` zone switch on
    a sustained voice doesn't jump in level.
    """
    period = sr / f0
    base = int(round(target_s * sr))
    span = int(2 * period)
    if loop_start + base + span >= len(x):
        raise ValueError(f"source too short for a {target_s}s loop at {loop_start}")
    # search the endpoint over +/-2 periods for the length whose wrap best
    # matches in BOTH value and slope (a small step and a continuing trend) —
    # value-only can pick a point where level matches but the waveform is
    # heading the wrong way, which still clicks.
    def seam_cost(length):
        i, j = loop_start, loop_start + length
        val = abs(x[i] - x[j])
        slope = abs((x[i + 1] - x[i]) - (x[j] - x[j - 1]))
        return val + slope
    length = min(range(base - span, base + span + 1),
                 key=lambda L: seam_cost(L) if L >= 4 else 9e9)
    seg = x[loop_start:loop_start + length]
    mean = sum(seg) / len(seg)
    seg = [v - mean for v in seg]
    rms = math.sqrt(sum(v * v for v in seg) / len(seg))
    tgt = BAGPIPE_TARGET_RMS if target_rms is None else target_rms
    g = tgt / rms if rms > 0 else 1.0
    return [v * g for v in seg]


def resample(x, sr_in, sr_out):
    if sr_in == sr_out:
        return x
    ratio = sr_in / sr_out
    out = []
    for i in range(int(len(x) / ratio)):
        pos = i * ratio
        j = int(pos)
        f = pos - j
        a = x[j]
        b = x[j + 1] if j + 1 < len(x) else a
        out.append(a + (b - a) * f)
    return out


def measure_f0(x, sr, lo=80.0, hi=3000.0):
    """Autocorrelation over a window starting past the attack."""
    start = int(0.20 * sr)
    win = int(0.10 * sr)
    seg = x[start:start + win]
    if len(seg) < win:
        seg = x[len(x) // 3:len(x) // 3 + win]
    mean = sum(seg) / len(seg)
    seg = [v - mean for v in seg]
    min_lag = int(sr / hi)
    max_lag = int(sr / lo)
    e0 = sum(v * v for v in seg[:win - max_lag])
    corr = {}
    for lag in range(min_lag, max_lag):
        num = 0.0
        den = 0.0
        for i in range(win - max_lag):
            num += seg[i] * seg[i + lag]
            den += seg[i + lag] * seg[i + lag]
        corr[lag] = num / math.sqrt(e0 * den) if den > 0 and e0 > 0 else -1.0
    best = max(corr.values())
    # a periodic signal correlates equally at every multiple of its period;
    # take the SMALLEST lag that comes close to the maximum
    best_lag = next(lag for lag in sorted(corr) if corr[lag] >= best - 0.03)
    # parabolic interpolation around the peak for sub-sample lag accuracy
    lag = float(best_lag)
    if best_lag - 1 in corr and best_lag + 1 in corr:
        a, b, c = corr[best_lag - 1], corr[best_lag], corr[best_lag + 1]
        den = a - 2 * b + c
        if den != 0:
            lag += 0.5 * (a - c) / den
    return sr / lag, corr[best_lag]


def trim_to_onset(x, sr, keep_s, fade_s):
    """Cut `x` to its onset, de-click both ends, and peak-normalize.

    Returns the finished segment: PRE_S of lead-in, then `keep_s` of audio,
    with a 2 ms fade-in and a `fade_s` squared fade-out, normalized to 0.9.
    """
    peak = max(abs(v) for v in x)
    # onset: first sample above 3% of peak
    thr = 0.03 * peak
    onset = next(i for i, v in enumerate(x) if abs(v) > thr)
    start = max(0, onset - int(PRE_S * sr))
    seg = x[start:start + int((PRE_S + keep_s) * sr)]
    # De-click fade-in, sized to the lead-in that ACTUALLY EXISTS.
    #
    # `start` clamps at 0, so a source trimmed tight to its onset yields less
    # than PRE_S of lead-in — and a fixed 2 ms fade then runs straight over the
    # attack, attenuating precisely the transient the LA layer exists to
    # capture. That is not hypothetical: 74 of the 210 sources have their onset
    # inside 2 ms (measured), worst among them the Martin steel takes (median
    # onset 8 samples, 0.18 ms) which would lose their entire pick attack.
    # Every source begins at near-silence (max |x[0]| over the bank is 0.015),
    # so there is no step to de-click in the first place and shortening the
    # fade cannot introduce one. Capping the fade at `lead` therefore fixes the
    # tight-trim case and is exactly inert for the 136 sources with >= 2 ms of
    # lead-in. Pinned by test_fade_in_never_exceeds_available_lead_in and
    # test_fade_in_is_inert_when_lead_in_exceeds_the_window.
    lead = onset - start
    fin = min(int(0.002 * sr), lead)
    for i in range(min(fin, len(seg))):
        seg[i] *= i / fin
    fout = int(fade_s * sr)
    for i in range(fout):
        j = len(seg) - fout + i
        if 0 <= j < len(seg):
            t = 1.0 - i / fout
            seg[j] *= t * t
    pk = max(abs(v) for v in seg)
    g = 0.9 / pk if pk > 0 else 1.0
    return [v * g for v in seg]


def trim_lead_and_ring(x, sr, pre_s, end_fade_s):
    """Trim leading pre-onset silence, KEEP the full ring, de-click both ends,
    peak-normalize to 0.9.

    Unlike `trim_to_onset` (which caps the kept audio to a short attack window),
    this keeps everything from just before the onset to the end of the recording —
    a gong's multi-second bloom is the whole instrument, so nothing after the
    attack may be discarded. Only leading silence is dropped (with a `pre_s`
    lead-in pad); a `pre_s`-bounded 2 ms fade-in de-clicks the start and an
    `end_fade_s` squared fade-out removes the end-truncation click.
    """
    peak = max(abs(v) for v in x)
    thr = 0.03 * peak
    onset = next(i for i, v in enumerate(x) if abs(v) > thr)
    start = max(0, onset - int(pre_s * sr))
    seg = x[start:]
    # de-click fade-in, sized to the lead-in that ACTUALLY exists (as trim_to_onset)
    lead = onset - start
    fin = min(int(0.002 * sr), lead)
    for i in range(min(fin, len(seg))):
        seg[i] *= i / fin
    fout = int(end_fade_s * sr)
    for i in range(fout):
        j = len(seg) - fout + i
        if 0 <= j < len(seg):
            t = 1.0 - i / fout
            seg[j] *= t * t
    pk = max(abs(v) for v in seg)
    g = 0.9 / pk if pk > 0 else 1.0
    return [v * g for v in seg]


def write_wav_mono(path, seg, sr):
    """Quantize a float mono signal to 16-bit PCM and write it as a WAV."""
    pcm = struct.pack(f"<{len(seg)}h",
                      *[max(-32768, min(32767, int(v * 32767))) for v in seg])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)


def _bake_bagpipe(src):
    """Bake the looped bagpipe drones + chanter; return print-table rows.

    Separate from the onset loop in `main`: these are looped sustains, so they
    use `extract_loop` (SFZ loop points + common-RMS) not `trim_to_onset`, and a
    tight per-file f0 window — a single chanter range can't work, since the 2nd
    harmonic of the lowest zone (F4, ~684 Hz) sits below the highest fundamental
    (G5, ~774 Hz), so one ceiling cannot be both above 774 and below 684.
    """
    with open(os.path.join(src, "bagpipe.sfz"), encoding="utf-8",
              errors="replace") as f:
        loops = parse_sfz_loops(f.read())
    rows = []
    for fn, member in sorted(BAGPIPE_SOURCES.items()):
        x, sr = read_wav(os.path.join(src, fn))
        ls, _le = loops[os.path.basename(member)]
        if sr != OUT_SR:
            ls = int(ls * OUT_SR / sr)
            x = resample(x, sr, OUT_SR)
            sr = OUT_SR
        note = next(p for p in fn[:-4].split("_")
                    if p[0] in "ABCDEFG" and p[-1].isdigit())
        nominal = NOTE_HZ[note]
        # measure f0 from the steady loop region with a tight +/-2 semitone
        # window (source is 30-50 cents flat) — never wide enough to lock onto a
        # harmonic (a single chanter range can't: F4's 2nd harmonic < G5's f0)
        f0, conf = measure_f0(x[ls:], sr, nominal * 2 ** (-2 / 12),
                              nominal * 2 ** (2 / 12))
        target_s = BAGPIPE_LOOP_S[fn.split("_")[0]]
        seg = extract_loop(x, sr, ls, f0, target_s)
        click = _seam_click(seg)
        if click > 3.0:
            raise ValueError(f"{fn}: loop seam click x{click:.2f} of p95 step "
                             f"— reed too variable here, widen search")
        write_wav_mono(sample_output_path(fn), seg, sr)
        rows.append((fn, f0, f0, nominal, 1200 * math.log2(f0 / nominal),
                     click, len(seg) / sr))
    return rows


def main():
    socket.setdefaulttimeout(60)
    # `--local-only` skips the fetched full bank (network + rewriting the tracked
    # core/orchestral WAVs) and regenerates ONLY the local gong intake below.
    local_only = "--local-only" in sys.argv[1:]

    rows = []
    if not local_only:
        src = os.path.join(tempfile.gettempdir(), "vsco2ce_src", VSCO_REV)
        os.makedirs(src, exist_ok=True)
        for fn, url in SOURCES.items():
            ensure_source(fn, url, src)
        for fn, url in STEEL_URLS.items():
            ensure_source(fn, url, src)
        for fn, url in HARPSICHORD_URLS.items():
            ensure_source(fn, url, src)
        ensure_guitar_sources(src)
        ensure_bagpipe_sources(src)

        # Looped bagpipe sustains (own transform: extract_loop, not trim_to_onset)
        rows += _bake_bagpipe(src)
        for fn in sorted(SOURCES | GUITAR_SOURCES | STEEL_URLS | HARPSICHORD_URLS):
            x, sr = read_wav(os.path.join(src, fn))
            x = resample(x, sr, OUT_SR)
            sr = OUT_SR
            keep_s, fade_s = KEEP_FILE.get(fn, KEEP_FAM.get(fn.split("_")[0], (KEEP_S, FADE_S)))
            seg = trim_to_onset(x, sr, keep_s, fade_s)
            if fn in DRUM_SOURCES:
                root = f0 = cand = cents = conf = None
            else:
                lo, hi = F0_RANGE.get(fn.split("_")[0], (80.0, 3000.0))
                f0, conf = measure_f0(seg, sr, lo, hi)
                # nominal pitch from the filename, e.g. violin_G3_f / flute_C4
                note = next(p for p in fn[:-4].split("_") if p[0] in "ABCDEFG" and p[-1].isdigit())
                nominal = NOTE_HZ[note]
                # snap measured f0 to the nearest octave of the nominal note
                cand = min((nominal * 2 ** k for k in range(-2, 3)),
                           key=lambda c: abs(math.log(f0 / c)))
                cents = 1200 * math.log2(f0 / cand)
                root = f0 if abs(cents) < 60 else cand
            write_wav_mono(sample_output_path(fn), seg, sr)
            rows.append((fn, root, f0, cand, cents, conf, len(seg) / sr))

    # Local-file intake (gong): full ring kept, one-shot (no f0), explicit routing.
    for out_name, (src_fn, package, end_fade_s) in sorted(LOCAL_SOURCES.items()):
        x, sr = read_wav(os.path.join(GONG_SRC, src_fn))
        x = resample(x, sr, OUT_SR)
        sr = OUT_SR
        seg = trim_lead_and_ring(x, sr, PRE_S, end_fade_s)
        output = os.path.join(REPO_ROOT, "crates", package, "samples", out_name)
        write_wav_mono(output, seg, sr)
        rows.append((out_name, None, None, None, None, None, len(seg) / sr))

    print(f"{'file':26} {'root_hz':>9} {'measured':>9} {'nominal':>9} {'cents':>7} {'conf':>5} {'len_s':>6}")
    for r in rows:
        if r[1] is None:
            print(f"{r[0]:26} {'hit':>9} {'':>9} {'':>9} {'':>7} {'':>5} {r[6]:6.3f}")
        else:
            print(f"{r[0]:26} {r[1]:9.2f} {r[2]:9.2f} {r[3]:9.2f} {r[4]:7.1f} {r[5]:5.2f} {r[6]:6.3f}")


if __name__ == "__main__":
    sys.exit(main())
