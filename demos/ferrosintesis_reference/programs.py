#!/usr/bin/env python3
"""programs.py - the data table that drives the reference audition.

Every fact the builder and the oracles need about a GM program lives here, so the
music is a loop over data, not four hand-written tracks. Three ideas only:

  * REGISTER - a (lo, hi) MIDI-key range, one per GM family (16 rows) plus a handful
    of documented overrides. Keeps each voice in its natural range (a tuba at C5
    tells you nothing) and keeps the LA sample layer engaged.
  * GESTURE  - SUSTAIN (figure + held single note), CHORD (figure + held triad, for
    chordal families - organs, ensembles, pads, brass sections), STRUCK (figure +
    triad left to ring) or ONESHOT (single hit whose length is the voice's own
    envelope). Picks the phrase shape.
  * ALIAS    - programs that share one voice factory AND, once dry, one effect
    profile render identically. We audition the canonical one and cross-reference
    the rest in the marker/lyrics index, rather than commit duplicate audio.
    verify.py's check_alias_dispatch re-derives this claim from the `make()` match
    in crates/ferrosintesis/src/voices.rs, so a stale alias fails the gate.

Traps that would otherwise render silence or a wrong pitch are OVERRIDE rows with a
`note`, mirrored from crates/ferrosintesis/src/ (cited inline). See the HLD
(wrk_docs/2026.07.12 - HLD - ferrosintesis reference audition.md) for the why.
"""
from __future__ import annotations

from dataclasses import dataclass, field

SUSTAIN = "sustain"
STRUCK = "struck"
ONESHOT = "oneshot"
CHORD = "chord"

GM_NAMES = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavinet",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone",
    "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)",
    "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics",
    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
    "Violin", "Viola", "Cello", "Contrabass",
    "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
    "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",
    "Trumpet", "Trombone", "Tuba", "Muted Trumpet",
    "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2",
    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax",
    "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute",
    "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass+lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet",
    "Telephone Ring", "Helicopter", "Applause", "Gunshot",
]

# One (register_lo, register_hi, gesture) per GM family of 8, keyed by family start.
FAMILY: dict[int, tuple[int, int, str]] = {
    0:   (48, 84, STRUCK),    # Piano
    8:   (60, 88, STRUCK),    # Chromatic percussion
    16:  (48, 84, CHORD),     # Organ - chordal: land a held triad (HLD 2.14 item 3)
    24:  (45, 76, STRUCK),    # Guitar
    32:  (28, 52, SUSTAIN),   # Bass - single landing; a low triad is mud, not audition
    40:  (48, 79, SUSTAIN),   # Strings / orchestral
    48:  (48, 76, CHORD),     # Ensemble - chordal: land a held triad (HLD 2.14 item 3)
    56:  (48, 72, SUSTAIN),   # Brass (solo; sections 61-63 override to CHORD)
    64:  (52, 79, SUSTAIN),   # Reed
    72:  (67, 91, SUSTAIN),   # Pipe
    80:  (48, 79, SUSTAIN),   # Synth lead
    88:  (48, 76, CHORD),     # Synth pad - chordal: land a held triad (HLD 2.14 item 3)
    96:  (60, 88, STRUCK),    # Synth FX
    104: (48, 79, STRUCK),    # Ethnic
    112: (60, 88, STRUCK),    # Percussive
    120: (60, 60, ONESHOT),   # Sound effects (key ignored)
}

# program -> {register?, gesture?, note?} - documented deviations from the family row.
# Every `note` is a trap verified against crates/ferrosintesis/src/ (cite inline).
OVERRIDE: dict[int, dict] = {
    # Chromatic percussion voice registers (bespoke bodies).
    11: {"register": (53, 89)},                       # Vibraphone: F3-F6 bars, voices.rs:609
    14: {"register": (60, 77)},                       # Tubular Bells: chime partials, voices.rs:583
    15: {"register": (53, 88)},                       # Dulcimer: double-course body 170Hz, voices.rs:1748
    # Guitar
    28: {"register": (40, 64)},                       # Muted: short palm-chug lives low, voices.rs:1489
    31: {"register": (40, 63),
         "note": "sounding pitch != written key (2f below key 64), voices.rs:2083"},
    # Bass - synth basses reach lower
    38: {"register": (28, 55)},
    39: {"register": (28, 55)},
    # Strings / orchestral
    # 42/43: the family row (48,79) put a cello at E3+ and a CONTRABASS at C4 - the
    # alt A/B was then 8/20 semitones apart (HLD 2.14 item 1). Pin both defaults to
    # the instrument's idiomatic range (which the alt slot now inherits): roots land
    # at E3 (cello) / E2 (contrabass), inside the LA zone spans (sampler.rs
    # celens_C1..B3 / celens_C1..D2).
    42: {"register": (40, 72)},                       # Cello: idiomatic range
    43: {"register": (28, 60)},                       # Contrabass: idiomatic range
    45: {"register": (55, 84)},                       # Pizzicato: violin body pluck
    46: {"register": (36, 84), "note": "full-compass harp, no wound split, voices.rs:1673"},
    47: {"register": (36, 53), "gesture": SUSTAIN,
         "note": "single-note landing - a timpani is not chordal (HLD 2.5); "
                 "thump LP fixed 300Hz - not a timpani above ~key62, voices.rs:697"},
    # Ensemble
    55: {"register": (44, 57), "gesture": ONESHOT,
         "note": "one-shot; thump tracks key only over 44-57, voices.rs:5523"},
    # Brass - tuba/trombone sit low; the sections 61-63 are chordal
    57: {"register": (40, 72)},                       # Trombone
    58: {"register": (28, 58)},                       # Tuba: bore 230Hz, voices.rs:6383
    60: {"register": (41, 77)},                       # French Horn
    61: {"gesture": CHORD},                           # Brass Section: land a held triad
    62: {"gesture": CHORD},                           # Synth Brass 1
    63: {"gesture": CHORD},                           # Synth Brass 2
    # Reed - the voice declares a hard `range:` (voices.rs:5652..5798); use it.
    64: {"register": (56, 88)}, 65: {"register": (49, 81)}, 66: {"register": (44, 76)},
    67: {"register": (36, 69)}, 68: {"register": (58, 88)}, 69: {"register": (52, 81)},
    70: {"register": (34, 72)}, 71: {"register": (50, 88)},
    # Pipe - hard `range:` (voices.rs:4528..4687).
    72: {"register": (74, 96)}, 73: {"register": (60, 91)}, 74: {"register": (60, 91)},
    75: {"register": (55, 84)}, 76: {"register": (48, 80)}, 77: {"register": (57, 84)},
    78: {"register": (72, 96)}, 79: {"register": (60, 84)},
    # Bass+lead reaches low
    87: {"register": (36, 72)},
    # Ethnic overrides
    109: {"register": (60, 84), "gesture": SUSTAIN,
          "note": "keys<=54 sound NO chanter; chanter notes ALSO spawn a drone (always polyphonic), engine.rs:1039"},
    110: {"register": (55, 84), "gesture": SUSTAIN},   # Fiddle
    111: {"register": (60, 84), "gesture": SUSTAIN},   # Shanai
    # Percussive - modelled melodic percussion registers. 112/113/116 have a
    # same-instrument set-B ALT bank -- match its register (see check_dual_bank_registers).
    112: {"register": (72, 96)},                       # Tinkle bell: strike bp 7200Hz, voices.rs:741
    113: {"register": (60, 84)},                       # Agogo
    114: {"register": (48, 79)},                       # Steel drum
    116: {"register": (36, 55), "gesture": STRUCK},    # Taiko: boom LP 260Hz, voices.rs:857
    117: {"register": (36, 67), "gesture": STRUCK},    # Melodic tom
    118: {"register": (36, 72), "gesture": STRUCK},    # Synth drum
    119: {"register": (60, 60), "gesture": ONESHOT,
          "note": "key ignored; fixed 1.02s swell, note-off cannot kill it, voices.rs:944"},
}

# program -> canonical program it renders identically to (once dry). Audition the
# canonical, index the rest. Ground truth is the `make()` match in
# crates/ferrosintesis/src/voices.rs: a true alias shares one match arm whose body
# never reads `program` (byte discarded), AND no engine-level per-program insert
# splits the pair (e.g. 29/30 share `Pluck::new(&DRIVE, ..)` but engine.rs:262
# gives them different Drive profiles - NOT aliases). check_alias_dispatch
# (verify.py) re-derives the arm claim mechanically on every --verify.
#
# Regenerated 2026-07-14 (HLD 2.14 item 2). Un-aliased, with the dispatch fact:
#   17->16   percussive organ grew its own drawbars + percussion tap (voices.rs:3494)
#   37->36   split into SLAP (thumb) vs SLAP_POP (bridge pop) presets (voices.rs:8034)
#   51->50   synth_strings() now keys a lush 6-osc variant off program 51 (voices.rs:4067)
#   89-94->88  pad() is per-program since the Stage 2 distinctness work (voices.rs:4509)
#   97/99/103->88, 98/100/102->96, 101->95  the FX family 96-103 is eight distinct
#     Fx::from_spec presets (voices.rs:7633,8169), no longer pads/bells
ALIAS: dict[int, int] = {
    1: 0, 2: 0, 3: 0,  # 0..=3 one arm, one acoustic_piano() + one piano_bank(), voices.rs:7911
}

# Note on the LA sample layer: programs 0, 24, 40, 42, 43, 48, 49, 56-61, 68-73 and 110
# carry a sampled attack (sampler.rs), which silently drops out past ~1 octave from a
# sample-zone root (sampler.rs:815). Their registers above are centred in the sampled
# range; since the phrase only spans a 7-semitone figure near the register root,
# check_registers (notes stay inside the register) already keeps the layer engaged.

# Alt-bank (CC0=1) programs that are a genuinely DIFFERENT voice (not just samples
# pinned off). program -> label. Mirrored from altbank.rs:997.
#
# The alt slot inherits its default twin's register AND gesture (melodic_slots), so
# every A/B is pitch-, velocity- and gesture-matched - a hand-tuned alt register let
# e.g. GM 43 audition C4 vs E2, a 20-semitone rigged A/B (HLD 2.14 item 1).
# check_ab_parity (verify.py) pins this. Voices with their own internal key clamp or
# fold (tam-tam, set B percussion) still get identical WRITTEN keys; the clamp is the
# voice's own character and is noted in the label.
ALT_BANK: dict[int, str] = {
    14:  "tam-tam (folds written keys to its octave, voices.rs:1184)",
    19:  "legacy Leslie church organ",
    29:  "DRIVE_LEAD - sustaining, e-bow hold",
    30:  "DRIVE_LEAD - sustaining, e-bow hold",
    40:  "frozen v0.9 bowed violin",
    41:  "frozen v0.9 bowed viola",
    42:  "frozen v0.9 bowed cello",
    43:  "frozen v0.9 bowed contrabass",
    44:  "frozen v0.9 tremolo",
    45:  "frozen v0.9 pizzicato",
    48:  "frozen v0.9 string ensemble",
    49:  "frozen v0.9 slow strings",
    50:  "frozen v0.9 synth strings",
    52:  "frozen v0.9 choir aahs",
    53:  "frozen v0.9 voice oohs",
    54:  "frozen v0.9 synth voice",
    112: "percussion set B tinkle bell",
    113: "set B agogo (dry, t60 0.15s)",
    114: "set B steel pan",
    115: "set B woodblock (clamp 60-96, voices.rs:1084)",
    116: "set B taiko (clamp 31-55)",
    117: "set B melodic tom (clamp 36-72)",
    118: "set B synth drum (clamp 33-81)",
    119: "set B reverse cymbal - IS key-tracked (clamp 48-72, drums.rs:2239); "
         "auditioned at the default's fixed one-shot key",
}


@dataclass(frozen=True)
class Slot:
    """One audition: a program (optionally on the alt bank) with its phrase shape."""

    program: int
    register: tuple[int, int]
    gesture: str
    alt: bool = False
    note: str | None = None

    @property
    def name(self) -> str:
        return GM_NAMES[self.program]

    @property
    def label(self) -> str:
        bank = " [alt]" if self.alt else ""
        return f"GM {self.program:03d} {self.name}{bank}"


def _resolve(program: int) -> Slot:
    lo, hi, gesture = FAMILY[(program // 8) * 8]
    ov = OVERRIDE.get(program, {})
    register = ov.get("register", (lo, hi))
    return Slot(program, register, ov.get("gesture", gesture), alt=False, note=ov.get("note"))


def melodic_slots(lo: int, hi: int) -> list[Slot]:
    """Ordered audition slots for programs [lo, hi]: each rendered voice, with its
    alt-bank twin inlined immediately after, skipping aliases (indexed elsewhere).
    The alt twin inherits the default's register and gesture so the A/B compares
    timbre at matched pitch, velocity and phrase (check_ab_parity)."""
    out: list[Slot] = []
    for p in range(lo, hi + 1):
        if p in ALIAS:
            continue
        default = _resolve(p)
        out.append(default)
        if p in ALT_BANK:
            out.append(Slot(p, default.register, default.gesture, alt=True, note=ALT_BANK[p]))
    return out


def alias_index() -> list[tuple[int, int]]:
    """(program, canonical) pairs, ascending - for the marker/lyrics cross-reference."""
    return sorted(ALIAS.items())


# Dual-bank programs whose ALT is a genuinely DIFFERENT instrument, so a shared register
# would be wrong. Every other dual-bank program must audition both banks in the SAME
# register - see check_dual_bank_registers().
REGISTER_MAY_DIVERGE = {
    14: "alt is a tam-tam/gong, not tubular bells; it folds to one octave (voices.rs:1184)",
    119: "main ignores the key entirely (fixed 1.02s swell); the alt IS key-tracked",
}


def check_dual_bank_registers() -> list[str]:
    """An A/B must vary ONE thing: the bank. Not the notes.

    Every dual-bank program whose alt is the same instrument must audition both banks in
    the same register, or the listener is comparing pitches rather than voices. This is
    not hypothetical: the contrabass (GM 43) used to inherit the strings family row
    (48, 79) for its main and (28, 60) for its alt -- so the main was auditioned an
    octave-and-a-fourth ABOVE a double bass's compass, exactly where its loop-latency
    pitch bug was worst (-45 cents), while the alt was played in compass. The A/B was
    rigged against the main, and the resulting "the alt sounds better" was half real
    defect and half harness artefact. Twelve of the twenty-four dual-bank rows were
    mismatched like this.

    Returns a list of human-readable failures (empty == good).
    """
    problems: list[str] = []
    for program, (alt_register, _gesture, label) in sorted(ALT_BANK.items()):
        if program in REGISTER_MAY_DIVERGE:
            continue
        main_register = _resolve(program).register
        if main_register != alt_register:
            problems.append(
                f"GM {program:03d} ({GM_NAMES[program]}): the A/B compares DIFFERENT "
                f"REGISTERS - main {main_register} vs alt {alt_register} ({label}). "
                f"Add an OVERRIDE so both banks audition the same notes, or document the "
                f"divergence in REGISTER_MAY_DIVERGE."
            )
    return problems
