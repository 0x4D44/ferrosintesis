#!/usr/bin/env python3
"""Derive PROGRAM_TRIM_DB percussive-family trims from a ferro/SC-55 calibration run.

Implements the M-CAL **v2** tooling design
(`wrk_docs/2026.07.21 - HLD - M-CAL v2 tooling implementation.md`), which supersedes the
percussive half of the 2026.07.20 HLD. The metric is a peak-normalised momentary-block
**trajectory** comparison, not the candidate-1 max-momentary scalar (which was wrong in sign
for ~8 percussive voices: a 400 ms mean dilutes a sub-400 ms note by its duty cycle and the
ferro/SC-55 envelopes differ in shape).

    python tools/instrument-balance/derive_trims.py \
        _cal/ferro_guardcheck.levels.tsv _cal/sc55_guardcheck.levels.tsv
    python tools/instrument-balance/derive_trims.py --selftest

Inputs are calmeter v2 level TSVs, parsed BY HEADER NAME (columns may be added/reordered):
`idx program key velocity max_m peak_block clipped sounded b0 b1 ... bK`, where `b0..bK` is the
onset-relative momentary-block trajectory. The ferro render is made WITH program trims applied,
so this tool backs the shipped trim out of the ferro peak to recover raw voice level; SC-55
carries no such trim.

Method (tooling HLD §3, revised after review):
  * body = blocks b2..bK, the held region past the b0-b1 attack ramp. note_body = median of the
    PRESENT body blocks (> peak - FLOOR_REL_DB). A note with no present body has collapsed / is
    too short to meter a level at 400 ms resolution -> the key is UNMETRABLE (a static trim
    would mistake duration for level; Codex #3).
  * trajectory shape over the body: peak-normalise each engine's trajectory (whole-note peak),
    floor at -FLOOR_REL_DB, shape_dev = max over body blocks of |ferro_norm - sc_norm|
    (level-independent by construction; the attack ramp is excluded so fast-vs-slow attack is
    not penalised).
  * a program is EXCLUDED (routed to voice-fix) if MORE THAN ONE key is unmetrable or has
    shape_dev > SHAPE_DB; or per-key body-level spread > PITCH_TILT_DB; or the anchor-free
    velocity delta > VEL_GUARD.
  * level: g(p) = RENDERED ferro body - SC body (shipped NOT backed out). anchor = engine offset
    K = median over the vetted sustained cohort of g (their frozen trims are correct, so their
    rendered output already matches SC up to K). D_p = g(p) - SHIPPED[p] - anchor. trim = 0 if
    |D_p| < DEADBAND else clamp(round(-DAMP * D_p), +-CLAMP). The implied undamped trim -D_p
    reproduces a correctly-shipped program's trim (the cross-check).

PRECONDITION (Codex #1): the differential is valid only if the ferro BusGlue bus-compressor is
inert for probe notes (single notes at CC7=100 should stay below its 0.32 threshold) — verify
by peak-inspecting the ferro probe render. If not, the dB back-out and the shape guard are
biased on loud notes.
"""
from __future__ import annotations

import statistics
import sys

# --- policy constants (tooling HLD §3) --------------------------------------
DAMP = 0.70
CLAMP = 6.0
DEADBAND = 1.0
BODY_LO = 2  # first BODY block: skip the b0-b1 attack ramp (fast-vs-slow attack is a
# legitimate ferro/SC-55 difference a level trim need not reconcile). The level and the
# shape guard both work on the held body b2..bK.
# Shape divergence over the BODY that invalidates a static trim. NOT 3 dB: the trajectory
# max-deviation is a larger statistic than a two-window delta. The guardcheck run showed a
# clean bimodal gap — gentle sustain/decay differences (organ ~1, ensembles/pad ~2-7 dB)
# vs a genuine collapse (GM28 palm-mute ~38 dB, one engine gone while the other rings). 12
# sits in that gap: it excludes the catastrophe, trims the gently-differing rest (ears
# arbitrate the approximation downstream).
SHAPE_DB = 12.0
FLOOR_REL_DB = 40.0  # a block this far below the note peak is "gone" (floored)
PITCH_TILT_DB = 6.0  # per-key body-level spread that invalidates a single trim
VEL_GUARD = 3.0  # within-program velocity-response mismatch that invalidates a trim
MAX_FAIL_KEYS = 1  # exclude when MORE than this many keys fail (tolerate 1 fluke)
MIN_COHORT = 4  # minimum vetted sustained programs for a trustworthy anchor
FLOOR_ABS = -115.0  # a block at/below this is the calmeter -120 sentinel / dead silence

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
# percussive: newly derived. sustained: FROZEN (cross-check + anchor cohort). never: stay 0.0.
GM_FAMILY = {}


def _fam(lo, hi, role, name):
    for p in range(lo, hi + 1):
        GM_FAMILY[p] = (role, name)


_fam(0, 7, "percussive", "Piano")
_fam(8, 15, "percussive", "ChromPerc")
_fam(16, 23, "sustained", "Organ")
_fam(24, 31, "percussive", "Guitar")
_fam(32, 39, "percussive", "Bass")
# Strings 40-47: bowed 40-44 sustained (frozen); pizz/harp/timpani 45-47 percussive.
_fam(40, 44, "sustained", "Strings")
_fam(45, 47, "percussive", "Str-pizz/harp/timp")
# Ensemble 48-55: sections/choir 48-54 sustained; orch-hit 55 percussive.
_fam(48, 54, "sustained", "Ensemble")
_fam(55, 55, "percussive", "OrchHit")
_fam(56, 63, "sustained", "Brass")
_fam(64, 71, "sustained", "Reed")
_fam(72, 79, "sustained", "Pipe")
_fam(80, 87, "sustained", "SynthLead")
_fam(88, 95, "sustained", "SynthPad")
_fam(96, 103, "never", "SynthFX")
_fam(104, 111, "percussive", "Ethnic")
_fam(112, 119, "percussive", "Percussive")
_fam(120, 127, "never", "SoundFX")


# --- loading (parse by header name; retain per-key trajectories) -------------
def load(path):
    """program -> key -> velocity -> trajectory [b0..bK], for sounded notes."""
    lines = open(path).read().splitlines()
    if not lines:
        raise SystemExit(f"{path}: empty")
    header = lines[0].split("\t")
    col = {name: i for i, name in enumerate(header)}
    for n in ("program", "key", "velocity", "sounded"):
        if n not in col:
            raise SystemExit(f"{path}: missing required column {n!r}")
    bnames = sorted(
        (n for n in header if len(n) > 1 and n[0] == "b" and n[1:].isdigit()),
        key=lambda n: int(n[1:]),
    )
    if not bnames:
        raise SystemExit(f"{path}: no bN trajectory columns - is this a calmeter v2 TSV?")
    bidx = [col[n] for n in bnames]
    maxcol = max(col["program"], col["key"], col["velocity"], col["sounded"], max(bidx))
    data = {}
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) <= maxcol:
            continue
        if f[col["sounded"]] != "1":
            continue
        p, k, v = int(f[col["program"]]), int(f[col["key"]]), int(f[col["velocity"]])
        traj = [float(f[i]) for i in bidx]
        data.setdefault(p, {}).setdefault(k, {})[v] = traj
    return data


# --- pure primitives (unit-tested by --selftest) ----------------------------
def note_peak(traj):
    finite = [b for b in traj if b > FLOOR_ABS]
    return max(finite) if finite else None


def note_body(traj):
    """Median level of the PRESENT held-body blocks (b2..bK above peak - FLOOR_REL_DB), or
    None when the note has no sustained body — it has collapsed / is too short to meter a
    level at 400 ms resolution (Codex #3: the sub-hop class is refused, not mis-trimmed)."""
    pk = note_peak(traj)
    if pk is None:
        return None
    present = [b for b in traj[BODY_LO:] if b > FLOOR_ABS and b > pk - FLOOR_REL_DB]
    return statistics.median(present) if present else None


def shape_dev(tf, ts):
    """Max deviation between peak-normalised, floor-clamped BODY trajectories (dB). Peak is
    over the whole note (so a decay into the body reads as divergence); the attack ramp
    (b0..b1) is excluded. Anchor/level-independent by construction."""
    pf, ps = note_peak(tf), note_peak(ts)
    if pf is None or ps is None:
        return None
    fb, sb = tf[BODY_LO:], ts[BODY_LO:]
    dev = 0.0
    for j in range(min(len(fb), len(sb))):
        nf = max(fb[j] - pf, -FLOOR_REL_DB)
        ns = max(sb[j] - ps, -FLOOR_REL_DB)
        dev = max(dev, abs(nf - ns))
    return dev


def key_verdict(fkey, skey):
    """fkey/skey: {vel: traj}. Returns (unmetrable, worst_shape_dev|None) over shared vels.
    A key is unmetrable when either engine has no sustained body at some velocity."""
    vels = sorted(set(fkey) & set(skey))
    if not vels:
        return (True, None)
    unm, best, seen = False, 0.0, False
    for v in vels:
        if note_body(fkey[v]) is None or note_body(skey[v]) is None:
            unm = True
            continue
        d = shape_dev(fkey[v], skey[v])
        if d is not None:
            best, seen = max(best, d), True
    return (unm, best if seen else None)


def key_body(kdata, vel=None):
    """median body level over velocities at one key (as RENDERED — no back-out; the shipped
    trim is a per-program constant that cancels in every guard and is applied explicitly, once,
    in D_p)."""
    xs = []
    for v, t in kdata.items():
        if vel is not None and v != vel:
            continue
        b = note_body(t)
        if b is not None:
            xs.append(b)
    return statistics.median(xs) if xs else None


def prog_body(pdata, keys, vel=None):
    """median over keys of key_body."""
    xs = [kb for k in keys if (kb := key_body(pdata.get(k, {}), vel)) is not None]
    return statistics.median(xs) if xs else None


def shape_guard(fp, sp):
    """Returns (excluded, fail_keys, clean_keys) over keys present in both engines."""
    keys = sorted(set(fp) & set(sp))
    fail, clean = [], []
    for k in keys:
        unm, d = key_verdict(fp[k], sp[k])
        if unm or (d is not None and d > SHAPE_DB):
            fail.append(k)
        else:
            clean.append(k)
    return (len(fail) > MAX_FAIL_KEYS, fail, clean)


def pitch_tilt(fp, sp, keys):
    diffs = []
    for k in keys:
        fpk, spk = key_body(fp.get(k, {})), key_body(sp.get(k, {}))
        if fpk is not None and spk is not None:
            diffs.append(fpk - spk)
    return (max(diffs) - min(diffs)) if len(diffs) >= 2 else 0.0


def vel_guard(fp, sp, keys):
    """Anchor-free within-program velocity-response mismatch (the shipped trim cancels)."""
    f110, f72 = prog_body(fp, keys, 110), prog_body(fp, keys, 72)
    s110, s72 = prog_body(sp, keys, 110), prog_body(sp, keys, 72)
    if None in (f110, f72, s110, s72):
        return 0.0
    return abs((f110 - f72) - (s110 - s72))


def clamp_trim(dp):
    if abs(dp) < DEADBAND:
        return 0.0
    return max(-CLAMP, min(CLAMP, float(round(-DAMP * dp))))


def evaluate(ferro, sc):
    """Run all guards + level for every shared program. Returns a list of row dicts and the
    anchor. Pure over the two loaded tables — the heart of the derivation and the selftest."""
    progs = sorted(set(ferro) & set(sc))
    rows = []
    for p in progs:
        fp, sp = ferro[p], sc[p]
        role, name = GM_FAMILY.get(p, ("?", "?"))
        shipped = SHIPPED[p] if p < len(SHIPPED) else 0.0
        excl_shape, fail_keys, clean = shape_guard(fp, sp)
        keyset = clean or sorted(set(fp) & set(sp))
        tilt = pitch_tilt(fp, sp, keyset)
        vg = vel_guard(fp, sp, keyset)
        reasons = []
        if excl_shape:
            reasons.append(f"shape/short ({len(fail_keys)} keys: {fail_keys})")
        if tilt > PITCH_TILT_DB:
            reasons.append(f"pitch-tilt {tilt:.1f}dB")
        if vg > VEL_GUARD:
            reasons.append(f"velocity {vg:.1f}dB")
        # RENDERED gap g = ferro(with its shipped trim applied) - SC, over clean keys. The
        # shipped trim is NOT backed out here: the sustained cohort's frozen trims are correct,
        # so their rendered output already matches SC up to the engine offset the anchor removes.
        rf_body = prog_body(fp, clean) if clean else None
        s_body = prog_body(sp, clean) if clean else None
        g = (rf_body - s_body) if (rf_body is not None and s_body is not None) else None
        # median per-key shape_dev over clean keys — the cohort sanity diagnostic.
        sdevs = [d for k in clean if (d := key_verdict(fp[k], sp[k])[1]) is not None]
        med_shape = statistics.median(sdevs) if sdevs else None
        rows.append(
            {
                "p": p, "name": name, "role": role, "shipped": shipped,
                "excluded": bool(reasons), "reasons": reasons,
                "clean": clean, "g": g, "tilt": tilt, "vel": vg, "med_shape": med_shape,
            }
        )
    # Paired anchor = engine offset K = median over the vetted (correctly-trimmed) sustained
    # cohort of the RENDERED gap g. A percussive program's needed trim is then how far its own
    # rendered gap (minus any shipped trim it already carries) sits from that frame.
    cohort = [r for r in rows if r["role"] == "sustained" and not r["excluded"]
              and r["g"] is not None]
    anchor = statistics.median([r["g"] for r in cohort]) if cohort else None
    for r in rows:
        if anchor is not None and r["g"] is not None:
            r["D_p"] = r["g"] - r["shipped"] - anchor
            r["trim"] = 0.0 if r["excluded"] else clamp_trim(r["D_p"])
        else:
            r["D_p"] = None
            r["trim"] = 0.0
        if r["role"] == "never":
            r["trim"] = 0.0
    return rows, anchor, cohort


def run(ferro_path, sc_path):
    ferro, sc = load(ferro_path), load(sc_path)
    only_f, only_s = sorted(set(ferro) - set(sc)), sorted(set(sc) - set(ferro))
    if only_f or only_s:
        print(f"!! programs in one engine only (no differential): ferro-only={only_f} "
              f"sc-only={only_s}")
    rows, anchor, cohort = evaluate(ferro, sc)

    print(f"# SHAPE_DB={SHAPE_DB} FLOOR_REL={FLOOR_REL_DB} PITCH_TILT={PITCH_TILT_DB} "
          f"VEL_GUARD={VEL_GUARD} MAX_FAIL_KEYS={MAX_FAIL_KEYS} DAMP={DAMP} CLAMP=+/-{CLAMP}")
    if anchor is None:
        print("!! no sustained-cohort anchor could be formed - cannot derive trims.")
    else:
        print(f"# paired anchor = engine offset K (median rendered ferro-SC gap over "
              f"{len(cohort)} sustained progs): {anchor:.2f} dB")
        members = ", ".join(f"GM{r['p']}({r['name']})" for r in cohort)
        print(f"# cohort: {members}")
        cshape = statistics.median([r["med_shape"] for r in cohort if r["med_shape"] is not None])
        print(f"# cohort median shape_dev: {cshape:.2f} dB (want ~0 - a large value warns the "
              f"frame itself is envelope-mismatched)")
        if len(cohort) < MIN_COHORT:
            print(f"!! cohort {len(cohort)} < MIN_COHORT {MIN_COHORT} - anchor is low-confidence.")

    print(f"\n{'GM':>4} {'family':>18} {'role':>10} {'D_p':>6} {'tilt':>5} {'vel':>5} "
          f"{'shp':>5} {'ship':>5} {'new':>4} {'note':<32}")
    for r in rows:
        d = f"{r['D_p']:6.2f}" if r["D_p"] is not None else "   n/a"
        ms = f"{r['med_shape']:5.1f}" if r["med_shape"] is not None else "  n/a"
        note = "; ".join(r["reasons"]) if r["excluded"] else (
            "FROZEN" if r["role"] == "sustained" else "never" if r["role"] == "never" else "")
        print(f"{r['p']:>4} {r['name']:>18} {r['role']:>10} {d} {r['tilt']:5.1f} {r['vel']:5.1f} "
              f"{ms} {r['shipped']:5.1f} {r['trim']:4.0f} {note:<32}")

    print("\n=== proposed NEW percussive-family trims (nonzero, non-excluded) ===")
    any_trim = False
    for r in rows:
        if r["role"] == "percussive" and not r["excluded"] and r["trim"] != 0.0:
            any_trim = True
            flag = "  [LOW-CONFIDENCE: heterogeneous family, verify fallback]" if (
                8 <= r["p"] <= 15 or 72 <= r["p"] <= 79) else ""
            print(f"    GM{r['p']:<3} {r['name']:<18} {r['trim']:+.0f} dB   (D_p {r['D_p']:+.1f}){flag}")
    if not any_trim:
        print("    (none)")

    excl = [r for r in rows if r["excluded"]]
    print("\n=== guard-excluded (route to voice-fix / ears) ===")
    for r in excl:
        print(f"    GM{r['p']:<3} {r['name']:<18} {r['role']:<10} {'; '.join(r['reasons'])}")

    # Sustained cross-check: the metric's IMPLIED (undamped) trim is -D_p; for a
    # correctly-shipped sustained program it should reproduce SHIPPED[p]. A gap flags a cohort
    # member whose rendered level deviates from the frame (e.g. an outlier that should not
    # anchor). ASCII only — Greek Δ crashes cp1252 stdout when redirected on Windows.
    print("\n=== sustained cross-check (implied trim -D_p vs shipped; |d|>1.5 = drift) ===")
    drift = [(r["p"], r["name"], r["shipped"], -r["D_p"], -r["D_p"] - r["shipped"])
             for r in rows if r["role"] == "sustained" and not r["excluded"]
             and r["D_p"] is not None and abs(-r["D_p"] - r["shipped"]) > 1.5]
    if drift:
        for p, name, ship, implied, dl in sorted(drift, key=lambda x: -abs(x[4])):
            print(f"    GM{p:<3} {name:<12} shipped {ship:+.1f} implies {implied:+.1f} (d{dl:+.1f})")
    else:
        print("    all vetted sustained programs within 1.5 dB of shipped.")
    return 0


# --- self-test (A3): synthetic tables through the guards + anchor ------------
def _flat(level, n=9):
    return [level] * n


def _decay(level, step, n=9, floor_after=5):
    return [max(level - step * j, -120.0) if j < floor_after else -120.0 for j in range(n)]


def _prog(traj_by_key):
    """{key: (ferro_traj, sc_traj)} -> (ferro_prog, sc_prog) with 2 velocities each."""
    fp, sp = {}, {}
    for k, (tf, ts) in traj_by_key.items():
        fp[k] = {72: tf, 110: tf}
        sp[k] = {72: ts, 110: ts}
    return fp, sp


def selftest():
    keys = [48, 53, 58, 63, 68, 73]
    ferro, sc = {}, {}

    # Sustained cohort: correctly-calibrated -> RENDERED ferro == SC (engine offset K=0), so
    # g=0 and anchor=0. Use real sustained programs with SHIPPED=0 (62 brass, 70/71 reed, 89/94
    # pad) so their recomputed trim is a clean 0.
    for p in (62, 70, 71, 89, 94):
        ferro[p], sc[p] = _prog({k: (_flat(-20.0), _flat(-20.0)) for k in keys})

    # GM6 Piano (percussive, SHIPPED +6): CORRECTLY shipped -> rendered is +6 hot (raw==SC),
    # so g=6 but D_p = g - SHIPPED - anchor = 6-6-0 = 0 -> trim 0. Tests the shipped back-out.
    ferro[6], sc[6] = _prog({k: (_flat(-14.0), _flat(-20.0)) for k in keys})

    # GM8 ChromPerc (percussive, SHIPPED 0): matched flat, rendered 3 dB hot -> trim -2.
    ferro[8], sc[8] = _prog({k: (_flat(-17.0), _flat(-20.0)) for k in keys})

    # GM9 ChromPerc: matched MEDIUM one-shot (both decay identically, body present), rendered
    # 2 dB hot -> KEPT, trim -1. Guards must NOT falsely exclude it (F1).
    ferro[9], sc[9] = _prog({k: (_decay(-18.0, 4), _decay(-20.0, 4)) for k in keys})

    # GM24 Guitar: shape mismatch (ferro decays hard, SC flat) at all keys -> excluded.
    ferro[24], sc[24] = _prog({k: (_decay(-18.0, 6, floor_after=4), _flat(-18.0)) for k in keys})

    # GM25 Guitar: sub-hop (no present body) at all keys -> unmetrable -> excluded.
    ferro[25], sc[25] = _prog({k: ([-18.0] + [-120.0] * 8, _flat(-18.0)) for k in keys})

    # GM26 Guitar: pitch-tilt - flat matched SHAPE per key, but ferro level tilts +10 dB across
    # register while SC is flat -> shape passes, pitch-tilt guard excludes.
    ferro[26], sc[26] = _prog(
        {k: (_flat(-20.0 + 2.0 * i), _flat(-20.0)) for i, k in enumerate(keys)}
    )

    rows, anchor, cohort = evaluate(ferro, sc)
    byp = {r["p"]: r for r in rows}

    assert anchor is not None and abs(anchor) < 1e-6, f"anchor {anchor}"
    assert len(cohort) == 5, f"cohort {len(cohort)}"
    assert not byp[6]["excluded"] and byp[6]["trim"] == 0.0, ("shipped back-out", byp[6])
    assert not byp[8]["excluded"] and byp[8]["trim"] == -2.0, byp[8]
    assert not byp[9]["excluded"] and byp[9]["trim"] == -1.0, ("matched one-shot", byp[9])
    assert byp[24]["excluded"] and "shape" in byp[24]["reasons"][0], byp[24]
    assert byp[25]["excluded"] and "shape/short" in byp[25]["reasons"][0], byp[25]
    assert byp[26]["excluded"] and any("pitch-tilt" in r for r in byp[26]["reasons"]), byp[26]
    for p in (62, 70, 71, 89, 94):  # cohort members: not excluded, recompute to 0.
        assert not byp[p]["excluded"], (p, byp[p])
        assert abs(byp[p]["trim"]) < 1e-6, (p, byp[p]["trim"])
    print("selftest OK - anchor=0.00, cohort=5; GM6 back-out trim 0, GM8 trim -2, GM9 "
          "(matched one-shot) kept trim -1; GM24 shape / GM25 sub-hop / GM26 pitch-tilt excluded.")
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        return selftest()
    if len(sys.argv) < 3:
        print("usage: derive_trims.py <ferro.levels.tsv> <sc55.levels.tsv>  |  --selftest")
        return 2
    return run(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
