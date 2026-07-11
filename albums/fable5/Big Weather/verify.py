"""verify.py — the shared structural-oracle library of *Big Weather*.

The Through Lines generic disciplines (structure, programs, pan, ranges,
gaps, overlaps, bend hygiene, movement bounds) plus the Big Weather
song-oracles that encode the album brief as numbers (HLD §6.1):

  * check_song_energy   — duration-weighted section-energy inequalities
                          (builds and drops as a contour of numbers);
  * check_late_channels — orchestral layers silent before their entry
                          beat ("the orchestra arrives as the song builds");
  * check_bass_melody   — the bass is a melodic line, not a root pump;
  * check_choir_layers  — layered wordless choir on the declared tracks;
  * check_feature_coverage — >= 6 advanced-MIDI features authored
                          ON-TARGET (the program active at the event's
                          beat must honor the controller);
  * check_drum_solo     — the drum-feature windows really are dense,
                          wide, alternating solos.

Every song-oracle reads its config from the track module and is skipped
when the module omits the attribute (used deliberately: only drum-feature
tracks declare DRUM_SOLO_SPEC; non-choir tracks omit CHOIR_SPEC).
`run_track(module, sc, info, spans)` returns [(check_name, failures)];
build.py prefixes the track tag and exits nonzero on any failure.  `info`
may be None (build.py --check): file-dependent checks are then skipped.
"""

from __future__ import annotations

import engine as en

PPQ = en.PPQ
DRUM_CH = 9
GM_PERCUSSION = set(range(35, 82))       # the standard GM percussion map
GM2_PERCUSSION = (27, 87)                # GM2 extends the map downward
MAX_GAP_BEATS = 1.5
_REPORT_CAP = 8

# ---------------------------------------------------------------------------
# The drum-kit stereo placement table — a PINNED COPY of ferrosintesis
# `crates/ferrosintesis/src/engine.rs::drum_pan()` (~lines 172-184) at
# synth v0.13.x (drummer's perspective, 0.5 = centre).  The synth is
# frozen for this task (HLD non-goal); if the kit is ever retuned, refresh
# this table.  Keys absent here render centred (0.5).
# ---------------------------------------------------------------------------

DRUM_PAN = {
    42: 0.33, 44: 0.33, 46: 0.33,        # hats
    49: 0.25, 55: 0.25,                  # crash-1, splash
    41: 0.55, 43: 0.62, 45: 0.62,        # floor/low toms
    47: 0.42, 48: 0.42, 50: 0.32,        # mid/high toms
    51: 0.70, 53: 0.70, 59: 0.70,        # ride family
    52: 0.75, 57: 0.75,                  # china, crash-2
}

# The WIDE set (HLD §6.1, Codex-4): keys with |pan - 0.5| >= 0.17.  Mid and
# floor toms (0.05-0.12 off-centre) count toward pan-group diversity and
# L/R alternation, never the wide quota.  The 1e-9 tolerance keeps the hats
# at pan 0.33 in the set: |0.33 - 0.5| evaluates to 0.16999999999999998 in
# binary float, so a bare `>= 0.17` would silently drop keys 42/44/46 that
# the HLD names explicitly as wide.
WIDE_KEYS = {k for k, p in DRUM_PAN.items() if abs(p - 0.5) >= 0.17 - 1e-9}

# ---------------------------------------------------------------------------
# The advanced-MIDI honoring table (HLD §5): feature -> the GM programs on
# which ferrosintesis actually renders it audibly.  A feature event counts
# ONLY when the program active on its channel at its onset beat honors it
# (presence in the MIDI is not audibility in the render — repo lesson).
# Sets are conservative: under-counting is safe, over-counting is not.
# ---------------------------------------------------------------------------

_SUSTAINED = (set(range(40, 55)) | set(range(56, 80))
              | set(range(80, 86)) | {22, 23})
FEATURE_PROGRAMS = {
    "bend_range":     None,                       # any pitched channel
    "pitch_bend":     None,
    "cc1_vibrato":    _SUSTAINED,
    "cc1_leslie":     {16, 17, 18},
    "cc68_legato":    set(range(24, 55)) | set(range(56, 86)),
    "cc74_wah":       None,                       # filter insert: universal
    "cc64_sustain":   set(range(0, 8)) | set(range(24, 32)) | {46},
    "cc67_soft":      {0, 1, 2, 3},
    "cc11_expression": None,
    "cc2_breath":     set(range(56, 80)),
    "aftertouch":     set(range(16, 24)) | {47} | set(range(40, 80)),
    "portamento":     set(range(32, 40)) | set(range(72, 88)),
    "cc70_vowel":     {52, 53, 54, 91},
    "cc94_echo":      None,
    "program_change": None,
}


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


def _program_timeline(sc, ch):
    """Deterministic per-channel program timeline: sorted [(beat, prog)].

    The channel() setup program plus every scheduled program() change,
    from the Score's own events (HLD §6.1 Codex-2 contract).  A change at
    beat b governs events at beats >= b.
    """
    return sorted(_programs(sc, ch))


def _program_at(timeline, beat):
    prog = None
    for b, p in timeline:
        if b <= beat + 1e-9:
            prog = p
        else:
            break
    return prog


def _section(part, name):
    for n, t0, t1 in part.MOVEMENTS:
        if n == name:
            return t0, t1
    return None


def _cap(fails):
    if len(fails) > _REPORT_CAP:
        extra = len(fails) - _REPORT_CAP
        return fails[:_REPORT_CAP] + [
            f"{fails[0].split(':')[0]}: ... and {extra} more failures"]
    return fails


# ---------------------------------------------------------------------------
# The generic checks (parameterized by the track module) — Through Lines
# ---------------------------------------------------------------------------

def check_structure(module, sc, info):
    part = module.PART
    fails = []
    if info is not None:
        lo, hi = module.DURATION_WINDOW
        if not lo <= info["seconds"] <= hi:
            fails.append(f"duration {info['seconds']:.1f}s outside "
                         f"({lo:.1f}, {hi:.1f})")
        want_tracks = 1 + len(part.CHANNELS)
        if info["tracks"] != want_tracks:
            fails.append(f"{info['tracks']} tracks, want {want_tracks} "
                         f"(conductor + {len(part.CHANNELS)} channels)")
        score_notes = len(_all_notes(sc))
        if info["notes"] != score_notes:
            fails.append(f"file has {info['notes']} notes, Score built "
                         f"{score_notes}")
    if sorted(sc.tempos) != sorted(part.TEMPO_MAP):
        fails.append("tempo map differs from PART.TEMPO_MAP")
    want_keysigs = sorted((b, int(s), 1 if m else 0)
                          for b, s, m in part.KEYSIGS)
    if sorted(sc.keysigs) != want_keysigs:
        fails.append("key signature grid differs from PART.KEYSIGS")
    marker_beats = {b for b, _t in sc.markers}
    for name, t0, _t1 in part.MOVEMENTS:
        if t0 not in marker_beats:
            fails.append(f"missing movement marker '{name}' at beat {t0}")
    for beat, text in part.EXTRA_MARKERS:
        if beat not in marker_beats:
            fails.append(f"missing extra marker '{text}' at beat {beat}")
    return _cap(fails)


def check_programs(module, sc):
    fails = []
    for ch in sorted(sc.events):
        if ch == DRUM_CH:
            continue
        for beat, prog in _programs(sc, ch):
            if prog not in module.PROGRAM_WHITELIST:
                fails.append(f"ch{ch} program {prog} at beat {beat:.1f} "
                             f"not in the track's whitelist")
    return _cap(fails)


def check_pan(module, sc):
    fails = []
    for ch in sorted(module.CENTERED_CHANNELS):
        bad = [(b, v) for b, v in _cc_events(sc, ch, 10) if v != 64]
        if bad:
            fails.append(f"ch{ch} is a centered channel but pans to "
                         f"{bad[:3]} (must stay 64)")
    return _cap(fails)


def check_ranges(module, sc):
    fails = []
    for ch, (lo, hi) in sorted(module.NOTE_RANGES.items()):
        for on, _off, p, _v in _note_spans(sc, ch):
            if not lo <= p <= hi:
                fails.append(f"ch{ch} pitch {p} at beat {on:.1f} outside "
                             f"[{lo},{hi}]")
    if DRUM_CH in module.NOTE_RANGES:
        g_lo, g_hi = GM2_PERCUSSION
        for on, _off, p, _v in _note_spans(sc, DRUM_CH):
            if not g_lo <= p <= g_hi:
                fails.append(f"drum note {p} at {on:.1f} outside GM2 "
                             f"percussion [{g_lo},{g_hi}]")
    else:
        for on, _off, p, _v in _note_spans(sc, DRUM_CH):
            if p not in GM_PERCUSSION:
                fails.append(f"drum note {p} at {on:.1f} outside GM range")
    return _cap(fails)


def check_gaps(module, sc, max_gap=MAX_GAP_BEATS):
    spans = sorted((on, off) for _ch, on, off, _p, _v in _all_notes(sc))
    if not spans:
        return ["check_gaps: the piece is silent"]
    fails = []
    horizon = 0.0
    for on, off in spans:
        if on - horizon > max_gap:
            if not any(lo <= horizon and on <= hi
                       for lo, hi in module.GAP_WHITELIST):
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


def check_bend_hygiene(module, sc):
    part = module.PART
    fails = []
    boundaries = [t0 for _n, t0, _t1 in part.MOVEMENTS][1:]
    for ch in sorted(sc.events):
        fracs = _bend_fracs(sc, ch)
        if not fracs:
            continue
        if ch in module.BEND_EXEMPT:
            for name, t0, t1 in part.MOVEMENTS:
                vals = [f for b, f in fracs if t0 - 0.05 <= b < t1 - 0.05]
                if vals and max(vals) - min(vals) > 1e-6:
                    fails.append(f"ch{ch} bend moves inside '{name}' "
                                 f"({min(vals):+.3f}..{max(vals):+.3f}); "
                                 f"BEND_EXEMPT channels must hold constant")
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
# The Big Weather song-oracles (HLD §6.1) — each driven by module config,
# skipped when the module omits the attribute.
# ---------------------------------------------------------------------------

def _beats_per_bar(part, beat):
    """Quarter-note beats per bar under the time signature active at `beat`."""
    num, den = 4, 4
    for b, n, d in sorted(part.TIME_SIGNATURES):
        if b <= beat + 1e-9:
            num, den = n, d
    return num * 4.0 / den


def section_energy(module, sc, name):
    """Duration-weighted energy per bar of the named section (HLD D10).

    E = sum(vel * min(dur_beats, 2.0)) / bars — counts held power chords
    and pads honestly where a bare note-on count would measure density.
    """
    span = _section(module.PART, name)
    if span is None:
        return None
    t0, t1 = span
    acc = 0.0
    for _ch, on, off, _p, vel in _all_notes(sc):
        if t0 - 1e-9 <= on < t1 - 1e-9:
            acc += vel * min(max(off - on, 0.05), 2.0)
    bars = (t1 - t0) / _beats_per_bar(module.PART, t0)
    return acc / bars if bars > 0 else 0.0


def check_song_energy(module, sc):
    """ENERGY_RULES: [(lhs, op, rhs, factor)] with op in {'>=', '<='} —
    E[lhs] op factor * E[rhs].  Explicit pairwise inequalities only; no
    global max (HLD D10)."""
    rules = getattr(module, "ENERGY_RULES", None)
    if rules is None:
        return []
    fails = []
    cache: dict[str, float | None] = {}

    def energy(name):
        if name not in cache:
            cache[name] = section_energy(module, sc, name)
        return cache[name]

    for lhs, op, rhs, factor in rules:
        if op not in (">=", "<="):
            fails.append(f"ENERGY_RULES has unknown op {op!r} "
                         f"(must be '>=' or '<=')")
            continue
        el, er = energy(lhs), energy(rhs)
        if el is None or er is None:
            missing = lhs if el is None else rhs
            fails.append(f"ENERGY_RULES names unknown section '{missing}'")
            continue
        ok = el >= factor * er if op == ">=" else el <= factor * er
        if not ok:
            fails.append(f"E[{lhs}]={el:.0f} not {op} {factor} * "
                         f"E[{rhs}]={er:.0f}")
    return _cap(fails)


def check_late_channels(module, sc):
    """LATE_CHANNELS: {ch: first_beat} — the orchestral layers must be
    silent before their declared entry (HLD: 'the orchestra arrives as
    the song builds').  Author entries with jt=0 (boundary lesson)."""
    late = getattr(module, "LATE_CHANNELS", None)
    if late is None:
        return []
    fails = []
    for ch, first in sorted(late.items()):
        notes = _note_spans(sc, ch)
        if not notes:
            fails.append(f"ch{ch} is declared late (entry {first}) but "
                         f"never sounds at all")
            continue
        early = [on for on, _off, _p, _v in notes if on < first - 0.05]
        if early:
            fails.append(f"ch{ch} sounds at beat {min(early):.2f}, before "
                         f"its declared entry at {first}")
    return _cap(fails)


def check_bass_melody(module, sc):
    """BASS_SPEC: {"channel": ch, "sections": [(name, root_pc), ...],
    "hook": name} — the bass is a melodic line (HLD §6.1): per listed
    section >= 5 distinct pitches and >= 2 non-root pitch classes; >= 40%
    stepwise motion across the listed sections; whole-track span >= 12
    semitones; the hook section carries a countermelody (>= 6 distinct
    pitches spanning >= 7 semitones)."""
    spec = getattr(module, "BASS_SPEC", None)
    if spec is None:
        return []
    ch = spec["channel"]
    notes = _note_spans(sc, ch)
    fails = []
    if not notes:
        return [f"BASS_SPEC: ch{ch} has no notes"]
    pitches = [p for _on, _off, p, _v in notes]
    if max(pitches) - min(pitches) < 12:
        fails.append(f"bass span {max(pitches) - min(pitches)} semitones "
                     f"(< 12) across the track")
    steps = total = 0
    for name, root_pc in spec["sections"]:
        span = _section(module.PART, name)
        if span is None:
            fails.append(f"BASS_SPEC names unknown section '{name}'")
            continue
        t0, t1 = span
        sect = [(on, p) for on, _off, p, _v in notes
                if t0 - 1e-9 <= on < t1 - 1e-9]
        pcs = {p % 12 for _on, p in sect}
        if len({p for _on, p in sect}) < 5:
            fails.append(f"'{name}': {len({p for _on, p in sect})} distinct "
                         f"bass pitches (< 5)")
        if len(pcs - {root_pc % 12}) < 2:
            fails.append(f"'{name}': fewer than 2 non-root pitch classes "
                         f"(root pc {root_pc % 12})")
        ordered = [p for _on, p in sorted(sect)]
        for a, b in zip(ordered, ordered[1:]):
            total += 1
            if abs(a - b) <= 2:
                steps += 1
    if total and steps / total < 0.40:
        fails.append(f"stepwise motion {steps}/{total} = "
                     f"{steps / total:.0%} (< 40%) across listed sections")
    hook = spec.get("hook")
    if hook:
        span = _section(module.PART, hook)
        if span is None:
            fails.append(f"BASS_SPEC hook names unknown section '{hook}'")
        else:
            t0, t1 = span
            hp = [p for on, _off, p, _v in notes
                  if t0 - 1e-9 <= on < t1 - 1e-9]
            if len(set(hp)) < 6 or (hp and max(hp) - min(hp) < 7):
                fails.append(f"hook '{hook}': bass countermelody too plain "
                             f"({len(set(hp))} pitches, span "
                             f"{max(hp) - min(hp) if hp else 0})")
    return _cap(fails)


def _concurrency_runs(spans, t0, t1, want):
    """Longest contiguous run (in beats) inside [t0,t1) during which the
    number of DISTINCT sounding pitches across `spans` is >= want."""
    events = []
    for on, off, p in spans:
        on, off = max(on, t0), min(off, t1)
        if off > on:
            events.append((on, 1, p))
            events.append((off, -1, p))
    events.sort()
    active: dict[int, int] = {}
    best = run_start = 0.0
    running = False
    for beat, delta, p in events:
        if delta > 0:
            active[p] = active.get(p, 0) + 1
        else:
            active[p] -= 1
            if active[p] <= 0:
                del active[p]
        now = len(active)
        if not running and now >= want:
            running, run_start = True, beat
        elif running and now < want:
            best = max(best, beat - run_start)
            running = False
    if running:
        best = max(best, t1 - run_start)
    return best


def check_choir_layers(module, sc):
    """CHOIR_SPEC: {"channels": [...], "sections": [names]} — layered
    wordless choir (HLD §6.1): in each listed section >= 2 choir channels
    sound simultaneously (>= 1 beat) and >= 3 concurrent distinct pitches
    hold >= 2 beats; CC70 authored on >= 1 choir channel in the track."""
    spec = getattr(module, "CHOIR_SPEC", None)
    if spec is None:
        return []
    chans = spec["channels"]
    fails = []
    pitch_spans = []
    chan_spans = []
    for ch in chans:
        for on, off, p, _v in _note_spans(sc, ch):
            pitch_spans.append((on, off, p))
            chan_spans.append((on, off, ch))
    for name in spec["sections"]:
        span = _section(module.PART, name)
        if span is None:
            fails.append(f"CHOIR_SPEC names unknown section '{name}'")
            continue
        t0, t1 = span
        if _concurrency_runs(chan_spans, t0, t1, 2) < 1.0:
            fails.append(f"'{name}': no >=1-beat stretch with 2 choir "
                         f"channels sounding together")
        if _concurrency_runs(pitch_spans, t0, t1, 3) < 2.0:
            fails.append(f"'{name}': no >=2-beat stretch with 3 concurrent "
                         f"distinct choir pitches")
    if not any(_cc_events(sc, ch, 70) for ch in chans):
        fails.append("no CC70 vowel morph authored on any choir channel")
    return _cap(fails)


def _detect_features(sc):
    """The set of §5 features authored ON-TARGET (see FEATURE_PROGRAMS)."""
    found: set[str] = set()
    timelines = {ch: _program_timeline(sc, ch)
                 for ch in sc.events if ch != DRUM_CH}

    def on_target(feature, ch, beat):
        progs = FEATURE_PROGRAMS[feature]
        if progs is None:
            return True
        prog = _program_at(timelines.get(ch, []), beat)
        return prog in progs

    for ch in sorted(sc.events):
        if ch == DRUM_CH:
            continue
        cc: dict[int, list[tuple[float, int]]] = {}
        for tick, _prio, data in sc.events[ch]:
            if (data[0] & 0xF0) == 0xB0:
                cc.setdefault(data[1], []).append((tick / PPQ, data[2]))
        # RPN0 bend range != 2: CC6 while the last CC100/101 pair is (0,0).
        rpn = {100: 127, 101: 127}
        stream = sorted(((b, n, v) for n, evs in cc.items()
                         for b, v in evs if n in (6, 100, 101)),
                        key=lambda e: e[0])
        for beat, num, val in stream:
            if num in (100, 101):
                rpn[num] = val
            elif num == 6 and rpn[100] == 0 and rpn[101] == 0 and val != 2:
                found.add("bend_range")
        bends = _bend_fracs(sc, ch)
        if len({v for _b, v in bends}) >= 3:
            found.add("pitch_bend")
        # cc67_soft needs >= 64: CC67 is a pedal, and a lone pedal-UP
        # (value 0) event must not count as using the feature.  CC70=0
        # stays countable — 0 is the "mm" vowel, a real setting.
        for feature, num, min_events, min_peak in (
                ("cc1_vibrato", 1, 1, 20), ("cc1_leslie", 1, 1, 20),
                ("cc74_wah", 74, 3, 0), ("cc11_expression", 11, 4, 0),
                ("cc2_breath", 2, 2, 0), ("cc70_vowel", 70, 1, 0),
                ("cc67_soft", 67, 1, 64)):
            evs = cc.get(num, [])
            hits = [(b, v) for b, v in evs
                    if v >= min_peak and on_target(feature, ch, b)]
            if len(hits) >= min_events:
                found.add(feature)
        if any(v >= 64 and on_target("cc68_legato", ch, b)
               for b, v in cc.get(68, [])):
            found.add("cc68_legato")
        if any(v >= 64 and on_target("cc64_sustain", ch, b)
               for b, v in cc.get(64, [])):
            found.add("cc64_sustain")
        if (any(v >= 64 and on_target("portamento", ch, b)
                for b, v in cc.get(65, []))
                and cc.get(5)):
            found.add("portamento")
        if any(v > 0 for _b, v in cc.get(94, [])):
            found.add("cc94_echo")
        for tick, _prio, data in sc.events[ch]:
            if (data[0] & 0xF0) == 0xD0 and on_target(
                    "aftertouch", ch, tick / PPQ):
                found.add("aftertouch")
                break
        if len(_programs(sc, ch)) > 1:
            found.add("program_change")
    return found


def check_feature_coverage(module, sc):
    """FEATURES_EXPECTED: set of feature names the track claims (>= 6).
    Verifies every claimed feature is authored on-target and that at
    least 6 distinct on-target features exist overall."""
    expected = getattr(module, "FEATURES_EXPECTED", None)
    if expected is None:
        return []
    fails = []
    unknown = set(expected) - set(FEATURE_PROGRAMS)
    if unknown:
        fails.append(f"unknown feature names: {sorted(unknown)}")
    found = _detect_features(sc)
    missing = set(expected) - unknown - found
    if missing:
        fails.append(f"claimed features not authored on-target: "
                     f"{sorted(missing)}")
    if len(found) < 6:
        fails.append(f"only {len(found)} on-target features "
                     f"({sorted(found)}); need >= 6")
    return _cap(fails)


def check_drum_solo(module, sc):
    """DRUM_SOLO_SPEC: {"windows": [(t0, t1)], "accompanists": {ch}} —
    each window is a real, wide, dense solo (HLD §6.1): non-drum silence
    except declared accompanists; >= 6 distinct keys over >= 5 pan
    groups; density >= 12 hits/bar avg with >= 2 bars >= 20 hits; wide-set
    hits >= 2 per bar on average; >= 4 L/R alternations."""
    spec = getattr(module, "DRUM_SOLO_SPEC", None)
    if spec is None:
        return []
    if not spec["windows"]:
        return ["DRUM_SOLO_SPEC declares no windows (a drum-feature "
                "track must name at least one)"]
    fails = []
    allowed = set(spec.get("accompanists", ()))
    for t0, t1 in spec["windows"]:
        tag = f"solo [{t0:.0f},{t1:.0f})"
        for ch in sorted(sc.events):
            if ch == DRUM_CH or ch in allowed:
                continue
            intruders = [on for on, _off, _p, _v in _note_spans(sc, ch)
                         if t0 - 1e-9 <= on < t1 - 0.05]
            if intruders:
                fails.append(f"{tag}: ch{ch} plays at beat "
                             f"{min(intruders):.2f} (not an accompanist)")
        hits = [(on, p) for on, _off, p, _v in _note_spans(sc, DRUM_CH)
                if t0 - 1e-9 <= on < t1 - 1e-9]
        bars = (t1 - t0) / _beats_per_bar(module.PART, t0)
        keys = {p for _on, p in hits}
        groups = {DRUM_PAN.get(p, 0.5) for p in keys}
        if len(keys) < 6:
            fails.append(f"{tag}: {len(keys)} distinct keys (< 6)")
        if len(groups) < 5:
            fails.append(f"{tag}: {len(groups)} pan groups (< 5)")
        if bars > 0 and len(hits) / bars < 12:
            fails.append(f"{tag}: {len(hits) / bars:.1f} hits/bar (< 12)")
        bpb = _beats_per_bar(module.PART, t0)
        burst_bars = 0
        b = t0
        while b < t1 - 1e-9:
            n = sum(1 for on, _p in hits if b <= on < b + bpb)
            if n >= 20:
                burst_bars += 1
            b += bpb
        if burst_bars < 2:
            fails.append(f"{tag}: {burst_bars} bars with >= 20 hits (< 2 "
                         f"32nd-note burst bars)")
        wide = sum(1 for _on, p in hits if p in WIDE_KEYS)
        if bars > 0 and wide / bars < 2.0:
            fails.append(f"{tag}: {wide} wide-set hits over {bars:.0f} "
                         f"bars (< 2/bar; wide = |pan-0.5| >= 0.17)")
        sides = [DRUM_PAN.get(p, 0.5) for on, p in sorted(hits)]
        sides = ["L" if s < 0.5 else "R" for s in sides if s != 0.5]
        alternations = sum(1 for a, b2 in zip(sides, sides[1:]) if a != b2)
        if alternations < 4:
            fails.append(f"{tag}: {alternations} L/R alternations (< 4)")
    return _cap(fails)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_track(module, sc, info, spans) -> list[tuple[str, list[str]]]:
    """All generic checks, the song-oracles, then the module's own."""
    results = [
        ("check_structure", check_structure(module, sc, info)),
        ("check_programs", check_programs(module, sc)),
        ("check_pan", check_pan(module, sc)),
        ("check_ranges", check_ranges(module, sc)),
        ("check_gaps", check_gaps(module, sc)),
        ("check_overlaps", check_overlaps(sc)),
        ("check_bend_hygiene", check_bend_hygiene(module, sc)),
        ("check_movement_bounds", check_movement_bounds(
            spans, whitelist=module.BOUNDS_WHITELIST)),
        ("check_song_energy", check_song_energy(module, sc)),
        ("check_late_channels", check_late_channels(module, sc)),
        ("check_bass_melody", check_bass_melody(module, sc)),
        ("check_choir_layers", check_choir_layers(module, sc)),
        ("check_feature_coverage", check_feature_coverage(module, sc)),
        ("check_drum_solo", check_drum_solo(module, sc)),
    ]
    results.extend(module.oracles(sc, info, spans))
    return results
