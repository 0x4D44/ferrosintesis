"""Structural MIDI oracles for the reference audition.

The showcase's check_arc / check_stereo (and analyze.py's arc + mono-loss) are dropped:
a flat, dry, centred reference must NOT have a dynamic arc or stereo movement. What
matters here is coverage, isolation-friendly authoring, and the traps that would
otherwise render silence. See the HLD section 3.9.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
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
            results.append((f"{prefix} A/B parity", check_ab_parity(spec.number, sc)))
    if suite:
        results.append(("coverage: melodic voices", check_coverage_melodic(by_num)))
        results.append(("coverage: alt bank", check_coverage_alt(by_num)))
        results.append(("coverage: drum keys", check_coverage_drums(by_num)))
        results.append(("coverage: effects CCs", check_coverage_effects(by_num)))
        results.append(("alias vs make() dispatch", check_alias_dispatch()))
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


def check_ab_parity(num: int, sc: en.Score) -> list[str]:
    """Every default/alt program pair is auditioned at the same root key, velocity
    and gesture (HLD 2.14 item 1). Checked on the EMITTED notes, not just the
    tables: the alt slot's note-ons must equal the default twin's, shifted by
    exactly one slot - so a hand-tuned alt register (the 20-semitone GM 43 rigged
    A/B) can never silently return."""
    fails = []
    slots = _slots_for(num)
    ons = note_ons(sc, MELODIC_CH)

    def emitted(idx: int):
        t0 = idx * 8.0
        return [(round(b - t0, 4), k, v) for b, k, v in ons if t0 - 1e-6 <= b < t0 + 8.0 - 1e-6]

    for i, slot in enumerate(slots):
        if not slot.alt:
            continue
        if slot.program in pr.STANDALONE_ALT:
            # a standalone alt is deliberately NOT an A/B (different instrument,
            # own register/gesture) - check_registers still pins its notes
            continue
        if i == 0 or slots[i - 1].program != slot.program or slots[i - 1].alt:
            fails.append(f"{slot.label}: not preceded by its default twin")
            continue
        default = slots[i - 1]
        if (default.register, default.gesture) != (slot.register, slot.gesture):
            fails.append(
                f"{slot.label}: register/gesture {slot.register}/{slot.gesture} != "
                f"default's {default.register}/{default.gesture}"
            )
        if emitted(i - 1) != emitted(i):
            fails.append(f"{slot.label}: emitted notes differ from default twin (unfair A/B)")
        if len(fails) >= 6:
            break
    return fails


# --- ALIAS vs the Rust dispatch ----------------------------------------------------
#
# ALIAS claims "renders byte-identically to the canonical voice once dry". The ground
# truth is the `match program` in voices.rs `make()`: a true alias must share one
# match arm whose body never reads `program` (the byte is discarded). That is
# NECESSARY, not sufficient - the engine can still split a shared arm with a
# per-program insert (needs_drive, engine.rs:262, gives 29/30 different Drive
# profiles despite one `Pluck::new(&DRIVE, ..)` arm) - so ALIAS stays curated, but a
# STALE entry (dispatch split under it, like the 2026-07 pad/FX/organ/slap splits)
# now fails mechanically instead of rotting in a hand table.

_VOICES_RS = Path(__file__).resolve().parents[2] / "crates" / "ferrosintesis" / "src" / "voices.rs"


def _make_arms(src: str) -> list[tuple[str, str]]:
    """(pattern, body) for each arm of `make()`'s `match program`, in order."""
    start = src.index("pub fn make(")
    start = src.index("match program {", start)
    text = re.sub(r"//[^\n]*", "", src[src.index("{", start) + 1:])  # comments lie about depth
    arms: list[tuple[str, str]] = []
    pat: list[str] = []
    body: list[str] = []
    in_body = False
    depth = 0
    j = 0
    while j < len(text):
        if not in_body and depth == 0 and text.startswith("=>", j):
            in_body = True
            j += 2
            continue
        c = text[j]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:  # the match's own closing brace - flush the last arm
                if in_body:
                    arms.append(("".join(pat), "".join(body)))
                return arms
            depth -= 1
            if in_body:
                body.append(c)
                if depth == 0 and "".join(body).lstrip().startswith("{"):
                    arms.append(("".join(pat), "".join(body)))  # block arm: no comma needed
                    pat, body, in_body = [], [], False
                j += 1
                continue
        if in_body and depth == 0 and c == ",":
            arms.append(("".join(pat), "".join(body)))
            pat, body, in_body = [], [], False
            j += 1
            continue
        (body if in_body else pat).append(c)
        j += 1
    return arms


def _arm_programs(pattern: str) -> list[int] | None:
    """Programs a match pattern covers; None for `_` or anything unparsable."""
    out: list[int] = []
    for tok in pattern.strip().lstrip(",").split("|"):
        tok = tok.strip()
        m = re.fullmatch(r"(\d+)\s*\.\.=\s*(\d+)", tok)
        if m:
            out.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif tok.isdigit():
            out.append(int(tok))
        else:
            return None
    return out


def check_alias_dispatch() -> list[str]:
    """Every ALIAS pair shares one `make()` arm and that arm discards `program`."""
    if not _VOICES_RS.exists():
        return [f"{_VOICES_RS} not found - cannot verify ALIAS against the dispatch"]
    try:
        arms = _make_arms(_VOICES_RS.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"could not parse make() dispatch in {_VOICES_RS}: {exc}"]
    prog_arm: dict[int, tuple[int, str]] = {}
    for idx, (pattern, body) in enumerate(arms):
        progs = _arm_programs(pattern)
        if progs is None:
            continue  # `_` fallback; no alias may rely on it
        for p in progs:
            prog_arm.setdefault(p, (idx, body))  # first matching arm wins, like rustc
    fails = []
    for p, canon in sorted(pr.ALIAS.items()):
        got_p, got_c = prog_arm.get(p), prog_arm.get(canon)
        if got_p is None or got_c is None:
            fails.append(f"GM {p}->{canon}: not matched by an explicit make() arm")
        elif got_p[0] != got_c[0]:
            fails.append(f"GM {p} and canonical GM {canon} sit in different make() arms - stale alias")
        elif re.search(r"\bprogram\b", got_p[1]):
            fails.append(f"GM {p}->{canon}: shared make() arm reads `program` - not byte-identical")
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
        # an alt slot authors a non-zero CC0 (1 = the single legacy alt; 2 = the
        # GM19 CathedralOrgan bank); the program active at that point is the alt
        # program - the LATEST program change before the CC0 (a max over program
        # NUMBERS only held for the ascending inline walk, and a STANDALONE_ALT
        # tail slot re-authors a lower number after higher ones)
        progs = program_events(sc, MELODIC_CH)
        for beat, val in cc_events(sc, MELODIC_CH, 0):
            if val != 0:
                latest = max(
                    ((b, p) for b, p in progs if b <= beat + 1e-6),
                    default=None,
                )
                if latest is not None:
                    seen.add(latest[1])
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
