"""movements — the ten songs of *Big Weather*, in registry order.

Each module tNN_<stem>.py is SELF-CONTAINED: it declares its registry
identity (NUMBER / TITLE / FILE / SEED), its `PART` (the conductor.Part
grid whose movements are the song's sections — verse / pre-chorus /
chorus / middle-8 / feature windows), its `BUILDERS` (one per section,
run in order by build.py), its verification config (PROGRAM_WHITELIST,
CENTERED_CHANNELS, NOTE_RANGES, GAP_WHITELIST, BEND_EXEMPT,
DURATION_WINDOW, BOUNDS_WHITELIST) plus the Big Weather song-oracle
configs (ENERGY_RULES, LATE_CHANNELS, BASS_SPEC, CHOIR_SPEC,
FEATURES_EXPECTED, and DRUM_SOLO_SPEC on the drum-feature tracks), and
its track-specific `oracles()` (plus an optional `audio_checks()` for
analyze.py).  A composer replaces a stub file wholesale and the album
machinery picks it up unchanged.

`load_tracks()` yields the module list in conductor.REGISTRY order;
loading also asserts each module still agrees with the registry on its
identity.  Loading is LAZY and can be scoped to one track
(`load_tracks(only=N)`) so composers can work concurrently: a half-saved
syntax error in one module must not break another track's
`build.py --track N` loop.
"""

from __future__ import annotations

import importlib

import conductor


def load_tracks(only: int | None = None) -> list:
    """Import and identity-check the track modules (all, or just one)."""
    mods = []
    for num, stem, title, file, seed in conductor.REGISTRY:
        if only is not None and num != only:
            continue
        mod = importlib.import_module(f"{__name__}.{stem}")
        for attr, want in (("NUMBER", num), ("TITLE", title),
                           ("FILE", file), ("SEED", seed)):
            got = getattr(mod, attr, None)
            if got != want:
                raise RuntimeError(
                    f"movements/{stem}.py: {attr} = {got!r} disagrees "
                    f"with conductor.REGISTRY ({want!r})")
        mods.append(mod)
    if not mods:
        raise SystemExit(f"no track {only} "
                         f"(have 1..{len(conductor.REGISTRY)})")
    return mods
