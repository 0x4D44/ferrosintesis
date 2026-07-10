"""verify.py — structural oracles for *The Ninth Bell* (one track).

`run_all(sc, info, spans)` returns [(check_name, failures)]; build.py
prints the table and exits nonzero on any failure.  `info` may be None
(build.py --check): file-dependent checks are then skipped.

The piece-specific requirements encoded here (HLD section 7):

  * Intro fidelity — ch0 beats 0-32 must be the demo gesture EXACTLY
    (recomputed from the engine, not hardcoded): the pad_block voicings
    with ties, the vel 44->70 ramp (+-3 jitter), the CC11 swell
    breakpoints, the demo channel setup, and nothing else sounding.
  * Program whitelist — nothing in GM 55-71 anywhere (unmodeled).
  * Pan discipline — sustained beds emit pan 64 only.
  * The nine bells — ch4 note-ons match the toll ledger (plus the
    climax peal window); the piece's final note-on is the ninth bell's
    lone A.
  * Scored silences — no note-on inside either silence window; no
    sustained-family note held through them (the cello sag excepted).
  * The dynamic arc — per-bar velocity-sum contour must rise, cliff,
    void, rebuild with the bar-62 feint, peak at the climax, die in
    the embers.  This is Arthur's "builds and drops", numerically.
  * Bend hygiene — every channel recentred at every movement boundary.
"""

from __future__ import annotations

import conductor
import engine as en
import material

PPQ = en.PPQ
CH = conductor

DURATION_WINDOW = (5 * 60.0, 7 * 60.0)
EXPECTED_TRACKS = 14                     # conductor + 13 channels
KEYSIG_GRID = [(0.0, 0, 1)]              # A minor at beat 0

INTRO_END = 32.0
INTRO_SETUP = {7: 88, 10: 64, 91: 74}    # the demo's exact ch0 setup CCs
INTRO_CC11 = [(0.0, 20), (8.0, 90), (16.0, 105)]

PROGRAM_WHITELIST = {48, 42, 52, 19, 14, 46, 47, 10, 40, 0, 89, 43}
CENTERED_CHANNELS = (CH.CH_STRINGS, CH.CH_CELLO, CH.CH_CHOIR, CH.CH_ORGAN,
                     CH.CH_VIOLIN, CH.CH_PAD, CH.CH_CBASS)

# Scored silences: (no-note-on window, no-sustain-held window, exempt chs)
SILENCE_1 = ((128.6, 131.8), (129.5, 131.8), {CH.CH_CELLO, CH.CH_BELLS,
             CH.CH_TIMPANI, CH.CH_DRUMS, CH.CH_HARP, CH.CH_PIANO})
SILENCE_2 = ((352.6, 357.8), (353.5, 357.8), {CH.CH_BELLS, CH.CH_TIMPANI,
             CH.CH_DRUMS})
GAP_WHITELIST = [(128.4, 132.4), (352.4, 358.4)]
MAX_GAP_BEATS = 1.5

NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH.CH_STRINGS: (36, 96),
    CH.CH_CELLO:   (36, 79),
    CH.CH_CHOIR:   (43, 86),
    CH.CH_ORGAN:   (24, 86),
    CH.CH_BELLS:   (48, 86),
    CH.CH_HARP:    (36, 100),
    CH.CH_TIMPANI: (36, 62),
    CH.CH_MBOX:    (57, 108),
    CH.CH_VIOLIN:  (55, 103),
    CH.CH_PIANO:   (21, 108),
    CH.CH_PAD:     (36, 92),
    CH.CH_CBASS:   (24, 62),
}
GM_PERCUSSION = set(range(35, 82))

_REPORT_CAP = 8


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------

def _cc_events(sc, ch, num, lo=0.0, hi=1e12):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] == num:
            beat = tick / PPQ
            if lo - 1e-9 <= beat <= hi + 1e-9:
                out.append((beat, data[2]))
    return sorted(out)


def _bend_fracs(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def _note_spans(sc, ch):
    """[(on_beat, off_beat, pitch, vel)] with FIFO on/off pairing."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out = []
    evs = sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1]))
    for tick, _prio, data in evs:
        status = data[0] & 0xF0
        if status == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append((tick / PPQ, data[2]))
        elif status == 0x80 or (status == 0x90 and data[2] == 0):
            queue = pending.get(data[1])
            if queue:
                on, vel = queue.pop(0)
                out.append((on, tick / PPQ, data[1], vel))
    for pitch, queue in pending.items():
        for on, vel in queue:
            out.append((on, on, pitch, vel))
    return sorted(out)


def _all_notes(sc):
    out = []
    for ch in sc.events:
        for on, off, pitch, vel in _note_spans(sc, ch):
            out.append((ch, on, off, pitch, vel))
    return out


def _programs(sc, ch):
    return [(tick / PPQ, data[1]) for tick, _prio, data
            in sc.events.get(ch, [])
            if (data[0] & 0xF0) == 0xC0]


def _cap(fails):
    if len(fails) > _REPORT_CAP:
        extra = len(fails) - _REPORT_CAP
        return fails[:_REPORT_CAP] + [
            f"{fails[0].split(':')[0]}: ... and {extra} more failures"]
    return fails


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------

def check_material():
    return material.verify_material()


def check_structure(sc, info):
    fails = []
    if info is not None:
        if not DURATION_WINDOW[0] <= info["seconds"] <= DURATION_WINDOW[1]:
            fails.append(f"duration {info['seconds']:.1f}s outside "
                         f"{DURATION_WINDOW}")
        if info["tracks"] != EXPECTED_TRACKS:
            fails.append(f"{info['tracks']} tracks, want {EXPECTED_TRACKS}")
        score_notes = sum(1 for _ in _all_notes(sc))
        if info["notes"] != score_notes:
            fails.append(f"file has {info['notes']} notes, Score built "
                         f"{score_notes}")
    if sorted(sc.tempos) != sorted(conductor.TEMPO_MAP):
        fails.append("tempo map differs from conductor.TEMPO_MAP")
    if sorted(sc.keysigs) != sorted(KEYSIG_GRID):
        fails.append("key signature grid differs")
    marker_beats = {b for b, _t in sc.markers}
    for name, t0, _t1 in conductor.MOVEMENTS:
        if t0 not in marker_beats:
            fails.append(f"missing movement marker at beat {t0}")
    for beat, _text in conductor.EXTRA_MARKERS:
        if beat not in marker_beats:
            fails.append(f"missing dramatic marker at beat {beat}")
    return fails


def _expected_intro():
    """Recompute the demo ch0 gesture: pad_block voicings with ties."""
    chords = material.home_triads()
    bed = chords + chords
    voicings, prev = [], None
    for pcs in bed:
        prev = en.voice_lead(pcs, prev, 4, 52, 79)
        voicings.append(prev)
    total = len(bed) * 4.0
    expected = []                        # (pitch, on, dur, vel)
    for vi in range(4):
        i = 0
        while i < len(voicings):
            p = voicings[i][vi]
            j = i
            while j + 1 < len(voicings) and voicings[j + 1][vi] == p:
                j += 1
            on = i * 4.0
            vel = int(en.lerp(44, 70, on / total))
            expected.append((p, on, (j - i + 1) * 4.0 + 0.25, vel))
            i = j + 1
    return sorted(expected, key=lambda x: (x[1], x[0]))


def _expected_intro_cc11():
    probe = en.Score(seed=0)
    en.cc_curve(probe, 0, 11, INTRO_CC11, step=0.5)
    return _cc_events(probe, 0, 11)


def check_intro_fidelity(sc):
    fails = []
    # 1. Channel setup CCs at beat 0 (the demo's exact parameters).
    for num, want in INTRO_SETUP.items():
        evs = [v for b, v in _cc_events(sc, 0, num, 0.0, 0.0)]
        if evs[:1] != [want]:
            fails.append(f"ch0 setup CC{num} at beat 0 is {evs[:1]}, "
                         f"want [{want}]")
    progs = _programs(sc, 0)
    if not progs or progs[0] != (0.0, 48):
        fails.append(f"ch0 program setup {progs[:1]}, want [(0.0, 48)]")

    # 2. The pad_block notes: pitch/onset/duration/velocity-ramp.
    actual = [(on, off, p, v) for on, off, p, v in _note_spans(sc, 0)
              if on < INTRO_END - 0.1]
    # Sort by jitter-rounded onset so +-4-tick humanisation cannot
    # scramble same-beat chords against the expected ordering.
    actual = sorted(actual, key=lambda x: (round(x[0] * 4) / 4, x[2]))
    expected = _expected_intro()
    if len(actual) != len(expected):
        fails.append(f"intro ch0 has {len(actual)} notes, expected "
                     f"{len(expected)}")
    tol = 6.0 / PPQ
    for (exp_p, exp_on, exp_dur, exp_vel), (on, off, p, v) in zip(
            expected, actual):
        if p != exp_p or abs(on - exp_on) > tol \
                or abs((off - on) - exp_dur) > 3 * tol:
            fails.append(f"intro note ({p} @{on:.3f} dur {off-on:.2f}) != "
                         f"expected ({exp_p} @{exp_on} dur {exp_dur})")
        elif abs(v - exp_vel) > 3:
            fails.append(f"intro note {p}@{on:.1f} vel {v}, expected "
                         f"{exp_vel}+-3")

    # 3. The CC11 swell, exactly the demo breakpoints.
    got = _cc_events(sc, 0, 11, 0.0, 16.0)
    want = _expected_intro_cc11()
    if got != want:
        fails.append(f"ch0 CC11 swell differs from the demo curve "
                     f"({len(got)} events vs {len(want)})")
    stray = _cc_events(sc, 0, 11, 16.5, INTRO_END - 0.01)
    if stray:
        fails.append(f"{len(stray)} stray ch0 CC11 events inside the "
                     f"intro after the swell")

    # 4. Nothing else sounds before beat 32.
    for ch in sc.events:
        if ch == 0:
            continue
        early = [on for on, _off, _p, _v in _note_spans(sc, ch)
                 if on < INTRO_END - 0.1]
        if early:
            fails.append(f"ch{ch} has {len(early)} note-on(s) inside the "
                         f"verbatim intro (first at {min(early):.2f})")
    return _cap(fails)


def check_programs(sc):
    fails = []
    for ch in sorted(sc.events):
        if ch == CH.CH_DRUMS:
            continue
        for beat, prog in _programs(sc, ch):
            if 55 <= prog <= 71:
                fails.append(f"ch{ch} program {prog} at beat {beat:.1f} "
                             f"is UNMODELED (GM 55-71 renders as a pluck)")
            elif prog not in PROGRAM_WHITELIST:
                fails.append(f"ch{ch} program {prog} at beat {beat:.1f} "
                             f"not in the piece's whitelist")
    return fails


def check_pan(sc):
    fails = []
    for ch in CENTERED_CHANNELS:
        bad = [(b, v) for b, v in _cc_events(sc, ch, 10) if v != 64]
        if bad:
            fails.append(f"ch{ch} is a sustained bed but pans to "
                         f"{bad[:3]} (must stay 64)")
    return fails


def check_nine_bells(sc):
    fails = []
    notes = _note_spans(sc, CH.CH_BELLS)
    ons = [(on, p) for on, _off, p, _v in notes]
    pc = lambda deg: en.pitch(material.TONIC, material.MODE, deg) % 12

    claimed = set()
    for beat, kind in material.TOLL_LEDGER:
        if kind == "fall":
            window = [(on, p) for on, p in ons if beat - 0.6 <= on <= beat + 4.5]
            pcs = [p % 12 for _on, p in window]
            if len(window) < 2 or pcs[0] not in (pc(10), pc(8)) \
                    or pcs[1] != pc(5):
                fails.append(f"toll at {beat}: want falling 10->5 (or 8->5), "
                             f"got {window}")
        elif kind.startswith("single-"):
            deg = int(kind.split("-")[1])
            window = [(on, p) for on, p in ons if beat - 0.6 <= on <= beat + 1.5]
            if len(window) != 1 or window[0][1] % 12 != pc(deg):
                fails.append(f"toll at {beat}: want one degree-{deg} bell, "
                             f"got {window}")
        else:                                   # cadence: 8, 5, lone 1
            window = [(on, p) for on, p in ons if beat - 2.0 <= on <= beat + 8.0]
            pcs = [p % 12 for _on, p in window]
            if len(window) < 3 or pcs[-3:] != [pc(8), pc(5), pc(1)]:
                fails.append(f"ninth bell at {beat}: want 8,5 then the "
                             f"lone A, got {window}")
        claimed.update(on for on, _p in ons
                       if beat - 2.0 <= on <= beat + 8.0)

    lo, hi = material.PEAL_WINDOW
    stray = [on for on, _p in ons
             if on not in claimed and not lo - 0.1 <= on <= hi + 0.1]
    if stray:
        fails.append(f"{len(stray)} ch4 bell note(s) outside the toll "
                     f"ledger and peal window (first at {min(stray):.1f})")

    # The final note-on of the WHOLE piece is the ninth bell's A.
    last = max(_all_notes(sc), key=lambda x: x[1])
    if last[0] != CH.CH_BELLS or last[3] % 12 != pc(1):
        fails.append(f"the piece's last note-on is ch{last[0]} pitch "
                     f"{last[3]} at {last[1]:.1f}; must be the bell's A")
    return _cap(fails)


def check_organ_secondary_bank(sc, info):
    """The written MIDI's Leslie lane must select legacy GM19 first."""
    if info is None:
        evs = [(tk, data[0], data[1:])
               for tk, _prio, data in
               sorted(sc.events.get(CH.CH_ORGAN, []), key=lambda e: (e[0], e[1]))]
    else:
        evs = [(tk, status, payload)
               for tk, status, payload in info["channel_events"]
               if status & 0x0F == CH.CH_ORGAN]
    bank = [i for i, (_tk, status, payload) in enumerate(evs)
            if (status & 0xF0) == 0xB0 and payload == bytes([0, 1])]
    prog = [i for i, (_tk, status, payload) in enumerate(evs)
            if (status & 0xF0) == 0xC0 and payload == bytes([19])]
    note = [i for i, (_tk, status, payload) in enumerate(evs)
            if (status & 0xF0) == 0x90 and payload[1] > 0]
    fails = []
    if not bank:
        fails.append("organ lane has no CC0=1 secondary-bank select")
    if not prog:
        fails.append("organ lane has no GM19 program change")
    if bank and prog and bank[0] > prog[0]:
        fails.append("organ CC0=1 serializes after GM19 program change")
    if bank and note and bank[0] > note[0]:
        fails.append("organ CC0=1 serializes after its first note")
    return fails


def check_silences(sc):
    fails = []
    for (on_w, hold_w, exempt), tag in ((SILENCE_1, "hit"),
                                        (SILENCE_2, "fracture")):
        for ch, on, off, p, _v in _all_notes(sc):
            if on_w[0] < on < on_w[1]:
                fails.append(f"{tag} silence broken: ch{ch} note-on "
                             f"{p} at beat {on:.2f}")
            elif ch not in exempt and on <= hold_w[0] and off > hold_w[0] + 0.2:
                fails.append(f"{tag} silence: ch{ch} sustained note {p} "
                             f"(on {on:.2f}) held into the void")
    return _cap(fails)


def _bar_energy(sc):
    e = [0.0] * 102                              # 1-based bars 1..101
    for _ch, on, _off, _p, vel in _all_notes(sc):
        bar = int(on // 4) + 1
        if 1 <= bar <= 101:
            e[bar] += vel
    return e


def check_arc(sc):
    e = _bar_energy(sc)
    mean = lambda a, b: sum(e[a:b + 1]) / (b - a + 1)
    fails = []
    s1, s2, s3 = mean(1, 8), mean(9, 24), mean(25, 32)
    if not s1 < s2 < s3:
        fails.append(f"no first build: section means {s1:.0f} -> {s2:.0f} "
                     f"-> {s3:.0f} must strictly rise")
    if e[33] < 0.7 * max(e[25:33]):
        fails.append(f"the hit bar 33 ({e[33]:.0f}) is weaker than 0.7x "
                     f"the ascent's loudest bar ({max(e[25:33]):.0f})")
    void = mean(34, 41)
    if void > 0.25 * s2:
        fails.append(f"the void (bars 34-41 mean {void:.0f}) is not a "
                     f"drop (must be <= 0.25x processional {s2:.0f})")
    if e[62] >= 0.6 * e[61]:
        fails.append(f"no feint: bar 62 ({e[62]:.0f}) must fall below "
                     f"0.6x bar 61 ({e[61]:.0f})")
    climax = mean(74, 88)
    sections = [mean(1, 8), mean(9, 24), mean(25, 32), mean(34, 49),
                mean(50, 73), climax, mean(90, 101)]
    if climax < max(sections) or climax <= s3:
        fails.append(f"climax (74-88 mean {climax:.0f}) is not the "
                     f"piece's peak (sections {[f'{s:.0f}' for s in sections]})")
    coda = mean(90, 101)
    if coda > 0.2 * climax:
        fails.append(f"embers (90-101 mean {coda:.0f}) must die to "
                     f"<= 0.2x the climax ({climax:.0f})")
    return fails


def check_bend_hygiene(sc):
    fails = []
    boundaries = [t0 for _n, t0, _t1 in conductor.MOVEMENTS][1:]
    for ch in sorted(sc.events):
        fracs = _bend_fracs(sc, ch)
        if not fracs:
            continue
        for t in boundaries:
            state = 0.0
            for b, f in fracs:
                if b > t - 0.05:
                    break
                state = f
            if abs(state) > 0.02:
                fails.append(f"ch{ch} bend not recentred at movement "
                             f"boundary {t} (state {state:+.2f})")
    return _cap(fails)


def check_ranges(sc):
    fails = []
    for ch, (lo, hi) in NOTE_RANGES.items():
        for on, _off, p, _v in _note_spans(sc, ch):
            if not lo <= p <= hi:
                fails.append(f"ch{ch} pitch {p} at beat {on:.1f} outside "
                             f"[{lo},{hi}]")
    for on, _off, p, _v in _note_spans(sc, CH.CH_DRUMS):
        if p not in GM_PERCUSSION:
            fails.append(f"drum note {p} at {on:.1f} outside GM range")
    return _cap(fails)


def check_gaps(sc, max_gap=MAX_GAP_BEATS):
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: the piece is silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            if not any(lo <= horizon and on <= hi
                       for lo, hi in GAP_WHITELIST):
                fails.append(f"unscored silence from beat {horizon:.2f} "
                             f"to {on:.2f}")
        horizon = max(horizon, off)
    return _cap(fails)


def check_overlaps(sc):
    sc._resolve_overlaps()
    fails = []
    for ch in sorted(sc.events):
        per_pitch: dict[int, list[tuple[float, float]]] = {}
        for on, off, p, _v in _note_spans(sc, ch):
            per_pitch.setdefault(p, []).append((on, off))
        for p, spans in per_pitch.items():
            spans.sort()
            for (on1, off1), (on2, _off2) in zip(spans, spans[1:]):
                if off1 > on2 + 1e-6:
                    fails.append(f"ch{ch} pitch {p}: note at {on1:.2f} "
                                 f"overlaps re-strike at {on2:.2f}")
    return _cap(fails)


def check_movement_bounds(spans, whitelist=()):
    fails = []
    for name, t0, t1, notes in spans:
        for ch, beat in notes:
            if t0 - 0.05 <= beat < t1:
                continue
            if any(w_ch == ch and lo - 1e-6 <= beat <= hi + 1e-6
                   for w_ch, lo, hi in whitelist):
                continue
            fails.append(f"'{name}' wrote a ch{ch} note at beat "
                         f"{beat:.2f}, outside [{t0:.0f}, {t1:.0f})")
    return _cap(fails)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(sc, info, spans, bounds_whitelist=()):
    return [
        ("check_material", check_material()),
        ("check_structure", check_structure(sc, info)),
        ("check_intro_fidelity", check_intro_fidelity(sc)),
        ("check_programs", check_programs(sc)),
        ("check_organ_secondary_bank", check_organ_secondary_bank(sc, info)),
        ("check_pan", check_pan(sc)),
        ("check_nine_bells", check_nine_bells(sc)),
        ("check_silences", check_silences(sc)),
        ("check_arc", check_arc(sc)),
        ("check_bend_hygiene", check_bend_hygiene(sc)),
        ("check_ranges", check_ranges(sc)),
        ("check_gaps", check_gaps(sc)),
        ("check_overlaps", check_overlaps(sc)),
        ("check_movement_bounds", check_movement_bounds(
            spans, whitelist=bounds_whitelist)),
    ]
