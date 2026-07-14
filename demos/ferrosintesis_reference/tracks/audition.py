"""The one slot emitter, and the melodic-track builder that loops it.

A slot auditions a single voice: reset the channel to a virgin state, switch program
(and bank), force the sends dry, play a fixed phrase, let it ring, choke it with
CC120, then tag a single soft (vel 48) note - choked again - so the p dynamic layer
is heard too. Every constant here is shared with verify.py so the oracles check
exactly what this emits.
"""
from __future__ import annotations

import engine as en

import programs as pr

# One channel for the whole melodic walk - isolation is temporal, not per-channel.
CH = 0

SLOT_BEATS = 8.0            # fixed grid: a slot is looked up by index, so keep it regular
TAIL_BEATS = 2.0           # trailing silence after the last slot

# Phrase layout inside a slot that starts at beat t0 (all multiples of 0.1 beat, so a
# jittered note would land off-grid and check_flat would catch it).
_RESET_AT = 0.05
_PROGRAM_AT = 0.30
_SENDS_AT = 0.40           # CC91/93/94 = 0, AFTER the program change (a PC re-derives them)
_ONSET = 1.0
_FIGURE_STEP = 0.6
_LAND_AT = 2.8
_CHOKE_AT = 6.6            # CC120 - the only lever that stops a ringing voice
_SOFT_AT = 7.0             # soft (p) tag: sampled banks have a vel<80 layer (sampler.rs)
_SOFT_DUR = 0.5
_CHOKE2_AT = 7.8           # choke the soft tag too, so the next slot starts clean

# Fixed velocities per gesture (jv=0, so these are exact - check_flat relies on it).
VEL = {pr.SUSTAIN: 96, pr.CHORD: 96, pr.STRUCK: 104, pr.ONESHOT: 112}
SOFT_VEL = 48              # under the sampler's vel>=80 f/p split - audition the p layer
VELS = set(VEL.values()) | {SOFT_VEL}

# Rising figure + landing, as semitone offsets from the slot root.
_FIGURE = (0, 4, 7)
_CHORD = (0, 4, 7)


def dry_sends(sc: en.Score, ch: int, beat: float) -> None:
    """Force reverb/chorus/echo off. Must be authored AFTER a program change, which
    re-derives NON-ZERO chorus/echo defaults from fx_profile (engine.rs:1349)."""
    for num in (91, 93, 94):
        sc.cc(ch, num, 0, beat)


def _root(register: tuple[int, int]) -> int:
    lo, hi = register
    return max(lo, min(hi - 7, lo + (hi - lo - 7) // 2))


def slot_reset(sc: en.Score, ch: int, beat: float) -> None:
    """Return the channel to a VIRGIN state - unlike engine.reset_controls, this omits
    CC70, CC71 and CC74, which would author a controller and stop the raw voice being
    raw: 71/74 instantiate the wah filter (engine.rs:1286), and CC70 - at ANY value,
    including 0 - latches vowel_authored (engine.rs:1319), pinning every choir slot to
    the closed "mm" vowel (HLD 2.2 B2). Bank is cleared to 0 explicitly (CC121 never
    clears it)."""
    sc.bend(ch, 0.0, beat)
    sc.cc(ch, 0, 0, beat)                     # leave any alt bank
    for num in (64, 65, 66, 67, 68):
        sc.cc(ch, num, 0, beat)
    sc.aftertouch(ch, 0, beat)


def emit_slot(sc: en.Score, slot: pr.Slot, t0: float) -> None:
    ch = CH
    sc.marker(t0, slot.label)
    slot_reset(sc, ch, t0 + _RESET_AT)
    sc.program(ch, slot.program, t0 + _PROGRAM_AT)
    if slot.alt:
        sc.cc(ch, 0, 1, t0 + _PROGRAM_AT + 0.02)   # select alt bank after the PC
    dry_sends(sc, ch, t0 + _SENDS_AT)
    vel = VEL[slot.gesture]
    root = _root(slot.register)
    if slot.gesture == pr.ONESHOT:
        sc.note(ch, root, t0 + _ONSET, 3.0, vel, jt=0, jv=0)
    else:
        for i, off in enumerate(_FIGURE):
            sc.note(ch, root + off, t0 + _ONSET + i * _FIGURE_STEP, 0.5, vel, jt=0, jv=0)
        if slot.gesture in (pr.STRUCK, pr.CHORD):
            for off in _CHORD:
                sc.note(ch, root + off, t0 + _LAND_AT, 3.2, vel, jt=0, jv=0)
        else:  # SUSTAIN
            sc.note(ch, root + 7, t0 + _LAND_AT, 3.2, vel, jt=0, jv=0)
    sc.cc(ch, 120, 0, t0 + _CHOKE_AT)               # All Sound Off - choke the tail
    # Soft tag: one p-layer root note (vel 48), then choke again. Without it every
    # sampled bank is only ever heard on its forte layer (HLD 2.14 item 4).
    sc.note(ch, root, t0 + _SOFT_AT, _SOFT_DUR, SOFT_VEL, jt=0, jv=0)
    sc.cc(ch, 120, 0, t0 + _CHOKE2_AT)


def onset_beat(index: int) -> float:
    return index * SLOT_BEATS + _ONSET


def track_beats(n_slots: int) -> float:
    return n_slots * SLOT_BEATS + TAIL_BEATS


def build_melodic(sc: en.Score, slots: list[pr.Slot]) -> None:
    sc.channel(CH, "audition", program=None, volume=110, pan=64, reverb=0, chorus=0, echo=0)
    for i, slot in enumerate(slots):
        emit_slot(sc, slot, i * SLOT_BEATS)
