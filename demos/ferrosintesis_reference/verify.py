"""Structural MIDI oracles for the reference audition.

The showcase's check_arc / check_stereo (and analyze.py's arc + mono-loss) are dropped:
a flat, dry, centred reference must NOT have a dynamic arc or stereo movement. What
matters here is coverage, isolation-friendly authoring, and the traps that would
otherwise render silence. See the HLD section 3.9.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import tempfile

import engine as en

import programs as pr
from tracks import MELODIC
from tracks.audition import CH as MELODIC_CH, VELS
from tracks.effects import CH as EFFECTS_CH, REQUIRED as FX_REQUIRED
from tracks.kit import DRUM_KEYS


def run_all(spec_scores, suite: bool = True):
    results = []
    by_num = {spec.number: (spec, sc) for spec, sc in spec_scores}
    for spec, sc in spec_scores:
        prefix = f"{spec.number:02d} {spec.title}"
        results.append((f"{prefix} structure", check_structure(spec, sc)))
        if spec.number in MELODIC:
            results.append((f"{prefix} flat", check_flat(sc)))
            results.append((f"{prefix} dry", check_dry(sc)))
            results.append((f"{prefix} gap", check_gap(sc)))
            results.append((f"{prefix} registers", check_registers(spec.number, sc)))
    if suite:
        results.append(("coverage: melodic voices", check_coverage_melodic(by_num)))
        results.append(("coverage: alt bank", check_coverage_alt(by_num)))
        results.append(("coverage: drum keys", check_coverage_drums(by_num)))
        results.append(("coverage: effects CCs", check_coverage_effects(by_num)))
    return results


# --- helpers (read the in-memory Score) -----------------------------------------

def note_ons(sc: en.Score, ch: int):
    """(beat, key, vel) for every note-on on ch, ascending."""
    out = []
    for tk, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tk, data[1], data[2]))
    out.sort()
    return [(tk / en.PPQ, key, vel) for tk, key, vel in out]


def cc_events(sc: en.Score, ch: int, cc: int):
    return sorted(
        (tk / en.PPQ, data[2])
        for tk, _prio, data in sc.events.get(ch, [])
        if (data[0] & 0xF0) == 0xB0 and data[1] == cc
    )


def program_events(sc: en.Score, ch: int):
    return sorted(
        (tk / en.PPQ, data[1])
        for tk, _prio, data in sc.events.get(ch, [])
        if (data[0] & 0xF0) == 0xC0
    )


# --- oracles ---------------------------------------------------------------------

def check_structure(spec: en.TrackSpec, sc: en.Score) -> list[str]:
    fails = []
    secs = sc.duration_seconds()
    if not spec.duration_window[0] <= secs <= spec.duration_window[1]:
        fails.append(f"duration {secs:.1f}s outside {spec.duration_window}")
    if sum(len(note_ons(sc, ch)) for ch in sc.events) < 1:
        fails.append("track has no notes")
    data = sc.to_bytes(spec.title)
    en.BUILD_DIR.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mid", dir=en.BUILD_DIR)
    tmp = Path(handle.name)
    handle.write(data)
    handle.close()
    info = en.parse_midi(tmp)
    try:
        tmp.unlink()
    except OSError:
        pass
    if info["division"] != en.PPQ:
        fails.append(f"PPQ {info['division']}, want {en.PPQ}")
    if info["tracks"] != len(sc.events) + 1:
        fails.append(f"{info['tracks']} MIDI tracks, want {len(sc.events) + 1}")
    return fails


def check_flat(sc: en.Score) -> list[str]:
    """No humanisation: every note-on lands on the 0.1-beat grid with a fixed velocity.
    This is the A/B premise - a jittered note would break the voice comparison."""
    fails = []
    grid = en.PPQ // 10
    for tk, _prio, data in sc.events.get(MELODIC_CH, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            if tk % grid != 0:
                fails.append(f"note-on tick {tk} off the 0.1-beat grid (jitter present)")
            if data[2] not in VELS:
                fails.append(f"note-on velocity {data[2]} not a fixed gesture velocity {sorted(VELS)}")
            if len(fails) >= 6:
                return fails
    return fails


def check_dry(sc: en.Score) -> list[str]:
    """Dry means CC91 AND CC93 AND CC94 are authored to 0 after each program change -
    a PC re-derives a NON-ZERO chorus/echo default (engine.rs:1349)."""
    fails = []
    progs = program_events(sc, MELODIC_CH)
    for beat, prog in progs:
        for cc in (91, 93, 94):
            vals = [v for b, v in cc_events(sc, MELODIC_CH, cc) if beat - 1e-6 <= b <= beat + 0.6]
            if 0 not in vals:
                fails.append(f"program change at {beat:.2f} (GM{prog}) not followed by CC{cc}=0")
                if len(fails) >= 6:
                    return fails
                break
    return fails


def check_gap(sc: en.Score) -> list[str]:
    """Every slot's ringing voice is choked (CC120) before the next slot's first note."""
    fails = []
    ons = note_ons(sc, MELODIC_CH)
    chokes = sorted(b for b, v in cc_events(sc, MELODIC_CH, 120))
    # group note-ons into slots by the 8-beat grid
    slots = defaultdict(list)
    for beat, _k, _v in ons:
        slots[int(beat // 8.0)].append(beat)
    for idx in sorted(slots):
        last_on = max(slots[idx])
        next_on = min(slots[idx + 1]) if (idx + 1) in slots else None
        if next_on is None:
            continue
        if not any(last_on - 1e-6 <= c <= next_on + 1e-6 for c in chokes):
            fails.append(f"slot {idx}: no CC120 between {last_on:.2f} and next onset {next_on:.2f}")
            if len(fails) >= 6:
                return fails
    return fails


def _slots_for(num: int) -> list[pr.Slot]:
    lo, hi = MELODIC[num]
    return pr.melodic_slots(lo, hi)


def check_registers(num: int, sc: en.Score) -> list[str]:
    """Every note lands inside its slot's declared register (the sampler-repitch guard;
    sampler.rs keys off the WRITTEN key). Not a claim about sounding pitch.

    This subsumes the HLD's proposed check_la_band: for LA-layered voices the register
    IS the sampled range, and the phrase only spans a 7-semitone figure near its root,
    so a note can never stray the >1 octave from a zone root that drops the LA layer.
    A separate width oracle would just mirror sampler.rs zone tables (rot-prone)."""
    fails = []
    slots = _slots_for(num)
    ons = note_ons(sc, MELODIC_CH)
    # walk slots and their note windows in lockstep (both ascending by construction)
    for i, slot in enumerate(slots):
        lo, hi = slot.register
        t0 = i * 8.0
        window = [k for b, k, _v in ons if t0 - 1e-6 <= b < t0 + 8.0]
        for key in window:
            if not (lo <= key <= hi):
                fails.append(f"{slot.label}: key {key} outside register {slot.register}")
                if len(fails) >= 8:
                    return fails
                break
    return fails


def check_coverage_melodic(by_num) -> list[str]:
    """Every distinct (non-alias) melodic voice appears exactly once, ascending."""
    fails = []
    want = [p for p in range(128) if p not in pr.ALIAS]
    got = []
    for num in sorted(MELODIC):
        if num not in by_num:
            return []  # partial verify (--track); skip suite oracle
        sc = by_num[num][1]
        for beat, prog in program_events(sc, MELODIC_CH):
            # ignore the alt-bank re-statement of the same program and the dry-reset PCs
            got.append((beat, prog))
    # default-bank slots: the first PC of each program in ascending track/beat order
    seen = []
    for _beat, prog in got:
        if not seen or seen[-1] != prog:
            seen.append(prog)
    # collapse consecutive duplicates from alt inlining (prog, prog[alt]) share a number
    deduped = []
    for prog in seen:
        if not deduped or deduped[-1] != prog:
            deduped.append(prog)
    missing = set(want) - set(deduped)
    if missing:
        fails.append(f"missing melodic voices {sorted(missing)}")
    extra = set(deduped) - set(range(128))
    if extra:
        fails.append(f"unexpected programs {sorted(extra)}")
    return fails


def check_coverage_alt(by_num) -> list[str]:
    fails = []
    seen = set()
    for num in sorted(MELODIC):
        if num not in by_num:
            return []
        sc = by_num[num][1]
        # an alt slot authors CC0=1; the program active at that point is the alt program
        progs = program_events(sc, MELODIC_CH)
        for beat, val in cc_events(sc, MELODIC_CH, 0):
            if val == 1:
                active = max((p for b, p in progs if b <= beat + 1e-6), default=None)
                if active is not None:
                    seen.add(active)
    missing = set(pr.ALT_BANK) - seen
    if missing:
        fails.append(f"missing alt-bank voicings {sorted(missing)}")
    return fails


def check_coverage_drums(by_num) -> list[str]:
    fails = []
    if 5 not in by_num:
        return []
    sc = by_num[5][1]
    keys = {k for _b, k, _v in note_ons(sc, 9)}
    missing = set(DRUM_KEYS) - keys
    if missing:
        fails.append(f"missing drum keys {sorted(missing)}")
    return fails


def check_coverage_effects(by_num) -> list[str]:
    fails = []
    if 6 not in by_num:
        return []
    sc = by_num[6][1]
    seen = {cc for cc in FX_REQUIRED if cc_events(sc, EFFECTS_CH, cc)}
    missing = FX_REQUIRED - seen
    if missing:
        fails.append(f"missing effect CCs {sorted(missing)}")
    bends = sum(1 for _tk, _p, d in sc.events.get(EFFECTS_CH, []) if (d[0] & 0xF0) == 0xE0)
    ats = sum(1 for _tk, _p, d in sc.events.get(EFFECTS_CH, []) if (d[0] & 0xF0) == 0xD0 and d[1] > 0)
    if bends < 1:
        fails.append("no pitch-bend demonstrated")
    if ats < 1:
        fails.append("no aftertouch demonstrated")
    return fails
