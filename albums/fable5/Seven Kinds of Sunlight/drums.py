"""drums.py — the groove and fill engine of *Seven Kinds of Sunlight*.

The brief for this song is INCREDIBLE DRUMS: grooves for every meter
the song visits (4/4, 7/8 as 3+2+2, 6/8, 5/4 as 3+2), ghost-note
snare work, and a fill LIBRARY — five distinct fill styles that the
section writers rotate through, each seeded through the Score's RNG so
no two fills land identically but every build is reproducible.

GM map used here: 36 kick, 38 snare, 37 side stick, 39 clap, 42 closed
hat, 46 open hat, 41/43/45/47/48/50 toms (low->high), 49/57 crashes,
51 ride, 53 ride bell, 55 splash.
"""

from __future__ import annotations

import engine as en
from engine import lerp

K, SN, STICK, CLAP = 36, 38, 37, 39
HH, OH, RIDE, BELL, SPLASH = 42, 46, 51, 53, 55
TOMS = (50, 48, 47, 45, 43, 41)                 # high -> low
CRASH, CRASH2 = 49, 57


# ---------------------------------------------------------------------------
# Fills — one bar or half-bar statements; `style` rotates per call site.
# ---------------------------------------------------------------------------

FILL_STYLES = ("cascade", "ruff", "flam", "kick16", "scatter")


def fill(sc: en.Score, t: float, beats: float, style: str,
         vel: int = 84) -> None:
    """Write a fill occupying [t, t + beats).  Ends hot; the caller
    supplies the landing crash."""
    rng = sc.rng
    if style == "cascade":                       # toms high -> low
        n = int(beats * 4)
        for s in range(n):
            drum = TOMS[min(len(TOMS) - 1, (s * len(TOMS)) // n)]
            v = int(lerp(vel - 12, vel + 12, s / max(1, n - 1)))
            sc.hit(drum, t + s * 0.25, v, jt=2)
    elif style == "ruff":                        # 32nd snare ruffs + accents
        b = 0.0
        while b < beats - 1e-9:
            if rng.random() < 0.35:
                for k in range(3):               # the ruff
                    sc.hit(SN, t + b + k * 0.125, vel - 28 + 6 * k, jt=1)
                sc.hit(SN, t + b + 0.375, vel + 8, jt=1)
                b += 0.5
            else:
                sc.hit(SN, t + b, vel - rng.randint(0, 18), jt=2)
                b += 0.25
    elif style == "flam":                        # flammed snare/tom pairs
        n = int(beats * 2)
        for s in range(n):
            drum = SN if s % 2 == 0 else TOMS[rng.randint(0, 3)]
            sc.hit(drum, t + s * 0.5 - 0.03, vel - 26, jt=1)
            sc.hit(drum, t + s * 0.5, vel + (6 if s == n - 1 else 0), jt=1)
    elif style == "kick16":                      # kick/snare 16th interplay
        pattern = [K, K, SN, K, SN, K, K, SN, K, SN, SN, K, SN, SN, SN, SN]
        n = int(beats * 4)
        for s in range(n):
            drum = pattern[s % 16]
            v = vel + (8 if s % 4 == 0 else -8)
            sc.hit(drum, t + s * 0.25, v, jt=1)
    elif style == "scatter":                     # broken kit, gaps included
        slots = int(beats * 4)
        kit = (SN, TOMS[0], TOMS[2], TOMS[4], K, SPLASH)
        for s in range(slots):
            if rng.random() < 0.72:
                drum = kit[rng.randint(0, len(kit) - 1)]
                sc.hit(drum, t + s * 0.25,
                       vel - 14 + rng.randint(0, 20), jt=2)
    else:
        raise ValueError(f"unknown fill style {style!r}")


def snare_build(sc: en.Score, t0: float, t1: float, v0: int, v1: int,
                step: float = 0.25) -> None:
    b = t0
    while b < t1 - 1e-9:
        sc.hit(SN, b, int(lerp(v0, v1, (b - t0) / (t1 - t0))), jt=2, jv=3)
        b += step


# ---------------------------------------------------------------------------
# Grooves.  `energy` 1..3 scales velocity and ghost density.
# ---------------------------------------------------------------------------


def groove_44(sc: en.Score, t0: float, bars: int, energy: int = 2,
              fill_every: int = 4, fill_styles=FILL_STYLES,
              ride_from: float | None = None) -> None:
    """The chorus engine: four on the floor leaning kick, clap-stacked
    backbeat, 16th hats with off-8th accents, open hat into each bar,
    and a rotating fill in the back half of every `fill_every`th bar."""
    rng = sc.rng
    base = 70 + 8 * energy
    fi = 0
    for bar in range(bars):
        t = t0 + 4.0 * bar
        fill_bar = fill_every and bar % fill_every == fill_every - 1
        for k, beat in enumerate((0.0, 1.0, 2.0, 3.0)):
            sc.hit(K, t + beat, base + (6 if k == 0 else -4))
        if energy >= 2:
            sc.hit(K, t + 2.75, base - 18)
        for beat in (1.0, 3.0):
            sc.hit(SN, t + beat, base + 6)
            sc.hit(CLAP, t + beat, base - 24)
        span = 2.0 if fill_bar else 4.0
        use_ride = ride_from is not None and t >= ride_from
        for s in range(int(span * 4)):
            beat = s * 0.25
            v = (base - 8 if s % 4 == 2 else
                 base - 20 if s % 2 == 0 else base - 32)
            sc.hit(RIDE if use_ride else HH, t + beat, v, jt=2, jv=3)
        if not fill_bar:
            sc.hit(OH, t + 3.75, base - 16, jt=2)
            if energy >= 3 and rng.random() < 0.5:
                sc.hit(SN, t + rng.choice((1.75, 3.25)), base - 34, jt=1)
        else:
            fill(sc, t + 2.0, 2.0, fill_styles[fi % len(fill_styles)],
                 vel=base + 6)
            fi += 1
            # the landing crash of the groove's FINAL bar belongs to
            # whatever section follows (every section opens with its
            # own crash) — writing it here would spill the module
            # bounds by jitter.
            if bar + 1 < bars:
                sc.hit(CRASH if fi % 2 else CRASH2, t + 4.0, base + 16)


def groove_78(sc: en.Score, t0: float, bars: int, energy: int = 2,
              fill_every: int = 8, fill_styles=FILL_STYLES) -> None:
    """The verse engine, 3+2+2: kick on the group starts, snare on the
    second group, 8th hats accenting the additive pattern, ghost snare
    16ths at higher energy, and a 7/8 fill each `fill_every` bars."""
    rng = sc.rng
    base = 58 + 8 * energy
    fi = 0
    for bar in range(bars):
        t = t0 + 3.5 * bar
        fill_bar = fill_every and bar % fill_every == fill_every - 1
        sc.hit(K, t, base + 8)
        sc.hit(K, t + 2.5, base - 2)
        if energy >= 2 and bar % 2 == 1:
            sc.hit(K, t + 1.0, base - 14)
        sc.hit(SN, t + 1.5, base + 6)
        span = 2.5 if fill_bar else 3.5
        for s in range(int(span * 2)):
            beat = s * 0.5
            accent = beat in (0.0, 1.5, 2.5)
            sc.hit(HH, t + beat, base - (8 if accent else 26), jt=2, jv=3)
        if not fill_bar:
            if energy >= 2:
                for ghost in (0.75, 2.25, 3.25):
                    if rng.random() < 0.3 + 0.15 * energy:
                        sc.hit(SN, t + ghost, base - 36, jt=1)
        else:
            fill(sc, t + 2.5, 1.0, fill_styles[fi % len(fill_styles)],
                 vel=base + 4)
            fi += 1
            sc.hit(CRASH, t + 3.5, base + 12)


def groove_68(sc: en.Score, t0: float, bars: int, energy: int = 2) -> None:
    """The pre-chorus lift, 6/8: kick on the dotted beats, snare
    answering, tom hits climbing the kit bar by bar, and a snare roll
    across the whole final bar into the chorus."""
    base = 62 + 8 * energy
    for bar in range(bars):
        t = t0 + 3.0 * bar
        last = bar == bars - 1
        sc.hit(K, t, base + 6)
        sc.hit(SN, t + 1.5, base + 2)
        if not last:
            for s in range(6):
                sc.hit(HH, t + s * 0.5, base - (10 if s % 3 == 0 else 26),
                       jt=2, jv=3)
            tom = TOMS[max(0, len(TOMS) - 1 - bar)]
            sc.hit(tom, t + 2.5, base - 6 + 2 * bar, jt=2)
            if bar >= bars // 2:
                sc.hit(K, t + 2.0, base - 10)
        else:
            snare_build(sc, t, t + 3.0, base - 24, base + 18, step=0.25)


def groove_54(sc: en.Score, t0: float, bars: int, energy: int = 1) -> None:
    """The middle-eight, 5/4 as 3+2: ride pattern with a skip, side
    stick instead of snare, kick on 0 and 3 — spacious on purpose."""
    base = 52 + 8 * energy
    for bar in range(bars):
        t = t0 + 5.0 * bar
        sc.hit(K, t, base + 6)
        sc.hit(K, t + 3.0, base - 2)
        sc.hit(STICK, t + 1.5, base - 6)
        sc.hit(STICK, t + 4.0, base - 10)
        for beat in (0.0, 1.0, 1.5, 2.0, 3.0, 3.5, 4.0, 4.5):
            sc.hit(RIDE, t + beat, base - (8 if beat in (0.0, 3.0) else 22),
                   jt=2, jv=3)
        if bar % 4 == 3:
            sc.hit(BELL, t + 3.0, base + 2, jt=2)
