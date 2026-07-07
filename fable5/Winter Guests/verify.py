"""verify.py — structural oracles for *Winter Guests* (roadmap section 6),
adapted from The Signal Fire's single-track oracles to TWO parts.

Every per-part check takes (part, sc, ...) where `part` is a
conductor.Part; `run_all(parts_data)` iterates both parts and returns one
flat [(check_name, failures)] list with "P1:"/"P2:" prefixes.  `sc` is the
in-memory Score (rebuilt deterministically from the fixed seed), `info`
the engine.parse_midi output of the written file, and `spans` the
per-movement note-on record built by build.py.

While the movements are still stubs, most checks FAIL — that is correct
and intentional: the oracles describe the finished piece.  The material
oracle (check_material) and the machinery itself must always run clean.

Novelties over The Signal Fire (HLD section 6):

  * RPN-AWARE bend hygiene: each channel's CC101/100/6 stream is walked
    into a bend-range timeline; a bend's real magnitude is
    raw_fraction * range_at(beat).  Range > 2 is legal only inside the
    per-part RPN_RANGE_WINDOWS (ch12, P1 [576, 832], range 12) and must
    be reset to 2 by its deadline; RPN 1 fine-tunes (ch11 -6c, ch13 +8c)
    keep the bend controller clean.
  * CC70 vowel inventory: mm (<= 10) sounding in the hum sections, ah
    (>= 80) in the chorus sections, per channel.
  * CC66 sostenuto downs == ups, CC67 una corda paired, CC5/65 present
    around the P1 M3 portamento solo with CC65 off by 832.
  * Channel-aftertouch minimums on ch1/ch6.
  * Lyric metas in M2/M6; key-signature metas exactly at the grid beats.
"""

from __future__ import annotations

import conductor
import engine as en
import material

PPQ = en.PPQ

# ---------------------------------------------------------------------------
# Requirement data (roadmap section 6)
# ---------------------------------------------------------------------------

DURATION_WINDOW = (8 * 60.0 + 45.0, 9 * 60.0 + 59.0)     # 8:45 - 9:59 per part
EXPECTED_TRACKS = 17                                 # conductor + 16 channels
MIN_MARKERS = 3

# Sensible per-channel note ranges (item 5): ch -> (lo, hi).
# Choir channels 40..96, the ice arp 45..100, the rest as The Signal Fire.
NOTE_RANGES: dict[int, tuple[int, int]] = {
    conductor.CH_PIANO:   (21, 108),
    conductor.CH_PAD:     (36, 96),
    conductor.CH_ARP:     (45, 100),
    conductor.CH_BASS:    (24, 69),
    conductor.CH_ORGAN:   (36, 96),
    conductor.CH_STRINGS: (36, 96),
    conductor.CH_CHOIR1:  (40, 96),
    conductor.CH_STEEL:   (40, 88),
    conductor.CH_NYLON:   (40, 88),
    conductor.CH_RHYTHM:  (38, 88),
    conductor.CH_CHOIR2:  (40, 96),
    conductor.CH_LEAD:    (40, 96),
    conductor.CH_DOUBLE:  (40, 96),
    conductor.CH_WINDS:   (55, 105),
    conductor.CH_BELLS:   (45, 100),
}
GM_PERCUSSION = set(range(35, 82))     # the standard GM percussion map

MAX_GAP_BEATS = 1.0                    # item 7
MIN_AFTERTOUCH = 30                    # item 3: ch1/ch6 aftertouch minimums
_REPORT_CAP = 8                        # per-check failure list cap

# Per-part oracle data.  Keys:
#   min_tempo_events / min_timesigs   grid counts (section 1)
#   keysig_grid                       EXACT (beat, sharps, minor) list
#   cc_inventory                      (ch, cc, lo, hi, min, trend, label)
#   vowel_sections                    (ch, lo, hi, "hum"|"chorus")
#   portamento                        (ch, lo, hi, off_deadline)
#   rpn_range_windows                 (ch, lo, hi, max_range)
#   rpn_reset_by                      {ch: beat by which range must be 2}
#   fine_tune_expect                  (ch, lo, hi, cents_lo, cents_hi)
#   bend_recenter_beats               beats where every bend must be centred
#   aftertouch_min                    (ch, min_events)
#   lyric_windows                     (lo, hi, min_count)
#   dynamics_order / density_peak     item 6
CH = conductor
PART_CONFIG: dict[int, dict] = {
    1: dict(
        min_tempo_events=9,
        min_timesigs=3,
        keysig_grid=[(0.0, 1, 1)],                       # E minor @0
        cc_inventory=[
            (CH.CH_ARP,   74,   0.0, 256.0, 8, "rise",
             "M1 ice-arp filter opening (CC74 45->95)"),
            (CH.CH_ARP,   71,   0.0, 256.0, 6, None,
             "M1 ice-arp resonance ride (CC71 50->85->60)"),
            (CH.CH_ARP,   74, 544.0, 832.0, 8, None,
             "M3 ice-arp cutoff sweeps (CC74)"),
            (CH.CH_ARP,   71, 544.0, 832.0, 4, None,
             "M3 ice-arp resonance high (CC71 80-100)"),
            (CH.CH_ORGAN, 66, 256.0, 544.0, 4, None,
             "M2 harmonium sostenuto pedal-points (CC66)"),
            (CH.CH_PIANO, 67, 256.0, 544.0, 1, None,
             "M2 una corda on (CC67)"),
            (CH.CH_BASS,   5,   0.0, 256.0, 1, None,
             "M1 fretless portamento time (CC5)"),
            (CH.CH_BASS,  65,   0.0, 256.0, 2, None,
             "M1 fretless portamento switch (CC65)"),
        ],
        vowel_sections=[
            (CH.CH_CHOIR1, 176.0, 256.0, "hum"),    # M1 the first hum
            (CH.CH_CHOIR1, 256.0, 544.0, "hum"),    # M2 the humming
        ],
        portamento=[(CH.CH_LEAD, 544.0, 832.0, 832.0)],
        rpn_range_windows=[(CH.CH_LEAD, 576.0, 832.0, 12.0)],
        rpn_reset_by={CH.CH_LEAD: 832.0},
        fine_tune_expect=[(CH.CH_CHOIR2, 240.0, 340.0, -10.0, -2.0)],
        bend_recenter_beats=[256.0, 544.0, 832.0, 864.0],
        aftertouch_min=[(CH.CH_PAD, MIN_AFTERTOUCH),
                        (CH.CH_CHOIR1, MIN_AFTERTOUCH)],
        lyric_windows=[(256.0, 544.0, 6)],           # M2 displayed humming
        dynamics_order=["Frost", "The Humming", "Footsteps in the Hall"],
        density_peak="Footsteps in the Hall",
    ),
    2: dict(
        min_tempo_events=5,
        min_timesigs=1,
        keysig_grid=[(0.0, 2, 0), (320.0, 4, 0)],        # D major, E @320
        cc_inventory=[
            (CH.CH_ORGAN,  1, 448.0,  896.0, 8, None,
             "M5 full-organ Leslie ramps (CC1)"),
            (CH.CH_PAD,   74, 896.0, 1024.0, 6, "fall",
             "M6 pad filter closing (CC74 95->30)"),
            (CH.CH_PIANO, 67, 896.0, 1024.0, 1, None,
             "M6 una corda back on (CC67)"),
            (CH.CH_PIANO, 64, 896.0, 1024.0, 2, None,
             "M6 piano pedal pairs (CC64)"),
        ],
        vowel_sections=[
            (CH.CH_CHOIR1,  64.0,  128.0, "chorus"),    # M4 chorus 1
            (CH.CH_CHOIR2,  64.0,  128.0, "chorus"),
            (CH.CH_CHOIR1, 224.0,  288.0, "chorus"),    # M4 chorus 2
            (CH.CH_CHOIR2, 224.0,  288.0, "chorus"),
            (CH.CH_CHOIR1, 320.0,  448.0, "chorus"),    # M4 chorus 3 (+2)
            (CH.CH_CHOIR2, 320.0,  448.0, "chorus"),
            (CH.CH_CHOIR2, 448.0,  896.0, "hum"),       # M5 low counterline
            (CH.CH_CHOIR1, 896.0, 1024.0, "hum"),       # M6 the final hum
        ],
        portamento=[],
        rpn_range_windows=[],
        rpn_reset_by={},
        fine_tune_expect=[(CH.CH_DOUBLE, 400.0, 500.0, 2.0, 12.0)],
        bend_recenter_beats=[448.0, 896.0, 1024.0],
        aftertouch_min=[(CH.CH_PAD, MIN_AFTERTOUCH),
                        (CH.CH_CHOIR1, MIN_AFTERTOUCH)],
        lyric_windows=[(896.0, 1024.0, 3)],          # M6 "(goodnight)"
        dynamics_order=["Last Light", "Searchlight", "The Glass Ballroom"],
        density_peak="The Glass Ballroom",
    ),
}


# ---------------------------------------------------------------------------
# Score introspection helpers
# ---------------------------------------------------------------------------

def _cc_events(sc: en.Score, ch: int, num: int,
               lo: float = 0.0, hi: float = 1e12) -> list[tuple[float, int]]:
    """Sorted (beat, value) of channel `ch` CC `num` events in [lo, hi]."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] == num:
            beat = tick / PPQ
            if lo - 1e-9 <= beat <= hi + 1e-9:
                out.append((beat, data[2]))
    return sorted(out)


def _bend_fracs(sc: en.Score, ch: int) -> list[tuple[float, float]]:
    """Sorted (beat, fraction) of pitch bends, fraction in [-1, +1] of
    whatever the channel's bend range is at that moment."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xE0:
            raw = data[1] | (data[2] << 7)
            out.append((tick / PPQ, (raw - 8192) / 8192.0))
    return sorted(out)


def _at_events(sc: en.Score, ch: int,
               lo: float = 0.0, hi: float = 1e12) -> list[tuple[float, int]]:
    """Sorted (beat, value) of channel-aftertouch (0xDn) events."""
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xD0:
            beat = tick / PPQ
            if lo - 1e-9 <= beat <= hi + 1e-9:
                out.append((beat, data[1]))
    return sorted(out)


def _rpn_state(sc: en.Score, ch: int
               ) -> tuple[list[tuple[float, float]],
                          list[tuple[float, float]], list[str]]:
    """Walk the channel's CC101/100/6 stream.  Returns
    (bend_ranges, fine_tunes, problems): bend_ranges is a timeline of
    (beat, semitones) starting from the default 2.0; fine_tunes is
    (beat, cents); problems flags malformed sequences (CC6 with the RPN
    null/unknown, or a selection left open at the end)."""
    evs = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0xB0 and data[1] in (101, 100, 6):
            evs.append((tick, data[1], data[2]))
    evs.sort()
    sel_msb = sel_lsb = 127                      # RPN null
    ranges: list[tuple[float, float]] = [(-1e12, 2.0)]
    tunes: list[tuple[float, float]] = []
    problems: list[str] = []
    for tick, num, val in evs:
        beat = tick / PPQ
        if num == 101:
            sel_msb = val
        elif num == 100:
            sel_lsb = val
        else:                                    # CC6 data entry
            if (sel_msb, sel_lsb) == (0, 0):
                ranges.append((beat, float(val)))
            elif (sel_msb, sel_lsb) == (0, 1):
                tunes.append((beat, (val - 64) * 100.0 / 64.0))
            elif sel_msb == 127 and sel_lsb == 127:
                problems.append(f"ch{ch} CC6 at beat {beat:.2f} with the "
                                f"RPN selection null (no 101/100 first)")
            else:
                problems.append(f"ch{ch} CC6 at beat {beat:.2f} with "
                                f"unknown RPN ({sel_msb},{sel_lsb})")
    if evs and not (sel_msb == 127 and sel_lsb == 127):
        problems.append(f"ch{ch} RPN selection ({sel_msb},{sel_lsb}) left "
                        f"open at the end (missing the 101=127/100=127 "
                        f"close)")
    return ranges, tunes, problems


def _range_at(ranges: list[tuple[float, float]], beat: float) -> float:
    """Bend range in semitones in effect at `beat`."""
    current = ranges[0][1]
    for b, r in ranges:
        if b > beat + 1e-9:
            break
        current = r
    return current


def _note_spans(sc: en.Score, ch: int) -> list[tuple[float, float, int, int]]:
    """Paired notes on `ch` as sorted (on_beat, off_beat, pitch, velocity)."""
    pending: dict[int, list[tuple[float, int]]] = {}
    out: list[tuple[float, float, int, int]] = []
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
    for pitch, queue in pending.items():        # unmatched (defensive)
        for on, vel in queue:
            out.append((on, on, pitch, vel))
    return sorted(out)


def _all_notes(sc: en.Score) -> list[tuple[int, float, float, int, int]]:
    """(ch, on_beat, off_beat, pitch, velocity) for every note."""
    out = []
    for ch in sc.events:
        for on, off, pitch, vel in _note_spans(sc, ch):
            out.append((ch, on, off, pitch, vel))
    return out


def _cap(fails: list[str]) -> list[str]:
    if len(fails) > _REPORT_CAP:
        extra = len(fails) - _REPORT_CAP
        return fails[:_REPORT_CAP] + [
            f"{fails[0].split(':')[0]}: ... and {extra} more failures"]
    return fails


# ---------------------------------------------------------------------------
# The checks (roadmap section 6)
# ---------------------------------------------------------------------------

def check_structure(part, sc: en.Score, info: dict) -> list[str]:
    """Item 1: file parses, per-part duration window, track / marker /
    tempo / timesig counts."""
    cfg = PART_CONFIG[part.number]
    fails = []
    lo, hi = DURATION_WINDOW
    if not lo <= info["seconds"] <= hi:
        fails.append(f"check_structure: duration {info['seconds']:.1f}s "
                     f"outside [{lo:.0f}, {hi:.0f}]s (8:45-9:59)")
    if info["tracks"] != EXPECTED_TRACKS:
        fails.append(f"check_structure: {info['tracks']} MIDI tracks, "
                     f"expected {EXPECTED_TRACKS} (conductor + 16 channels)")
    if info["ppq"] != PPQ:
        fails.append(f"check_structure: PPQ {info['ppq']} != {PPQ}")
    if info["format"] != 1:
        fails.append(f"check_structure: format {info['format']} != 1")
    if len(sc.markers) < MIN_MARKERS:
        fails.append(f"check_structure: {len(sc.markers)} markers, "
                     f"need >= {MIN_MARKERS}")
    if info["tempo_events"] < cfg["min_tempo_events"]:
        fails.append(f"check_structure: {info['tempo_events']} tempo events, "
                     f"need >= {cfg['min_tempo_events']}")
    if len(sc.timesigs) < cfg["min_timesigs"]:
        fails.append(f"check_structure: {len(sc.timesigs)} time signatures, "
                     f"need >= {cfg['min_timesigs']}")
    return fails


def check_material() -> list[str]:
    """Item 2: delegate to the material oracle (tri-guise identity,
    hummable range, chord tones, clash-free stacks, gear-change ranges)."""
    return [f"check_material: {msg}" for msg in material.verify_material()]


def check_cc_inventory(part, sc: en.Score) -> list[str]:
    """Item 3 (counts): the data-driven controller inventory."""
    fails = []
    for ch, num, lo, hi, min_count, trend, label in \
            PART_CONFIG[part.number]["cc_inventory"]:
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


def check_vowels(part, sc: en.Score) -> list[str]:
    """Item 3 (CC70): mm (<= 10) sounding in every hum section, ah (>= 80)
    in every chorus section.  "Sounding" includes the last value set
    before the section starts."""
    fails = []
    for ch, lo, hi, kind in PART_CONFIG[part.number]["vowel_sections"]:
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


def check_pedals(part, sc: en.Score) -> list[str]:
    """Item 3 (pedals): CC64 sustain, CC66 sostenuto, CC67 una corda and
    CC68 legato all strictly alternate down/up and end UP on every channel
    (downs == ups, nothing stuck)."""
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


def check_portamento(part, sc: en.Score) -> list[str]:
    """Item 3 (glide): CC5 and CC65-on present inside each portamento
    passage; the channel's CC65 is OFF again by the deadline."""
    fails = []
    for ch, lo, hi, deadline in PART_CONFIG[part.number]["portamento"]:
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


def check_aftertouch(part, sc: en.Score) -> list[str]:
    """Item 3 (pressure): channel-aftertouch event minimums."""
    fails = []
    for ch, min_count in PART_CONFIG[part.number]["aftertouch_min"]:
        count = len(_at_events(sc, ch))
        if count < min_count:
            fails.append(f"check_aftertouch: ch{ch} has {count} aftertouch "
                         f"events, need >= {min_count}")
    return _cap(fails)


def check_rpn(part, sc: en.Score) -> list[str]:
    """Items 3+4 (RPN): every 101/100/6 sequence well-formed and closed;
    bend-range values sane, > 2 only inside the allowed windows, reset to
    2 by the deadline; the expected fine-tunes present and in range."""
    cfg = PART_CONFIG[part.number]
    fails = []
    tunes_by_ch: dict[int, list[tuple[float, float]]] = {}
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
                    for w_ch, lo, hi, w_r in cfg["rpn_range_windows"]):
                fails.append(f"check_rpn: ch{ch} bend range {r:.0f} at "
                             f"beat {beat:.2f} outside every allowed "
                             f"window")
        deadline = cfg["rpn_reset_by"].get(ch)
        if deadline is not None and len(ranges) > 1 \
                and abs(_range_at(ranges, deadline) - 2.0) > 1e-9:
            fails.append(f"check_rpn: ch{ch} bend range is "
                         f"{_range_at(ranges, deadline):.0f} at beat "
                         f"{deadline:.0f}, must be reset to 2")
    for ch, lo, hi, c_lo, c_hi in cfg["fine_tune_expect"]:
        hits = [(b, c) for b, c in tunes_by_ch.get(ch, [])
                if lo - 1e-6 <= b <= hi + 1e-6 and c_lo <= c <= c_hi]
        if not hits:
            fails.append(f"check_rpn: ch{ch} missing the RPN 1 fine-tune "
                         f"({c_lo:+.0f}..{c_hi:+.0f} cents) in "
                         f"[{lo:.0f},{hi:.0f}]")
    return _cap(fails)


def check_bend_hygiene(part, sc: en.Score) -> list[str]:
    """Item 4: RPN-aware bend magnitudes — |bend semis| = fraction *
    range_at(beat) must not exceed the range in force, and any bend wider
    than 2 semis needs a widened range (i.e. an allowed RPN window).
    Every channel recentred (|s| < 0.01) at the per-part recenter beats
    (movement boundaries + the P1 832 coda)."""
    cfg = PART_CONFIG[part.number]
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
        for b in cfg["bend_recenter_beats"]:
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


def check_lyrics(part, sc: en.Score) -> list[str]:
    """Item 9 (lyrics): lyric metas present in the humming windows."""
    fails = []
    for lo, hi, min_count in PART_CONFIG[part.number]["lyric_windows"]:
        count = sum(1 for beat, _text in sc.lyrics
                    if lo - 1e-9 <= beat <= hi + 1e-9)
        if count < min_count:
            fails.append(f"check_lyrics: {count} lyric metas in "
                         f"[{lo:.0f},{hi:.0f}], need >= {min_count}")
    return _cap(fails)


def check_keysigs(part, sc: en.Score) -> list[str]:
    """Item 9 (key signatures): the 0x59 metas match the grid EXACTLY."""
    expected = PART_CONFIG[part.number]["keysig_grid"]
    got = sorted(sc.keysigs)
    if got != sorted(expected):
        return [f"check_keysigs: keysig metas {got} != grid {expected}"]
    return []


def check_ranges(part, sc: en.Score) -> list[str]:
    """Item 5: notes stay in sensible per-channel MIDI ranges; ch9 uses
    only standard GM percussion notes."""
    fails = []
    for ch in sorted(sc.events):
        for on, _off, pitch, _vel in _note_spans(sc, ch):
            if ch == conductor.CH_DRUMS:
                if pitch not in GM_PERCUSSION:
                    fails.append(f"check_ranges: ch9 percussion note {pitch} "
                                 f"at beat {on:.2f} outside the GM map "
                                 f"(35-81)")
            else:
                lo, hi = NOTE_RANGES.get(ch, (0, 127))
                if not lo <= pitch <= hi:
                    fails.append(f"check_ranges: ch{ch} note {pitch} at "
                                 f"beat {on:.2f} outside [{lo}, {hi}]")
    return _cap(fails)


def check_dynamics_arc(part, sc: en.Score) -> list[str]:
    """Item 6: mean velocity strictly increasing along the per-part chain
    (P1: M1 < M2 < M3; P2: M6 < M4 < M5); density peaks per part."""
    cfg = PART_CONFIG[part.number]
    fails = []
    stats: dict[str, tuple[float, float]] = {}
    notes = _all_notes(sc)
    for name, t0, t1 in part.MOVEMENTS:
        vels = [vel for _ch, on, _off, _p, vel in notes if t0 <= on < t1]
        if not vels:
            fails.append(f"check_dynamics_arc: no notes in '{name}' "
                         f"[{t0:.0f}, {t1:.0f})")
            continue
        stats[name] = (sum(vels) / len(vels), len(vels) / (t1 - t0))
    if len(stats) == len(part.MOVEMENTS):
        chain = [(name, stats[name][0]) for name in cfg["dynamics_order"]]
        for (na, va), (nb, vb) in zip(chain, chain[1:]):
            if va >= vb:
                fails.append(f"check_dynamics_arc: mean velocity "
                             f"'{na}' ({va:.1f}) >= '{nb}' ({vb:.1f}); "
                             f"required order {cfg['dynamics_order']}")
        densest = max(stats, key=lambda nm: stats[nm][1])
        if densest != cfg["density_peak"]:
            fails.append(f"check_dynamics_arc: note density peaks in "
                         f"'{densest}' ({stats[densest][1]:.2f}/beat), "
                         f"must peak in '{cfg['density_peak']}'")
    return _cap(fails)


def check_gaps(part, sc: en.Score, max_gap: float = MAX_GAP_BEATS) -> list[str]:
    """Item 7: no all-channel silent gap longer than `max_gap` beats from
    beat 0 to the last note-off."""
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: no notes anywhere - the part is silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            fails.append(f"check_gaps: all channels silent from beat "
                         f"{horizon:.2f} to {on:.2f} "
                         f"({on - horizon:.2f} beats)")
        horizon = max(horizon, off)
    return _cap(fails)


def check_movement_bounds(part,
                          spans: list[tuple[str, float, float,
                                            list[tuple[int, float]]]],
                          whitelist: list[tuple[int, float, float]] = ()
                          ) -> list[str]:
    """Item 8: every movement module writes note-ons only inside its
    [t0, t1) span.  `spans` is built by build.py: (name, t0, t1,
    [(ch, on_beat), ...]) per module.  `whitelist` lists (ch, lo, hi)
    ranges for documented seam carry-overs.  0.05 beats of slack absorbs
    the humanisation jitter at span starts."""
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

def run_all(parts_data: list[tuple],
            bounds_whitelists: dict[int, list[tuple[int, float, float]]]
            | None = None) -> list[tuple[str, list[str]]]:
    """Run every oracle over both parts.  `parts_data` is a list of
    (part, sc, info, spans) tuples — one per track, in album order.
    Returns [(check_name, failures)]; the material oracle runs once."""
    bounds_whitelists = bounds_whitelists or {}
    results: list[tuple[str, list[str]]] = [
        ("check_material", check_material())]
    for part, sc, info, spans in parts_data:
        tag = f"P{part.number}"
        results += [
            (f"{tag}:check_structure", check_structure(part, sc, info)),
            (f"{tag}:check_cc_inventory", check_cc_inventory(part, sc)),
            (f"{tag}:check_vowels", check_vowels(part, sc)),
            (f"{tag}:check_pedals", check_pedals(part, sc)),
            (f"{tag}:check_portamento", check_portamento(part, sc)),
            (f"{tag}:check_aftertouch", check_aftertouch(part, sc)),
            (f"{tag}:check_rpn", check_rpn(part, sc)),
            (f"{tag}:check_bend_hygiene", check_bend_hygiene(part, sc)),
            (f"{tag}:check_lyrics", check_lyrics(part, sc)),
            (f"{tag}:check_keysigs", check_keysigs(part, sc)),
            (f"{tag}:check_ranges", check_ranges(part, sc)),
            (f"{tag}:check_dynamics_arc", check_dynamics_arc(part, sc)),
            (f"{tag}:check_gaps", check_gaps(part, sc)),
            (f"{tag}:check_movement_bounds", check_movement_bounds(
                part, spans,
                whitelist=bounds_whitelists.get(part.number, []))),
        ]
    return results
