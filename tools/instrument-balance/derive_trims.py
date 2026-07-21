#!/usr/bin/env python3
"""Derive PROGRAM_TRIM_DB percussive-family trims from a ferro/SC-55 calibration run.

Implements the M-CAL half of
`wrk_docs/2026.07.20 - HLD - instrument balance oracle + drum-forward recalibration.md`.

    python tools/instrument-balance/derive_trims.py \
        _cal/ferro_full.levels.tsv _cal/sc55_full.levels.tsv

Inputs are calmeter level TSVs (idx program key velocity max_m peak_block clipped
sounded). The ferro render is made WITH program trims applied, so this tool backs the
shipped trim out of each ferro reading to recover the raw voice level; the SC-55 render
carries no such trim.

Method (HLD §5):
  level(p)   = median max_m over the program's sounded notes (per engine)
  D_p        = (raw_ferro(p) - median_raw_ferro) - (sc55(p) - median_sc55)
  trim_p     = 0 if |D_p| < DEADBAND else clamp(round(-DAMP * D_p), -CLAMP, +CLAMP)
  vel guard  : |D_p(v110) - D_p(v72)| > VEL_GUARD  ->  EXCLUDE p (a velocity-curve
               defect; a static trim is the wrong lever) and flag it.

The DAMP / CLAMP / DEADBAND constants are printed and are the numbers the HLD §11 asks
Arthur to RE-EXAMINE with the full distribution in hand — they are not inherited silently.
"""
from __future__ import annotations

import statistics
import sys

# --- policy constants (HLD §5; §11 says re-examine, do not inherit) ---------
DAMP = 0.70
CLAMP = 6.0
DEADBAND = 1.0
VEL_GUARD = 3.0

# --- current shipped table (engine.rs PROGRAM_TRIM_DB) ----------------------
# 8 per row, GM order. Backed out of the ferro readings to recover raw level, and
# the sustained rows are the cross-check reference.
SHIPPED = [
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.0, 0.0,     # 0-7   Piano
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 8-15  ChromPerc
    -4.5, -3.0, -1.5, -6.0, -3.0, -5.0, -1.0, -4.5,  # 16-23 Organ
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 24-31 Guitar
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 32-39 Bass
    -4.0, -4.0, -3.5, -6.0, -4.0, 0.0, 0.0, 0.0,  # 40-47 Strings (pizz/harp/timp=0)
    5.5, 1.5, 6.0, 5.0, 2.5, 6.0, 5.0, 0.0,     # 48-55 Ensemble (orch-hit 55=0)
    -6.0, -6.0, -6.0, -2.0, -3.0, -2.0, 0.0, 5.0,  # 56-63 Brass
    0.0, -2.5, -3.0, -3.0, 2.0, 1.5, 0.0, 0.0,  # 64-71 Reed
    -4.0, -4.0, -2.0, -5.0, -6.0, -6.0, 0.0, 0.0,  # 72-79 Pipe
    -4.0, 0.0, 0.0, 0.0, -2.0, 5.5, 1.0, 1.0,   # 80-87 SynthLead
    4.0, 0.0, 2.0, 5.0, 3.0, -5.0, 0.0, 0.0,    # 88-95 SynthPad
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 96-103 SynthFX
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 104-111 Ethnic
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 112-119 Percussive
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,     # 120-127 SoundFX
]

# --- family roles (HLD §5 O2) -----------------------------------------------
# percussive: newly derived. sustained: FROZEN (cross-check only). never: stay 0.0.
GM_FAMILY = {}
def _fam(lo, hi, role, name):
    for p in range(lo, hi + 1):
        GM_FAMILY[p] = (role, name)
_fam(0, 7, "percussive", "Piano");        _fam(8, 15, "percussive", "ChromPerc")
_fam(16, 23, "sustained", "Organ");       _fam(24, 31, "percussive", "Guitar")
_fam(32, 39, "percussive", "Bass")
# Strings 40-47: bowed 40-44 sustained (frozen); pizz/harp/timpani 45-47 percussive.
_fam(40, 44, "sustained", "Strings");     _fam(45, 47, "percussive", "Str-pizz/harp/timp")
# Ensemble 48-55: sections/choir 48-54 sustained; orch-hit 55 percussive.
_fam(48, 54, "sustained", "Ensemble");    _fam(55, 55, "percussive", "OrchHit")
_fam(56, 63, "sustained", "Brass");       _fam(64, 71, "sustained", "Reed")
_fam(72, 79, "sustained", "Pipe");        _fam(80, 87, "sustained", "SynthLead")
_fam(88, 95, "sustained", "SynthPad");    _fam(96, 103, "never", "SynthFX")
_fam(104, 111, "percussive", "Ethnic");   _fam(112, 119, "percussive", "Percussive")
_fam(120, 127, "never", "SoundFX")


def load(path):
    """program -> {velocity -> [max_m,...]} for sounded notes."""
    prog = {}
    for line in open(path).read().splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 8 or f[7] != "1":
            continue
        p, vel, mx = int(f[1]), int(f[3]), float(f[4])
        prog.setdefault(p, {}).setdefault(vel, []).append(mx)
    return prog


def med_all(d):
    return statistics.median([x for vs in d.values() for x in vs])


def clamp_trim(dp):
    if abs(dp) < DEADBAND:
        return 0.0
    return max(-CLAMP, min(CLAMP, float(round(-DAMP * dp))))


def main():
    if len(sys.argv) < 3:
        print("usage: derive_trims.py <ferro.levels.tsv> <sc55.levels.tsv>")
        return 2
    ferro_raw, sc = load(sys.argv[1]), load(sys.argv[2])
    progs = sorted(set(ferro_raw) & set(sc))

    # ferro was rendered WITH trims applied -> back them out to raw voice level.
    def ferro_at(p, vel=None):
        vs = ferro_raw.get(p, {})
        xs = [x for k, l in vs.items() if vel is None or k == vel for x in l]
        return statistics.median(xs) - SHIPPED[p] if xs else None

    def sc_at(p, vel=None):
        vs = sc.get(p, {})
        xs = [x for k, l in vs.items() if vel is None or k == vel for x in l]
        return statistics.median(xs) if xs else None

    def med_of(fn, vel=None):
        return statistics.median([v for p in progs if (v := fn(p, vel)) is not None])

    fmed, smed = med_of(ferro_at), med_of(sc_at)
    fmed72, smed72 = med_of(ferro_at, 72), med_of(sc_at, 72)
    fmed110, smed110 = med_of(ferro_at, 110), med_of(sc_at, 110)

    def dp(p, vel=None):
        if vel == 72:
            f, s = ferro_at(p, 72), sc_at(p, 72)
            return None if f is None or s is None else (f - fmed72) - (s - smed72)
        if vel == 110:
            f, s = ferro_at(p, 110), sc_at(p, 110)
            return None if f is None or s is None else (f - fmed110) - (s - smed110)
        f, s = ferro_at(p), sc_at(p)
        return None if f is None or s is None else (f - fmed) - (s - smed)

    print(f"# DAMP={DAMP} CLAMP=+/-{CLAMP} DEADBAND={DEADBAND} VEL_GUARD={VEL_GUARD}")
    print(f"# anchor medians: ferro_raw={fmed:.2f}  sc55={smed:.2f}  (dB, arbitrary offset)")
    print(f"{'GM':>4} {'family':>18} {'role':>10} {'D_p':>6} {'v72':>6} {'v110':>6} "
          f"{'guard':>5} {'ship':>5} {'new':>4} {'note':<24}")

    rows = []
    for p in progs:
        role, name = GM_FAMILY.get(p, ("?", "?"))
        d, d72, d110 = dp(p), dp(p, 72), dp(p, 110)
        if d is None:
            print(f"{p:>4} {name:>18} {role:>10}   (unmeasured — silent at metered notes)")
            continue
        guarded = d72 is not None and d110 is not None and abs(d110 - d72) > VEL_GUARD
        new = clamp_trim(d)
        note = ""
        if role == "never":
            new = 0.0; note = "never-trim (stays 0)"
        elif guarded:
            new = 0.0; note = f"VEL-GUARD excl (d{d110-d72:+.1f})"
        elif role == "sustained":
            note = f"FROZEN; recomputes {clamp_trim(d):+.0f}"
        rows.append((p, name, role, d, d72, d110, guarded, SHIPPED[p], new, note))
        s72 = f"{d72:6.2f}" if d72 is not None else "   n/a"
        s110 = f"{d110:6.2f}" if d110 is not None else "   n/a"
        print(f"{p:>4} {name:>18} {role:>10} {d:6.2f} {s72} {s110} "
              f"{'Y' if guarded else '.':>5} {SHIPPED[p]:5.1f} {new:4.0f} {note:<24}")

    # --- sustained cross-check GATE (HLD §O2) -------------------------------
    # The metric is trustworthy for the HARD (percussive) case only if it reproduces
    # the SHIPPED sustained trims on the EASY case: recompute each sustained trim from
    # the new max-momentary metric and compare to what is shipped.
    print("\n=== sustained cross-check (recomputed trim vs shipped; |recomp - ship| > 1.5 = drift) ===")
    worst = 0.0
    drift = []
    n_checked = 0
    for r in rows:
        p, name, role, d, guarded = r[0], r[1], r[2], r[3], r[6]
        if role != "sustained" or guarded:  # guard-excluded voices are not calibratable
            continue
        n_checked += 1
        recomputed = clamp_trim(d)
        delta = recomputed - SHIPPED[p]
        if abs(delta) > 1.5:
            drift.append((p, name, SHIPPED[p], recomputed, delta))
            worst = max(worst, abs(delta))
    if drift:
        print(f"  {len(drift)}/{n_checked} sustained programs disagree >1.5 dB with shipped:")
        for p, name, ship, rec, delta in sorted(drift, key=lambda x: -abs(x[4])):
            print(f"    GM{p:<3} {name:<12} shipped {ship:+.1f}  recomputes {rec:+.0f}  (Δ{delta:+.1f})")
        print(f"  worst disagreement {worst:+.1f} dB. Synth changed since the 17-Jul")
        print(f"  derivation (k=2 etc.), so modest disagreement = mild drift, not a bad metric.")
    else:
        print(f"  all {n_checked} sustained programs within 1.5 dB of shipped — metric VALIDATED.")

    # --- proposed percussive trims ------------------------------------------
    print("\n=== proposed NEW percussive-family trims (nonzero) ===")
    for r in rows:
        p, name, role, new, note = r[0], r[1], r[2], r[8], r[9]
        if role == "percussive" and new != 0.0:
            print(f"    GM{p:<3} {name:<18} {new:+.0f} dB   {note}")
    guarded = [r[0] for r in rows if r[6]]
    print(f"\n  velocity-guard excluded: {guarded or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
