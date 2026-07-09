"""verify.py — structural oracles for *Seven Kinds of Sunlight*.

Adapted from the Sub Rosa suite; the song-specific requirements:

  * The METER MAP is exact: the 0x58 grid must equal conductor's
    (4/4, 7/8, 6/8, 5/4 and the drum-break flip back to 4/4).
  * DRIVING BASS, in the audio-facing data: >= 1.8 note-ons per beat
    inside every chorus, and the sounding pitch at every chorus bar
    line is the ground root's pitch class (gear change respected).
  * DRUM coverage: every chorus contains tom fills; the Drum Break
    uses >= 6 distinct drum pitches at >= 3 hits/beat.
  * The final chorus actually STACKS the counterpoint: hook, descant,
    counter A (arp), counter B (strings), vocalise and bass all sound
    in its first statement window.
  * RPN bend-range 12 legal only in the solo window; recentres at the
    section seams; portamento off at each deadline; pedals paired.
  * CC70: verse oohs closed (<= 10), every chorus open (>= 80).
  * Lyric syllables in all three choruses.
  * Mean-velocity chains V1 < PC1 < Ch1, V2 < PC2 < Ch2, and
    {M8, Ch2, Outro} below the Final Chorus; density peaks there.
"""

from __future__ import annotations

import conductor
import engine as en
import material

PPQ = en.PPQ
CH = conductor

DURATION_WINDOW = (3 * 60 + 40.0, 4 * 60 + 20.0)
EXPECTED_TRACKS = 17
MIN_TEMPO_EVENTS = 3
MIN_MARKERS = 13

NOTE_RANGES: dict[int, tuple[int, int]] = {
    CH.CH_PIANO:   (21, 108),
    CH.CH_PAD:     (36, 96),
    CH.CH_ARP:     (45, 103),
    CH.CH_BASS:    (24, 67),
    CH.CH_LEAD:    (48, 103),
    CH.CH_STRINGS: (36, 96),
    CH.CH_CHOIR1:  (48, 96),
    CH.CH_CHOIR2:  (48, 96),
    CH.CH_GLOCK:   (60, 108),
    CH.CH_GTR:     (38, 90),
    CH.CH_SOLO:    (43, 100),
    CH.CH_ORGAN:   (33, 91),
    CH.CH_OOHS:    (48, 96),
    CH.CH_FLUTE:   (55, 103),
    CH.CH_VIBES:   (48, 103),
}
GM_PERCUSSION = set(range(35, 82))

MAX_GAP_BEATS = 1.0
MIN_AFTERTOUCH = 30
_REPORT_CAP = 8

CHORUSES = [                       # (t0, t1, transpose semis)
    (112.0, 176.0, 0), (264.0, 328.0, 0), (446.0, 510.0, 2),
]
BASS_MIN_RATE = 1.8

CC_INVENTORY = [
    (CH.CH_ARP,    74,   0.0,  32.0,  6, "rise",
     "intro riff filter opening (CC74)"),
    (CH.CH_ARP,    74,  88.0, 112.0,  6, "rise",
     "pre-chorus 1 riser (CC74)"),
    (CH.CH_ARP,    71,  88.0, 112.0,  4, None,
     "pre-chorus 1 resonance (CC71)"),
    (CH.CH_ARP,    74, 240.0, 264.0,  6, "rise",
     "pre-chorus 2 riser (CC74)"),
    (CH.CH_GTR,    74, 184.0, 240.0, 12, None,
     "verse-2 wah funk LFO (CC74)"),
    (CH.CH_ORGAN,   1, 446.0, 478.0,  6, "rise",
     "final-chorus Leslie spin-up (CC1)"),
    (CH.CH_SOLO,    1, 368.0, 424.0,  6, None,
     "solo vibrato wheel (CC1)"),
    (CH.CH_PAD,    74, 510.0, 542.0,  4, "fall",
     "outro pad filter closing (CC74)"),
    (CH.CH_PIANO,  64, 328.0, 368.0,  2, None,
     "middle-eight piano pools (CC64)"),
]

VOWEL_SECTIONS = [
    (CH.CH_OOHS,    32.0, 112.0, "hum"),
    (CH.CH_CHOIR1, 112.0, 176.0, "chorus"),
    (CH.CH_CHOIR1, 264.0, 328.0, "chorus"),
    (CH.CH_CHOIR2, 264.0, 328.0, "chorus"),
    (CH.CH_CHOIR1, 446.0, 510.0, "chorus"),
    (CH.CH_CHOIR2, 446.0, 510.0, "chorus"),
]

PORTAMENTO = [
    (CH.CH_LEAD, 328.0, 368.0, 370.0),
    (CH.CH_BASS, 510.0, 542.0, 542.0),
]

RPN_RANGE_WINDOWS = [(CH.CH_SOLO, 368.0, 428.0, 12.0)]
RPN_RESET_BY = {CH.CH_SOLO: 428.0}
FINE_TUNE_EXPECT = [(CH.CH_LEAD, 180.0, 244.0, -8.0, -2.0)]
BEND_RECENTER_BEATS = [112.0, 176.0, 264.0, 328.0, 368.0, 426.0,
                       510.0, 542.0]
AFTERTOUCH_MIN = [(CH.CH_PAD, MIN_AFTERTOUCH), (CH.CH_CHOIR1, MIN_AFTERTOUCH)]
LYRIC_WINDOWS = [(112.0, 176.0, 3), (264.0, 328.0, 3), (446.0, 510.0, 4)]

VEL_CHAINS = [
    ["Verse 1", "Pre-Chorus 1", "Chorus 1"],
    ["Verse 2", "Pre-Chorus 2", "Chorus 2"],
]
QUIETER_THAN_PEAK = ["Middle Eight", "Chorus 2", "Outro"]
DENSITY_PEAK = "Final Chorus"

BREAK_WINDOW = (424.0, 446.0)
BREAK_MIN_PITCHES = 6
BREAK_MIN_RATE = 3.0
TOM_PITCHES = {41, 43, 45, 47, 48, 50}
CHORUS_MIN_TOMS = 6

# every one of these channels must have note-ons inside the final
# chorus's first statement — the stack is real, not implied
STACK_WINDOW = (446.0, 478.0)
STACK_CHANNELS = [CH.CH_CHOIR1, CH.CH_CHOIR2, CH.CH_ARP, CH.CH_STRINGS,
                  CH.CH_OOHS, CH.CH_BASS, CH.CH_GTR, CH.CH_DRUMS]


# ---------------------------------------------------------------------------
# Introspection helpers (as Sub Rosa)
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
        fails.append(f"check_structure: {info['tracks']} tracks != "
                     f"{EXPECTED_TRACKS}")
    if info["ppq"] != PPQ:
        fails.append(f"check_structure: PPQ {info['ppq']} != {PPQ}")
    if info["format"] != 1:
        fails.append(f"check_structure: format {info['format']} != 1")
    if len(sc.markers) < MIN_MARKERS:
        fails.append(f"check_structure: {len(sc.markers)} markers < "
                     f"{MIN_MARKERS}")
    if info["tempo_events"] < MIN_TEMPO_EVENTS:
        fails.append(f"check_structure: {info['tempo_events']} tempo "
                     f"events < {MIN_TEMPO_EVENTS}")
    return fails


def check_material():
    return [f"check_material: {msg}" for msg in material.verify_material()]


def check_meters(sc):
    """The 0x58 grid matches conductor.TIME_SIGNATURES exactly."""
    got = sorted(sc.timesigs)
    want = sorted(conductor.TIME_SIGNATURES)
    if got != want:
        return [f"check_meters: timesig grid {got} != {want}"]
    return []


def check_keysigs(sc):
    got = sorted(sc.keysigs)
    if got != sorted(conductor.KEYSIGS):
        return [f"check_keysigs: {got} != {conductor.KEYSIGS}"]
    return []


def check_driving_bass(sc):
    """>= BASS_MIN_RATE note-ons/beat in every chorus; the sounding
    bass pitch class at every chorus bar line is the ground root."""
    fails = []
    spans = _note_spans(sc, CH.CH_BASS)
    base = en.n("D2")
    for t0, t1, semis in CHORUSES:
        ons = [on for on, _off, _p, _v in spans if t0 - 0.05 <= on < t1]
        rate = len(ons) / (t1 - t0)
        if rate < BASS_MIN_RATE:
            fails.append(f"check_driving_bass: {rate:.2f} notes/beat in "
                         f"chorus [{t0:.0f},{t1:.0f}) < {BASS_MIN_RATE}")
        for bar in range(int((t1 - t0) // 4)):
            db = t0 + 4.0 * bar
            root = material.CHORUS_GROUND[bar % 8]
            want_pc = (base + semis
                       + en.deg_semis(material.MODE, root)) % 12
            sounding = [p for on, off, p, _v in spans
                        if on - 0.05 <= db < off]
            if sounding and all(p % 12 != want_pc for p in sounding):
                fails.append(f"check_driving_bass: bar line {db:.0f} "
                             f"sounds pcs {sorted({p % 12 for p in sounding})}, "
                             f"expected root pc {want_pc}")
    return _cap(fails)


def check_drums(sc):
    """Tom fills in every chorus; the break covers the kit, densely."""
    fails = []
    spans = _note_spans(sc, CH.CH_DRUMS)
    for t0, t1, _semis in CHORUSES:
        toms = [1 for on, _off, p, _v in spans
                if p in TOM_PITCHES and t0 <= on < t1]
        if len(toms) < CHORUS_MIN_TOMS:
            fails.append(f"check_drums: {len(toms)} tom hits in chorus "
                         f"[{t0:.0f},{t1:.0f}) < {CHORUS_MIN_TOMS}")
    lo, hi = BREAK_WINDOW
    hits = [(on, p) for on, _off, p, _v in spans if lo <= on < hi]
    pitches = {p for _on, p in hits}
    if len(pitches) < BREAK_MIN_PITCHES:
        fails.append(f"check_drums: break uses {len(pitches)} drum "
                     f"pitches < {BREAK_MIN_PITCHES}")
    rate = len(hits) / (hi - lo)
    if rate < BREAK_MIN_RATE:
        fails.append(f"check_drums: break density {rate:.2f} hits/beat "
                     f"< {BREAK_MIN_RATE}")
    return _cap(fails)


def check_stack(sc):
    """Every stack channel sounds inside the final chorus's opening."""
    fails = []
    lo, hi = STACK_WINDOW
    for ch in STACK_CHANNELS:
        ons = [on for on, _off, _p, _v in _note_spans(sc, ch)
               if lo - 0.05 <= on < hi]
        if not ons:
            fails.append(f"check_stack: ch{ch} silent in the final-chorus "
                         f"stack [{lo:.0f},{hi:.0f})")
    return fails


def check_cc_inventory(sc):
    fails = []
    for ch, num, lo, hi, min_count, trend, label in CC_INVENTORY:
        evs = _cc_events(sc, ch, num, lo, hi)
        if len(evs) < min_count:
            fails.append(f"check_cc_inventory: {label}: {len(evs)} CC{num} "
                         f"events on ch{ch}, need >= {min_count}")
            continue
        if trend == "rise" and evs[-1][1] < evs[0][1] + 20:
            fails.append(f"check_cc_inventory: {label}: no rise")
        elif trend == "fall" and evs[-1][1] > evs[0][1] - 20:
            fails.append(f"check_cc_inventory: {label}: no fall")
    return _cap(fails)


def check_vowels(sc):
    fails = []
    for ch, lo, hi, kind in VOWEL_SECTIONS:
        vals = [v for _b, v in _cc_events(sc, ch, 70, lo, hi)]
        prior = _cc_events(sc, ch, 70, 0.0, lo - 1e-9)
        if prior:
            vals.append(prior[-1][1])
        if not vals:
            fails.append(f"check_vowels: ch{ch} no CC70 in effect in "
                         f"{kind} [{lo:.0f},{hi:.0f}]")
        elif kind == "hum" and min(vals) > 10:
            fails.append(f"check_vowels: ch{ch} hum [{lo:.0f},{hi:.0f}]: "
                         f"min {min(vals)} > 10")
        elif kind == "chorus" and max(vals) < 80:
            fails.append(f"check_vowels: ch{ch} chorus [{lo:.0f},{hi:.0f}]: "
                         f"max {max(vals)} < 80")
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
                                 f"not alternating at {beat:.2f}")
                    break
                state = on
            else:
                if state:
                    fails.append(f"check_pedals: ch{ch} CC{num} ({label}) "
                                 f"left DOWN")
    return _cap(fails)


def check_portamento(sc):
    fails = []
    for ch, lo, hi, deadline in PORTAMENTO:
        if not _cc_events(sc, ch, 5, lo, hi):
            fails.append(f"check_portamento: ch{ch} no CC5 in "
                         f"[{lo:.0f},{hi:.0f}]")
        switches = _cc_events(sc, ch, 65, lo, hi)
        if not any(v >= 64 for _b, v in switches):
            fails.append(f"check_portamento: ch{ch} CC65 never ON in "
                         f"[{lo:.0f},{hi:.0f}]")
        upto = _cc_events(sc, ch, 65, 0.0, deadline)
        if upto and upto[-1][1] >= 64:
            fails.append(f"check_portamento: ch{ch} CC65 still ON at "
                         f"{deadline:.0f}")
    return _cap(fails)


def check_aftertouch(sc):
    fails = []
    for ch, min_count in AFTERTOUCH_MIN:
        count = len(_at_events(sc, ch))
        if count < min_count:
            fails.append(f"check_aftertouch: ch{ch} {count} events < "
                         f"{min_count}")
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
                fails.append(f"check_rpn: ch{ch} range {r:.0f} at "
                             f"{beat:.2f} not sane")
            elif r > 2.0 and not any(
                    w_ch == ch and lo - 1e-6 <= beat <= hi + 1e-6
                    and r <= w_r + 1e-9
                    for w_ch, lo, hi, w_r in RPN_RANGE_WINDOWS):
                fails.append(f"check_rpn: ch{ch} range {r:.0f} at "
                             f"{beat:.2f} outside every window")
        deadline = RPN_RESET_BY.get(ch)
        if deadline is not None and len(ranges) > 1 \
                and abs(_range_at(ranges, deadline) - 2.0) > 1e-9:
            fails.append(f"check_rpn: ch{ch} range not reset to 2 by "
                         f"{deadline:.0f}")
    for ch, lo, hi, c_lo, c_hi in FINE_TUNE_EXPECT:
        hits = [(b, c) for b, c in tunes_by_ch.get(ch, [])
                if lo - 1e-6 <= b <= hi + 1e-6 and c_lo <= c <= c_hi]
        if not hits:
            fails.append(f"check_rpn: ch{ch} missing fine-tune "
                         f"({c_lo:+.0f}..{c_hi:+.0f}c) in "
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
                fails.append(f"check_bend_hygiene: ch{ch} {semis:+.2f} "
                             f"semis at {beat:.2f} exceeds range {r:.0f}")
            elif abs(semis) > 2.0 + 1e-6 and r <= 2.0 + 1e-9:
                fails.append(f"check_bend_hygiene: ch{ch} {semis:+.2f} "
                             f"semis at {beat:.2f} with default range")
        for b in BEND_RECENTER_BEATS:
            frac = 0.0
            for beat, f in bends:
                if beat > b + 1e-6:
                    break
                frac = f
            semis = frac * _range_at(ranges, b)
            if abs(semis) >= 0.01:
                fails.append(f"check_bend_hygiene: ch{ch} {semis:+.2f} "
                             f"semis not recentred at {b:.0f}")
    return _cap(fails)


def check_lyrics(sc):
    fails = []
    for lo, hi, min_count in LYRIC_WINDOWS:
        count = sum(1 for beat, _t in sc.lyrics
                    if lo - 1e-9 <= beat <= hi + 1e-9)
        if count < min_count:
            fails.append(f"check_lyrics: {count} lyrics in "
                         f"[{lo:.0f},{hi:.0f}] < {min_count}")
    return _cap(fails)


def check_ranges(sc):
    fails = []
    for ch in sorted(sc.events):
        for on, _off, pitch, _vel in _note_spans(sc, ch):
            if ch == CH.CH_DRUMS:
                if pitch not in GM_PERCUSSION:
                    fails.append(f"check_ranges: drum note {pitch} at "
                                 f"{on:.2f} outside the GM map")
            else:
                lo, hi = NOTE_RANGES.get(ch, (0, 127))
                if not lo <= pitch <= hi:
                    fails.append(f"check_ranges: ch{ch} note {pitch} at "
                                 f"{on:.2f} outside [{lo},{hi}]")
    return _cap(fails)


def check_dynamics_arc(sc):
    fails = []
    stats = {}
    notes = _all_notes(sc)
    for name, t0, t1 in conductor.SECTIONS:
        vels = [vel for _ch, on, _off, _p, vel in notes if t0 <= on < t1]
        if not vels:
            fails.append(f"check_dynamics_arc: no notes in '{name}'")
            continue
        stats[name] = (sum(vels) / len(vels), len(vels) / (t1 - t0))
    if len(stats) == len(conductor.SECTIONS):
        for chain in VEL_CHAINS:
            pairs = [(name, stats[name][0]) for name in chain]
            for (na, va), (nb, vb) in zip(pairs, pairs[1:]):
                if va >= vb:
                    fails.append(f"check_dynamics_arc: '{na}' ({va:.1f}) "
                                 f">= '{nb}' ({vb:.1f})")
        peak = stats[DENSITY_PEAK][0]
        for name in QUIETER_THAN_PEAK:
            if stats[name][0] >= peak:
                fails.append(f"check_dynamics_arc: '{name}' "
                             f"({stats[name][0]:.1f}) >= peak "
                             f"({peak:.1f})")
        densest = max(stats, key=lambda nm: stats[nm][1])
        if densest != DENSITY_PEAK:
            fails.append(f"check_dynamics_arc: density peaks in "
                         f"'{densest}', must be '{DENSITY_PEAK}'")
    return _cap(fails)


def check_gaps(sc, max_gap=MAX_GAP_BEATS):
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            fails.append(f"check_gaps: silence {horizon:.2f} -> {on:.2f}")
        horizon = max(horizon, off)
    return _cap(fails)


def check_module_bounds(spans, whitelist=()):
    fails = []
    for name, t0, t1, notes in spans:
        for ch, beat in notes:
            if t0 - 0.05 <= beat < t1:
                continue
            if any(w_ch == ch and lo - 1e-6 <= beat <= hi + 1e-6
                   for w_ch, lo, hi in whitelist):
                continue
            fails.append(f"check_module_bounds: '{name}' wrote ch{ch} "
                         f"note at {beat:.2f}, outside "
                         f"[{t0:.0f},{t1:.0f})")
    return _cap(fails)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(sc, info, spans, bounds_whitelist=()):
    return [
        ("check_material", check_material()),
        ("check_structure", check_structure(sc, info)),
        ("check_meters", check_meters(sc)),
        ("check_keysigs", check_keysigs(sc)),
        ("check_driving_bass", check_driving_bass(sc)),
        ("check_drums", check_drums(sc)),
        ("check_stack", check_stack(sc)),
        ("check_cc_inventory", check_cc_inventory(sc)),
        ("check_vowels", check_vowels(sc)),
        ("check_pedals", check_pedals(sc)),
        ("check_portamento", check_portamento(sc)),
        ("check_aftertouch", check_aftertouch(sc)),
        ("check_rpn", check_rpn(sc)),
        ("check_bend_hygiene", check_bend_hygiene(sc)),
        ("check_lyrics", check_lyrics(sc)),
        ("check_ranges", check_ranges(sc)),
        ("check_dynamics_arc", check_dynamics_arc(sc)),
        ("check_gaps", check_gaps(sc)),
        ("check_module_bounds", check_module_bounds(
            spans, whitelist=bounds_whitelist)),
    ]
