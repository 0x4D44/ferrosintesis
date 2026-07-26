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
import json
import math
import os
import re
import shutil
import socket
import statistics
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
# RETIRED (2026.07.26) — deliberately NOT merged into SOURCES any more, so no bake
# writes these eight overlays into any crate. Nothing in ferrosintesis loads them (the
# sampled kit in `ferrosintesis-samples-drumkit` superseded the overlay path), so
# ~919 KiB of `include_bytes!` payload was shipping in every binary and in the published
# `-orchestral` package for nothing. The baked WAVs now live in
# `tools/ferrosintesis-samples/retired-drum-overlays/` — see that directory's README.
#
# The table is KEPT, not deleted: it is the upstream pin for files we still hold, and
# `drum_crash1_ff_rr1.wav` is the real-cymbal measurement reference behind the shipped
# MetalPlate model. It is kept *inert* rather than retargeted at the archive directory
# because the trim/fade path has changed since these were baked (see `old_trim` in
# test_prepare.py), so a re-bake would NOT reproduce the archived bytes — it would
# quietly overwrite the calibration evidence with something else. Git history, not this
# table, is the integrity record for what is committed. `KEEP_FILE` below keeps their
# per-file trim recipe for the same documentary reason.
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
PIANO_ZONE_NOTES = ("C2", "G2", "C3", "G3", "C4", "G4", "C5", "G5", "C6")
PIANO_ZONE_MIDI = dict(zip(PIANO_ZONE_NOTES, (36, 43, 48, 55, 60, 67, 72, 79, 84)))
PIANO_SINGLE_TAKE_CELLS = frozenset({("C2", "pp"), ("G2", "pp")})


def piano_take_names(note, dynamic):
    """Return the real output takes available for one upright-piano cell."""
    first = f"piano_{note}_{dynamic}.wav"
    if (note, dynamic) in PIANO_SINGLE_TAKE_CELLS:
        return (first,)
    return (first, f"piano_{note}_{dynamic}_rr2.wav")

SOURCES = {
    f"violin_{n}_{d}.wav": f"{BASE}/Strings/Solo%20Violin/Arco%20Vib/LLVln_ArcoVib_{n}_{d}.wav"
    for n in ("G3", "E4", "C5", "G5", "C6", "E6")
    for d in ("f", "p")
} | {
    f"flute_{n}.wav": f"{BASE}/Woodwinds/Flute/susvib/LDFlute_susvib_{n}_v1_1.wav"
    for n in ("C4", "A4", "E5", "A5", "C6")
} | {
    f"piano_{n}_{d}.wav": f"{BASE}/Keys/Upright%20Nr1/UR1_{n}_{d}_RR1.wav"
    for n in PIANO_ZONE_NOTES
    for d in ("pp", "mf", "f")
} | {
    # The pinned VSCO revision has no pp RR2 for C2/G2. Those cells are
    # deliberately single-take instead of manufacturing duplicate output files.
    f"piano_{n}_{d}_rr2.wav": f"{BASE}/Keys/Upright%20Nr1/UR1_{n}_{d}_RR2.wav"
    for n in PIANO_ZONE_NOTES
    for d in ("pp", "mf", "f")
    if (n, d) not in PIANO_SINGLE_TAKE_CELLS
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
}
# NB: `DRUM_SOURCES` used to be merged in here. It is retired — see its comment above.

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

# Electric bass (GM 33 finger / 34 pick, + 35 fretless riding finger) — FreePats "Clean
# Electric Bass" (electric-bass-YR), a real Yamaha RBX recorded by Andrea Biasior, CC0 1.0
# (LICENSE.txt inside each archive). MM-BUG-KILN-00016. Two separate SFZ+WAV archives —
# FingerBassYR (GM33) and PickedBassYR (GM34) — pinned by SHA-256, extracted with 7z. The
# sample carries the finger/pick attack; the Pluck model keeps the decay (0.9 s keep). The
# SFZ `key=` fields give the exact pitch (finger E1..D#2 = MIDI 28..39; pick E1..E2 = 28..40),
# so dest names use the SFZ pitch and roots are re-measured near it. Whole-tone-spaced zone
# subset (max repitch ±1 st). Low bass → 2f-strong (per-note cap). Output → the new CC0
# -bass crate.
EBASS_FINGER_URL = (
    "https://github.com/freepats/electric-bass-YR/releases/download/2019-09-30/"
    "FingerBassYR-SFZ+WAV-20190930.7z"
)
EBASS_FINGER_SHA256 = "7a8075f8560c0f397283b221e35139473a2517a6fc427beed4f3fffa0619333d"
EBASS_PICK_URL = (
    "https://github.com/freepats/electric-bass-YR/releases/download/2019-09-30/"
    "PickedBassYR-SFZ+WAV-20190930.7z"
)
EBASS_PICK_SHA256 = "ba301f87e5e677d486d0c112950006531523479e54b891aef21dc71b754a0e3a"
_FB_MEMBER = "FingerBassYR SFZ+WAV-20190930/samples/finger"
_PB_MEMBER = "PickedBassYR SFZ+WAV-20190930/samples/pick"
# (dest sounding pitch, source note-name in the archive)
_FINGERBASS_ZONES = [
    ("E1", "E"), ("F#1", "F#"), ("G#1", "G#"), ("A#1", "A#"), ("C2", "C"), ("D2", "D"),
]
_PICKBASS_ZONES = [
    ("E1", "E"), ("F#1", "F#"), ("G#1", "G#"), ("A#1", "A#"), ("C2", "C"), ("D2", "D"),
    ("E2", "E2"),
]
FINGERBASS_SOURCES = {
    f"fingerbass_{d}.wav": f"{_FB_MEMBER}/{s}.wav" for d, s in _FINGERBASS_ZONES
}
PICKBASS_SOURCES = {
    f"pickbass_{d}.wav": f"{_PB_MEMBER}/{s}.wav" for d, s in _PICKBASS_ZONES
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

# Solo cello (GM 42) onset — Karoryfer x bigcat "Bigcat Cello" arco sustains, down-bow
# (CC0-1.0; github.com/sfzinstruments/karoryfer-bigcat.cello, pinned SHA). Replaces the
# repitched cello-SECTION celens onset with a REAL SOLO cellist: one player (no ensemble
# chorus) and a crisp bow-catch (measured onset t50 ~0-55 ms vs the section's ~85 ms slow
# swell, which was ducking the model's own attack). File labels sit ONE OCTAVE BELOW
# sounding pitch (measured: "A1" is a clean 110 Hz A2, no 55 Hz energy) — like the VSCO
# sections — so dest names use the SOUNDING pitch and the URL the octave-down source label.
# Harmonic-rich, spans >1 octave -> in TWO_F_STRONG (per-note ceiling nominal*1.5). Dynamic
# p -> p, f -> f; down-bow ("_d") is the standard detache start. Roots MEASURED at bake.
# Output -> the new CC0 -strings crate.
BIGCAT_REV = "6fd75fbfc1dbb3109bf26220ba1adea46188a18b"
BIGCAT_BASE = (
    f"https://raw.githubusercontent.com/sfzinstruments/karoryfer-bigcat.cello/{BIGCAT_REV}"
)
_CELLO_ZONES = [
    ("C2", "C1"), ("A2", "A1"), ("C3", "C2"), ("A3", "A2"),
    ("C4", "C3"), ("A4", "A3"), ("C5", "C4"), ("F#5", "Gb4"),
]
SOLO_CELLO_URLS = {
    f"cellosolo_{snd}_{d}.wav": f"{BIGCAT_BASE}/Samples/sus/{label}_{d}_d.wav"
    for snd, label in _CELLO_ZONES
    for d in ("p", "f")
}

# Solo double bass (GM 43) onset — VSCO 2 CE "Solo Contrabass" SusNV (NON-vibrato, so the
# model's own vibrato is not doubled), same VSCO_REV pin (CC0). Replaces the repitched
# cello-SECTION celens onset — GM43 was literally a cello section an octave low — with a
# REAL solo double bass (correct body radiation, slower/noisier speech, low-string growl).
# Labels sit ONE OCTAVE BELOW sounding pitch (measured: "C1" is 65.9 Hz C2), like the VSCO
# sections; dest names use SOUNDING pitch. Bowed low strings are strongly 2f-dominant -> in
# TWO_F_STRONG (per-note ceiling nominal*1.5). v1 -> p, v3 -> f. Roots MEASURED at bake.
# Output -> the new CC0 -strings crate.
_DBASS_ZONES = [
    ("E1", "E0"), ("A#1", "A#0"), ("E2", "E1"), ("A2", "A1"),
    ("C#3", "C#2"), ("E3", "E2"), ("G#3", "G#2"), ("B3", "B2"),
]
SOLO_DBASS_URLS = {
    f"dbass_{snd}_{d}.wav": (
        f"{BASE}/Strings/Solo%20Contrabass/SusNV/"
        f"BKCtbss_SusNV_{label.replace('#', '%23')}_{v}_rr1.wav"
    )
    for snd, label in _DBASS_ZONES
    for d, v in (("p", "v1"), ("f", "v3"))
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

# Vibraphone (GM 11) — VCSL "Vibraphone" Soft Mallets (CC0, VCSL_REV). MM-BUG-KILN-00015
# batch 2. Struck metal bars: the sample carries the mallet strike + early ring; the
# bell(VIBES) model keeps the settling body + motor tremolo (KEEP_FAM 0.9 s, like the other
# mallets). Soft (yarn) mallets = the classic mellow vibe attack — v2 layer, the louder of
# the two soft takes; the Hard Mallets are the bright/glassy alternative, left as an
# ear-tunable follow-up. Single layer, no motor/tremolo take, so every onset is a clean
# strike. Metal bar → 2f-strong (in TWO_F_STRONG, per-note ceiling nominal*1.5). VCSL
# keyboard labels can sit an octave below sounding pitch, so dest is named by the source
# label for the fetch and the SOUNDING root comes from the MEASURED bake — VERIFY the
# printed roots. Output → -orchestral2 (CC0). No '#' in any zone label.
_VIBES_DIR = "Idiophones/Struck Idiophones/Vibraphone/Soft Mallets"
# F2 DROPPED after measurement: it read 127 Hz / -545 cents at 0.96 conf (the low bar's
# fundamental is weak, so autocorr locked a partial) — same failure as the dropped glock
# zones. The 10 kept zones sound A2 112 .. E5 659 Hz (labels ARE the sounding pitch here);
# LaVoice's +-1 octave repitch covers vibraphone's F3-F6 register with margin.
_VIBES_ZONES = ["A2", "C3", "E3", "G3", "B3", "D4", "F4", "A4", "C5", "E5"]
VIBES_URLS = {
    f"vibes_{n}.wav": (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(_VIBES_DIR)}/"
        f"{urllib.parse.quote(f'Vibes_soft_{n}_v2_rr1_Main')}.wav"
    )
    for n in _VIBES_ZONES
}

# Tubular bells / chimes (GM 14) — VCSL "Tubular Bells 2" (CC0, VCSL_REV). MM-BUG-KILN-00015
# batch 2. Metal tubes: the sample carries the mallet strike + early metallic ring, the
# bell(TUBULAR) model keeps the long ring (KEEP_FAM 0.9 s, like the other struck mallets).
# The v4 (loud) TB_hit take gives a clean, defined strike onset. 11 zones C4..F5 cover the
# GM14 register (60-77) exactly; LaVoice's +-1 octave repitch covers ~C3-F6. Tubular bells
# have a complex partial structure (strike tone vs hum + inharmonic partials), so they are
# in TWO_F_STRONG and the roots are MEASURED at bake — VERIFY the printed roots (drop any
# zone whose measured pitch strays, like the dropped vibes/glock zones). rr suffix varies
# per pitch, so each zone maps an explicit source name. Output → -orchestral2 (CC0).
_TUBULAR_DIR = "Idiophones/Struck Idiophones/Tubular Bells 2"
_TUBULAR_ZONES = [
    ("tubular_C4.wav", "TB_hit_C4_v4_1"),
    ("tubular_D4.wav", "TB_hit_D4_v4_2"),
    ("tubular_E4.wav", "TB_hit_E4_v4_1"),
    ("tubular_F4.wav", "TB_hit_F4_v4_1"),
    ("tubular_G4.wav", "TB_hit_G4_v4_1"),
    ("tubular_A4.wav", "TB_hit_A4_v4_1"),
    ("tubular_B4.wav", "TB_hit_B4_v4_1"),
    ("tubular_C5.wav", "TB_hit_C5_v4_1"),
    ("tubular_D5.wav", "TB_hit_D5_v4_1"),
    # E5/F5 DROPPED after measurement: autocorr locked the HUM tone (~octave below the
    # strike), so the octave-snap set their root an octave low (E5->E4, F5->F4) — they would
    # play an octave flat. The 9 kept zones sound C4 262 .. D5 584 Hz with correct strike-tone
    # roots; D5 repitched up covers the top of the GM14 register (E5/F5).
]
TUBULAR_URLS = {
    dest: (
        f"https://raw.githubusercontent.com/sgossner/VCSL/{VCSL_REV}/"
        f"{urllib.parse.quote(_TUBULAR_DIR)}/{urllib.parse.quote(src)}.wav"
    )
    for dest, src in _TUBULAR_ZONES
}

# Acoustic (upright/double) bass PIZZICATO onset (GM 32) — VSCO 2 CE "Solo Contrabass" Pizz,
# same VSCO_REV pin (CC0), SIBLING of the GM43 arco (dbass) above. MM-BUG-KILN-00016. The
# sample carries the finger-pluck attack + string speech; the Pluck(&UPRIGHT) model keeps the
# decay (0.9 s keep, like the other plucks). Labels sit ONE OCTAVE BELOW sounding pitch (a
# MEASURED fact for this VSCO source — see dbass), so dest names use SOUNDING pitch; roots are
# re-MEASURED at bake (verify, drop octave-mismeasures). Single v1 layer (v1 is the complete
# layer; v3 exists for only 6 pitches). Low bass string → 2f-strong (per-note cap). Output ->
# the CC0 -strings crate (with dbass/cellosolo).
# C#3/E3 (source C#2/E2) DROPPED after measurement: autocorr grabbed a subharmonic (C#3 read
# an octave low at 69 Hz/conf 0.59; E3 read garbage 55 Hz) — the low pizz fundamentals are
# weak, like the dropped vibes/tubular zones. G#2->G#3 confirms the +1-octave convention. The
# 8 kept zones sound E1 41 .. G#3 206 Hz; LaVoice +-1oct covers the GM32 bass register.
_PIZZBASS_ZONES = [
    ("E1", "E0"), ("G1", "G0"), ("A#1", "A#0"), ("C2", "C1"),
    ("E2", "E1"), ("G#2", "G#1"), ("A2", "A1"), ("G#3", "G#2"),
]
PIZZBASS_URLS = {
    f"pizzbass_{snd}.wav": (
        f"{BASE}/Strings/Solo%20Contrabass/Pizz/"
        f"BKCtbss_Pizz_{label.replace('#', '%23')}_v1_rr1.wav"
    )
    for snd, label in _PIZZBASS_ZONES
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

# === RETIRED 2026-07-23 — kept for history only, NOT baked (see the note by the fetch
# dispatch above). The GM 105 banjo is now a real 5-string banjo (samples/banjo/*.opus,
# extracted by banjo_extract.py). The ganjo below was spectrally dull (a guitar-banjo). ===
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
# The loopable chanter inventory (MM-REQ-KILN-00025): every take that meets
# the -14 dB wrap gate (probe 2026-07-21). The archive holds 13 pitches F4-G5
# (`_31`) + 11 `_32` round robins, but D#5/E5/F5 are UNLOOPABLE in either take
# (best wrap -12.6 / -5.3 / +1.3 dB — the takes carry internal level/timbre
# drift no window inside BAGPIPE_LOOP_S dodges), and 6 of the `_32` takes fail
# likewise (G4 -0.1, C#5 -6.8, D#5 -10.4, E5 -6.2, F5 -13.0, F#5 -13.3). What
# remains: 10 RR1 zones (worst gap D5->F#5, ~1.9-semitone max repitch, down
# from ~2.5) + 5 RR2 takes. Do NOT re-add the failures without a better source;
# never weaken the gate. Filenames keep the note token `_`-separated so the
# bake's note parser and the `chanter` family prefix both keep working;
# `_rr2` never matches the note regex.
BAGPIPE_SOURCES = {
    "drone_G2.wav": f"{_BP_MEMBERS}/samples/drone_G2_1.wav",
    "drone_G3.wav": f"{_BP_MEMBERS}/samples/drone_G3_3.wav",
    "chanter_F4.wav": f"{_BP_MEMBERS}/samples/F4_31.wav",
    "chanter_G4.wav": f"{_BP_MEMBERS}/samples/G4_31.wav",
    "chanter_A4.wav": f"{_BP_MEMBERS}/samples/A4_31.wav",
    "chanter_A#4.wav": f"{_BP_MEMBERS}/samples/A#4_31.wav",
    "chanter_B4.wav": f"{_BP_MEMBERS}/samples/B4_31.wav",
    "chanter_C5.wav": f"{_BP_MEMBERS}/samples/C5_31.wav",
    "chanter_C#5.wav": f"{_BP_MEMBERS}/samples/C#5_31.wav",
    "chanter_D5.wav": f"{_BP_MEMBERS}/samples/D5_31.wav",
    "chanter_F#5.wav": f"{_BP_MEMBERS}/samples/F#5_31.wav",
    "chanter_G5.wav": f"{_BP_MEMBERS}/samples/G5_31.wav",
    "chanter_A4_rr2.wav": f"{_BP_MEMBERS}/samples/A4_32.wav",
    "chanter_A#4_rr2.wav": f"{_BP_MEMBERS}/samples/A#4_32.wav",
    "chanter_B4_rr2.wav": f"{_BP_MEMBERS}/samples/B4_32.wav",
    "chanter_C5_rr2.wav": f"{_BP_MEMBERS}/samples/C5_32.wav",
    "chanter_D5_rr2.wav": f"{_BP_MEMBERS}/samples/D5_32.wav",
}
BAGPIPE_SFZ_MEMBER = f"{_BP_MEMBERS}/Bagpipe-20221204.sfz"
# Loop length RANGES (lo, hi) for the search. Short by design: the original 0.4 s
# chanter / 1.5 s drone windows could not avoid the reed's own level and timbre
# drift, and repeated at ~2.5 Hz / 0.7 Hz — squarely in the range the ear counts as
# a periodic click. Under ~0.12 s the repeat sits above ~8 Hz and fuses into the
# timbre instead. The drones are lower, so they need a longer window for the same
# number of pitch periods.
BAGPIPE_LOOP_S = {"drone": (0.08, 0.20), "chanter": (0.06, 0.14)}
# Hard gate on the baked loop: the wrap must inject a discontinuity at least this
# far below the note itself (see `wrap_error_db`). The loops that shipped the
# periodic-click bug measured -11.8 dB (the one good zone) up to +4.8 dB (no
# waveform continuity at all); a corrected search reaches -20 dB or better, so
# this threshold passes every good bake and fails every bad one with margin.
BAGPIPE_MAX_WRAP_DB = -14.0
# Every bagpipe sample is normalized to this RMS at bake; the drone/chanter MIX is
# then set by the per-voice gains in Rust (mirroring the modeled 0.154 : 0.075).
BAGPIPE_TARGET_RMS = 0.18

# GM 0 Acoustic Grand — Salamander Grand Piano V3 (a Yamaha C5 concert grand, AB
# pair), by Alexander Holm, CC BY 3.0. Salamander is GM 0 CC0=2.
# The VSCO upright is GM 0 CC0=1; unlike it, Salamander is a real grand.
# Distributed as a .tar.bz2 — stdlib `tarfile` reads
# bz2 directly (no 7z, unlike the LZMA FreePats archives), so this gets its own
# extraction helper while sharing the pinned-archive cache verifier. 16-bit STEREO 44.1 kHz
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

# --- GM0 alternate grand banks (CC0-selectable audition; see the 2026.07.18 PLN) ---
# VCSL "Grand Piano, Steinway B" (CC0) -> GM0 CC0=3. A warm, intimate vintage
# Steinway, the tonal opposite of the bright Salamander C5. Whole-tone sampled, so
# the grand's C/F# zone pitches are all present; labels are TRUE sounding pitch
# (probed: C2=65.7, C4=262, C6=1050 Hz -> NOT octave-mislabelled like the VCSL
# keyboard/ocarina). 24-bit stereo WAV (read_wav downmixes + decodes). 3 velocity
# layers vl2/vl3/vl4 (pp/mf/f), single round robin -> RR2 is an adjacent velocity
# layer (peak-normalized to 0.9, so same level, harder-strike timbre = real RR
# variation, exactly the Salamander/grand trick that defeats the machine-gun tell).
_VCSL_STEINWAY_BASE = (
    "https://raw.githubusercontent.com/sgossner/VCSL/master/"
    "Chordophones/Zithers/Grand%20Piano%2C%20Steinway%20B/Sus"
)
_STEINWAYB_ZONES = ["C2", "F#2", "C3", "F#3", "C4", "F#4", "C5", "F#5", "C6"]
# dynamic -> (RR1 velocity layer, RR2 velocity layer). vl4 has no higher neighbour,
# so f's RR2 borrows vl3 (a softer strike at the same normalized level).
_STEINWAYB_VEL = {"pp": (2, 3), "mf": (3, 4), "f": (4, 3)}
STEINWAYB_SOURCES = {
    f"steinwayb_{z}_{d}{rr}.wav":
        f"{_VCSL_STEINWAY_BASE}/JHPiano_Sus_Close_{z.replace('#', '%23')}_vl{v}_rr1.wav"
    for z in _STEINWAYB_ZONES
    for d, (v_rr1, v_rr2) in _STEINWAYB_VEL.items()
    for rr, v in (("", v_rr1), ("_rr2", v_rr2))
}

# VCSL "Grand Piano, Kawai" (CC0) -> the GM 1 Bright Acoustic default (not GM0 at
# all). A darker, rounder vintage grand.
# CAUTION: Kawai labels sit ONE OCTAVE BELOW sounding pitch (probed: label C2 -> 131 Hz,
# label C4 -> 525 Hz, label A#3 -> 469 Hz) -- the VCSL keyboard octave trap, UNLIKE the
# Steinway B. So each dest zone (named by SOUNDING pitch) maps to the source file
# labelled one octave DOWN. 16-bit stereo WAV, velocity layers v1..v4. Sampling is
# irregular, so 8 zones from the pitches with full v1..v4 coverage (measured, verified).
_VCSL_KAWAI_BASE = (
    "https://raw.githubusercontent.com/sgossner/VCSL/master/"
    "Chordophones/Zithers/Grand%20Piano%2C%20Kawai/Sustains"
)
# sounding-pitch dest zone -> source file label (one octave down); all have full v1..v4.
# VERIFIED by measurement: a Kawai label sounds one octave ABOVE its nominal (label C1
# -> C2 65 Hz, label A1 -> A2 110 Hz, label A#2 -> A#3 233 Hz). Sounding A3 (220) is not
# reachable from Kawai's sparse A-labels, so A#3 fills that slot.
_KAWAI_ZONE_LABEL = {
    "C2": "C1", "A2": "A1", "C3": "C2", "A#3": "A#2",
    "C4": "C3", "A#4": "A#3", "C5": "C4", "C6": "C5",
}
# dynamic -> (RR1 velocity, RR2 velocity) over v1..v4.
_KAWAI_VEL = {"pp": (1, 2), "mf": (2, 3), "f": (4, 3)}
KAWAI_SOURCES = {
    f"kawai_{zone}_{d}{rr}.wav":
        f"{_VCSL_KAWAI_BASE}/GPiano_sus_{lbl.replace('#', '%23')}_v{v}_rr1_Player.wav"
    for zone, lbl in _KAWAI_ZONE_LABEL.items()
    for d, (v_rr1, v_rr2) in _KAWAI_VEL.items()
    for rr, v in (("", v_rr1), ("_rr2", v_rr2))
}

# Headroom / Intimate Piano (Bengt Nilsson, Yamaha C3), CC-BY 4.0 -> GM0 CC0=4.
# A warm, intimate close-mic C3 studio grand. Distributed as FLAC (ffmpeg-transcoded,
# same precedent as the banjo/sax/drumkit). MIDI-number labels ARE sounding pitch
# (probed: 36->65 Hz C2, 60->262 Hz C4, 84->1050 Hz C6) -- no octave trap. 5 velocity
# LEVELs, single mic set (CLOSE). ATTRIBUTION REQUIRED (CC-BY): credit Bengt Nilsson +
# keep the instrument name (see the crate NOTICE).
HEADROOM_REV = "2a7df3f7252227a3484202c1d61bc1bfe352a971"
HEADROOM_RECIPE_REV = "ffmpeg-pcm-s16le-v1"
_HEADROOM_BASE = (
    "https://raw.githubusercontent.com/sfzinstruments/BengtNilsson.HeadroomPiano/"
    f"{HEADROOM_REV}/Samples"
)
# dest zone -> MIDI note (C/F# every minor third, C2..C6; all multiples of 3 in the set).
_HEADROOM_ZONE_MIDI = {
    "C2": 36, "F#2": 42, "C3": 48, "F#3": 54, "C4": 60,
    "F#4": 66, "C5": 72, "F#5": 78, "C6": 84,
}
# dynamic -> (RR1 LEVEL, RR2 LEVEL) over LEVEL1..5. L5 is loudest; f's RR2 borrows L4.
_HEADROOM_VEL = {"pp": (1, 2), "mf": (3, 4), "f": (5, 4)}
HEADROOM_SOURCES = {
    f"headroom_{z}_{d}{rr}.wav":
        f"{_HEADROOM_BASE}/HEADROOM%20PIANO%20LEVEL{lv}%20CLOSE%20{midi}.flac"
    for z, midi in _HEADROOM_ZONE_MIDI.items()
    for d, (lv_rr1, lv_rr2) in _HEADROOM_VEL.items()
    for rr, lv in (("", lv_rr1), ("_rr2", lv_rr2))
}
# SHA-256 of every unique selected FLAC at HEADROOM_REV. The 54 destination
# names reuse LEVEL4 for two dynamics, so there are 45 authenticated payloads.
_HEADROOM_FLAC_HASHES = {
    (1, 36): "5a3e645a06d7dadea9d7056a414dd425342a00a1e85f46f90f26b2cb5c81d2a1",
    (1, 42): "dcab1158816f06ad97131fec567b759b811e6376634bfc8b4cf9926e73d6158f",
    (1, 48): "3da2e34d41f76fdd437fe77ead5ba58223414c1f9df351494d0357995d27d95a",
    (1, 54): "b1ef3012cdb17ff228b7de35b5d6cf4d6cc090e1cecc3c68539044970e6be8f4",
    (1, 60): "c1c411e534b6e65f127ac2343ddb9c9f8691e649bcae2907acf7e28a4e96678d",
    (1, 66): "e0e6161519b2e5bb40f16212960b2e893e92d6209e79284f96553cd6391fda68",
    (1, 72): "acca9bf965ef0ddf9c4b504b1e1e4fef782f652403b0d20eb345c826decfc5e3",
    (1, 78): "bf2fbd720b33f814599b81d5dc128eea4c69d26a6e1f7c01c8ebf4a084589894",
    (1, 84): "fe0ba98d14653b78f3c2ef10faa8c042e49645797419139454abef72d4438523",
    (2, 36): "910796ba9bf0b6f75ef5cab4b1ae870d9ec38211e2f262b1cc8cf43ceceba0da",
    (2, 42): "e89b613d10dccb14153ff83f3102da2fadd56f32e983572044748ca092c63594",
    (2, 48): "52eaac81dbe6248cb4cd8e504e4c3a355d4419045181c847197f1c7efc92c52a",
    (2, 54): "f21dd28ce50ff445e8adea188005e8cb8ce372d46f1cfbeeeab5abb71be7bbc5",
    (2, 60): "01786069fa402d0d6657f125ffd9a884297980054c8db7ee294a0778f553c17e",
    (2, 66): "06cc6e15851e6e39253743992da5bd46e02c0b08c71303f475d08c647679f9c9",
    (2, 72): "913c48000bdd7344a9769a6670e54524e32ab71f2031f76931ea6d84d4dfb10f",
    (2, 78): "958f25a9da1d247bb11a73a26e66df058c7b230553e4465a2ff79e9f8dedbe78",
    (2, 84): "dd499915381d582edbdcf41450981b5473154d4d5897eecf5d645da759a6cef3",
    (3, 36): "3a905f3d7f57153213027c8c818fbe9f28e1f8d17bf39c267d735d67c411764c",
    (3, 42): "033a2d00715a0dd963412fa8d535f3710899d711f5cff6e2e1b5fc25aeca296b",
    (3, 48): "a256066caf31bee87afa57f54c19d9420a4ff7a0faba34d5f81d3e5ad75df738",
    (3, 54): "eafc6897676982f1fca56d5a2f58707ec1a5439892c014bae128954add61fabe",
    (3, 60): "2ac13b4b386ae4533474f2a9885cf089c090b2bac4842d9efc6eb29ab2b8846d",
    (3, 66): "60af1091563a45f38438a78e2d4238d212137c6ffde05f0ffe13fb2cb1a9b9c0",
    (3, 72): "e82dae78feb8141e7794b0e71b318efbe7c1c2c0ef1fc1889c4378232f276527",
    (3, 78): "39d28d0b927125076f0ece9b948cf0267cd7978095872cbfa5800415bd98b612",
    (3, 84): "f6f89ef9782913c70768eed6d94ee7f137cf1ef3183b7f601e99690e205e635d",
    (4, 36): "3b7fdccdd1c652365c0cec8fb850ea7bb773842de705d0fdcf8abde5aa1ad146",
    (4, 42): "4b87edb58cba4b3a565115c887238a69019d077d8e193db101b76c3084c198bb",
    (4, 48): "f37aac770e89bfd9715c461f8f0d33d0aee1585a925642edf98a688c117f4cbe",
    (4, 54): "e4162c39ecaa39217f1de5e0e498b5618ae4b23fee5d03ad76ed6650ef927dc0",
    (4, 60): "bbfdb70e1a866712d96955ad2c470a70eb89c3ac2a112b7220792bc6dfc885cf",
    (4, 66): "0ee820e070fee44b72cae7871653e86e8f375f58b2c5a689142e5c3c8689b9db",
    (4, 72): "2233c180bbf5974e65223ec6a0b74bc1ed5942c492fea3f9182768fc4229b5ad",
    (4, 78): "6ff81850b415da3912e172bf2bbf164a0986fe8b9d1a6be8819998b5ebded768",
    (4, 84): "bd1e317ad609933c3f208fa3a5ca9bb501cb57cb9d8568105f968c7d7046bbfb",
    (5, 36): "ecaf6688e2d757780b2aee461b6b11b48bb39b85ac285563f9d27fff69f7ef8d",
    (5, 42): "8ed61a1a2df5085ed18d1e710c07c060c9cefee79dc403661447170f8bf634cb",
    (5, 48): "c0776559919c2445da4ec79cf77249e3c194b7a8e0b899cfbcdd878f3f502af3",
    (5, 54): "a0df22bece2c7a3134b6e0f55709d7548b47875e60bd90a23fc4f6da797aab76",
    (5, 60): "3ed66aa66df6e9b275d07f5ba53b63fde8511beba78796ba331c30ef672a8836",
    (5, 66): "25942dfdf2df26a9f6d467c7a6a22f4d6c19be1d0408228221269fde2f3c34db",
    (5, 72): "51fa5c98c0d730e1e2921de2bba68a2407da958386650c87bc100703419e2ae0",
    (5, 78): "b57882fd231c5febee20ab7b0f013c7dd7fe3c77b0a210b015af5a7f569527e2",
    (5, 84): "41b37d094e196ffaf97cb36ba831ab5c1ddcc74bcad6d89aad0317aa1be645a8",
}
HEADROOM_FLAC_SHA256 = {
    f"HEADROOM PIANO LEVEL{level} CLOSE {midi}.flac": digest
    for (level, midi), digest in _HEADROOM_FLAC_HASHES.items()
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
# GM 1 CC0=2: the FULLER MuseScore_General soundfont's grand (MIT, S. Christian
# Collins), distinct from MS Basic above. Its "Grand Piano" preset (0) is a
# velocity-layered multisample across "Piano MF-low/high" + "Piano FF-low/high"
# instruments; we extract the MF tier as a dense single-velocity multisample (the LA
# layer + model carry dynamics). SHA-pinned (the FTP publishes no checksum).
MUSESCORE_GENERAL_URL = (
    "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/"
    "MuseScore_General.sf3"
)
MUSESCORE_GENERAL_SHA256 = (
    "5b85b6c2c61d10b2b91cddd41efcce7b25cd31c8271d511c73afafbef20b6fa3"
)
# GM 1 CC0=1: FreePats YDP Grand (Zenph Yamaha Disklavier Pro / OLPC), CC-BY 3.0 —
# a BRIGHTER, harder-onset Yamaha grand. A .tar.bz2 holding a real SF2 (raw 16-bit PCM,
# NOT SF3/Ogg). One preset "Grand Piano" (program 0) with 5 velocity-layer instruments
# "piano layer 1..5"; we extract the middle layer ("piano layer 3") as a single-velocity
# multisample. SHA-pinned.
YDP_URL = (
    "https://freepats.zenvoid.org/Piano/YDP-GrandPiano/"
    "YDP-GrandPiano-SF2-20160804.tar.bz2"
)
YDP_SHA256 = "d243dc3e182a60df2a16e92828c1821cf3eb5748b45e2e2bdcfa9cf7af056026"
# C/F# every minor third, C2..C6 (MIDI) — same zone grid as the other grands.
YDP_ZONE_MIDI = [36, 42, 48, 54, 60, 66, 72, 78, 84]

# The GM 3 default: FreePats Honky-tonk Piano (Frances Bacon player piano, Piotr Barcz),
# CC0 — a DISTINCTIVE detuned/tack/jangly attack no other bank has. A .7z of per-note
# FLAC (single velocity); extracted via 7z (as the guitar/bagpipe), then ffmpeg-decoded.
HONKYTONK_URL = (
    "https://github.com/freepats/old-piano-FB/releases/download/2020-04-01/"
    "PianoFB-SFZ+FLAC-20200401.7z"
)
HONKYTONK_SHA256 = "da35c93967c421b17f7219c12a37830ffd2b19f54f8a0a71203fc6161b079b45"
_HT_MEMBER_DIR = "PianoFB SFZ+FLAC-20200401/samples"
# 9 zones spanning C2..C6 — F#2/F#4 are absent from the source (SFZ-filled), so F2/F4
# stand in there. All measured (the detuned unisons read ~15 cents off — a tight window).
HONKYTONK_NOTES = ["C2", "F2", "C3", "F#3", "C4", "F4", "C5", "F#5", "C6"]
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
    # GM0 alternate grands: same C2..C6 window as the Salamander grand.
    "steinwayb": (45.0, 2500.0),
    "kawai": (45.0, 2500.0),
    "headroom": (45.0, 2500.0),
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
    # Eastman E1D picked/plucked: same E2 (82.4) … B5 (987.8) span and the same
    # reasoning as steel above — ceiling 1050 clears the top zone's fundamental
    # but stays under its 2nd harmonic (1976).
    "eastpick": (70.0, 1050.0),
    "eastpluck": (70.0, 1050.0),
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
    # vibraphone (VCSL Soft Mallets): sounding F3 175 .. E5/E6. Metal bar (2f-strong) → the
    # per-note cap (nominal*1.5) blocks 2f; this global range only brackets the fundamentals.
    "vibes": (70.0, 1600.0),
    # tubular bells (VCSL TB2): strike tones C4 262 .. F5 698. 2f-strong (complex partials);
    # per-note cap does the work, this range brackets the strike-tone fundamentals.
    "tubular": (200.0, 900.0),
    # solo cello (Bigcat, GM 42): sounding C2 65 .. F#5 740 Hz (labels one octave below
    # sounding). In TWO_F_STRONG -> per-note ceiling nominal*1.5 blocks 2f; this global
    # ceiling only clears the top fundamental.
    "cellosolo": (60.0, 1500.0),
    # solo double bass (VSCO Solo Contrabass, GM 43): sounding E1 41 .. B3 247 Hz. In
    # TWO_F_STRONG -> per-note cap does the work; global ceiling clears the top fundamental.
    "dbass": (38.0, 520.0),
    # acoustic bass pizzicato (VSCO Solo Contrabass Pizz): sounding E1 41 .. G#3 208, like
    # dbass. In TWO_F_STRONG -> per-note cap; global ceiling clears the top fundamental.
    "pizzbass": (38.0, 520.0),
    # electric bass (FreePats RBX): sounding E1 41 .. E2 82. In TWO_F_STRONG → per-note cap;
    # global ceiling clears the top fundamental.
    "fingerbass": (36.0, 100.0),
    "pickbass": (36.0, 100.0),
    # Freesound onsets: rhodes E1 41..C6 1047; dulcimer ~C4 262..D5 587; music box E5 659..C7
    # 2093. All in TWO_F_STRONG (per-note cap) — Rhodes tine + struck dulcimer + comb music box
    # are 2f-heavy — so the octave-snap corrects any label-octave slip (esp. the guessed dulcimer).
    "rhodes": (35.0, 1200.0),
    "dulcimer": (200.0, 800.0),
    "musicbox": (600.0, 2400.0),
    # Owner-recorded mandolin: G3 (~196 Hz) open to E6 (~1328 Hz) at the 12th fret.
    # Also in TWO_F_STRONG below — the bank spans nearly three octaves and a mandolin's
    # low fundamentals are weak (a small body radiates them poorly), so a single fixed
    # ceiling cannot separate f0 from 2f on the low zones.
    "mandolin": (170.0, 1450.0),
}
# Families whose recordings are 2f-DOMINANT (autocorr grabs the 2nd harmonic if the
# ceiling admits it) AND span more than an octave, so a single fixed F0 ceiling can't
# separate the fundamental from 2f. For these, main() caps the ceiling per-note at
# label×1.5. (The ocarina avoids this list by keeping its zone span under one octave.)
TWO_F_STRONG = frozenset(("recorder", "banjo", "viola", "marimba", "xylo", "glock",
                          "vibes", "tubular", "cellosolo", "dbass", "pizzbass",
                          "fingerbass", "pickbass",
                          "rhodes", "dulcimer", "musicbox", "mandolin"))
# the piano has no expressive sustain to preserve: keep much more of the
# real recording and let the model take only the long tail
# plucks decay — keep more real body than the 0.62 s default (HLD §3)
KEEP_FAM = {
    "piano": (1.8, 0.6),
    # grand: keep a long body like the upright (the sample carries the note), but
    # 1.5 s rather than 1.8 s holds the standalone -grand crate well under the
    # crates.io 10 MiB limit (54 files, 16-bit mono) with headroom
    "grand": (1.5, 0.6),
    # GM0 alternate grand banks: same 1.5 s body as the Salamander grand.
    "steinwayb": (1.5, 0.6),
    "kawai": (1.5, 0.6),
    "headroom": (1.5, 0.6),
    "nylon": (0.9, 0.30),
    "steel": (0.9, 0.30),
    "eastpick": (0.9, 0.30),
    "eastpluck": (0.9, 0.30),
    "harpsi": (0.9, 0.30),
    "harp": (0.9, 0.30),
    "timpani": (0.9, 0.30),
    "banjo": (0.9, 0.30),
    "marimba": (0.9, 0.30),
    "xylo": (0.9, 0.30),
    "glock": (0.9, 0.30),
    "vibes": (0.9, 0.30),
    "tubular": (0.9, 0.30),
    "pizzbass": (0.9, 0.30),
    "fingerbass": (0.9, 0.30),
    "pickbass": (0.9, 0.30),
    "rhodes": (0.9, 0.30),
    "dulcimer": (0.9, 0.30),
    "musicbox": (0.9, 0.30),
    "mandolin": (0.9, 0.30),
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

# Freesound onset sources (GM4 Rhodes CC-BY, GM15 dulcimer CC-BY, GM10 music box CC0) —
# Freesound gates downloads behind a login, so (like gong-src) the DECODED + trimmed source
# notes are committed here, not auto-fetched. ensure_freesound_sources copies them into the
# temp `src` so the main bake loop trims to onset + measures the root. Routed by
# FAMILY_PACKAGE: rhodes/dulcimer → the CC-BY `-ccby` crate; musicbox → the CC0 `-orchestral2`.
# Provenance (exact pack IDs/SHAs) in crates/ferrosintesis-samples-ccby/PROVENANCE.md.
FREESOUND_SRC = os.path.join(TOOL_DIR, "freesound-src")
# The GM 76 blown bottle is a WHOLE-VOICE loop, not an onset: it is baked by
# `bake_bottle_loop` into its own crate, with its own trim and its own source pin. The
# generic onset loop below would trim it to an attack and route it to `-orchestral`
# (family "bottle" has no FAMILY_PACKAGE entry), so it is excluded from discovery here
# rather than special-cased in five downstream places (MM-BUG-KILN-00065).
BOTTLE_LOOP_SOURCE = "bottle_G3.wav"

FREESOUND_SOURCES = {
    fn: fn
    for fn in (sorted(os.listdir(FREESOUND_SRC)) if os.path.isdir(FREESOUND_SRC) else [])
    if fn.endswith(".wav") and fn != BOTTLE_LOOP_SOURCE
}

# Owner-recorded mandolin onsets (GM 25 steel guitar + bank LSB 96 — the XG Mandolin
# cell; GM itself has no mandolin program). Like gong-src/freesound-src these are not
# fetchable, so the per-note source cuts are committed here already downmixed to mono
# 16-bit 44.1 kHz — exactly what the bake consumes — and ensure_mandolin_sources copies
# them into the temp `src` for the main loop to trim and measure. Ten zones (open + 5th
# fret on all four courses, plus 10th and 12th on the E course) x four ordered
# round-robin takes at one dynamic. Provenance, measured roots, take order and source
# checksums are in
# crates/ferrosintesis-samples-mandolin/PROVENANCE.md.
MANDOLIN_SRC = os.path.join(TOOL_DIR, "mandolin-src")
MANDOLIN_SOURCES = {
    fn: fn
    for fn in (sorted(os.listdir(MANDOLIN_SRC)) if os.path.isdir(MANDOLIN_SRC) else [])
    if fn.endswith(".wav")
}
# Steel-string acoustic (GM 25), FIRST-PARTY alternates — Arthur's own Eastman E1D
# dreadnought, recorded 2026-07-23 and dedicated CC0-1.0. Unlike every other family
# here there is NO URL and NO SHA pin, and that is not an omission: the sources are
# not fetched from a third party at all, they are committed in THIS repo, so git
# history (not a remote digest) is the integrity record — there is no upstream that
# could move under us. The full-length masters live at
# `samples/acoustic-guitar-eastman-e1d/{picked,plucked}.opus`; the per-note bake
# sources under that dir's `zones/` are already PRE-CUT single notes (lossless mono
# 44.1 kHz, target onset near the start) — exactly the shape the Martin `steel_*`
# files arrive in, so they run the SAME one-file-per-zone path (read_wav → resample →
# trim_to_onset → write_wav_mono). No slicing/segmentation happens here.
#
# Two picking styles = two independent banks: `eastpick` (plectrum — brighter, harder
# transient) and `eastpluck` (fingerstyle — rounder). The zone grids differ by one
# pitch each; each is what the style was cleanly recorded at. One take per note — no
# velocity layers, no round robins — so, exactly like nylon/steel, these are single
# flat layers and LaVoice's vel_amp does the dynamic scaling. Bake params mirror steel
# (KEEP_FAM 0.9/0.30, F0_RANGE 70–1050); roots are MEASURED at bake and printed — the
# measured value, not the label, is what belongs in sampler.rs. Output → the CC0
# `-orchestral2` crate (`-orchestral` is at the ~10 MiB crates.io cap).
EASTMAN_SRC = os.path.join(REPO_ROOT, "samples", "acoustic-guitar-eastman-e1d", "zones")
_EASTPICK_ZONES = ("E2", "B2", "E3", "A#3", "E4", "A#4", "F5", "B5")
_EASTPLUCK_ZONES = ("E2", "A#2", "E3", "A#3", "E4", "B4", "F5", "B5")
# dest name -> source filename under EASTMAN_SRC
EASTPICK_SOURCES = {f"eastpick_{n}.wav": f"picked_{n}.wav" for n in _EASTPICK_ZONES}
EASTPLUCK_SOURCES = {f"eastpluck_{n}.wav": f"plucked_{n}.wav" for n in _EASTPLUCK_ZONES}

CORE_FAMILIES = frozenset(("piano", "violin", "flute"))
# Families that live in their OWN sample crate (not core/orchestral) — the grand is
# a ~6.9 MiB CC-BY bank kept separate so core stays under the crates.io 10 MiB cap.
FAMILY_PACKAGE = {
    "grand": "ferrosintesis-samples-grand",
    # GM 76 blown bottle: a whole-voice loop in its own CC0 crate. Both spellings are
    # mapped so a stray onset-style `bottle_*.wav` cannot land in `-orchestral` either
    # (MM-BUG-KILN-00065).
    "bottle": "ferrosintesis-samples-bottle",
    "bottleloop": "ferrosintesis-samples-bottle",
    # GM0 alternate grand banks each get their own crate (attribution/licence
    # isolation, and the crates.io 10 MiB cap): CC0 VCSL Steinway B.
    "steinwayb": "ferrosintesis-samples-vcsl-steinway",
    "kawai": "ferrosintesis-samples-vcsl-kawai",
    "headroom": "ferrosintesis-samples-headroom",
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
    "vibes": "ferrosintesis-samples-orchestral2",
    "tubular": "ferrosintesis-samples-orchestral2",
    # Solo bowed strings (GM 42 cello / GM 43 double bass) — real CC0 soloists in their own
    # crate, replacing the repitched cello-SECTION celens onset.
    "cellosolo": "ferrosintesis-samples-strings",
    "dbass": "ferrosintesis-samples-strings",
    "pizzbass": "ferrosintesis-samples-strings",
    "fingerbass": "ferrosintesis-samples-bass",
    "pickbass": "ferrosintesis-samples-bass",
    "rhodes": "ferrosintesis-samples-ccby",
    "dulcimer": "ferrosintesis-samples-ccby",
    "musicbox": "ferrosintesis-samples-orchestral2",
    # Owner-recorded CC0 mandolin (GM 25 + bank LSB 96) — its own crate, like the
    # other owner-recorded bank (-rain), keeping licence provenance isolated.
    "mandolin": "ferrosintesis-samples-mandolin",
    # First-party CC0 Eastman E1D guitar banks (GM 25 alternates).
    "eastpick": "ferrosintesis-samples-orchestral2",
    "eastpluck": "ferrosintesis-samples-orchestral2",
    # The GM 0 default (CC0=0): Arthur's own Yamaha B1 upright. `_bake_b1upright` direct-writes
    # into this crate (like ydp/honkytonk), so this entry is belt-and-braces — the
    # key is the OUTPUT filename prefix (`b1_normal_C3.wav`.split("_", 1)[0] == "b1"),
    # not the `--only=b1upright` family selector, so `sample_output_path` routes a
    # `b1_*.wav` correctly if it is ever called on one.
    "b1": "ferrosintesis-samples-b1-upright",
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


def sha256_file(path):
    """SHA-256 of a file, read in chunks (these archives are hundreds of MB)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def member_manifest_path(src, url):
    """Where the extracted-member hash manifest for `url`'s archive lives."""
    return os.path.join(src, os.path.basename(url) + ".members.json")


def cached_members_match(src, url, sha256, member_map):
    """Do the cached members provably come from the archive pinned at `sha256`?

    The manifest binds the extracted members to the archive PIN, so a warm cache
    can be trusted without re-fetching hundreds of megabytes. Any doubt — no
    manifest (including every cache written before this existed), a different
    pin, a member missing, altered or truncated — answers False, and the caller
    rebuilds. That is the whole fix for MM-BUG-KILN-00062: the old warm path
    returned on `os.path.exists` alone, so the pinned hash below it was
    unreachable and a stale or altered member was rebaked into the tracked crate
    as if it came from the pinned archive.
    """
    try:
        with open(member_manifest_path(src, url), "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        return False
    if manifest.get("archive_sha256") != sha256:
        return False
    recorded = manifest.get("members") or {}
    if set(recorded) < set(member_map):  # a caller added a member since
        return False
    for fn in member_map:
        path = os.path.join(src, fn)
        if not os.path.exists(path) or sha256_file(path) != recorded.get(fn):
            return False
    return True


def verified_archive_path(src, url, sha256):
    """Return the locally cached archive after verifying its pinned digest.

    A local archive whose digest does not match the pin is removed and re-fetched
    ONCE — the common cause is a truncated or superseded download, and self-healing
    beats failing a rebuild that a `rm` would fix. A second mismatch raises: at that
    point the served bytes disagree with the pin, which is not ours to paper over.
    """
    arc = os.path.join(src, os.path.basename(url))
    for attempt in (1, 2):
        if not os.path.exists(arc):
            print(f"fetching {os.path.basename(arc)} ...", file=sys.stderr)
            fetch(url, arc)
        digest = sha256_file(arc)
        if digest == sha256:
            break
        if attempt == 2:
            raise ValueError(f"{arc}: sha256 {digest} != pinned {sha256}")
        print(f"{os.path.basename(arc)}: sha256 {digest} != pinned — refetching once",
              file=sys.stderr)
        os.remove(arc)
    return arc


def rebuild_archive_cache(src, url, sha256, member_map, extract_subdir):
    """Verify a pinned 7z archive, extract it, and copy its selected members."""
    arc = verified_archive_path(src, url, sha256)
    seven = shutil.which("7z") or r"C:\Program Files\7-Zip\7z.exe"
    ext = os.path.join(src, extract_subdir)
    subprocess.run([seven, "x", "-y", f"-o{ext}", arc], check=True,
                   stdout=subprocess.DEVNULL)
    for fn, member in member_map.items():
        shutil.copyfile(os.path.join(ext, *member.split("/")),
                        os.path.join(src, fn))


def write_member_manifest(src, url, sha256, member_map):
    """Record the pin and each extracted member's hash, so a later run can trust them."""
    manifest = {
        "archive_sha256": sha256,
        "members": {fn: sha256_file(os.path.join(src, fn)) for fn in member_map},
    }
    path = member_manifest_path(src, url)
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def ensure_archive_sources(src, url, sha256, member_map, extract_subdir):
    """Fetch + sha256-verify + 7z-extract an archive, copying members into `src`.

    Generalizes the FreePats fetch: two callers (Spanish guitar, bagpipe) are
    structurally identical — a `.7z` pinned by SHA-256, extracted with 7z (the
    archives use an LZMA filter bsdtar cannot decode), members copied out by a
    dest -> member-path map. Kept to exactly these four params; if a third caller
    ever needs a post-process hook, copy-paste rather than grow this.

    The cache is CONTENT-ADDRESSED: a warm cache is used only when a manifest
    proves its members came from this exact pin (MM-BUG-KILN-00062).
    """
    if cached_members_match(src, url, sha256, member_map):
        return
    rebuild_archive_cache(src, url, sha256, member_map, extract_subdir)
    write_member_manifest(src, url, sha256, member_map)


def ensure_guitar_sources(src):
    """Fetch + verify + extract the pinned FreePats Spanish-guitar archive."""
    ensure_archive_sources(src, SCG_ARCHIVE_URL, SCG_ARCHIVE_SHA256,
                           GUITAR_SOURCES, "scg_extract")


def ensure_ebass_sources(src):
    """Fetch + verify + extract the pinned FreePats electric-bass-YR archives (finger+pick)."""
    ensure_archive_sources(src, EBASS_FINGER_URL, EBASS_FINGER_SHA256,
                           FINGERBASS_SOURCES, "fingerbass_extract")
    ensure_archive_sources(src, EBASS_PICK_URL, EBASS_PICK_SHA256,
                           PICKBASS_SOURCES, "pickbass_extract")


def ensure_bagpipe_sources(src):
    """Fetch + verify + extract the pinned FreePats bagpipe archive (+ its SFZ)."""
    members = dict(BAGPIPE_SOURCES)
    members["bagpipe.sfz"] = BAGPIPE_SFZ_MEMBER
    ensure_archive_sources(src, BAGPIPE_ARCHIVE_URL, BAGPIPE_ARCHIVE_SHA256,
                           members, "bagpipe_extract")


def ensure_direct_sources(src, source_map, label):
    """Fetch each `dest_name -> url` in `source_map` straight to `src/<dest_name>`.

    For GM0 alternate banks distributed as individual raw files (not an archive):
    VCSL etc. Idempotent — skips files already present. The main bake loop then
    reads `src/<dest_name>`, trims, measures the root, and routes it to the crate.
    """
    for fn, url in source_map.items():
        dst = os.path.join(src, fn)
        if not os.path.exists(dst):
            print(f"fetching {label} {fn} ...", file=sys.stderr)
            fetch(url, dst)


def ensure_freesound_sources(src):
    """Copy the committed Freesound onset sources (freesound-src/*.wav) into `src` for the
    main bake loop (they are auth-gated, so committed as source like gong-src, not fetched)."""
    for fn in FREESOUND_SOURCES:
        shutil.copyfile(os.path.join(FREESOUND_SRC, fn), os.path.join(src, fn))


def ensure_mandolin_sources(src):
    """Copy the committed owner-recorded mandolin cuts (mandolin-src/*.wav) into `src`
    for the main bake loop (owner-held recording, nothing to fetch — same intake shape
    as gong-src and freesound-src)."""
    for fn in MANDOLIN_SOURCES:
        shutil.copyfile(os.path.join(MANDOLIN_SRC, fn), os.path.join(src, fn))
def ensure_eastman_sources(src, source_map):
    """Copy the committed Eastman E1D zone WAVs into `src` under their DEST names.

    First-party recordings tracked in this repo (see the EASTMAN block above), so
    there is nothing to fetch and no digest to verify — same local-file intake shape
    as `ensure_freesound_sources` / the gong sources, never `ensure_source`. The main
    bake loop then reads `src/<dest>` and runs the normal trim / measure / route chain.
    """
    for dest, fn in source_map.items():
        shutil.copyfile(os.path.join(EASTMAN_SRC, fn), os.path.join(src, dest))


def validate_pcm16_wav(path):
    """Reject incomplete or non-PCM16 decoded cache entries."""
    with wave.open(path, "rb") as w:
        channels = w.getnchannels()
        width = w.getsampwidth()
        sample_rate = w.getframerate()
        frames = w.getnframes()
        raw = w.readframes(frames)
    if channels not in (1, 2):
        raise ValueError(f"{path}: unsupported channel count {channels}")
    if width != 2:
        raise ValueError(f"{path}: sample width {width} is not PCM16")
    if sample_rate <= 0 or frames <= 0:
        raise ValueError(f"{path}: empty or invalid PCM stream")
    expected = frames * channels * width
    if len(raw) != expected:
        raise ValueError(f"{path}: truncated WAV data ({len(raw)} bytes, expected {expected})")


def decoded_source_manifest_path(wav):
    return wav + ".source.json"


def headroom_cache_path(root=None, source_revision=None, recipe_revision=None):
    """Dedicated cache identity for Headroom source bytes and decode semantics."""
    return os.path.join(
        root or tempfile.gettempdir(),
        "headroom_src",
        source_revision or HEADROOM_REV,
        recipe_revision or HEADROOM_RECIPE_REV,
    )


def decoded_wav_matches(wav, source_sha256, recipe_revision):
    """Does a complete PCM16 WAV match its authenticated source and recipe?"""
    try:
        with open(decoded_source_manifest_path(wav), "r", encoding="utf-8") as f:
            manifest = json.load(f)
        if not isinstance(manifest, dict):
            return False
        if manifest.get("source_sha256") != source_sha256:
            return False
        if manifest.get("recipe_revision") != recipe_revision:
            return False
        if sha256_file(wav) != manifest.get("wav_sha256"):
            return False
        validate_pcm16_wav(wav)
    except (OSError, ValueError, EOFError, wave.Error):
        return False
    return True


def write_decoded_source_manifest(wav, source_sha256, recipe_revision):
    """Atomically bind a decoded WAV to the source bytes and decode recipe."""
    manifest = {
        "recipe_revision": recipe_revision,
        "source_sha256": source_sha256,
        "wav_sha256": sha256_file(wav),
    }
    directory = os.path.dirname(wav)
    fd, tmp = tempfile.mkstemp(
        prefix=os.path.basename(wav) + ".", suffix=".source.json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        os.replace(tmp, decoded_source_manifest_path(wav))
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def ensure_flac_sources(src, source_map, source_sha256, label, recipe_revision):
    """Authenticate FLACs and atomically cache complete PCM16 decodes.

    Source files are cached once by their upstream basename, rather than once per
    destination (Headroom's 54 names reuse 9 of its 45 FLACs). A decoded WAV is
    accepted only when a manifest binds its exact bytes to both the pinned FLAC
    and the decode recipe.
    """
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    for fn, url in source_map.items():
        wav = os.path.join(src, fn)
        source_name = urllib.parse.unquote(os.path.basename(url))
        expected = source_sha256.get(source_name)
        if expected is None:
            raise ValueError(f"{label}: no SHA-256 pin for {source_name}")
        flac = os.path.join(src, source_name)
        if os.path.exists(flac) and sha256_file(flac) != expected:
            print(f"cached {source_name} disagrees with pin; refetching ...",
                  file=sys.stderr)
            os.remove(flac)
        if not os.path.exists(flac):
            print(f"fetching {label} {fn} ...", file=sys.stderr)
            fetch(url, flac)
            actual = sha256_file(flac)
            if actual != expected:
                os.remove(flac)
                raise ValueError(
                    f"{source_name}: sha256 {actual} != pinned {expected}")
        if decoded_wav_matches(wav, expected, recipe_revision):
            continue
        fd, tmp = tempfile.mkstemp(
            prefix=os.path.basename(wav) + ".", suffix=".wav", dir=src)
        os.close(fd)
        try:
            subprocess.run(
                [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                 "-i", flac, "-acodec", "pcm_s16le", tmp],
                check=True,
            )
            validate_pcm16_wav(tmp)
            os.replace(tmp, wav)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        write_decoded_source_manifest(wav, expected, recipe_revision)


def rebuild_salamander_cache(src, url, sha256, member_map):
    """Verify and stage the selected tar members before replacing the warm cache."""
    arc = verified_archive_path(src, url, sha256)
    wanted = {member: fn for fn, member in member_map.items()}
    with tempfile.TemporaryDirectory(prefix=".salamander-", dir=src) as staging:
        found = set()
        with tarfile.open(arc, "r:bz2") as tf:
            for member in tf:
                fn = wanted.get(member.name)
                if fn is None:
                    continue
                if member.name in found or not member.isfile():
                    raise ValueError(
                        f"salamander: invalid archive member {member.name!r}")
                extracted = tf.extractfile(member)
                if extracted is None:
                    raise ValueError(
                        f"salamander: could not extract archive member {member.name!r}")
                staged = os.path.join(staging, fn)
                os.makedirs(os.path.dirname(staged), exist_ok=True)
                with extracted, open(staged, "wb") as out:
                    shutil.copyfileobj(extracted, out)
                found.add(member.name)
        if found != set(wanted):
            raise ValueError(
                f"salamander: extracted {len(found)}/{len(wanted)} members "
                f"(archive layout changed?)")
        for fn in member_map:
            os.replace(os.path.join(staging, fn), os.path.join(src, fn))


def ensure_salamander_sources(src):
    """Fetch + sha256-verify + extract the pinned Salamander Grand Piano V3 subset.

    A sibling of `ensure_archive_sources`, not a caller of it: the Salamander
    archive is a `.tar.bz2` (stdlib `tarfile` decodes bz2 with no 7z), and bz2 is
    not seekable, so we stream the tar ONCE and pull the wanted members in a single
    pass rather than re-opening per file. Extraction is staged before any warm
    member is replaced. A content manifest binds every member to the archive pin.
    """
    if cached_members_match(
            src, SALAMANDER_ARCHIVE_URL, SALAMANDER_ARCHIVE_SHA256, GRAND_SOURCES):
        return
    rebuild_salamander_cache(
        src, SALAMANDER_ARCHIVE_URL, SALAMANDER_ARCHIVE_SHA256, GRAND_SOURCES)
    write_member_manifest(
        src, SALAMANDER_ARCHIVE_URL, SALAMANDER_ARCHIVE_SHA256, GRAND_SOURCES)


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


def wrap_error_db(x, start, length, probe):
    """The PHYSICAL wrap discontinuity, in dB relative to the loop's own RMS.

    After the last sample of the loop, a modulo wrap plays `x[start:start+probe]`
    (the head). What naturally FOLLOWED in the recording is
    `x[start+length:start+length+probe]`. Their difference is exactly the signal
    the wrap injects that the instrument never made — the click. Reported against
    the loop's RMS, so it is a level-independent SNR: -20 dB is inaudible,
    0 dB means the wrap error is as loud as the note, and +3 dB is the
    decorrelation ceiling (two unrelated segments of equal level).

    This is measurable only AT BAKE TIME: it needs the source continuation, which
    the shipped buffer no longer carries. It sees every harmonic, a phase jump and
    a level/timbre step alike — all the things a single-sample seam check misses.
    """
    num = 0.0
    for i in range(probe):
        d = x[start + i] - x[start + length + i]
        num += d * d
    den = 0.0
    for i in range(length):
        v = x[start + i]
        den += v * v
    if den <= 0.0 or num <= 0.0:
        return -99.0
    return 10.0 * math.log10((num / probe) / (den / length))


def _prefix_sums(x):
    """(energy, hf-energy) prefix sums, so any window's RMS and brightness are
    O(1) to evaluate — the search below visits tens of thousands of windows and
    prepare.py is stdlib-only (no numpy), so O(L) per candidate is far too slow."""
    n = len(x)
    cs = [0.0] * (n + 1)
    ch = [0.0] * (n + 1)
    prev = 0.0
    for i in range(n):
        v = x[i]
        cs[i + 1] = cs[i] + v * v
        d = v - prev
        ch[i + 1] = ch[i] + d * d
        prev = v
    return cs, ch


def find_loop(x, sr, search_from, f0, lo_s, hi_s, shortlist=24):
    """Search a sustained recording for the best short loop window.

    Returns `(start, length, wrap_db)`.

    Two stages, because the objective we actually care about (`wrap_error_db`) is
    too costly to evaluate everywhere:

    1. A cheap O(1) cost ranks every candidate window. Lengths are INTEGER
       multiples of the pitch period (a fractional count guarantees the harmonics
       wrap out of phase), each also probed +/-2 samples to absorb error in `f0`.
       Both the start AND the length are searched — the old code fixed the start
       at the SFZ loop point and only moved the endpoint, which is why it could
       never escape a window that straddled a swell in the take.
       Cost terms: seam value and slope (normalised by the body's own p95 step),
       the RMS imbalance between the window's two halves, and its brightness
       imbalance. The last two are what stop a "seam-clean" window from spanning
       the reed's own level/timbre drift — the failure recorded in
       `lessons_learnt.md` for the sax loop, and the dominant defect in the
       chanter G4/D5 zones.
    2. The best `shortlist` candidates are then scored by `wrap_error_db` and the
       winner returned. Ranking by the cheap proxy alone is what shipped the bug:
       for `chanter_G5` the old cost rated the broken loop 11x BETTER than the
       correct integer-period one.
    """
    period = sr / f0
    cs, ch = _prefix_sums(x)

    def energy(a, b):
        return cs[b] - cs[a]

    def hf(a, b):
        return ch[b] - ch[a]

    body = sorted(abs(x[i + 1] - x[i])
                  for i in range(search_from, min(len(x) - 1, search_from + 40000)))
    p95 = body[int(0.95 * (len(body) - 1))] if body else 1e-9
    p95 = max(p95, 1e-12)

    k_lo = max(2, int(math.ceil(lo_s * sr / period)))
    k_hi = max(k_lo, int(hi_s * sr / period))
    step = max(1, int(period / 2))
    cands = []
    for k in range(k_lo, k_hi + 1):
        for length in (int(round(k * period)) + o for o in (-2, -1, 0, 1, 2)):
            if length < 32:
                continue
            last = len(x) - length - int(4 * period) - 2
            for s in range(search_from, last, step):
                j = s + length
                val = abs(x[s] - x[j]) / p95
                slope = abs((x[s + 1] - x[s]) - (x[j] - x[j - 1])) / p95
                h = length // 2
                ea = energy(s, s + h) / h
                eb = energy(s + h, s + length) / (length - h)
                if ea <= 0.0 or eb <= 0.0:
                    continue
                dbal = abs(10.0 * math.log10(ea / eb))
                ba = hf(s, s + h) / (ea * h)
                bb = hf(s + h, s + length) / (eb * (length - h))
                dbright = abs(10.0 * math.log10((ba + 1e-12) / (bb + 1e-12)))
                cands.append((val + slope + 2.0 * dbal + 2.0 * dbright, s, length))
    if not cands:
        raise ValueError(f"no loop candidate in [{lo_s}, {hi_s}]s")
    cands.sort()
    probe = int(4 * period)
    best = None
    for _c, s, length in cands[:shortlist]:
        w = wrap_error_db(x, s, length, probe)
        if best is None or w < best[2]:
            best = (s, length, w)
    return best


def extract_loop(x, sr, loop_start, f0, target_s, target_rms=None,
                 max_wrap_db=None):
    """Emit a SHORT seamless loop region from a sustained sample.

    Unlike `trim_to_onset` (an attack extractor that seeks the onset, fades the
    tail to zero, and peak-normalizes) this keeps the STEADY interior and the
    whole returned buffer loops via a plain modulo wrap.

    `loop_start` is the SFZ's expertly-placed loop entry — trusted as the point
    the ATTACK is over, i.e. the earliest sample the search may consider, not as
    the loop start itself. `find_loop` then searches the whole steady remainder;
    the best window is often seconds later.

    `target_s` is a (lo, hi) length range. It is SHORT by design: a long window
    cannot avoid the reed's own drift, and a loop repeating at ~2.5 Hz is heard as
    a periodic click, while one repeating above ~10 Hz fuses into the timbre.

    Finally DC-remove (the drones carry -35/-41 dB DC) and normalize to a COMMON
    RMS (not per-file peak) so a `nearest()` zone switch on a sustained voice
    doesn't jump in level. Both are constant across the window, so neither
    disturbs the seam the search just optimized.
    """
    lo_s, hi_s = target_s
    if loop_start + int(hi_s * sr) + int(8 * sr / f0) >= len(x):
        raise ValueError(f"source too short for a {hi_s}s loop at {loop_start}")
    start, length, wrap_db = find_loop(x, sr, loop_start, f0, lo_s, hi_s)
    if max_wrap_db is not None and wrap_db > max_wrap_db:
        raise ValueError(
            f"best loop wrap error {wrap_db:.1f} dB exceeds {max_wrap_db:.1f} dB "
            f"(start={start} len={length}) — the take is too variable here")
    seg = x[start:start + length]
    mean = sum(seg) / len(seg)
    seg = [v - mean for v in seg]
    rms = math.sqrt(sum(v * v for v in seg) / len(seg))
    tgt = BAGPIPE_TARGET_RMS if target_rms is None else target_rms
    g = tgt / rms if rms > 0 else 1.0
    return [v * g for v in seg], wrap_db


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


def _biquad_hp(x, sr, fc, q):
    """One RBJ 2nd-order high-pass section (Direct Form I, single forward pass).

    Phase is irrelevant for a piano slice trimmed to its own onset, so one
    forward pass is enough; two of these in series make a 4th-order filter.
    """
    w0 = 2.0 * math.pi * fc / sr
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    b0 = (1.0 + cw) / 2.0
    b1 = -(1.0 + cw)
    b2 = (1.0 + cw) / 2.0
    a0 = 1.0 + alpha
    a1 = -2.0 * cw
    a2 = 1.0 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    out = [0.0] * len(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, v in enumerate(x):
        o = b0 * v + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, v
        y2, y1 = y1, o
        out[i] = o
    return out


# A 4th-order Butterworth is two 2nd-order sections whose poles sit at +/-22.5 deg
# and +/-67.5 deg — i.e. these two section Qs (1/(2*cos(theta))). Cascaded they give
# a maximally-flat passband: -3 dB at fc and just -0.08 dB at C1 (32.7 Hz) for a
# 20 Hz corner, exactly the figure the B1-upright HLD specifies.
_BUTTER4_HP_QS = (0.541196100146197, 1.306562964876377)


def _butter_hp4(x, sr, fc):
    """20 Hz-class 4th-order Butterworth high-pass.

    Kills the DR-05 takes' strong 2-5 Hz infrasonic rumble (peak ~-46 dBFS) and
    any DC before resampling, while leaving the piano body untouched (24 dB/oct,
    so 5 Hz is ~48 dB down from a 20 Hz corner). stdlib math only.
    """
    for q in _BUTTER4_HP_QS:
        x = _biquad_hp(x, sr, fc, q)
    return x


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
    # capture. That is not hypothetical: many measured sources have their onset
    # inside 2 ms, worst among them the Martin steel takes (median onset 8
    # samples, 0.18 ms) which would lose their entire pick attack.
    # Every source begins at near-silence (max |x[0]| over the bank is 0.015),
    # so there is no step to de-click in the first place and shortening the
    # fade cannot introduce one. Capping the fade at `lead` therefore fixes the
    # tight-trim case and is exactly inert for sources with >= 2 ms of lead-in.
    # Pinned by test_fade_in_never_exceeds_available_lead_in and
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


_PIANO_NAME_RE = re.compile(
    r"^piano_(C|G)([2-6])_(pp|mf|f)(?:_(rr2))?\.wav$"
)
_PIANO_MAX_CORRECTION_DB = 13.0
_PIANO_MAX_RATIO_SLOPE_DB_PER_SEMITONE = 0.26
_PIANO_MAX_RAMP_STEP_DB = 4.5
_PIANO_MAX_ADDED_RAMP_STEP_DB = 2.0


def _piano_name_parts(name):
    match = _PIANO_NAME_RE.match(name)
    if match is None:
        raise ValueError(f"not a default-upright sample name: {name}")
    return f"{match.group(1)}{match.group(2)}", match.group(3)


def _rms_window(x, start, end):
    window = x[max(0, start):min(len(x), end)]
    if not window:
        raise ValueError("piano envelope window falls outside the sample")
    return math.sqrt(sum(v * v for v in window) / len(window))


def _piano_onset(x, sr):
    # Anchor onset detection to the untouched hammer window. A conditioner may
    # legitimately raise the body above the source peak; using the whole take's
    # peak would then move the onset threshold even though the onset did not move.
    probe = x[:max(1, int(0.040 * sr))]
    peak = max((abs(v) for v in probe), default=0.0)
    if peak <= 0.0:
        raise ValueError("silent piano sample")
    threshold = 0.03 * peak
    return next(i for i, v in enumerate(x) if abs(v) > threshold)


def piano_envelope_stats(bank, sr):
    """Return attack/body ratio dB, body RMS dB, and onset for piano takes."""
    attack_len = int(0.030 * sr)
    body_start = int(0.140 * sr)
    body_end = int(0.220 * sr)
    stats = {}
    for name, x in bank.items():
        onset = _piano_onset(x, sr)
        attack = _rms_window(x, onset, onset + attack_len)
        body = _rms_window(x, onset + body_start, onset + body_end)
        stats[name] = (
            20.0 * math.log10(max(attack, 1e-12) / max(body, 1e-12)),
            20.0 * math.log10(max(body, 1e-12)),
            onset,
        )
    return stats


def _robust_line(points):
    """Theil-Sen median slope and median intercept for distinct x values."""
    slopes = [
        (yj - yi) / (xj - xi)
        for i, (xi, yi) in enumerate(points)
        for xj, yj in points[i + 1:]
        if xj != xi
    ]
    slope = statistics.median(slopes)
    intercept = statistics.median(y - slope * x for x, y in points)
    return slope, intercept


def _minimax_line(points):
    """Return a gradual line minimizing the largest absolute residual."""
    slopes = {
        (yj - yi) / (xj - xi)
        for i, (xi, yi) in enumerate(points)
        for xj, yj in points[i + 1:]
        if xj != xi
    }
    if not slopes:
        raise ValueError("degenerate piano register trend")
    candidates = []
    for slope in slopes:
        residuals = [y - slope * x for x, y in points]
        low, high = min(residuals), max(residuals)
        candidates.append((high - low, abs(slope), slope, (low + high) / 2.0))
    _, _, slope, _ = min(candidates)
    slope = max(
        -_PIANO_MAX_RATIO_SLOPE_DB_PER_SEMITONE,
        min(_PIANO_MAX_RATIO_SLOPE_DB_PER_SEMITONE, slope),
    )
    residuals = [y - slope * x for x, y in points]
    intercept = (min(residuals) + max(residuals)) / 2.0
    return slope, intercept


def _smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def condition_piano_bank(bank, sr):
    """Match default-upright macro shape and absolute level across the bank."""
    expected = {
        name
        for note in PIANO_ZONE_NOTES
        for dyn in ("pp", "mf", "f")
        for name in piano_take_names(note, dyn)
    }
    if set(bank) != expected:
        missing = sorted(expected - set(bank))
        extra = sorted(set(bank) - expected)
        raise ValueError(
            f"piano conditioner needs the complete 52-take bank; "
            f"missing={missing}, extra={extra}"
        )

    source = {name: list(x) for name, x in bank.items()}
    source_stats = piano_envelope_stats(source, sr)
    ratio_points = [
        (
            PIANO_ZONE_MIDI[note],
            source_stats[name][0],
        )
        for dyn in ("pp", "mf", "f")
        for note in PIANO_ZONE_NOTES
        for name in piano_take_names(note, dyn)
    ]
    ratio_slope, ratio_intercept = _minimax_line(ratio_points)
    ratio_targets = {
        note: ratio_slope * PIANO_ZONE_MIDI[note] + ratio_intercept
        for note in PIANO_ZONE_NOTES
    }

    hold = int(0.040 * sr)
    ramp_end = int(0.140 * sr)
    shaped = {}
    for name, x in source.items():
        note, dyn = _piano_name_parts(name)
        ratio_db, _, onset = source_stats[name]
        correction_db = ratio_db - ratio_targets[note]
        if abs(correction_db) > _PIANO_MAX_CORRECTION_DB:
            raise ValueError(
                f"{name}: {correction_db:+.2f} dB piano-envelope correction exceeds "
                f"the {_PIANO_MAX_CORRECTION_DB:.0f} dB safety limit"
            )
        body_gain = 10.0 ** (correction_db / 20.0)
        log_gain = math.log(max(body_gain, 1e-12))
        y = []
        for i, value in enumerate(x):
            age = i - onset
            if age <= hold:
                weight = 0.0
            elif age < ramp_end:
                weight = _smoothstep((age - hold) / max(1, ramp_end - hold))
            else:
                weight = 1.0
            y.append(value * math.exp(log_gain * weight))

        if correction_db > 0.0:
            attack_end = onset + int(0.150 * sr)
            attack_peak = max(abs(v) for v in y[:attack_end])
            later_peak = max((abs(v) for v in y[attack_end:]), default=0.0)
            if later_peak > attack_peak * 1.000001:
                raise ValueError(
                    f"{name}: requested body gain creates a late peak "
                    f"({later_peak:.4f} > {attack_peak:.4f})"
                )
        shaped[name] = y

    shaped_stats = piano_envelope_stats(shaped, sr)
    level_points = []
    for note in PIANO_ZONE_NOTES:
        levels = [
            shaped_stats[name][1]
            for dyn in ("pp", "mf", "f")
            for name in piano_take_names(note, dyn)
        ]
        level_points.append((PIANO_ZONE_MIDI[note], statistics.median(levels)))
    level_slope, level_intercept = _robust_line(level_points)

    level_scales = {}
    max_peak = 0.0
    for name, x in shaped.items():
        note, _ = _piano_name_parts(name)
        target_db = level_slope * PIANO_ZONE_MIDI[note] + level_intercept
        scale = 10.0 ** ((target_db - shaped_stats[name][1]) / 20.0)
        level_scales[name] = scale
        max_peak = max(max_peak, max(abs(v) for v in x) * scale)
    common_headroom = min(1.0, 0.9 / max(max_peak, 1e-12))

    conditioned = {
        name: [v * level_scales[name] * common_headroom for v in x]
        for name, x in shaped.items()
    }

    ramp_windows = [
        (int(a * sr), int((a + 0.020) * sr))
        for a in (0.040, 0.060, 0.080, 0.100, 0.120)
    ]
    final_stats = piano_envelope_stats(conditioned, sr)
    for name, x in conditioned.items():
        onset = final_stats[name][2]
        levels = [
            20.0 * math.log10(
                max(_rms_window(x, onset + a, onset + b), 1e-12)
            )
            for a, b in ramp_windows
        ]
        source_onset = source_stats[name][2]
        source_levels = [
            20.0 * math.log10(
                max(_rms_window(source[name], source_onset + a, source_onset + b), 1e-12)
            )
            for a, b in ramp_windows
        ]
        out_steps = [b - a for a, b in zip(levels, levels[1:])]
        source_steps = [b - a for a, b in zip(source_levels, source_levels[1:])]
        worst_step = max((abs(step) for step in out_steps), default=0.0)
        worst_added = max(
            (abs(out) - abs(before) for out, before in zip(out_steps, source_steps)),
            default=0.0,
        )
        if (
            worst_step > _PIANO_MAX_RAMP_STEP_DB
            and worst_added > _PIANO_MAX_ADDED_RAMP_STEP_DB
        ):
            raise ValueError(
                f"{name}: conditioner creates a {worst_step:.2f} dB adjacent "
                f"20 ms ramp step ({worst_added:+.2f} dB beyond the source)"
            )
    return conditioned


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
    """Quantize a float mono signal and atomically replace its 16-bit PCM WAV."""
    pcm = struct.pack(f"<{len(seg)}h",
                      *[max(-32768, min(32767, int(v * 32767))) for v in seg])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    part = path + ".part"
    try:
        with wave.open(part, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm)
        os.replace(part, path)
    except Exception:
        if os.path.exists(part):
            os.remove(part)
        raise


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
        seg, wrap_db = extract_loop(x, sr, ls, f0, target_s,
                                    max_wrap_db=BAGPIPE_MAX_WRAP_DB)
        write_wav_mono(sample_output_path(fn), seg, sr)
        rows.append((fn, f0, f0, nominal, 1200 * math.log2(f0 / nominal),
                     wrap_db, len(seg) / sr))
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


def ensure_musescore_general_sf3(src):
    """Fetch + sha256-verify the pinned MuseScore_General soundfont (~38 MB)."""
    path = os.path.join(src, "MuseScore_General.sf3")
    if not os.path.exists(path):
        print("fetching MuseScore_General.sf3 (~38 MB) ...", file=sys.stderr)
        fetch(MUSESCORE_GENERAL_URL, path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if digest != MUSESCORE_GENERAL_SHA256:
        raise ValueError(f"{path}: sha256 {digest} != pinned {MUSESCORE_GENERAL_SHA256}")
    return path


def _bake_musescore_grand(src):
    """Bake the MuseScore_General grand's MF tier as a dense single-velocity
    multisample (GM 1 CC0=2). Resolves 'Piano MF-low' + 'Piano MF-high' by NAME,
    takes one sample per distinct originalPitch in the C2..C6+ range, decodes each Ogg
    (ffmpeg), keeps 1.5 s of body (`trim_to_onset`), and re-measures the root in a
    tight window. Writes `musescoregrand_<pitch>.wav`; returns print rows. Single
    velocity: the LA blend + model carry the dynamics."""
    sf3 = open(ensure_musescore_general_sf3(src), "rb").read()
    assert sf3[0:4] == b"RIFF" and sf3[8:12] == b"sfbk", "not an SF2/SF3 file"

    def u16(b, o):
        return struct.unpack("<H", b[o:o + 2])[0]

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

    smpl_off = walk(*lists[b"sdta"])[b"smpl"][0]
    pdta = walk(*lists[b"pdta"])

    def recs(name, width):
        o, s = pdta[name]
        return [sf3[o + i * width:o + (i + 1) * width] for i in range(s // width)]

    inst, ibag, igen = recs(b"inst", 22), recs(b"ibag", 4), recs(b"igen", 4)
    shdr = recs(b"shdr", 46)

    # one sample zone per distinct root (byte offsets into `smpl`), C2..C6+ range.
    best = {}
    for name in (b"Piano MF-low", b"Piano MF-high"):
        ii = next(i for i, r in enumerate(inst) if r[:20].split(b"\x00")[0] == name)
        for b in range(u16(inst[ii], 20), u16(inst[ii + 1], 20)):
            sid = None
            for g in range(u16(ibag[b], 0), u16(ibag[b + 1], 0)):
                if u16(igen[g], 0) == 53:  # gen 53 = sampleID
                    sid = u16(igen[g], 2)
            if sid is None:
                continue
            h = shdr[sid]
            start, end = struct.unpack("<II", h[20:28])
            root = h[40]  # originalPitch (MIDI) — the trustworthy sounding root
            if 34 <= root <= 88 and root not in best:
                best[root] = (start, end)

    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    out_dir = os.path.join(REPO_ROOT, "crates",
                           "ferrosintesis-samples-musescore-grand", "samples")
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for root in sorted(best):
        start, end = best[root]
        ogg = os.path.join(src, f"msgrand_{root}.ogg")
        wav = os.path.join(src, f"msgrand_{root}.wav")
        with open(ogg, "wb") as f:
            f.write(sf3[smpl_off + start:smpl_off + end])
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", ogg, "-acodec", "pcm_s16le", wav], check=True)
        x, wsr = read_wav(wav)
        if wsr != OUT_SR:
            x = resample(x, wsr, OUT_SR)
            wsr = OUT_SR
        seg = trim_to_onset(x, wsr, 1.5, 0.6)
        nominal = _midi_hz(root)
        f0, conf = measure_f0(seg, wsr, nominal * 0.8, nominal * 1.4)
        cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
        out_name = f"musescoregrand_{_midi_name(root)}.wav"
        write_wav_mono(os.path.join(out_dir, out_name), seg, wsr)
        rows.append((out_name, f0, f0, nominal, cents, conf, len(seg) / wsr))
    return rows


def ensure_ydp_sf2(src):
    """Fetch + sha256-verify the YDP Grand .tar.bz2 and extract its SF2."""
    sf2 = os.path.join(src, "YDP-GrandPiano.sf2")
    if not os.path.exists(sf2):
        arc = os.path.join(src, "ydp.tar.bz2")
        if not os.path.exists(arc):
            print("fetching YDP-GrandPiano SF2 (~36 MB) ...", file=sys.stderr)
            fetch(YDP_URL, arc)
        digest = hashlib.sha256(open(arc, "rb").read()).hexdigest()
        if digest != YDP_SHA256:
            raise ValueError(f"{arc}: sha256 {digest} != pinned {YDP_SHA256}")
        with tarfile.open(arc, "r:bz2") as tf:
            member = next(m for m in tf.getmembers() if m.name.endswith(".sf2"))
            with tf.extractfile(member) as f, open(sf2, "wb") as out:
                out.write(f.read())
    return sf2


def _bake_ydp_grand(src):
    """Bake the YDP Grand's middle velocity layer as a single-velocity multisample
    (GM 1 CC0=1). SF2 raw-PCM: resolves the "piano layer 3" instrument by name,
    extracts the C/F# minor-third zones (`YDP_ZONE_MIDI`) straight from the `smpl`
    chunk (shdr start/end are FRAME offsets — no ffmpeg), keeps 1.5 s of body, and
    re-measures each root. Writes `ydpgrand_<pitch>.wav`; returns print rows."""
    sf2 = open(ensure_ydp_sf2(src), "rb").read()
    assert sf2[0:4] == b"RIFF" and sf2[8:12] == b"sfbk", "not an SF2 file"

    def u16(b, o):
        return struct.unpack("<H", b[o:o + 2])[0]

    lists = {}
    pos = 12
    while pos + 12 <= len(sf2):
        cid = sf2[pos:pos + 4]
        sz = struct.unpack("<I", sf2[pos + 4:pos + 8])[0]
        if cid == b"LIST":
            lists[sf2[pos + 8:pos + 12]] = (pos + 12, sz - 4)
        pos += 8 + sz + (sz & 1)

    def walk(off, size):
        end = off + size
        subs = {}
        p = off
        while p + 8 <= end:
            cid = sf2[p:p + 4]
            sz = struct.unpack("<I", sf2[p + 4:p + 8])[0]
            subs[cid] = (p + 8, sz)
            p += 8 + sz + (sz & 1)
        return subs

    smpl_off = walk(*lists[b"sdta"])[b"smpl"][0]
    pdta = walk(*lists[b"pdta"])

    def recs(name, width):
        o, s = pdta[name]
        return [sf2[o + i * width:o + (i + 1) * width] for i in range(s // width)]

    inst, ibag, igen = recs(b"inst", 22), recs(b"ibag", 4), recs(b"igen", 4)
    shdr = recs(b"shdr", 46)

    # one sample zone per distinct root within "piano layer 3".
    ii = next(i for i, r in enumerate(inst)
              if r[:20].split(b"\x00")[0] == b"piano layer 3")
    by_root = {}
    for b in range(u16(inst[ii], 20), u16(inst[ii + 1], 20)):
        sid = None
        for g in range(u16(ibag[b], 0), u16(ibag[b + 1], 0)):
            if u16(igen[g], 0) == 53:
                sid = u16(igen[g], 2)
        if sid is None:
            continue
        h = shdr[sid]
        start, end = struct.unpack("<II", h[20:28])  # FRAME offsets (SF2 raw PCM)
        root = h[40]
        by_root.setdefault(root, (start, end))

    out_dir = os.path.join(REPO_ROOT, "crates",
                           "ferrosintesis-samples-ydp-grand", "samples")
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for midi in YDP_ZONE_MIDI:
        start, end = by_root[midi]
        pcm = sf2[smpl_off + start * 2:smpl_off + end * 2]
        x = [v / 32768.0 for v in struct.unpack(f"<{len(pcm) // 2}h", pcm)]
        seg = trim_to_onset(x, OUT_SR, 1.5, 0.6)
        nominal = _midi_hz(midi)
        f0, conf = measure_f0(seg, OUT_SR, nominal * 0.8, nominal * 1.4)
        cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
        out_name = f"ydpgrand_{_midi_name(midi)}.wav"
        write_wav_mono(os.path.join(out_dir, out_name), seg, OUT_SR)
        rows.append((out_name, f0, f0, nominal, cents, conf, len(seg) / OUT_SR))
    return rows


def _bake_honkytonk(src):
    """Bake the FreePats honky-tonk player piano as a single-velocity multisample
    (the GM 3 default). 7z-extract the per-note FLACs (as the guitar/bagpipe archives),
    ffmpeg-decode each, keep 1.5 s of body, and measure the (detuned) root in a tight
    window. Writes `honkytonk_<note>.wav`; returns print rows."""
    member_map = {f"htsrc_{n}.flac": f"{_HT_MEMBER_DIR}/{n}.flac"
                  for n in HONKYTONK_NOTES}
    ensure_archive_sources(src, HONKYTONK_URL, HONKYTONK_SHA256,
                           member_map, "honkytonk_extract")
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    out_dir = os.path.join(REPO_ROOT, "crates",
                           "ferrosintesis-samples-honkytonk", "samples")
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for n in HONKYTONK_NOTES:
        flac = os.path.join(src, f"htsrc_{n}.flac")
        wav = os.path.join(src, f"htsrc_{n}.wav")
        subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", flac, "-acodec", "pcm_s16le", wav], check=True)
        x, wsr = read_wav(wav)
        if wsr != OUT_SR:
            x = resample(x, wsr, OUT_SR)
            wsr = OUT_SR
        seg = trim_to_onset(x, wsr, 1.5, 0.6)
        nominal = NOTE_HZ[n]
        f0, conf = measure_f0(seg, wsr, nominal * 0.8, nominal * 1.4)
        cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
        out_name = f"honkytonk_{n}.wav"
        write_wav_mono(os.path.join(out_dir, out_name), seg, wsr)
        rows.append((out_name, f0, f0, nominal, cents, conf, len(seg) / wsr))
    return rows


# The GM 0 default (CC0=0): Arthur's own Yamaha B1 acoustic upright, recorded on a Tascam
# DR-05. The reproducible source of record is the committed Opus archive under
# `samples/b1-upright/`; the raw 24-bit takes are far too large to commit. Each
# take is decoded to a temp WAV named for the b1-slice TAKES table, sliced into
# per-note archival WAVs by that tool (run as a subprocess — the `b1-slice`
# directory name has a hyphen and cannot be imported), then baked here.
B1_OPUS_DIR = os.path.join(REPO_ROOT, "samples", "b1-upright")
# decoded WAV name (matches the slicer's TAKES keys) -> committed opus file
B1_OPUS_TAKES = {
    "DR0000_0195.wav": "DR0000_0195_normal_soft.opus",  # normal then soft pass
    "DR0000_0200.wav": "DR0000_0200_hard.opus",         # hard pass (re-recorded)
}
# Per-take slicer overrides. The top-octave inharmonic detector cannot pitch the
# hard take's B7 strike (a single weak partial under the soundboard knock — it
# reads ~2 octaves low), but B7 sits cleanly between G7 and C8 in the ladder, so
# it is force-assigned by position. Its measured f1 is meaningless, so the bake
# falls back to B7's ET frequency for that one zone's root (see below).
B1_SLICE_OVERRIDES = {
    "DR0000_0200.wav": ["--assign=hard:27:B7"],
}
B1_HPF_HZ = 20.0
# Beyond a semitone the slicer's measured f1 cannot be trusted as a repitch root
# (only the force-assigned B7 exceeds this); fall back to the note's ET frequency.
B1_ROOT_FALLBACK_CENTS = 100.0


def _bake_b1upright(src):
    """Bake Arthur's Yamaha B1 upright as a 2-timbre-layer GM0 default bank (CC0=0).

    Decodes the committed Opus takes, slices them with `tools/b1-slice/slice.py`
    (subprocess), then for every *assigned* slice: a 20 Hz 4th-order Butterworth
    high-pass on the 48 kHz signal, band-limited resample to 44.1 kHz,
    `trim_to_onset` (1.5 s body, 0.6 s fade, per-file 0.9 peak-normalise — the
    same path every alt-bank piano uses), 16-bit mono. Writes
    `b1_<layer>_<note>.wav` (layer = the slicer pass name: soft/normal/hard)
    straight into the crate `samples/` dir, and returns print rows.

    root = the slicer's measured first partial f1 (exact-ET repitch that keeps
    the per-note inharmonicity — the house convention), falling back to the
    note's ET frequency when the measurement lands more than a semitone off
    (only the force-assigned B7)."""
    ropusdec = shutil.which("ropusdec") or "ropusdec"
    slicer = os.path.join(REPO_ROOT, "tools", "b1-slice", "slice.py")
    slice_out = os.path.join(src, "slices")
    os.makedirs(src, exist_ok=True)
    os.makedirs(slice_out, exist_ok=True)
    out_dir = os.path.join(REPO_ROOT, "crates",
                           "ferrosintesis-samples-b1-upright", "samples")
    os.makedirs(out_dir, exist_ok=True)

    manifests = []
    for decoded_name, opus_name in B1_OPUS_TAKES.items():
        opus_path = os.path.join(B1_OPUS_DIR, opus_name)
        wav_path = os.path.join(src, decoded_name)
        subprocess.run([ropusdec, opus_path, "-o", wav_path, "-q"], check=True,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        argv = [sys.executable, slicer, f"--take={decoded_name}",
                f"--src={src}", f"--out={slice_out}", "--no-hash", "--no-extras"]
        argv += B1_SLICE_OVERRIDES.get(decoded_name, [])
        subprocess.run(argv, check=True, stdin=subprocess.DEVNULL)
        mpath = os.path.join(slice_out,
                             os.path.splitext(decoded_name)[0] + ".manifest.json")
        with open(mpath, encoding="utf-8") as f:
            manifests.append(json.load(f))

    rows = []
    for man in manifests:
        for sl in man["slices"]:
            if sl.get("status") != "assigned":
                continue
            layer = sl["pass"]               # soft / normal / hard
            note = sl["assigned_note"]       # e.g. C3 (both ladders are all-natural)
            midi = sl["assigned_midi"]
            x, sr = read_wav(os.path.join(slice_out, sl["file"]))
            x = _butter_hp4(x, sr, B1_HPF_HZ)          # on the 48 kHz signal
            x = resample(x, sr, OUT_SR)
            seg = trim_to_onset(x, OUT_SR, 1.5, 0.6)
            et = _midi_hz(midi)
            f1 = sl["f1_hz"] or 0.0
            cents = 1200.0 * math.log2(f1 / et) if f1 > 0 else 0.0
            root = f1 if (f1 > 0 and abs(cents) <= B1_ROOT_FALLBACK_CENTS) else et
            out_name = f"b1_{layer}_{note}.wav"
            write_wav_mono(os.path.join(out_dir, out_name), seg, OUT_SR)
            rows.append((out_name, root, f1, et, cents,
                         sl.get("pitch_confidence") or 0.0, len(seg) / OUT_SR))
    return rows


def _bake_darkened_grand(_src):
    """GM0 CC0=5: a WARMER Salamander — the committed `-grand` samples with a
    high-shelf cut above ~2 kHz (a one-pole shelf: y = x - g*(x - lowpass(x))). Tests
    whether the maintainer's dislike of the bright Salamander C5 is fixable by EQ
    rather than a new instrument, and is itself a cheap shippable win. Same 54 zones
    and roots as the grand; derives from the CC-BY 3.0 Salamander, so inherits that
    licence. EAR-TUNABLE (this box has no ears): `DARK_SHELF_HZ` / `DARK_CUT_DB`."""
    DARK_SHELF_HZ = 2000.0
    DARK_CUT_DB = -6.0
    grand_dir = os.path.join(REPO_ROOT, "crates",
                             "ferrosintesis-samples-grand", "samples")
    out_dir = os.path.join(REPO_ROOT, "crates",
                           "ferrosintesis-samples-dark-salamander", "samples")
    os.makedirs(out_dir, exist_ok=True)
    source_names = sorted(f for f in os.listdir(grand_dir) if f.endswith(".wav"))
    expected_outputs = {"dark" + fn for fn in source_names}
    unexpected_outputs = sorted(
        fn for fn in os.listdir(out_dir)
        if fn.startswith("darkgrand_")
        and fn.endswith(".wav")
        and fn not in expected_outputs
    )
    if unexpected_outputs:
        raise ValueError(
            "dark-grand output contains unexpected generated WAVs: "
            + ", ".join(unexpected_outputs)
        )
    a = 1.0 - math.exp(-2.0 * math.pi * DARK_SHELF_HZ / OUT_SR)
    g = 1.0 - 10.0 ** (DARK_CUT_DB / 20.0)
    rows = []
    for fn in source_names:
        x, sr = read_wav(os.path.join(grand_dir, fn))  # already mono 16-bit 44.1k
        lp = 0.0
        y = []
        for v in x:
            lp += a * (v - lp)
            y.append(v - g * (v - lp))
        pk = max(abs(v) for v in y) or 1.0
        y = [v * 0.9 / pk for v in y]
        out_name = "dark" + fn  # grand_C2_pp.wav -> darkgrand_C2_pp.wav
        write_wav_mono(os.path.join(out_dir, out_name), y, sr)
        note = next(p for p in fn[:-4].split("_")
                    if p[0] in "ABCDEFG" and p[-1].isdigit())
        nominal = NOTE_HZ[note]
        f0, conf = measure_f0(y, sr, nominal * 0.8, nominal * 1.4)
        cents = 1200 * math.log2(f0 / nominal) if f0 > 0 else 0.0
        rows.append((out_name, f0, f0, nominal, cents, conf, len(y) / sr))
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


# --- GM 76 blown bottle: the whole-voice loop -------------------------------------
#
# MM-BUG-KILN-00065: no checked-in tool emitted the ACTIVE `bottleloop_G3.wav`. The
# generic onset loop would have trimmed the source to an attack and written it to the
# wrong crate, and `--only=bottle` on a clean cache never staged the source at all.
# This is the asset's one owner.
#
# The recipe below was RECOVERED from the committed asset by measurement, not taken
# from the provenance note (which describes a 0.45-2.10 s trim of a 2.0 s source - an
# interval that does not exist). Measured against the committed WAV: the packaged audio
# is the source interval [0.1000 s, 1.7500 s) at gain 0.9/peak, with a short linear
# fade-in and a quadratic fade-out. `bottle_loop_matches_the_committed_asset` pins that,
# so the recipe cannot drift silently.
BOTTLE_LOOP_SRC_SHA256 = "56421959ee1aa62d43fa171b11f7626fa7ef08636abf9a3afed821c8d0e965fd"
BOTTLE_LOOP_OUT = "bottleloop_G3.wav"
BOTTLE_LOOP_TRIM = (4411, 72765)   # (start frame, length) at 44.1 kHz = 0.1000 s, 1.6500 s
BOTTLE_LOOP_FADE_IN = 131          # samples, linear
BOTTLE_LOOP_FADE_OUT = 2647        # samples, quadratic (1 - t)^2
BOTTLE_LOOP_PEAK = 0.9


def bake_bottle_loop(src_dir=FREESOUND_SRC, repo_root=REPO_ROOT, verify_source=True):
    """Bake the GM 76 whole-voice bottle loop from its pinned committed source.

    Returns the quantized 16-bit samples it wrote, so a test can compare them against
    the committed asset without reading the file back.
    """
    source = os.path.join(src_dir, BOTTLE_LOOP_SOURCE)
    if verify_source:
        digest = sha256_file(source)
        if digest != BOTTLE_LOOP_SRC_SHA256:
            raise ValueError(
                f"{source}: sha256 {digest} != pinned {BOTTLE_LOOP_SRC_SHA256} - the "
                f"committed CC0 source changed, so the bake cannot be trusted")
    x, sr = read_wav(source)
    if sr != OUT_SR:
        raise ValueError(f"{source}: {sr} Hz, expected {OUT_SR}")
    start, length = BOTTLE_LOOP_TRIM
    seg = x[start:start + length]
    if len(seg) != length:
        raise ValueError(f"{source}: too short for the {length}-frame bottle trim")
    for i in range(BOTTLE_LOOP_FADE_IN):
        seg[i] *= i / BOTTLE_LOOP_FADE_IN
    for i in range(BOTTLE_LOOP_FADE_OUT):
        j = length - BOTTLE_LOOP_FADE_OUT + i
        t = 1.0 - i / BOTTLE_LOOP_FADE_OUT
        seg[j] *= t * t
    peak = max(abs(v) for v in seg)
    gain = BOTTLE_LOOP_PEAK / peak if peak > 0 else 1.0
    seg = [v * gain for v in seg]
    out = os.path.join(repo_root, "crates", "ferrosintesis-samples-bottle", "samples",
                       BOTTLE_LOOP_OUT)
    write_wav_mono(out, seg, OUT_SR)
    return [max(-32768, min(32767, int(v * 32767))) for v in seg]


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


def _family_selection(args):
    """Return (`local_only`, selected families) for command-line arguments."""
    local_only = "--local-only" in args
    only = None
    for arg in args:
        if arg.startswith("--only="):
            only = set(filter(None, arg.split("=", 1)[1].split(",")))
    if local_only:
        only = {"gong"}
    return local_only, only


def _wants_family(only, family):
    return only is None or family in only


def _validate_headroom_output_inventory(sources=None, repo_root=None):
    """Fail closed when the Headroom package retains an obsolete generated WAV."""
    expected = set(HEADROOM_SOURCES if sources is None else sources)
    root = REPO_ROOT if repo_root is None else repo_root
    out_dir = os.path.dirname(sample_output_path("headroom_.wav", root))
    if not os.path.isdir(out_dir):
        return
    unexpected = sorted(
        name for name in os.listdir(out_dir)
        if name.startswith("headroom_")
        and name.endswith(".wav")
        and name not in expected
    )
    if unexpected:
        raise ValueError(
            "Headroom output contains unexpected generated WAVs: "
            + ", ".join(unexpected)
        )


def _bake_gong_bank():
    """Regenerate the local-source gong bank and return its report rows."""
    rows = []
    for out_name, (src_fn, package, end_fade_s) in sorted(LOCAL_SOURCES.items()):
        x, sr = read_wav(os.path.join(GONG_SRC, src_fn))
        x = resample(x, sr, OUT_SR)
        sr = OUT_SR
        seg = trim_lead_and_ring(x, sr, PRE_S, end_fade_s)
        output = os.path.join(REPO_ROOT, "crates", package, "samples", out_name)
        write_wav_mono(output, seg, sr)
        rows.append((out_name, None, None, None, None, None, len(seg) / sr))
    return rows


def _bake_selected_local_banks(only):
    """Run the selected local-source bank recipes and return their report rows."""
    rows = []
    if _wants_family(only, "gong"):
        rows += _bake_gong_bank()
    if _wants_family(only, "bottle"):
        seg = bake_bottle_loop()
        rows.append((BOTTLE_LOOP_OUT, None, None, None, None, None,
                     len(seg) / OUT_SR))
    return rows


def main():
    socket.setdefaulttimeout(60)
    # `--local-only` skips the fetched full bank (network + rewriting the tracked
    # core/orchestral WAVs) and regenerates ONLY the local gong intake below.
    local_only, only = _family_selection(sys.argv[1:])
    # `--only=fam[,fam2]` regenerates ONLY the named families (by filename prefix),
    # leaving every other tracked WAV untouched and skipping their fetches (incl. the
    # 7z / SF3 / tarball sources) — used to ADD one instrument without rewriting the
    # whole bank. `fam` is the sample-name prefix: harp, timpani, recorder, ocarina,
    # banjo, sitar, panflute, bottle, shakuhachi, clavinet, chanter (bagpipe), grand, sax,
    # eastpick, eastpluck (the first-party Eastman E1D guitars), …
    def want(fam):
        return _wants_family(only, fam)

    # Reject stale owned assets before fetching a source or writing any selected
    # output. Silently retaining or deleting one can republish a removed sample.
    if want("headroom"):
        _validate_headroom_output_inventory()

    # `--sax-only` bakes ONLY the MTG saxophone LA layer (network + the -sax crate),
    # skipping the slow VSCO fetch/rewrite — fast iteration on the sax bank alone.
    sax_only = "--sax-only" in sys.argv[1:]

    rows = []
    piano_pending = []
    if sax_only:
        sax_src = os.path.join(tempfile.gettempdir(), "mtg_sax_src", MTG_SAX_REV)
        os.makedirs(sax_src, exist_ok=True)
        rows += _bake_mtg_sax(sax_src)
        _print_sample_rows(rows)
        return
    if not local_only:
        src = os.path.join(tempfile.gettempdir(), "vsco2ce_src", VSCO_REV)
        os.makedirs(src, exist_ok=True)
        headroom_src = None
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
        for fn, url in SOLO_CELLO_URLS.items():
            if want("cellosolo"):
                ensure_source(fn, url, src)
        for fn, url in SOLO_DBASS_URLS.items():
            if want("dbass"):
                ensure_source(fn, url, src)
        for fn, url in PIZZBASS_URLS.items():
            if want("pizzbass"):
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
        for fn, url in VIBES_URLS.items():
            if want("vibes"):
                ensure_source(fn, url, src)
        for fn, url in TUBULAR_URLS.items():
            if want("tubular"):
                ensure_source(fn, url, src)
        # NB: the GM 105 banjo is NO LONGER baked here. As of 2026-07-23 it is a real
        # 5-string banjo recorded by Arthur (samples/banjo/*.opus), extracted by the
        # standalone `banjo_extract.py` — NOT the sfzinstruments/ganjo URL fetch below,
        # which is retained only as history. Do not re-enable `ensure_banjo_sources`: it
        # would overwrite the real-banjo WAVs with the dull ganjo ones.
        if want("nylon"):
            ensure_guitar_sources(src)
        if want("fingerbass") or want("pickbass"):
            ensure_ebass_sources(src)
        if want("rhodes") or want("dulcimer") or want("musicbox") or want("bottle"):
            ensure_freesound_sources(src)
        if want("mandolin"):
            ensure_mandolin_sources(src)
        if want("eastpick"):
            ensure_eastman_sources(src, EASTPICK_SOURCES)
        if want("eastpluck"):
            ensure_eastman_sources(src, EASTPLUCK_SOURCES)
        if want("chanter"):
            ensure_bagpipe_sources(src)
        if want("grand"):
            ensure_salamander_sources(src)
        if want("steinwayb"):
            ensure_direct_sources(src, STEINWAYB_SOURCES, "steinwayb")
        if want("kawai"):
            ensure_direct_sources(src, KAWAI_SOURCES, "kawai")
        if want("headroom"):
            headroom_src = headroom_cache_path()
            os.makedirs(headroom_src, exist_ok=True)
            ensure_flac_sources(
                headroom_src, HEADROOM_SOURCES, HEADROOM_FLAC_SHA256,
                "headroom", HEADROOM_RECIPE_REV)

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

        # GM 8 celesta: SF3 struck-bell onset → the MIT `-musescore` crate (same MS Basic
        # source/NOTICE). MM-BUG-KILN-00015 batch 2. A metal-bar keyboard — the sample carries
        # the bright bell strike, the bell(CELESTA) model keeps the ring. Struck → 0.9 s keep.
        # Roots re-measured near the SF3 originalPitch (verify the printed roots).
        if want("celesta"):
            ms_src = os.path.join(tempfile.gettempdir(), "musescore_sf3", MUSESCORE_REV)
            os.makedirs(ms_src, exist_ok=True)
            rows += _bake_sf_onset(
                ms_src, 8, "celesta", "ferrosintesis-samples-musescore", 0.9, 0.24
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

        # GM 1 CC0=2: MuseScore_General grand — own transform (SF3 preset extract
        # + Ogg decode), MF-tier single-velocity multisample to the MIT -musescore-grand crate.
        if want("musescoregrand"):
            msg_src = os.path.join(tempfile.gettempdir(), "musescore_general")
            os.makedirs(msg_src, exist_ok=True)
            rows += _bake_musescore_grand(msg_src)

        # GM0 CC0=5: darkened Salamander — the committed -grand samples, high-shelf
        # cut (warmer). No fetch: derives from the tracked grand crate.
        if want("darkgrand"):
            rows += _bake_darkened_grand(src)

        # GM 1 CC0=1: FreePats YDP Grand — bright Yamaha Disklavier (SF2 raw-PCM
        # extract of the middle velocity layer) to the CC-BY -ydp-grand crate.
        if want("ydpgrand"):
            ydp_src = os.path.join(tempfile.gettempdir(), "ydp_grand")
            os.makedirs(ydp_src, exist_ok=True)
            rows += _bake_ydp_grand(ydp_src)

        # The GM 3 default: FreePats honky-tonk (7z per-note FLAC) -> CC0 -honkytonk crate.
        if want("honkytonk"):
            ht_src = os.path.join(tempfile.gettempdir(), "honkytonk_fb")
            os.makedirs(ht_src, exist_ok=True)
            rows += _bake_honkytonk(ht_src)

        # The GM 0 default (CC0=0): Arthur's own Yamaha B1 upright (first-party DR-05
        # recording) -> the first-party -b1-upright crate. Own transform: decode the
        # committed opus takes, slice them (b1-slice subprocess), 2 timbre layers
        # (normal/hard). No network; the opus archive is the reproducible source.
        if want("b1upright"):
            b1_src = os.path.join(tempfile.gettempdir(), "b1_upright")
            os.makedirs(b1_src, exist_ok=True)
            rows += _bake_b1upright(b1_src)

        # GM 64-67 saxophones: MTG.SoloSax LA layer (own transform: FLAC fetch +
        # ffmpeg decode), cached by MTG rev, output to the separate CC-BY `-sax` crate.
        if want("sax"):
            sax_src = os.path.join(tempfile.gettempdir(), "mtg_sax_src", MTG_SAX_REV)
            os.makedirs(sax_src, exist_ok=True)
            rows += _bake_mtg_sax(sax_src)
        for fn in sorted(
            SOURCES | GUITAR_SOURCES | STEEL_URLS | HARPSICHORD_URLS | HARP_URLS
            | OCARINA_URLS | RECORDER_URLS | TIMPANI_URLS | VIOLA_URLS
            | MARIMBA_URLS | XYLO_URLS | GLOCK_URLS | VIBES_URLS | TUBULAR_URLS
            | SOLO_CELLO_URLS | SOLO_DBASS_URLS | PIZZBASS_URLS
            | FINGERBASS_SOURCES | PICKBASS_SOURCES | FREESOUND_SOURCES
            | MANDOLIN_SOURCES
            | EASTPICK_SOURCES | EASTPLUCK_SOURCES
            | GRAND_SOURCES
            | STEINWAYB_SOURCES | KAWAI_SOURCES | HEADROOM_SOURCES
        ):
            if not want(fn.split("_")[0]):
                continue
            family_src = headroom_src if fn in HEADROOM_SOURCES else src
            x, sr = read_wav(os.path.join(family_src, fn))
            x = resample(x, sr, OUT_SR)
            sr = OUT_SR
            keep_s, fade_s = KEEP_FILE.get(fn, KEEP_FAM.get(fn.split("_")[0], (KEEP_S, FADE_S)))
            seg = trim_to_onset(x, sr, keep_s, fade_s)
            fam = fn.split("_")[0]
            # Unpitched one-shots skip root measurement. Inert since the drum overlays
            # were retired out of SOURCES (see DRUM_SOURCES above); kept because it is
            # the recipe record for the archived files and the hook any future
            # unpitched family would reuse.
            if fn in DRUM_SOURCES:
                root = f0 = cand = cents = conf = None
            else:
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
            row = (fn, root, f0, cand, cents, conf, len(seg) / sr)
            if fam == "piano":
                piano_pending.append((fn, seg, row))
            else:
                write_wav_mono(sample_output_path(fn), seg, sr)
                rows.append(row)

        if piano_pending:
            conditioned = condition_piano_bank(
                {fn: seg for fn, seg, _ in piano_pending}, OUT_SR
            )
            for fn, _, row in piano_pending:
                write_wav_mono(sample_output_path(fn), conditioned[fn], OUT_SR)
                rows.append(row)

    # Local-file recipes: gong one-shots plus the GM 76 whole-voice bottle loop.
    # Family selection keeps `--only=<other>` from rewriting either tracked bank.
    rows += _bake_selected_local_banks(only)

    _print_sample_rows(rows)


if __name__ == "__main__":
    sys.exit(main())
