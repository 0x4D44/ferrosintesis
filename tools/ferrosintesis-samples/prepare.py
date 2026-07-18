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
import tarfile
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

# Harp (GM 46) — VCSL "Concert Harp" (Chordophones/Composite Chordophones/Concert
# Harp), CC0 1.0 (same VCSL_REV pin as the harpsichord). Plucked with a long natural
# decay: the sample carries the pluck onset + early ring (~0.9 s, like the guitars)
# and the Pluck(&HARP) model keeps the bendable decay. Uses the FORTE layer (`_f1`)
# — the only dynamic present at EVERY zone — over a ~7-semitone subset spanning
# G1..F7. Output routes to the NEW CC0 crate `-orchestral2` (the original
# `-orchestral` is at the ~10 MiB crates.io cap). Roots are MEASURED (printed by
# prepare.py); the label is nominal only.
_VCSL_HARP_DIR = "Chordophones/Composite Chordophones/Concert Harp"
_HARP_ZONES = [
    ("harp_G1.wav", "KSHarp_G1_f1"),
    ("harp_D2.wav", "KSHarp_D2_f1"),
    ("harp_A2.wav", "KSHarp_A2_f1"),
    ("harp_E3.wav", "KSHarp_E3_f1"),
    ("harp_B3.wav", "KSHarp_B3_f1"),
    ("harp_F4.wav", "KSHarp_F4_f1"),
    ("harp_C5.wav", "KSHarp_C5_f1"),
    ("harp_G5.wav", "KSHarp_G5_f1"),
    ("harp_D6.wav", "KSHarp_D6_f1"),
    ("harp_A6.wav", "KSHarp_A6_f1"),
    ("harp_F7.wav", "KSHarp_F7_f1"),
]
HARP_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(_VCSL_HARP_DIR)}/{src}.wav"
    )
    for dest, src in _HARP_ZONES
}

# Viola (GM 41) solo onset — VSCO Viola SECTION susvib as the proxy (VSCO has no solo
# viola). The ~380 ms onset carries the viola formant; the Bowed + BODY_VIOLA model owns
# the sustain, so the "section-ness" mostly stays out of the sound. This fixes 40==41 —
# GM 41 stops sharing the SOLO VIOLIN onset. VSCO string-section labels sound ~1 OCTAVE
# ABOVE the label (documented for vlnens/celens in F0_RANGE), so dest names use the
# SOUNDING pitch mapping to the octave-down source label. Harmonic-rich bowed section
# spanning >1 octave -> in TWO_F_STRONG, so main() caps the per-note ceiling at
# nominal*1.5. v1 -> p, v2 -> f. Roots MEASURED at bake. Output -> -orchestral2 (CC0;
# -orchestral is at the ~10 MiB crates.io cap).
_VIOLA_ZONES = [
    ("viola_C3", "C2"),
    ("viola_G3", "G2"),
    ("viola_D4", "D3"),
    ("viola_A4", "A3"),
    ("viola_E5", "E4"),
    ("viola_B5", "B4"),
    ("viola_D6", "D5"),
]
VIOLA_URLS = {
    f"{dest}_{d}.wav": (
        f"{BASE}/Strings/Viola%20Section/susvib/ViolaEns_susvib_{label}_{v}_1.wav"
    )
    for dest, label in _VIOLA_ZONES
    for d, v in (("p", "v1"), ("f", "v2"))
}

# Chromatic percussion LA onsets (MM-BUG-KILN-00015 batch 1) — VSCO-2-CE Percussion mallet
# subdirs, same VSCO_REV pin (CC0). Single flat dynamic layer (no p/f, no RR), so LaVoice's
# vel_amp does the dynamics. STRUCK -> KEEP_FAM (~0.9 s). Mallet bars are partial-heavy
# (xylophone emphasises the 3rd partial a 12th up, glockenspiel is inharmonic/weak-f0), so all
# three are in TWO_F_STRONG (per-note ceiling nominal*1.5) — assuming VSCO labels the recorded
# SOUNDING pitch (glock sounds ~2 oct, xylo ~1 oct above WRITTEN; VERIFY by the measured roots).
# Output -> -orchestral2 (CC0). No '#' in any zone label, so no URL-encoding needed.
_MARIMBA_ZONES = ["F1", "C2", "G2", "B2", "F3", "C4", "G4", "B4", "F5", "C6"]
MARIMBA_URLS = {
    f"marimba_{n}.wav": f"{BASE}/Percussion/Marimba/Marimba_hit_Outrigger_{n}_loud_01.wav"
    for n in _MARIMBA_ZONES
}
_XYLO_ZONES = ["G3", "C4", "G4", "C5", "G5", "C6", "G6", "C7"]
XYLO_URLS = {
    f"xylo_{n}.wav": f"{BASE}/Percussion/Xylo/Xylo_Medium_{n}_ff_01_far.wav" for n in _XYLO_ZONES
}
# Glock G4 + C6 DROPPED after measurement: G4 read 0.87-conf / +68 cents (weak low-f0),
# C6 read an octave low (530 Hz ~= C5, autocorr grabbed a subharmonic). The 4 kept zones
# span C5..C7 (523..2122 Hz); LaVoice's +-1 oct repitch covers glock's C5..C8 register.
_GLOCK_ZONES = ["C5", "G5", "G6", "C7"]
GLOCK_URLS = {
    f"glock_{n}.wav": f"{BASE}/Percussion/Glock/glock_medium_{n}.wav" for n in _GLOCK_ZONES
}

# Ocarina (GM 79) — VCSL "Ocarina, Typical" sustains (CC0, VCSL_REV). A soft near-sine
# vessel flute; the sample carries the breath onset and the Wind model keeps the body
# (a wind onset like the flute, so the default 0.62 s keep, NOT a plucked keep). Output
# → -orchestral2 (CC0). `#` in the source names is URL-encoded via quote(src).
#
# The ocarina has a STRONG 2nd harmonic, so autocorr locks onto 2f whenever the F0
# ceiling admits it (measured: A3/C#4 read 2f at a 600 ceiling; E4/G#4/C5 read the
# fundamental). To let a SINGLE ceiling measure every zone's true fundamental, the zone
# set is kept UNDER one octave — E4 330 … C5 523 Hz — so ceiling 600 is above every
# fundamental yet below the lowest 2f (E4's 659). `LaVoice` repitches ±1 octave, so
# these 3 zones still cover ~E3–C6 (ocarina is a high instrument; low notes are rare).
_VCSL_OCARINA_DIR = "Aerophones/Edge-blown Aerophones/Ocarina, Typical/Sustains/Sus"
_OCARINA_ZONES = [
    ("ocarina_E4.wav", "StdOcarina_Sus_E4"),
    ("ocarina_G#4.wav", "StdOcarina_Sus_G#4"),
    ("ocarina_C5.wav", "StdOcarina_Sus_C5"),
]
OCARINA_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(_VCSL_OCARINA_DIR)}/{urllib.parse.quote(src)}.wav"
    )
    for dest, src in _OCARINA_ZONES
}

# Recorder (GM 74) — VCSL Baroque recorders (CC0, VCSL_REV): alto lows + soprano
# mids/highs, one combined bank spanning F3–C6. Both are recorders (same family
# timbre). Wind onset over the Wind model (default 0.62 s keep). Zones come from two
# folders, so each zone carries its own dir. `#` in names → quote(src). Roots MEASURED
# (recorder F0 strength checked per the ocarina 2f lesson before locking the ceiling).
_VCSL_REC_SOP = "Aerophones/Edge-blown Aerophones/Baroque Soprano Recorder/Sustain"
_VCSL_REC_ALT = "Aerophones/Edge-blown Aerophones/Baroque Alto Recorder/Sustain"
_RECORDER_ZONES = [
    ("recorder_F3.wav", _VCSL_REC_ALT, "AltRecorder_Sus_F3_rr1_Main"),
    ("recorder_A#3.wav", _VCSL_REC_ALT, "AltRecorder_Sus_A#3_rr1_Main"),
    ("recorder_E4.wav", _VCSL_REC_SOP, "SopRecorder_Sus_E4_rr1_Main"),
    ("recorder_A#4.wav", _VCSL_REC_SOP, "SopRecorder_Sus_A#4_rr1_Main"),
    ("recorder_E5.wav", _VCSL_REC_SOP, "SopRecorder_Sus_E5_rr1_Main"),
    ("recorder_A#5.wav", _VCSL_REC_SOP, "SopRecorder_Sus_A#5_rr1_Main"),
    ("recorder_C6.wav", _VCSL_REC_SOP, "SopRecorder_Sus_C6_rr1_Main"),
]
RECORDER_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(d)}/{urllib.parse.quote(src)}.wav"
    )
    for dest, d, src in _RECORDER_ZONES
}

# Timpani (GM 47) — VCSL "Timpani 2" single hits (CC0, VCSL_REV). STRUCK/pitched:
# the sample carries the mallet strike + early ring, the timpani() model keeps the
# settling body (like the plucked banks — KEEP_FAM 0.9 s). The VCSL source names
# (Timpani<kettle><tuning>_hit_v<vel>_rr<n>) carry NO note, only kettle+tuning tokens,
# so each hit's PITCH was probed offline (2026.07.18) and the dest is named by the
# MEASURED pitch. One velocity (v3) + rr1 per chosen tuning; a high-confidence spread
# A#1–F3 (conf 0.77–0.92). LaVoice repitches ±1 octave (covers ~A0–F4). Output →
# -orchestral2 (CC0). Roots are re-measured at bake and printed (F0_RANGE below).
_VCSL_TIMP_DIR = "Membranophones/Struck Membranophones/Timpani 2/Hit"
_TIMPANI_ZONES = [
    ("timpani_A#1.wav", "Timpani3A_hit_v3_rr1_main"),
    ("timpani_F2.wav", "Timpani4A_hit_v3_rr1_main"),
    ("timpani_G#2.wav", "Timpani7A_hit_v3_rr1_main"),
    ("timpani_D3.wav", "Timpani6E_hit_v3_rr1_main"),
    ("timpani_F3.wav", "Timpani6A_hit_v3_rr1_main"),
]
TIMPANI_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(_VCSL_TIMP_DIR)}/{urllib.parse.quote(src)}.wav"
    )
    for dest, src in _TIMPANI_ZONES
}

# Banjo (GM 105) — sfzinstruments/ganjo (an SX 6-string guitar-banjo, recorded/mapped by
# 'itsclipping'), CC0 1.0 (verified LICENSE.md). A NEW external source (its own repo + REV
# pin, not VCSL/VSCO/MS Basic). Plucked, bright, fast decay — the sample owns the pick
# transient + resonator-head twang, the Pluck(&BANJO) model carries the decay (0.9 s keep,
# like the guitars). Source names carry spaces and `#` (URL-encoded via quote(src)); the
# files are IEEE-float WAV, transcoded to PCM by ensure_banjo_sources (ffmpeg). The ganjo
# labels sit ONE OCTAVE ABOVE sounding pitch (probed 2026.07.18: "…- A#4" sounds A#3), so
# each dest is named by its SOUNDING pitch — the 8-zone subset sounds D#2–B4. The banjo is
# harmonic-rich (a generous ceiling rails on upper harmonics for the low zones), so `banjo`
# is in TWO_F_STRONG below. Output → the CC0 `-orchestral2` crate.
GANJO_REV = "ccff5cd5cd3b513873a48994c07724d9d3c39e1c"
_GANJO_DIR = "Common"
_GANJO_ZONES = [
    ("banjo_D#2.wav", "Banjo_Common - D#3"),
    ("banjo_G#2.wav", "Banjo_Common - G#3"),
    ("banjo_C#3.wav", "Banjo_Common - C#4"),
    ("banjo_F#3.wav", "Banjo_Common - F#4"),
    ("banjo_A#3.wav", "Banjo_Common - A#4"),
    ("banjo_D#4.wav", "Banjo_Common - D#5"),
    ("banjo_G4.wav", "Banjo_Common - G5"),
    ("banjo_B4.wav", "Banjo_Common - B5"),
]
BANJO_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sfzinstruments/ganjo/{GANJO_REV}/"
        f"{urllib.parse.quote(_GANJO_DIR)}/{urllib.parse.quote(src)}.wav"
    )
    for dest, src in _GANJO_ZONES
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

# GM 0 Acoustic Grand — Salamander Grand Piano V3 (a Yamaha C5 concert grand, AB
# pair), by Alexander Holm, CC BY 3.0. Unlike the CC0 VSCO *upright* that voices
# GM 1/3, this is a real grand, so GM 0 becomes its own instrument instead of the
# upright with a treble shelf. Distributed as a .tar.bz2 — stdlib `tarfile` reads
# bz2 directly (no 7z, unlike the LZMA FreePats archives), so this gets its own
# fetch helper rather than growing `ensure_archive_sources`. 16-bit STEREO 44.1 kHz
# (downmixed to mono like every other family), sampled every minor third across 16
# velocity layers v1..v16, with NO round robins. We take 9 zones C2..C6 (F# is the
# nearest sampled pitch to each G, matching the upright's C/G spacing) x 3 dynamics.
# RR2 is sourced from an adjacent-higher velocity layer: `trim_to_onset` peak-
# normalizes every file to 0.9, so RR1/RR2 land at the SAME level and differ only in
# the natural harder-strike timbre — i.e. real round-robin variation, not a level
# step. The rel*/harm* hammer-release and string-resonance layers are skipped.
# Pinned by SHA-256 of the archive.org 16-bit tarball.
SALAMANDER_ARCHIVE_URL = (
    "https://archive.org/download/SalamanderGrandPianoV3/"
    "SalamanderGrandPianoV3_44.1khz16bit.tar.bz2"
)
SALAMANDER_ARCHIVE_SHA256 = (
    "fe595c7722b70860e6377f82948d1c0cfcf27ecebf500dc79534408a78a62892"
)
_SGP_MEMBERS = "SalamanderGrandPianoV3_44.1khz16bit/44.1khz16bit"
_GRAND_ZONES = ["C2", "F#2", "C3", "F#3", "C4", "F#4", "C5", "F#5", "C6"]
# dynamic -> (RR1 velocity layer, RR2 velocity layer). Salamander hivel bands:
# v2 27-34, v3 35-36 (pp); v9 65-72, v10 73-80 (mf); v15 113-120, v16 121-127 (f).
_GRAND_VEL = {"pp": (2, 3), "mf": (9, 10), "f": (15, 16)}
GRAND_SOURCES = {
    f"grand_{z}_{d}{rr}.wav": f"{_SGP_MEMBERS}/{z}v{v}.wav"
    for z in _GRAND_ZONES
    for d, (v_rr1, v_rr2) in _GRAND_VEL.items()
    for rr, v in (("", v_rr1), ("_rr2", v_rr2))
}

# Clavinet (GM 7) — the MuseScore "MS Basic" soundfont's clavinet (MIT, NOT CC0), the
# default sampled voice; the modeled Pluck moves to the CC0-nonzero alt bank + the
# --no-samples fallback. MS Basic is an SF3 soundfont: SF2 structure but each sample is
# a self-contained Ogg-Vorbis stream in the `smpl` chunk, so the SF3 shdr start/end are
# BYTE offsets (not sample frames) delimiting the Ogg — sliced out and decoded with
# ffmpeg (same shell-out precedent as the drumkit's FLAC). THE PIN IS LOAD-BEARING and
# the sha256 is verified before use. Output routes to the separate MIT-licensed
# `ferrosintesis-samples-clavinet` crate so the CC0 banks stay pure CC0.
MUSESCORE_REV = "d307a2bd899f15bf650efc3c2891211af5cb78b5"
MUSESCORE_SF3_URL = (
    f"https://raw.githubusercontent.com/musescore/MuseScore/{MUSESCORE_REV}/"
    "share/sound/MS%20Basic.sf3"
)
MUSESCORE_SF3_SHA256 = (
    "5ea2375e8bd7d8e71def1036978c1621e85b66934169b6a2744b27b9b3c2d99c"
)
# Each clavinet zone is baked into a self-contained decaying note: the ~0.2 s decoded
# Ogg body's sustain loop is made seamless (a short crossfade) and repeated under an
# exponential decay, so a held note rings and decays like a real clavinet string.
# CLAVINET_T60 is register-scaled and EAR-TUNABLE (this box has no ears): low notes ring
# longer. root MIDI 31 -> 2.4 s down to root 91 -> 0.9 s (linear in MIDI).
CLAVINET_KEEP_S = 1.6
CLAVINET_FADE_S = 0.05
CLAVINET_SEAM_XF = 160  # loop-seam crossfade length (samples)


def clavinet_t60(root_midi):
    """Register-scaled clavinet decay t60 (EAR-tunable): 2.4 s low -> 0.9 s high."""
    frac = (root_midi - 31) / 60.0
    return round(2.4 - max(0.0, min(1.0, frac)) * 1.5, 3)

# f0 search range per family (the default misses the piano's low octaves
# and the low brass/bassoon fundamentals)
F0_RANGE = {
    "piano": (45.0, 2500.0),
    # grand spans C2 65 Hz … C6 1047 Hz, same window as the upright
    "grand": (45.0, 2500.0),
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
    # harp G1 ~49 Hz … F7 ~2794 Hz; ceiling 3200 clears the top fundamental and
    # stays under its 2nd harmonic; measure_f0 + the octave-snap correct any label offset
    "harp": (40.0, 3200.0),
    # ocarina zones E4 330 … C5 523 Hz (kept under one octave); ceiling 600 is above
    # every fundamental but below the lowest 2f (659) — the ocarina's strong 2nd
    # harmonic otherwise steals autocorr (see the OCARINA block comment).
    "ocarina": (250.0, 600.0),
    # recorder F3 175 … C6 1047 Hz. The recorder is STRONGLY 2f-dominant (probed
    # 2026.07.18: at a 2000 ceiling every zone but C6 read its 2nd harmonic) and spans
    # 2.5 octaves, so no single fixed ceiling separates f from 2f. It is therefore in
    # TWO_F_STRONG below — main() caps the ceiling PER NOTE at label×1.5 so only the
    # fundamental is in range. This 2000 is only the upper bound before that per-note cap.
    "recorder": (150.0, 2000.0),
    # timpani A#1 58 … F3 173 Hz; ceiling 400 admits the principal (perceived) mode and
    # keeps autocorr off the higher inharmonic modes. Roots probed offline first; the
    # bake re-measures with this range (a struck membrane is mode-rich, conf 0.77–0.92).
    "timpani": (40.0, 400.0),
    # banjo SOUNDS D#2 79 … B4 495 Hz (ganjo labels are an octave high; dest named by the
    # sounding pitch). Harmonic-rich → in TWO_F_STRONG, so main() caps the ceiling per-note
    # at label×1.5; lo 55 clears the low D#2 fundamental. 1000 is the pre-cap upper bound.
    "banjo": (55.0, 1000.0),
    # violin section G2-name spans G3 196 Hz … D5-name D6 1175 Hz (VSCO's
    # octave labels sit one below sounding pitch here); ceiling 1300 keeps
    # autocorr off the top zone's 2nd harmonic (the brass/oboe lesson)
    "vlnens": (150.0, 1300.0),
    # cello section C1-name sounds C2 65.4 Hz … B3-name B4 493.9 Hz; ceiling
    # 550 sits just above the top fundamental, below its 2nd harmonic (988)
    "celens": (50.0, 550.0),
    # solo viola onset (VSCO Viola SECTION susvib): sounding C3 131 … D6 1175 Hz (labels
    # one octave below sounding, like vlnens/celens). In TWO_F_STRONG, so the per-note cap
    # (nominal*1.5) blocks 2f; this global ceiling only needs to clear the top fundamental.
    "viola": (120.0, 1400.0),
    # mallets (partial-heavy) — wide floor/ceiling; TWO_F_STRONG caps per-note at
    # nominal*1.5 so autocorr can't lock onto the 2nd/3rd bar partial. Sounding ranges:
    # marimba F1 44 .. C6 1047; xylophone G3 196 .. C7 2093; glock G4 392 .. C7 2093.
    "marimba": (40.0, 1200.0),
    "xylo": (180.0, 2400.0),
    "glock": (380.0, 2400.0),
}
# Families whose recordings are 2f-DOMINANT (autocorr grabs the 2nd harmonic if the
# ceiling admits it) AND span more than an octave, so a single fixed F0 ceiling can't
# separate the fundamental from 2f. For these, main() caps the ceiling per-note at
# label×1.5. (The ocarina avoids this list by keeping its zone span under one octave.)
TWO_F_STRONG = frozenset(("recorder", "banjo", "viola", "marimba", "xylo", "glock"))
# the piano has no expressive sustain to preserve: keep much more of the
# real recording and let the model take only the long tail
# plucks decay — keep more real body than the 0.62 s default (HLD §3)
KEEP_FAM = {
    "piano": (1.8, 0.6),
    # grand: keep a long body like the upright (the sample carries the note), but
    # 1.5 s rather than 1.8 s holds the standalone -grand crate well under the
    # crates.io 10 MiB limit (54 files, 16-bit mono) with headroom
    "grand": (1.5, 0.6),
    "nylon": (0.9, 0.30),
    "steel": (0.9, 0.30),
    "harpsi": (0.9, 0.30),
    "harp": (0.9, 0.30),
    "timpani": (0.9, 0.30),
    "banjo": (0.9, 0.30),
    "marimba": (0.9, 0.30),
    "xylo": (0.9, 0.30),
    "glock": (0.9, 0.30),
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
# Families that live in their OWN sample crate (not core/orchestral) — the grand is
# a ~6.9 MiB CC-BY bank kept separate so core stays under the crates.io 10 MiB cap.
FAMILY_PACKAGE = {
    "grand": "ferrosintesis-samples-grand",
    # New CC0 onsets: `-orchestral` is at the ~10 MiB crates.io cap, so harp (and the
    # timpani/recorder/ocarina/banjo units that follow) route to a second CC0 crate.
    "harp": "ferrosintesis-samples-orchestral2",
    "ocarina": "ferrosintesis-samples-orchestral2",
    "recorder": "ferrosintesis-samples-orchestral2",
    "timpani": "ferrosintesis-samples-orchestral2",
    "banjo": "ferrosintesis-samples-orchestral2",
    "viola": "ferrosintesis-samples-orchestral2",
    "marimba": "ferrosintesis-samples-orchestral2",
    "xylo": "ferrosintesis-samples-orchestral2",
    "glock": "ferrosintesis-samples-orchestral2",
}
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
    if family in FAMILY_PACKAGE:
        package = FAMILY_PACKAGE[family]
    elif family in CORE_FAMILIES:
        package = "ferrosintesis-samples-core"
    else:
        package = "ferrosintesis-samples-orchestral"
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


def ensure_salamander_sources(src):
    """Fetch + sha256-verify + extract the pinned Salamander Grand Piano V3 subset.

    A sibling of `ensure_archive_sources`, not a caller of it: the Salamander
    archive is a `.tar.bz2` (stdlib `tarfile` decodes bz2 with no 7z), and bz2 is
    not seekable, so we stream the tar ONCE and pull the wanted members in a single
    pass rather than re-opening per file. Members copy straight to `src/grand_*.wav`
    (no extract subdir); `sample_output_path` later routes them to the -grand crate.
    """
    if all(os.path.exists(os.path.join(src, fn)) for fn in GRAND_SOURCES):
        return
    arc = os.path.join(src, os.path.basename(SALAMANDER_ARCHIVE_URL))
    if not os.path.exists(arc):
        print(f"fetching {os.path.basename(arc)} ...", file=sys.stderr)
        fetch(SALAMANDER_ARCHIVE_URL, arc)
    digest = hashlib.sha256(open(arc, "rb").read()).hexdigest()
    if digest != SALAMANDER_ARCHIVE_SHA256:
        raise ValueError(f"{arc}: sha256 {digest} != pinned {SALAMANDER_ARCHIVE_SHA256}")
    wanted = {member: fn for fn, member in GRAND_SOURCES.items()}
    found = 0
    with tarfile.open(arc, "r:bz2") as tf:
        for member in tf:
            fn = wanted.get(member.name)
            if fn is None:
                continue
            extracted = tf.extractfile(member)
            with open(os.path.join(src, fn), "wb") as out:
                shutil.copyfileobj(extracted, out)
            found += 1
    if found != len(GRAND_SOURCES):
        raise ValueError(
            f"salamander: extracted {found}/{len(GRAND_SOURCES)} members "
            f"(archive layout changed?)")


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


def _autocorr_f0(seg, sr, lo, hi):
    """Normalized-autocorrelation f0 of ONE window: smallest near-maximal lag
    (octave-safe), parabolic-refined. Returns (f0_hz, confidence)."""
    n = len(seg)
    min_lag = max(1, int(sr / hi))
    max_lag = min(n - 1, int(sr / lo))
    if max_lag <= min_lag or n < max_lag + 2:
        return 0.0, -1.0
    mean = sum(seg) / n
    seg = [v - mean for v in seg]
    e0 = sum(v * v for v in seg[:n - max_lag])
    corr = {}
    for lag in range(min_lag, max_lag):
        num = 0.0
        den = 0.0
        for i in range(n - max_lag):
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


def measure_f0(x, sr, lo=80.0, hi=3000.0):
    """Autocorrelation over a window starting past the attack."""
    start = int(0.20 * sr)
    win = int(0.10 * sr)
    seg = x[start:start + win]
    if len(seg) < win:
        seg = x[len(x) // 3:len(x) // 3 + win]
    return _autocorr_f0(seg, sr, lo, hi)


def measure_f0_robust(x, sr, nominal):
    """Nominal-guided f0 for slow-attack notes: probe several STEADY-body windows and
    return the highest-confidence reading. A single fixed-offset window can land in the
    breathy sax/baritone attack, where the correlation is low and the pitch wobbles up
    to a semitone; the steady interior is clean (measured: bar G#3 reads 221 Hz/0.57 at
    0.2 s but a rock-solid 211 Hz/0.98 at 0.5-1.0 s). The band is +/-1.5 semitones of the
    SFZ-documented key, so only the true fundamental (never a neighbour or a harmonic)
    can fall in range."""
    lo, hi = nominal * 0.915, nominal * 1.093   # +/- ~1.5 semitones
    win = int(0.20 * sr)
    dur = len(x) / sr
    offsets = [o for o in (0.35, 0.60, 0.90, 1.30) if o + win / sr < dur - 0.03]
    if not offsets:
        offsets = [max(0.0, dur / 3.0)]
    best = (nominal, -1.0)
    for off in offsets:
        start = int(off * sr)
        f0, c = _autocorr_f0(x[start:start + win], sr, lo, hi)
        if f0 > 0 and c > best[1]:
            best = (f0, c)
    return best


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


_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _midi_name(m):
    return f"{_NOTE_NAMES[m % 12]}{m // 12 - 1}"


def _midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ensure_musescore_sf3(src):
    """Fetch + sha256-verify the pinned MuseScore MS Basic soundfont."""
    path = os.path.join(src, "MS_Basic.sf3")
    if not os.path.exists(path):
        print("fetching MS Basic.sf3 (~51 MB) ...", file=sys.stderr)
        fetch(MUSESCORE_SF3_URL, path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if digest != MUSESCORE_SF3_SHA256:
        raise ValueError(f"{path}: sha256 {digest} != pinned {MUSESCORE_SF3_SHA256}")
    return path


def _sf_preset_zones(sf3, preset=7):
    """Parse an SF2/SF3 soundfont and return a bank-0 preset's sample zones.

    `preset` is the GM program number in bank 0 (default 7 = clavinet, the
    original caller; the GM 75/76/77 pipes and GM 104 sitar reuse this same
    extractor). Returns (smpl_data_offset, [(root_midi, sample_start, sample_end,
    startloop, endloop, samplerate), ...]) — SF3 start/end are BYTE offsets into
    `smpl` (each slice is one self-contained Ogg-Vorbis stream); startloop/endloop
    are decoded-frame offsets from the sample start.
    """
    assert sf3[0:4] == b"RIFF" and sf3[8:12] == b"sfbk", "not an SF2/SF3 file"

    def u16(b, o):
        return struct.unpack("<H", b[o:o + 2])[0]

    # top-level walk: locate LIST sdta (holds `smpl`) and LIST pdta
    lists = {}
    pos = 12
    while pos + 12 <= len(sf3):
        cid = sf3[pos:pos + 4]
        sz = struct.unpack("<I", sf3[pos + 4:pos + 8])[0]
        if cid == b"LIST":
            lists[sf3[pos + 8:pos + 12]] = (pos + 12, sz - 4)
        pos += 8 + sz + (sz & 1)

    def walk(off, size):
        end = off + size
        subs = {}
        p = off
        while p + 8 <= end:
            cid = sf3[p:p + 4]
            sz = struct.unpack("<I", sf3[p + 4:p + 8])[0]
            subs[cid] = (p + 8, sz)
            p += 8 + sz + (sz & 1)
        return subs

    sdta = walk(*lists[b"sdta"])
    pdta = walk(*lists[b"pdta"])
    smpl_off = sdta[b"smpl"][0]

    def recs(name, width):
        o, s = pdta[name]
        return [sf3[o + i * width:o + (i + 1) * width] for i in range(s // width)]

    phdr, pbag, pgen = recs(b"phdr", 38), recs(b"pbag", 4), recs(b"pgen", 4)
    inst, ibag, igen = recs(b"inst", 22), recs(b"ibag", 4), recs(b"igen", 4)
    shdr = recs(b"shdr", 46)

    # bank==0 (phdr[22]), program==preset (phdr[20]); presetBagNdx at [24]
    pi = next(
        i for i, r in enumerate(phdr) if u16(r, 22) == 0 and u16(r, 20) == preset
    )
    instr = None
    for b in range(u16(phdr[pi], 24), u16(phdr[pi + 1], 24)):
        for g in range(u16(pbag[b], 0), u16(pbag[b + 1], 0)):
            if u16(pgen[g], 0) == 41:  # gen 41 = instrument index
                instr = u16(pgen[g], 2)
    if instr is None:
        raise ValueError(f"preset {preset} has no instrument generator")

    zones = []
    for b in range(u16(inst[instr], 20), u16(inst[instr + 1], 20)):
        sid = None
        for g in range(u16(ibag[b], 0), u16(ibag[b + 1], 0)):
            if u16(igen[g], 0) == 53:  # gen 53 = sampleID
                sid = u16(igen[g], 2)
        if sid is None:
            continue  # global zone
        h = shdr[sid]
        start, end, sl, el, sr = struct.unpack("<IIIII", h[20:40])
        root = h[40]  # originalPitch (MIDI) — trustworthy; sample NAME octave is +1
        zones.append((root, start, end, sl, el, sr))
    return smpl_off, zones


def _seamless_loop(x, sl, el, xf):
    """Return a length-(el-sl) loop whose wrap el->sl is click-free — PITCH-PRESERVING.

    A soundfont loop `x[sl:el]` is an integer number of fundamental periods, so its
    length MUST be preserved or the repeat re-pitches the note (shortening it broke the
    low zones, whose loop is only 1-2 periods). Instead of trimming, crossfade the
    loop's tail toward the `xf` samples that PRECEDE `sl`: the tail then trends into
    `x[sl-1]`, so wrapping to `x[sl]` is continuous while the loop length is unchanged.
    """
    L = el - sl
    xf = min(xf, L // 2, sl)  # bounded by the loop and the available pre-roll
    loop = list(x[sl:el])
    if xf >= 2:
        for k in range(xf):
            w = k / xf
            loop[L - xf + k] = loop[L - xf + k] * (1 - w) + x[sl - xf + k] * w
    return loop


def _bake_clavinet_note(x, root_hz, sr, t60, keep_s=None, fade_s=None):
    """Bake one decoded clavinet zone into a self-contained decaying note.

    The decoded Ogg body (~0.2 s, real attack) is extended by looping a PITCH-
    SYNCHRONOUS window under an exponential decay, then faded and peak-normalized.
    We do NOT trust the soundfont's own loop points: the Ogg decode drops ~80-100
    trailing frames (Vorbis padding), which shortens the short low-note loops below
    an integer period and re-pitches the note. Because `originalPitch` is accurate,
    we instead carve exactly `k` periods (`T = sr/root_hz`) out of the steady body,
    ending a hair before the decoded end, so the loop length is an exact multiple of
    the fundamental and the sustained pitch is dead-on.
    """
    keep_s = CLAVINET_KEEP_S if keep_s is None else keep_s
    fade_s = CLAVINET_FADE_S if fade_s is None else fade_s
    period = sr / root_hz
    guard = 8
    loop_end = min(len(x) - guard, len(x))
    attack = int(0.004 * sr)  # keep a few ms of the real onset before the loop
    max_k = max(1, int((loop_end - attack) / period))
    k = min(max_k, 16)  # a handful of periods: stable, still a tiny embedded window
    loop_len = int(round(k * period))
    loop_start = max(0, loop_end - loop_len)
    loop = _seamless_loop(x, loop_start, loop_end, CLAVINET_SEAM_XF)
    out = list(x[:loop_start])
    n = int(keep_s * sr)
    i = 0
    while len(out) < n:
        out.append(loop[i % len(loop)])
        i += 1
    out = out[:n]
    dec = 10 ** (-3.0 / (t60 * sr))
    g = 1.0
    for j in range(loop_start, len(out)):
        g *= dec
        out[j] *= g
    f = int(fade_s * sr)
    for c in range(f):
        j = len(out) - f + c
        if 0 <= j < len(out):
            out[j] *= 1.0 - c / f
    pk = max(abs(v) for v in out) or 1.0
    return [v * 0.9 / pk for v in out]


def _bake_clavinet(src):
    """Extract + decode + bake the 11 GM7 clavinet zones from MS Basic.sf3.

    Writes `clavinet_<sounding-pitch>.wav` into the MIT-licensed
    `ferrosintesis-samples-clavinet` crate; returns print-table rows. Ogg decode
    shells out to ffmpeg (mono 16-bit 44.1 kHz PCM), matching the drumkit's FLAC path.
    """
    sf3 = open(ensure_musescore_sf3(src), "rb").read()
    smpl_off, zones = _sf_preset_zones(sf3, 7)
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    out_dir = os.path.join(REPO_ROOT, "crates", "ferrosintesis-samples-clavinet", "samples")
    rows = []
    for root, start, end, _sl, _el, _sr in sorted(zones):
        ogg = os.path.join(src, f"clavinet_{root}.ogg")
        wav = os.path.join(src, f"clavinet_{root}.wav")
        with open(ogg, "wb") as f:
            f.write(sf3[smpl_off + start:smpl_off + end])
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", ogg, "-acodec", "pcm_s16le", wav], check=True)
        x, wsr = read_wav(wav)
        if wsr != OUT_SR:
            x = resample(x, wsr, OUT_SR)
            wsr = OUT_SR
        seg = _bake_clavinet_note(x, _midi_hz(root), wsr, clavinet_t60(root))
        # measure the baked note's root over its steady body (the zone table uses the
        # MEASURED fundamental, as every other bank does)
        nominal = _midi_hz(root)
        f0, conf = measure_f0(seg, wsr, nominal * 0.85, nominal * 1.2)
        cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
        out_name = f"clavinet_{_midi_name(root)}.wav"
        write_wav_mono(os.path.join(out_dir, out_name), seg, wsr)
        rows.append((out_name, f0, f0, nominal, cents, conf, len(seg) / wsr))
    return rows


def _bake_sf_onset(src, preset, prefix, dest_crate, keep_s, fade_s):
    """Extract a bank-0 preset's zones from MS Basic.sf3 as ONSET samples.

    Unlike `_bake_clavinet` (which bakes a full decaying LOOPED note), this trims each
    decoded zone to its attack + early body with `trim_to_onset`, exactly like the CC0
    wind/pluck LA banks — the modeled voice carries the sustain/decay. Used for the GM
    104 sitar and the GM 75/76/77 pipes. Ogg decode shells out to ffmpeg (same path as
    `_bake_clavinet`); a zone whose SF3 sample rate differs from 44.1 kHz is resampled.
    Writes `<prefix>_<sounding-pitch>.wav` into `dest_crate`/samples; returns print rows.
    Roots are re-measured in a tight window around the SF3 `originalPitch` (`h[40]`,
    trustworthy), so a 2f-dominant zone can't fool the measurement (window < 2×).
    """
    sf3 = open(ensure_musescore_sf3(src), "rb").read()
    smpl_off, zones = _sf_preset_zones(sf3, preset)
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    out_dir = os.path.join(REPO_ROOT, "crates", dest_crate, "samples")
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for root, start, end, _sl, _el, _sr in sorted(zones):
        ogg = os.path.join(src, f"{prefix}_{root}.ogg")
        wav = os.path.join(src, f"{prefix}_{root}.wav")
        with open(ogg, "wb") as f:
            f.write(sf3[smpl_off + start:smpl_off + end])
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", ogg, "-acodec", "pcm_s16le", wav], check=True)
        x, wsr = read_wav(wav)
        if wsr != OUT_SR:
            x = resample(x, wsr, OUT_SR)
            wsr = OUT_SR
        seg = trim_to_onset(x, wsr, keep_s, fade_s)
        nominal = _midi_hz(root)
        # measure near the known originalPitch; the window is < 2× so a 2f-dominant
        # zone (some SF3 pipe presets) cannot pull the estimate to the 2nd harmonic
        f0, conf = measure_f0(seg, wsr, nominal * 0.8, nominal * 1.4)
        cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
        out_name = f"{prefix}_{_midi_name(root)}.wav"
        write_wav_mono(os.path.join(out_dir, out_name), seg, wsr)
        rows.append((out_name, f0, f0, nominal, cents, conf, len(seg) / wsr))
    return rows


def ensure_banjo_sources(src):
    """Fetch the ganjo banjo WAVs and transcode them to 16-bit PCM.

    The ganjo source is IEEE-float WAV (fmt tag 3), which stdlib `wave` cannot read, so
    ffmpeg transcodes each to pcm_s16le (same shell-out precedent as the SF3/FLAC decodes)
    into the name the main loop expects. The float download is cached as `<name>.f32`;
    the PCM is (re)written each run so a prior crashed float file is overwritten.
    """
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    for fn, url in BANJO_URLS.items():
        ensure_source(fn + ".f32", url, src)
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
             "-i", os.path.join(src, fn + ".f32"),
             "-acodec", "pcm_s16le", os.path.join(src, fn)],
            check=True,
        )


# --- GM 64-67 saxophones: MTG.SoloSax LA sample layer (CC-BY 4.0) -------------
# Source: github.com/sfzinstruments/MTG.SoloSax — the MTG good-sounds.org single-note
# dataset (Neumann U87, 24-bit/48 kHz FLAC), pinned by commit. The FLAC filenames are
# NUMBERED, not pitched, so the authoritative note is the `key=` in each SFZ region
# file (Data/<inst>_<dyn>_rr1.txt). We still MEASURE f0 in a narrow window around the
# key's frequency and store the measured fundamental as the zone root, so each take's
# tuning offset (the SFZ `tune=` cents) never reaches the render — the repo's
# "labels can lie, measure f0" rule. Output routes EXPLICITLY to the separate CC-BY
# `ferrosintesis-samples-sax` crate (like the clavinet/gong intakes) so the CC0 core
# banks stay pure CC0. rr1 take only; p and f dynamic layers are INDEPENDENT zone
# lists (reed_bank picks a whole bank by velocity), so they need not be pitch-aligned.
MTG_SAX_REV = "b494d256549b3d088fdec176ce82867f8a1f58b2"
MTG_SAX_BASE = (
    "https://raw.githubusercontent.com/sfzinstruments/MTG.SoloSax/"
    f"{MTG_SAX_REV}/MTG%20Solo%20Saxophones"
)
# (out-prefix, sfz-prefix): GM 64 soprano, 65 alto, 66 tenor, 67 baritone
MTG_SAX_INSTR = [("sop", "sop"), ("alt", "alt"), ("ten", "ten"), ("bar", "bar")]
MTG_SAX_ZONE_STEP = 4   # keep every Nth sampled note (~N-semitone zones; max repitch ~N/2)
MTG_SAX_KEEP_S = 0.62   # attack + early body; the model carries the sustain (reed recipe)
MTG_SAX_FADE_S = 0.20
MTG_SAX_MIN_CONF = 0.85  # drop a zone whose measured root is not trustworthy (neighbours cover)


def _mtg_region_keys(src, prefix, dyn):
    """Parse Data/<prefix>_<dyn>_rr1.txt -> {midi_key: sample_basename} for MTG sax."""
    fn = f"{prefix}_{dyn}_rr1.txt"
    path = os.path.join(src, fn)
    if not os.path.exists(path):
        fetch(f"{MTG_SAX_BASE}/Data/{fn}", path)
    text = open(path, encoding="utf-8").read()
    return {int(m.group(1)): m.group(2)
            for m in re.finditer(r"key=(\d+)\s+sample=(\S+?)\.\$EXT", text)}


def _bake_mtg_sax(src):
    """Fetch + decode + bake the MTG.SoloSax LA layer for GM 64-67.

    Writes `sax_<inst>_<midiname>_<p|f>.wav` (16-bit mono 44.1 kHz) into the CC-BY
    `ferrosintesis-samples-sax` crate; returns print-table rows. FLAC decode shells
    out to ffmpeg (mono 24-bit, source rate), matching the clavinet/drumkit path.
    Zones are selected by index across each dynamic's available notes, so gaps in the
    source do not break selection; the ROOT stored is the measured f0.
    """
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    out_dir = os.path.join(REPO_ROOT, "crates", "ferrosintesis-samples-sax", "samples")
    rows = []
    for out_pre, sfz_pre in MTG_SAX_INSTR:
        for dyn in ("f", "p"):
            kmap = _mtg_region_keys(src, sfz_pre, dyn)
            skeys = sorted(kmap)
            chosen = skeys[::MTG_SAX_ZONE_STEP]
            if skeys and skeys[-1] not in chosen:
                chosen.append(skeys[-1])   # always cover the top note
            for key in chosen:
                base = kmap[key]
                nominal = 440.0 * 2 ** ((key - 69) / 12.0)
                flac = os.path.join(src, base + ".flac")
                wav = os.path.join(src, base + ".wav")
                if not os.path.exists(flac):
                    fetch(f"{MTG_SAX_BASE}/Samples/{base}.flac", flac)
                if not os.path.exists(wav):
                    subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                                    "-i", flac, "-ac", "1", "-acodec", "pcm_s24le", wav],
                                   check=True)
                x, wsr = read_wav(wav)
                x = resample(x, wsr, OUT_SR)
                wsr = OUT_SR
                # Measure on the RAW note's steady body (robust to the slow baritone
                # attack); THEN trim for output. A zone whose root can't be measured
                # confidently is dropped — its neighbours cover it under repitch.
                f0, conf = measure_f0_robust(x, wsr, nominal)
                if conf < MTG_SAX_MIN_CONF:
                    print(f"  SKIP sax_{out_pre} {_midi_name(key)} ({dyn}): f0 conf "
                          f"{conf:.2f} < {MTG_SAX_MIN_CONF}", file=sys.stderr)
                    continue
                seg = trim_to_onset(x, wsr, MTG_SAX_KEEP_S, MTG_SAX_FADE_S)
                cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
                out_name = f"sax_{out_pre}_{_midi_name(key)}_{dyn}.wav"
                write_wav_mono(os.path.join(out_dir, out_name), seg, wsr)
                rows.append((out_name, f0, f0, nominal, cents, conf, len(seg) / wsr))
    return rows


def _print_sample_rows(rows):
    print(f"{'file':26} {'root_hz':>9} {'measured':>9} {'nominal':>9} {'cents':>7} {'conf':>5} {'len_s':>6}")
    for r in rows:
        if r[1] is None:
            print(f"{r[0]:26} {'hit':>9} {'':>9} {'':>9} {'':>7} {'':>5} {r[6]:6.3f}")
        else:
            print(f"{r[0]:26} {r[1]:9.2f} {r[2]:9.2f} {r[3]:9.2f} {r[4]:7.1f} {r[5]:5.2f} {r[6]:6.3f}")


def main():
    socket.setdefaulttimeout(60)
    # `--local-only` skips the fetched full bank (network + rewriting the tracked
    # core/orchestral WAVs) and regenerates ONLY the local gong intake below.
    local_only = "--local-only" in sys.argv[1:]
    # `--only=fam[,fam2]` regenerates ONLY the named families (by filename prefix),
    # leaving every other tracked WAV untouched and skipping their fetches (incl. the
    # 7z / SF3 / tarball sources) — used to ADD one instrument without rewriting the
    # whole bank. `fam` is the sample-name prefix: harp, timpani, recorder, ocarina,
    # banjo, sitar, panflute, bottle, shakuhachi, clavinet, chanter (bagpipe), grand, sax, …
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = set(filter(None, a.split("=", 1)[1].split(",")))

    def want(fam):
        return only is None or fam in only

    # `--sax-only` bakes ONLY the MTG saxophone LA layer (network + the -sax crate),
    # skipping the slow VSCO fetch/rewrite — fast iteration on the sax bank alone.
    sax_only = "--sax-only" in sys.argv[1:]

    rows = []
    if sax_only:
        sax_src = os.path.join(tempfile.gettempdir(), "mtg_sax_src", MTG_SAX_REV)
        os.makedirs(sax_src, exist_ok=True)
        rows += _bake_mtg_sax(sax_src)
        _print_sample_rows(rows)
        return
    if not local_only:
        src = os.path.join(tempfile.gettempdir(), "vsco2ce_src", VSCO_REV)
        os.makedirs(src, exist_ok=True)
        for fn, url in SOURCES.items():
            if want(fn.split("_")[0]):
                ensure_source(fn, url, src)
        for fn, url in STEEL_URLS.items():
            if want("steel"):
                ensure_source(fn, url, src)
        for fn, url in HARPSICHORD_URLS.items():
            if want("harpsi"):
                ensure_source(fn, url, src)
        for fn, url in HARP_URLS.items():
            if want("harp"):
                ensure_source(fn, url, src)
        for fn, url in OCARINA_URLS.items():
            if want("ocarina"):
                ensure_source(fn, url, src)
        for fn, url in RECORDER_URLS.items():
            if want("recorder"):
                ensure_source(fn, url, src)
        for fn, url in TIMPANI_URLS.items():
            if want("timpani"):
                ensure_source(fn, url, src)
        for fn, url in VIOLA_URLS.items():
            if want("viola"):
                ensure_source(fn, url, src)
        for fn, url in MARIMBA_URLS.items():
            if want("marimba"):
                ensure_source(fn, url, src)
        for fn, url in XYLO_URLS.items():
            if want("xylo"):
                ensure_source(fn, url, src)
        for fn, url in GLOCK_URLS.items():
            if want("glock"):
                ensure_source(fn, url, src)
        if want("banjo"):
            ensure_banjo_sources(src)
        if want("nylon"):
            ensure_guitar_sources(src)
        if want("chanter"):
            ensure_bagpipe_sources(src)
        if want("grand"):
            ensure_salamander_sources(src)

        # Looped bagpipe sustains (own transform: extract_loop, not trim_to_onset)
        if want("chanter"):
            rows += _bake_bagpipe(src)

        # GM7 clavinet: own transform (SF3 Ogg extract + ffmpeg decode + decay bake),
        # cached by MuseScore rev, output to the separate MIT `-clavinet` crate.
        if want("clavinet"):
            clav_src = os.path.join(tempfile.gettempdir(), "musescore_sf3", MUSESCORE_REV)
            os.makedirs(clav_src, exist_ok=True)
            rows += _bake_clavinet(clav_src)

        # GM 104 sitar: SF3 onset (attack + jawari buzz) → the MIT `-musescore` crate
        # (same MS Basic source/NOTICE as the clavinet; kept a separate crate so the
        # published `-clavinet` crate stays clavinet-only). Plucked → 0.9 s keep.
        if want("sitar"):
            ms_src = os.path.join(tempfile.gettempdir(), "musescore_sf3", MUSESCORE_REV)
            os.makedirs(ms_src, exist_ok=True)
            rows += _bake_sf_onset(
                ms_src, 104, "sitar", "ferrosintesis-samples-musescore", 0.9, 0.20
            )

        # GM 75/76/77 pipes: SF3 WIND onsets (keep 0.62) → the MIT -musescore crate. Pan
        # flute (75) is a proper 8-zone multisample (mixed sample rates — _bake_sf_onset
        # resamples per zone); blown bottle (76) and shakuhachi (77) are SINGLE-zone in MS
        # Basic, so their onset engages only within ~1 octave of the sample and cleanly
        # falls back to the model elsewhere (thin, but a real breath onset near that range).
        for _preset, _prefix in ((75, "panflute"), (76, "bottle"), (77, "shakuhachi")):
            if want(_prefix):
                ms_src = os.path.join(tempfile.gettempdir(), "musescore_sf3", MUSESCORE_REV)
                os.makedirs(ms_src, exist_ok=True)
                rows += _bake_sf_onset(
                    ms_src, _preset, _prefix, "ferrosintesis-samples-musescore", 0.62, 0.24
                )

        # GM 64-67 saxophones: MTG.SoloSax LA layer (own transform: FLAC fetch +
        # ffmpeg decode), cached by MTG rev, output to the separate CC-BY `-sax` crate.
        if want("sax"):
            sax_src = os.path.join(tempfile.gettempdir(), "mtg_sax_src", MTG_SAX_REV)
            os.makedirs(sax_src, exist_ok=True)
            rows += _bake_mtg_sax(sax_src)
        for fn in sorted(
            SOURCES | GUITAR_SOURCES | STEEL_URLS | HARPSICHORD_URLS | HARP_URLS
            | OCARINA_URLS | RECORDER_URLS | TIMPANI_URLS | BANJO_URLS | VIOLA_URLS
            | MARIMBA_URLS | XYLO_URLS | GLOCK_URLS
            | GRAND_SOURCES
        ):
            if not want(fn.split("_")[0]):
                continue
            x, sr = read_wav(os.path.join(src, fn))
            x = resample(x, sr, OUT_SR)
            sr = OUT_SR
            keep_s, fade_s = KEEP_FILE.get(fn, KEEP_FAM.get(fn.split("_")[0], (KEEP_S, FADE_S)))
            seg = trim_to_onset(x, sr, keep_s, fade_s)
            if fn in DRUM_SOURCES:
                root = f0 = cand = cents = conf = None
            else:
                fam = fn.split("_")[0]
                lo, hi = F0_RANGE.get(fam, (80.0, 3000.0))
                # nominal pitch from the filename, e.g. violin_G3_f / flute_C4
                note = next(p for p in fn[:-4].split("_") if p[0] in "ABCDEFG" and p[-1].isdigit())
                nominal = NOTE_HZ[note]
                # 2f-dominant families: cap the ceiling per-note just above the label
                # so autocorr cannot lock onto the 2nd harmonic (see TWO_F_STRONG).
                if fam in TWO_F_STRONG:
                    hi = min(hi, nominal * 1.5)
                f0, conf = measure_f0(seg, sr, lo, hi)
                # snap measured f0 to the nearest octave of the nominal note
                cand = min((nominal * 2 ** k for k in range(-2, 3)),
                           key=lambda c: abs(math.log(f0 / c)))
                cents = 1200 * math.log2(f0 / cand)
                root = f0 if abs(cents) < 60 else cand
            write_wav_mono(sample_output_path(fn), seg, sr)
            rows.append((fn, root, f0, cand, cents, conf, len(seg) / sr))

    # Local-file intake (gong): full ring kept, one-shot (no f0), explicit routing.
    # Gated by `want("gong")` so `--only=<other>` never rewrites the tracked gong WAVs
    # (a full run or `--local-only` leaves `only` None, so gong still regenerates).
    for out_name, (src_fn, package, end_fade_s) in sorted(LOCAL_SOURCES.items()):
        if not want("gong"):
            continue
        x, sr = read_wav(os.path.join(GONG_SRC, src_fn))
        x = resample(x, sr, OUT_SR)
        sr = OUT_SR
        seg = trim_lead_and_ring(x, sr, PRE_S, end_fade_s)
        output = os.path.join(REPO_ROOT, "crates", package, "samples", out_name)
        write_wav_mono(output, seg, sr)
        rows.append((out_name, None, None, None, None, None, len(seg) / sr))

    _print_sample_rows(rows)


if __name__ == "__main__":
    sys.exit(main())
