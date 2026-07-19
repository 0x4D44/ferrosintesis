#!/usr/bin/env python3
"""Structural verification for *Bright Matter*."""

from __future__ import annotations

import engine as en
from tracks import common as c

# Every melodic program used by the album is deliberately in a modeled or curated
# ferrosintesis family. Channel 10 is the exception: there the program is a live
# KIT SELECTOR, not inert metadata — this album authors 25, which selects
# ferrosintesis's ORIGINAL drum kit (`Kit::V1`, the voices from before the
# 9-10 Jul 2026 kit-v2/realism overhaul), matching Three-Sixty-One and Slipstream.
# `curated_programs_only` below does NOT exempt channel 10, so the selector value
# has to be listed here as well.
PROGRAM_WHITELIST = {
    0, 1, 4, 5, 8, 11, 12, 19, 25, 28, 30, 38, 39, 46, 49, 52, 53,
    55, 60, 61, 81, 82, 89, 90, 91, 95, 114, 117, 118, 119,
}


def _programs(sc: en.Score) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for ch in sorted(sc.events):
        for event_tick, _priority, data in sc.events[ch]:
            if (data[0] & 0xF0) == 0xC0 and len(data) == 2:
                out.append((event_tick, ch, data[1]))
    return sorted(out)


def generic_checks(spec: en.TrackSpec, sc: en.Score) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []
    note_ons = c.note_ons(sc)

    failures: list[str] = []
    if len(note_ons) < spec.min_notes:
        failures.append(f"{len(note_ons)} note-ons < minimum {spec.min_notes}")
    channels = {ch for _t, ch, _p, _v in note_ons}
    if len(channels) < spec.min_channels:
        failures.append(f"{len(channels)} sounding channels < minimum {spec.min_channels}")
    if len(sc.markers) < spec.min_markers:
        failures.append(f"{len(sc.markers)} markers < minimum {spec.min_markers}")
    if len(sc.tempos) < spec.min_tempo_events:
        failures.append(f"{len(sc.tempos)} tempo events < minimum {spec.min_tempo_events}")
    seconds = sc.duration_seconds()
    if not spec.duration_window[0] <= seconds <= spec.duration_window[1]:
        failures.append(
            f"duration {seconds:.2f}s outside {spec.duration_window[0]:.1f}..{spec.duration_window[1]:.1f}s"
        )
    results.append(("density_breadth_and_duration", failures))

    failures = []
    stray = [(tick, ch, prog) for tick, ch, prog in _programs(sc)
             if prog not in PROGRAM_WHITELIST]
    if stray:
        failures.append(f"programs outside whitelist: {stray[:6]}")
    if 9 not in sc.events:
        failures.append("no percussion channel")
    results.append(("curated_programs_only", failures))

    failures = []
    for ch in sorted(sc.events):
        if ch == 9:
            continue
        cc64 = c.cc_lane(sc, ch, 64)
        bends = c.bend_lane(sc, ch)
        if not cc64 or cc64[-1][1] != 0:
            failures.append(f"ch{ch} sustain is not reset")
        if bends and bends[-1][1] != 8192:
            failures.append(f"ch{ch} bend ends at {bends[-1][1]}, not centre")
    results.append(("sticky_controller_hygiene", failures[:8]))

    failures = []
    # Sustained scenic beds remain centered. The only intentionally wide fixed
    # channels identify themselves by name; the orbit must return to centre.
    for ch, name in sc.names.items():
        lane = c.cc_lane(sc, ch, 10)
        values = {value for _tick, value in lane}
        lowered = name.lower()
        if lowered.endswith(" left") or " left " in lowered:
            if values != {18} and values != {20} and values != {22} and values != {24}:
                failures.append(f"{name} pans {sorted(values)}")
        elif lowered.endswith(" right") or " right " in lowered:
            if values != {104} and values != {106} and values != {108} and values != {110}:
                failures.append(f"{name} pans {sorted(values)}")
        elif "orbit" in name:
            if lane and lane[-1][1] != 64:
                failures.append(f"{name} does not land at centre")
        elif values - {64}:
            failures.append(f"sustained channel {name!r} leaves centre: {sorted(values)[:6]}")
    results.append(("stereo_width_is_transient_or_antiphonal", failures[:8]))

    failures = []
    marker_beats = [beat for beat, _text in sorted(sc.markers)]
    if marker_beats != sorted(set(marker_beats)):
        failures.append("markers are duplicated or out of order")
    if not marker_beats or marker_beats[0] != 0.0:
        failures.append("first marker is not at beat zero")
    if marker_beats and marker_beats[-1] >= spec.beats:
        failures.append("last marker is outside the score")
    results.append(("section_map_is_well_formed", failures))

    failures = []
    # The signature sequence is not a documentation-only claim: require the bass
    # to state at least sixteen complete vi-V-ii-I cycles somewhere in the score.
    bass_candidates = [ch for ch, name in sc.names.items() if "bass" in name]
    if not bass_candidates:
        failures.append("no named bass channel")
    else:
        bass = bass_candidates[0]
        downbeats: list[int] = []
        for beat in range(0, int(spec.beats), 4):
            pitches = c.notes_near(sc, bass, float(beat), tolerance_ticks=4)
            if pitches:
                downbeats.append(min(pitches) % 12)
        transitions = [((b - a) % 12) for a, b in zip(downbeats, downbeats[1:])]
        hits = sum(1 for i in range(len(transitions) - 2)
                   if transitions[i:i + 3] == [10, 7, 10])
        if hits < 8:
            failures.append(f"only {hits} downbeat 6-5-2-1 transition triplets")
    results.append(("signature_progression_is_audible_in_bass", failures))

    return results


def run_track(spec: en.TrackSpec, sc: en.Score) -> list[tuple[str, list[str]]]:
    prefix = f"T{spec.number:02d}"
    rows = generic_checks(spec, sc) + spec.oracle(sc)
    return [(f"{prefix} {name}", failures) for name, failures in rows]


def run_all(built: list[tuple[en.TrackSpec, en.Score]]) -> list[tuple[str, list[str]]]:
    results: list[tuple[str, list[str]]] = []
    for spec, score in built:
        results.extend(run_track(spec, score))

    failures: list[str] = []
    if len(built) != 5:
        failures.append(f"album has {len(built)} tracks, want 5")
    titles = [spec.title for spec, _score in built]
    if len(titles) != len(set(titles)):
        failures.append("track titles are not unique")
    if not all("6521" in spec.tags for spec, _score in built):
        failures.append("not every track declares the 6521 through-line")
    results.append(("ALBUM five_tracks_one_through_line", failures))

    return results
