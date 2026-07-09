"""verify.py — structural oracles for *Sub Rosa* (one track).

Adapted from Winter Guests' two-part oracle suite to a single Score.
`run_all(sc, info, spans)` returns [(check_name, failures)]; build.py
prints the table and exits nonzero on any failure.

The piece-specific requirements encoded here:

  * RPN-aware bend hygiene — the glide lead may widen its bend range
    to 12 semitones ONLY inside the M4 window and must reset to 2 by
    the seam; every channel recentred at every movement boundary.
  * CC70 vowel inventory — the chant hums (mm) in M1/M2, opens to full
    voice (ah) in M5; the breath channel stays closed-mouth in M4.
  * Portamento paired and off at the seams (bass M1/M4/M6, lead M4).
  * Pedal hygiene — CC64/66/67/68 strictly alternating, nothing stuck.
  * Aftertouch minimums on the pad and the chant.
  * The whispered text present in M4, one last word in M6.
  * The Morse woodblock in M4 taps exactly the dots and dashes of
    "SUB ROSA".
  * Mean velocity strictly increasing Sigillum -> The Chant -> The
    Bamboo Voice -> Limina; the breakdown and afterglow sit below the
    climax; note density peaks in Limina.
"""

from __future__ import annotations

import conductor
import engine as en
import material

PPQ = en.PPQ
CH = conductor

DURATION_WINDOW = (7 * 60.0 + 20.0, 8 * 60.0 + 40.0)
EXPECTED_TRACKS = 17                       # conductor + 16 channels
MIN_MARKERS = 6
MIN_TEMPO_EVENTS = 5
MIN_TIMESIGS = 1
KEYSIG_GRID = [(0.0, -1, 1)]               # D minor at beat 0

NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH.CH_PIANO:   (21, 108),
    CH.CH_PAD:     (36, 96),
    CH.CH_ARP:     (45, 103),
    CH.CH_BASS:    (24, 64),
    CH.CH_SHAKU:   (55, 103),
    CH.CH_STRINGS: (36, 96),
    CH.CH_CHOIR1:  (40, 96),
    CH.CH_CHOIR2:  (40, 96),
    CH.CH_CRYSTAL: (55, 108),
    CH.CH_GUITAR:  (38, 88),
    CH.CH_LEAD:    (40, 100),
    CH.CH_DRONE:   (26, 80),
    CH.CH_WHISPER: (40, 96),
    CH.CH_BELL:    (45, 96),
    CH.CH_MBOX:    (55, 108),
}
GM_PERCUSSION = set(range(35, 82))

MAX_GAP_BEATS = 1.0
MIN_AFTERTOUCH = 30
_REPORT_CAP = 8

CC_INVENTORY = [
    # (ch, cc, lo, hi, min_count, trend, label)
    (CH.CH_ARP,    74, 128.0, 256.0,  8, "rise",
     "M2 sequencer filter opening (CC74)"),
    (CH.CH_ARP,    71, 576.0, 832.0,  6, None,
     "M5 sequencer resonance ride (CC71)"),
    (CH.CH_GUITAR, 74, 256.0, 448.0, 12, None,
     "M3 wah LFO on the guitar skanks (CC74)"),
    (CH.CH_DRONE,   1, 576.0, 648.0,  6, "rise",
     "M5 organ Leslie spin-up (CC1)"),
    (CH.CH_BASS,    5, 448.0, 576.0,  1, None,
     "M4 bass portamento time (CC5)"),
    (CH.CH_PAD,    74, 832.0, 928.0,  6, "fall",
     "M6 pad filter closing (CC74)"),
    (CH.CH_PIANO,  67, 448.0, 576.0,  1, None,
     "M4 una corda on (CC67)"),
    (CH.CH_PIANO,  64, 448.0, 576.0,  2, None,
     "M4 piano pedal pools (CC64)"),
    (CH.CH_PIANO,  66, 448.0, 576.0,  2, None,
     "M4 sostenuto pedal point (CC66)"),
    (CH.CH_SHAKU,   1, 256.0, 448.0,  6, None,
     "M3 flute vibrato wheel (CC1)"),
]

VOWEL_SECTIONS = [
    # (ch, lo, hi, "hum" needs CC70 <= 10 sounding; "chorus" needs >= 80)
    (CH.CH_CHOIR1,   32.0,  64.0, "hum"),
    (CH.CH_CHOIR1,   96.0, 256.0, "hum"),
    (CH.CH_WHISPER, 448.0, 576.0, "hum"),
    (CH.CH_CHOIR1,  608.0, 832.0, "chorus"),
    (CH.CH_CHOIR2,  608.0, 832.0, "chorus"),
]

PORTAMENTO = [
    # (ch, lo, hi, off_deadline)
    (CH.CH_BASS,  32.0,  64.0,  66.0),
    (CH.CH_BASS, 448.0, 576.0, 580.0),
    (CH.CH_LEAD, 480.0, 576.0, 578.0),
    (CH.CH_BASS, 832.0, 928.0, 928.0),
]

RPN_RANGE_WINDOWS = [(CH.CH_LEAD, 480.0, 578.0, 12.0)]
RPN_RESET_BY = {CH.CH_LEAD: 578.0}
FINE_TUNE_EXPECT = [(CH.CH_CHOIR2, 440.0, 470.0, -10.0, -2.0)]
BEND_RECENTER_BEATS = [64.0, 256.0, 448.0, 578.0, 832.0, 928.0]
AFTERTOUCH_MIN = [(CH.CH_PAD, MIN_AFTERTOUCH), (CH.CH_CHOIR1, MIN_AFTERTOUCH)]
LYRIC_WINDOWS = [(448.0, 576.0, 3), (832.0, 928.0, 1)]

DYNAMICS_ORDER = ["Sigillum", "The Chant", "The Bamboo Voice", "Limina"]
QUIETER_THAN_PEAK = ["Sub Rosa", "Afterglow"]
DENSITY_PEAK = "Limina"

MORSE_TEXT = "SUB ROSA"
MORSE_WINDOW = (496.0, 560.0)
MORSE_DRUM = 76                     # hi woodblock


# ---------------------------------------------------------------------------
# Score introspection helpers (as Winter Guests)
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


def _at_events(sc, ch, lo=0.0, hi=1e12):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xD0:
            beat = tick / PPQ
            if lo - 1e-9 <= beat <= hi + 1e-9:
                out.append((beat, data[1]))
    return sorted(out)


def _rpn_state(sc, ch):
    evs = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] in (101, 100, 6):
            evs.append((tick, data[1], data[2]))
    evs.sort()
    sel_msb = sel_lsb = 127
    ranges = [(-1e12, 2.0)]
    tunes = []
    problems = []
    for tick, num, val in evs:
        beat = tick / PPQ
        if num == 101:
            sel_msb = val
        elif num == 100:
            sel_lsb = val
        else:
            if (sel_msb, sel_lsb) == (0, 0):
                ranges.append((beat, float(val)))
            elif (sel_msb, sel_lsb) == (0, 1):
                tunes.append((beat, (val - 64) * 100.0 / 64.0))
            elif sel_msb == 127 and sel_lsb == 127:
                problems.append(f"ch{ch} CC6 at beat {beat:.2f} with the "
                                f"RPN selection null")
            else:
                problems.append(f"ch{ch} CC6 at beat {beat:.2f} with "
                                f"unknown RPN ({sel_msb},{sel_lsb})")
    if evs and not (sel_msb == 127 and sel_lsb == 127):
        problems.append(f"ch{ch} RPN selection left open at the end")
    return ranges, tunes, problems


def _range_at(ranges, beat):
    current = ranges[0][1]
    for b, r in ranges:
        if b > beat + 1e-9:
            break
        current = r
    return current


def _note_spans(sc, ch):
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


def _cap(fails):
    if len(fails) > _REPORT_CAP:
        extra = len(fails) - _REPORT_CAP
        return fails[:_REPORT_CAP] + [
            f"{fails[0].split(':')[0]}: ... and {extra} more failures"]
    return fails


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------

def check_structure(sc, info):
    fails = []
    lo, hi = DURATION_WINDOW
    if not lo <= info["seconds"] <= hi:
        fails.append(f"check_structure: duration {info['seconds']:.1f}s "
                     f"outside [{lo:.0f}, {hi:.0f}]s")
    if info["tracks"] != EXPECTED_TRACKS:
        fails.append(f"check_structure: {info['tracks']} MIDI tracks, "
                     f"expected {EXPECTED_TRACKS}")
    if info["ppq"] != PPQ:
        fails.append(f"check_structure: PPQ {info['ppq']} != {PPQ}")
    if info["format"] != 1:
        fails.append(f"check_structure: format {info['format']} != 1")
    if len(sc.markers) < MIN_MARKERS:
        fails.append(f"check_structure: {len(sc.markers)} markers, "
                     f"need >= {MIN_MARKERS}")
    if info["tempo_events"] < MIN_TEMPO_EVENTS:
        fails.append(f"check_structure: {info['tempo_events']} tempo "
                     f"events, need >= {MIN_TEMPO_EVENTS}")
    if len(sc.timesigs) < MIN_TIMESIGS:
        fails.append(f"check_structure: {len(sc.timesigs)} time "
                     f"signatures, need >= {MIN_TIMESIGS}")
    return fails


def check_material():
    return [f"check_material: {msg}" for msg in material.verify_material()]


def check_cc_inventory(sc):
    fails = []
    for ch, num, lo, hi, min_count, trend, label in CC_INVENTORY:
        evs = _cc_events(sc, ch, num, lo, hi)
        if len(evs) < min_count:
            fails.append(f"check_cc_inventory: {label}: {len(evs)} CC{num} "
                         f"events on ch{ch} in [{lo:.0f},{hi:.0f}], "
                         f"need >= {min_count}")
            continue
        if trend == "rise" and evs[-1][1] < evs[0][1] + 20:
            fails.append(f"check_cc_inventory: {label}: no rise "
                         f"({evs[0][1]} -> {evs[-1][1]})")
        elif trend == "fall" and evs[-1][1] > evs[0][1] - 20:
            fails.append(f"check_cc_inventory: {label}: no fall "
                         f"({evs[0][1]} -> {evs[-1][1]})")
    return _cap(fails)


def check_vowels(sc):
    fails = []
    for ch, lo, hi, kind in VOWEL_SECTIONS:
        vals = [v for _b, v in _cc_events(sc, ch, 70, lo, hi)]
        prior = _cc_events(sc, ch, 70, 0.0, lo - 1e-9)
        if prior:
            vals.append(prior[-1][1])
        if not vals:
            fails.append(f"check_vowels: ch{ch} has no CC70 vowel in effect "
                         f"in {kind} section [{lo:.0f},{hi:.0f}]")
        elif kind == "hum" and min(vals) > 10:
            fails.append(f"check_vowels: ch{ch} hum section "
                         f"[{lo:.0f},{hi:.0f}]: no CC70 <= 10 (mm); "
                         f"min sounding value {min(vals)}")
        elif kind == "chorus" and max(vals) < 80:
            fails.append(f"check_vowels: ch{ch} chorus section "
                         f"[{lo:.0f},{hi:.0f}]: no CC70 >= 80 (ah); "
                         f"max sounding value {max(vals)}")
    return _cap(fails)


def check_pedals(sc):
    fails = []
    for ch in sorted(sc.events):
        for num, label in ((64, "sustain"), (66, "sostenuto"),
                           (67, "una corda"), (68, "legato")):
            state = False
            for beat, val in _cc_events(sc, ch, num):
                on = val >= 64
                if on == state:
                    fails.append(f"check_pedals: ch{ch} CC{num} ({label}) "
                                 f"not alternating at beat {beat:.2f}")
                    break
                state = on
            else:
                if state:
                    fails.append(f"check_pedals: ch{ch} CC{num} ({label}) "
                                 f"left DOWN after the last event")
    return _cap(fails)


def check_portamento(sc):
    fails = []
    for ch, lo, hi, deadline in PORTAMENTO:
        if not _cc_events(sc, ch, 5, lo, hi):
            fails.append(f"check_portamento: ch{ch} has no CC5 (time) in "
                         f"[{lo:.0f},{hi:.0f}]")
        switches = _cc_events(sc, ch, 65, lo, hi)
        if not any(v >= 64 for _b, v in switches):
            fails.append(f"check_portamento: ch{ch} CC65 never ON in "
                         f"[{lo:.0f},{hi:.0f}]")
        upto = _cc_events(sc, ch, 65, 0.0, deadline)
        if upto and upto[-1][1] >= 64:
            fails.append(f"check_portamento: ch{ch} CC65 still ON at "
                         f"beat {deadline:.0f} (last value "
                         f"{upto[-1][1]} at {upto[-1][0]:.2f})")
    return _cap(fails)


def check_aftertouch(sc):
    fails = []
    for ch, min_count in AFTERTOUCH_MIN:
        count = len(_at_events(sc, ch))
        if count < min_count:
            fails.append(f"check_aftertouch: ch{ch} has {count} aftertouch "
                         f"events, need >= {min_count}")
    return _cap(fails)


def check_rpn(sc):
    fails = []
    tunes_by_ch = {}
    for ch in sorted(sc.events):
        ranges, tunes, problems = _rpn_state(sc, ch)
        tunes_by_ch[ch] = tunes
        fails += [f"check_rpn: {p}" for p in problems]
        for beat, r in ranges[1:]:
            if not 1.0 <= r <= 24.0:
                fails.append(f"check_rpn: ch{ch} bend range {r:.0f} at "
                             f"beat {beat:.2f} is not sane (1..24)")
            elif r > 2.0 and not any(
                    w_ch == ch and lo - 1e-6 <= beat <= hi + 1e-6
                    and r <= w_r + 1e-9
                    for w_ch, lo, hi, w_r in RPN_RANGE_WINDOWS):
                fails.append(f"check_rpn: ch{ch} bend range {r:.0f} at "
                             f"beat {beat:.2f} outside every allowed window")
        deadline = RPN_RESET_BY.get(ch)
        if deadline is not None and len(ranges) > 1 \
                and abs(_range_at(ranges, deadline) - 2.0) > 1e-9:
            fails.append(f"check_rpn: ch{ch} bend range is "
                         f"{_range_at(ranges, deadline):.0f} at beat "
                         f"{deadline:.0f}, must be reset to 2")
    for ch, lo, hi, c_lo, c_hi in FINE_TUNE_EXPECT:
        hits = [(b, c) for b, c in tunes_by_ch.get(ch, [])
                if lo - 1e-6 <= b <= hi + 1e-6 and c_lo <= c <= c_hi]
        if not hits:
            fails.append(f"check_rpn: ch{ch} missing the RPN 1 fine-tune "
                         f"({c_lo:+.0f}..{c_hi:+.0f} cents) in "
                         f"[{lo:.0f},{hi:.0f}]")
    return _cap(fails)


def check_bend_hygiene(sc):
    fails = []
    for ch in sorted(sc.events):
        bends = _bend_fracs(sc, ch)
        if not bends:
            continue
        ranges, _tunes, _problems = _rpn_state(sc, ch)
        for beat, frac in bends:
            r = _range_at(ranges, beat)
            semis = frac * r
            if abs(semis) > r + 1e-6:
                fails.append(f"check_bend_hygiene: ch{ch} bend "
                             f"{semis:+.3f} semis at beat {beat:.2f} "
                             f"exceeds the range in force ({r:.0f})")
            elif abs(semis) > 2.0 + 1e-6 and r <= 2.0 + 1e-9:
                fails.append(f"check_bend_hygiene: ch{ch} bend "
                             f"{semis:+.3f} semis at beat {beat:.2f} "
                             f"with only the default +/-2 range")
        for b in BEND_RECENTER_BEATS:
            frac = 0.0
            for beat, f in bends:
                if beat > b + 1e-6:
                    break
                frac = f
            semis = frac * _range_at(ranges, b)
            if abs(semis) >= 0.01:
                fails.append(f"check_bend_hygiene: ch{ch} bend "
                             f"{semis:+.3f} semis not recentred at "
                             f"beat {b:.0f}")
    return _cap(fails)


def check_lyrics(sc):
    fails = []
    for lo, hi, min_count in LYRIC_WINDOWS:
        count = sum(1 for beat, _text in sc.lyrics
                    if lo - 1e-9 <= beat <= hi + 1e-9)
        if count < min_count:
            fails.append(f"check_lyrics: {count} lyric metas in "
                         f"[{lo:.0f},{hi:.0f}], need >= {min_count}")
    return _cap(fails)


def check_keysigs(sc):
    got = sorted(sc.keysigs)
    if got != sorted(KEYSIG_GRID):
        return [f"check_keysigs: keysig metas {got} != grid {KEYSIG_GRID}"]
    return []


def check_morse(sc):
    """The M4 woodblock taps exactly the dot/dash sequence of MORSE_TEXT
    (dashes are the long notes — 3 units vs 1)."""
    lo, hi = MORSE_WINDOW
    taps = [(on, off) for on, off, pitch, _v in _note_spans(sc, CH.CH_DRUMS)
            if pitch == MORSE_DRUM and lo - 1e-6 <= on <= hi + 1e-6]
    expected = "".join(en._MORSE[c] for c in MORSE_TEXT if c != " ")
    if len(taps) != len(expected):
        return [f"check_morse: {len(taps)} woodblock taps in "
                f"[{lo:.0f},{hi:.0f}], expected {len(expected)} "
                f"(the symbols of {MORSE_TEXT!r})"]
    fails = []
    durs = [off - on for on, off in sorted(taps)]
    for i, (sym, d) in enumerate(zip(expected, durs)):
        long = d > 0.35                      # unit 0.25: dash 0.675, dot 0.225
        if long != (sym == "-"):
            fails.append(f"check_morse: tap {i} duration {d:.2f} does not "
                         f"read as {sym!r}")
    return _cap(fails)


def check_ranges(sc):
    fails = []
    for ch in sorted(sc.events):
        for on, _off, pitch, _vel in _note_spans(sc, ch):
            if ch == CH.CH_DRUMS:
                if pitch not in GM_PERCUSSION:
                    fails.append(f"check_ranges: ch9 percussion note {pitch} "
                                 f"at beat {on:.2f} outside the GM map")
            else:
                lo, hi = NOTE_RANGES.get(ch, (0, 127))
                if not lo <= pitch <= hi:
                    fails.append(f"check_ranges: ch{ch} note {pitch} at "
                                 f"beat {on:.2f} outside [{lo}, {hi}]")
    return _cap(fails)


def check_dynamics_arc(sc):
    fails = []
    stats = {}
    notes = _all_notes(sc)
    for name, t0, t1 in conductor.MOVEMENTS:
        vels = [vel for _ch, on, _off, _p, vel in notes if t0 <= on < t1]
        if not vels:
            fails.append(f"check_dynamics_arc: no notes in '{name}'")
            continue
        stats[name] = (sum(vels) / len(vels), len(vels) / (t1 - t0))
    if len(stats) == len(conductor.MOVEMENTS):
        chain = [(name, stats[name][0]) for name in DYNAMICS_ORDER]
        for (na, va), (nb, vb) in zip(chain, chain[1:]):
            if va >= vb:
                fails.append(f"check_dynamics_arc: mean velocity "
                             f"'{na}' ({va:.1f}) >= '{nb}' ({vb:.1f}); "
                             f"required order {DYNAMICS_ORDER}")
        peak_vel = stats[DENSITY_PEAK][0]
        for name in QUIETER_THAN_PEAK:
            if stats[name][0] >= peak_vel:
                fails.append(f"check_dynamics_arc: '{name}' mean velocity "
                             f"{stats[name][0]:.1f} >= '{DENSITY_PEAK}' "
                             f"({peak_vel:.1f})")
        densest = max(stats, key=lambda nm: stats[nm][1])
        if densest != DENSITY_PEAK:
            fails.append(f"check_dynamics_arc: note density peaks in "
                         f"'{densest}' ({stats[densest][1]:.2f}/beat), "
                         f"must peak in '{DENSITY_PEAK}'")
    return _cap(fails)


def check_gaps(sc, max_gap=MAX_GAP_BEATS):
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: no notes anywhere - the piece is silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            fails.append(f"check_gaps: all channels silent from beat "
                         f"{horizon:.2f} to {on:.2f}")
        horizon = max(horizon, off)
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
            fails.append(f"check_movement_bounds: '{name}' wrote a ch{ch} "
                         f"note at beat {beat:.2f}, outside "
                         f"[{t0:.0f}, {t1:.0f})")
    return _cap(fails)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(sc, info, spans, bounds_whitelist=()):
    return [
        ("check_material", check_material()),
        ("check_structure", check_structure(sc, info)),
        ("check_cc_inventory", check_cc_inventory(sc)),
        ("check_vowels", check_vowels(sc)),
        ("check_pedals", check_pedals(sc)),
        ("check_portamento", check_portamento(sc)),
        ("check_aftertouch", check_aftertouch(sc)),
        ("check_rpn", check_rpn(sc)),
        ("check_bend_hygiene", check_bend_hygiene(sc)),
        ("check_lyrics", check_lyrics(sc)),
        ("check_keysigs", check_keysigs(sc)),
        ("check_morse", check_morse(sc)),
        ("check_ranges", check_ranges(sc)),
        ("check_dynamics_arc", check_dynamics_arc(sc)),
        ("check_gaps", check_gaps(sc)),
        ("check_movement_bounds", check_movement_bounds(
            spans, whitelist=bounds_whitelist)),
    ]
