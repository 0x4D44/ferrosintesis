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
    python tools/instrument-balance/derive_trims.py \
        _cal/ferro_full.levels.tsv _cal/sc55_full.levels.tsv _cal/yxg_full.levels.tsv
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

The run is CERTIFIED rather than assumed. Four certificates are printed with the derivation:

  1. GLUE INERTNESS. The differential is only valid where ferro's chain is LINEAR (the SC-55
     reference has no equivalent master stage). calmeter proves per note that the bus
     compressor never engaged - see `GLUE_CEILING` there for the identity that makes this
     observable from the output alone. Measured at the GM-default CC7=100, 23/128 programs
     FAILED this, so the probe now runs at `mkprobe.PROBE_CC7 = 50`; that is a uniform gain,
     which the anchor absorbs exactly, so nothing needs correcting for it.
  2. RESIDUAL ORACLE. Every program carrying a nonzero shipped trim is an ear judgment already
     made; `residual = anchor - g` measures how far its rendered output sits from the frame.
     This is the cheapest detector for the one class the guards CANNOT see - a voice that is
     spectrally broken but envelope-clean, which would otherwise collect a confident trim that
     merely levels a broken sound.
  3. SAMPLED/FALLBACK GROUND TRUTH. Obtained by diffing the probe against its `--no-samples`
     twin (calmeter `--vs`), NOT by re-implementing the sampler's routing - its repitch cutoff
     is applied at three separate call sites, so a re-implementation would silently drift. A
     program whose probe straddles its bank edge measures two different instruments across
     keys and is flagged low-confidence.
  4. ANCHOR ADMISSION. Two passes: a provisional frame, then admission by measurement quality
     (see the anchor block in `evaluate`), reporting cohort size and MAD.

REQUIRES A RAW RENDER: the CLI loudness-normalizes to -18 LUFS, which destroys absolute sample
level and so makes certificate 1 impossible. Render the probe with the `raw_dump` example.
"""
from __future__ import annotations

import csv
import io
import math
import pathlib
import re
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
FLOOR_ABS = -115.0  # a block at/below this is the calmeter -120 sentinel / dead silence

# --- anchor admission (the anchor is the ONLY coupling between programs, so a bad
# --- member contaminates every derived trim; admit by measurement quality, not family) --
MIN_COHORT = 10  # a median over 4 is moved by one outlier; 10+ is robust
MAD_MAX_DB = 1.0  # cohort median-absolute-deviation above this = the frame is mush
ADMIT_TILT_DB = 3.0  # admitted members must be far inside the pitch-tilt guard
ADMIT_RESIDUAL_DB = 2.0  # ...and must agree with their own ear-vetted shipped trim
RESIDUAL_FLAG_DB = 2.5  # |implied - shipped| above this = metric contradicts the ear
# Programs tilted between PITCH_TILT_DB and this are not auto-trimmed, but are surfaced as
# ear-vet candidates: a median trim would be right on average and ~+-tilt/2 off at the
# register extremes. Metric confidence alone does not justify shipping that; ears do.
EARVET_TILT_DB = 10.0

# --- reference panel -------------------------------------------------------------------
# A single reference cannot tell you whether IT or ferro is the outlier. Two INDEPENDENT
# references can: where they agree, their consensus is a trustworthy target; where they
# disagree with each other, there is no consensus GM answer for that patch and only ears
# can settle it. Pick references whose errors are uncorrelated - the Roland SC-55mkII (ROM
# sampler, 1991) and the Yamaha S-YXG50 (software wavetable) are different vendors, eras and
# synthesis methods. The repo already trusts this pair: the velocity-law calibration fit
# k=1.997 on the SC-55 and 1.981 on the S-YXG50 independently.
#
# 3 dB is where the measured distribution splits: agreeing programs land at 0.2-1.3 dB
# (GM7 0.16, GM110 0.32, GM14 1.29) and disagreeing ones at 5-10 dB (GM0 5.5, GM38 9.2,
# GM11 9.9). Nothing sits in between.
PANEL_AGREE_DB = 3.0

# --- cross-run residual oracle ---------------------------------------------------------
# A standalone derivation can miss exactly the regression it is meant to catch: a large
# voice-level change may trip a guard, then disappear from the ordinary residual oracle.
# Compare every program/reference row, INCLUDING guard-excluded rows, with the last accepted
# panel. Intentional trim changes cancel because the stable voice-level quantity is
# `residual + shipped_db` (residual moves by the inverse of an applied scalar trim).
DRIFT_FLAG_DB = 1.0
BASELINE_REFERENCES = ("sc55", "yxg")
RESIDUAL_BASELINE = pathlib.Path(__file__).with_name("residual-baseline.csv")

# --- current shipped table -------------------------------------------------
# DERIVED from engine.rs at start-up, never hand-copied. It used to be a literal,
# and fc1ef10 shipped five trims to engine.rs without updating it. Run on
# 2026-07-25 data the stale copy proposed GM14 -> -5 and GM110 -> -2, i.e. it
# would have UNDONE trims already in place, a +3 dB move in the wrong direction
# on GM110 -- and it silently dropped those five programs out of the residual
# oracle's watch list (MM-BUG-KILN-00109).
#
# Parsing the one source of truth removes the whole class: there is no second
# list to drift. Fail loudly rather than falling back to zeros, because a
# silently-empty table looks exactly like "nothing is trimmed yet" and would
# make every proposal wrong in the same direction.
ENGINE_RS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "crates" / "ferrosintesis" / "src" / "engine.rs"
)
_SHIPPED_RE = re.compile(
    r"(?m)^[ \t]*(?:pub(?:\s*\([^)\r\n]*\))?[ \t]+)?"
    r"\bconst\s+PROGRAM_TRIM_DB\b\s*:\s*"
    r"\[\s*f32\s*;\s*128\s*\]\s*=\s*\[(.*?)\]\s*;",
    re.S,
)
_EAR_DECIDED_RE = re.compile(
    r"(?m)^[ \t]*assert_eq!\(\s*PROGRAM_TRIM_DB\[\s*(\d+)\s*\]"
    r"\s*,\s*0\.0\s*\)\s*;"
)


def parse_shipped(text: str, source: object = "engine.rs") -> list[float]:
    """Parse the one exact `PROGRAM_TRIM_DB` declaration, or fail loudly."""
    matches = _SHIPPED_RE.findall(text)
    if len(matches) != 1:
        raise SystemExit(
            f"derive_trims: expected exactly one "
            f"`const PROGRAM_TRIM_DB: [f32; 128] = [...]` in {source}, "
            f"found {len(matches)}. The table was renamed, duplicated, or reshaped; "
            "fix this parser rather than re-copying the numbers "
            "(MM-BUG-KILN-00109, MM-BUG-KILN-00116)."
        )
    body = re.sub(r"//.*", "", matches[0])  # strip the per-row comments
    vals = [v.strip() for v in body.split(",") if v.strip()]
    if len(vals) != 128:
        raise SystemExit(
            f"derive_trims: parsed {len(vals)} entries from PROGRAM_TRIM_DB, expected 128."
        )
    try:
        return [float(v) for v in vals]
    except ValueError as e:
        raise SystemExit(f"derive_trims: non-numeric entry in PROGRAM_TRIM_DB: {e}") from e


def parse_ear_decided(text: str, source: object = "engine.rs") -> set[int]:
    """Derive the programs whose explicit zero pins record an ear decision."""
    matches = _EAR_DECIDED_RE.findall(text)
    if not matches:
        raise SystemExit(
            f"derive_trims: found no canonical "
            f"`assert_eq!(PROGRAM_TRIM_DB[P], 0.0);` pins in {source}. "
            "The pins were removed or reshaped; fix this parser rather than "
            "re-copying their program numbers (MM-BUG-KILN-00117)."
        )
    programs = [int(program) for program in matches]
    invalid = sorted(program for program in programs if program not in range(128))
    if invalid:
        raise SystemExit(
            f"derive_trims: ear-decision pins outside GM program 0..127 in "
            f"{source}: {invalid}."
        )
    if len(programs) != len(set(programs)):
        duplicates = sorted(
            program for program in set(programs) if programs.count(program) > 1
        )
        raise SystemExit(
            f"derive_trims: duplicate ear-decision pins in {source}: {duplicates}."
        )
    return set(programs)


def load_shipped(path: pathlib.Path = ENGINE_RS) -> tuple[list[float], set[int]]:
    """Read and parse the shipped trims and recorded zero decisions out of engine.rs."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"derive_trims: cannot read {path}: {e}") from e
    return parse_shipped(text, path), parse_ear_decided(text, path)


SHIPPED, EAR_DECIDED = load_shipped()


def parse_residual_baseline(text: str, source: object = "residual-baseline.csv"):
    """Parse one complete 128-program x 2-reference baseline, or fail loudly."""
    columns = [
        "program",
        "reference",
        "residual_db",
        "shipped_db",
        "guard_excluded",
    ]
    data_lines = [
        line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]
    reader = csv.DictReader(data_lines)
    if reader.fieldnames != columns:
        raise SystemExit(
            f"derive_trims: {source} columns must be {columns}, found {reader.fieldnames}."
        )

    rows = {}
    for line_no, row in enumerate(reader, 2):
        if None in row or any(row[column] is None for column in columns):
            raise SystemExit(
                f"derive_trims: malformed baseline row at {source}:{line_no}: {row}."
            )
        try:
            program = int(row["program"])
            reference = row["reference"]
            residual = float(row["residual_db"]) if row["residual_db"] else None
            shipped = float(row["shipped_db"])
        except (TypeError, ValueError) as e:
            raise SystemExit(
                f"derive_trims: invalid numeric baseline row at {source}:{line_no}: {e}"
            ) from e
        if program not in range(128):
            raise SystemExit(
                f"derive_trims: baseline program outside 0..127 at {source}:{line_no}: {program}."
            )
        if reference not in BASELINE_REFERENCES:
            raise SystemExit(
                f"derive_trims: unsupported baseline reference at {source}:{line_no}: "
                f"{reference!r}; expected one of {BASELINE_REFERENCES}."
            )
        if residual is not None and not math.isfinite(residual):
            raise SystemExit(
                f"derive_trims: non-finite residual at {source}:{line_no}: {residual}."
            )
        if not math.isfinite(shipped):
            raise SystemExit(
                f"derive_trims: non-finite shipped trim at {source}:{line_no}: {shipped}."
            )
        excluded_text = row["guard_excluded"].lower()
        if excluded_text not in ("true", "false"):
            raise SystemExit(
                f"derive_trims: guard_excluded must be true or false at "
                f"{source}:{line_no}, found {row['guard_excluded']!r}."
            )
        key = (reference, program)
        if key in rows:
            raise SystemExit(f"derive_trims: duplicate baseline row at {source}:{line_no}: {key}.")
        rows[key] = {
            "residual_db": residual,
            "shipped_db": shipped,
            "guard_excluded": excluded_text == "true",
        }

    expected = {(reference, program) for reference in BASELINE_REFERENCES for program in range(128)}
    if set(rows) != expected:
        missing = sorted(expected - set(rows))
        extra = sorted(set(rows) - expected)
        raise SystemExit(
            f"derive_trims: {source} must contain exactly every program 0..127 for "
            f"{BASELINE_REFERENCES}; missing={missing[:8]}, extra={extra[:8]}."
        )
    return rows


def load_residual_baseline(path: pathlib.Path = RESIDUAL_BASELINE):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"derive_trims: cannot read residual baseline {path}: {e}") from e
    return parse_residual_baseline(text, path)


def residual_snapshot(refs):
    """Return reference-addressed residual, shipped-trim and guard state for every row."""
    labels = [ref["label"] for ref in refs]
    if len(labels) != len(set(labels)):
        raise SystemExit(f"derive_trims: duplicate reference labels in panel: {labels}.")
    if set(labels) != set(BASELINE_REFERENCES):
        raise SystemExit(
            f"derive_trims: residual oracle requires references {BASELINE_REFERENCES}, "
            f"found {tuple(labels)}. Name input files with canonical sc55_/yxg_ prefixes."
        )
    return {
        (ref["label"], program): {
            "residual_db": row["residual"],
            "shipped_db": row["shipped"],
            "guard_excluded": row["excluded"],
        }
        for ref in refs
        for program, row in ref["by"].items()
    }


def residual_baseline_findings(baseline, current, drift_bar=DRIFT_FLAG_DB):
    """Return all measurement, guard-state and level changes; excluded rows stay included."""
    findings = []
    for reference, program in sorted(baseline, key=lambda key: (key[1], key[0])):
        old = baseline[(reference, program)]
        new = current.get((reference, program))
        if new is None:
            findings.append(
                {
                    "program": program,
                    "reference": reference,
                    "kind": "missing",
                    "detail": "program/reference is absent from the current derivation",
                }
            )
            continue

        if old["guard_excluded"] != new["guard_excluded"]:
            findings.append(
                {
                    "program": program,
                    "reference": reference,
                    "kind": "guard",
                    "detail": "guard-excluded changed "
                    f"{old['guard_excluded']} -> {new['guard_excluded']}",
                }
            )

        old_residual, new_residual = old["residual_db"], new["residual_db"]
        if (old_residual is None) != (new_residual is None):
            findings.append(
                {
                    "program": program,
                    "reference": reference,
                    "kind": "measurement",
                    "detail": "measurability changed "
                    f"{'unmeasurable' if old_residual is None else 'measured'} -> "
                    f"{'unmeasurable' if new_residual is None else 'measured'}",
                }
            )
        elif old_residual is not None:
            # Applying +t dB moves residual by -t dB. Adding the contemporaneous shipped
            # trim removes that intentional table change and leaves voice/reference drift.
            delta = (new_residual + new["shipped_db"]) - (
                old_residual + old["shipped_db"]
            )
            if abs(delta) > drift_bar:
                findings.append(
                    {
                        "program": program,
                        "reference": reference,
                        "kind": "drift",
                        "delta": delta,
                        "detail": f"normalized residual drift {delta:+.2f} dB "
                        f"(baseline excluded={old['guard_excluded']}, "
                        f"current excluded={new['guard_excluded']})",
                    }
                )
    return findings


def serialize_residual_baseline(snapshot):
    expected = {(reference, program) for reference in BASELINE_REFERENCES for program in range(128)}
    if set(snapshot) != expected:
        missing = sorted(expected - set(snapshot))
        raise SystemExit(
            "derive_trims: cannot write an incomplete residual baseline; "
            f"missing={missing[:8]}."
        )
    out = io.StringIO(newline="")
    out.write("# generated by tools/instrument-balance/derive_trims.py --write-baseline\n")
    out.write("# residual_db is anchor minus rendered ferro/reference gap; blank means unmeasurable.\n")
    out.write("# shipped_db lets comparisons remove intentional PROGRAM_TRIM_DB changes.\n")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(
        ["program", "reference", "residual_db", "shipped_db", "guard_excluded"]
    )
    for program in range(128):
        for reference in BASELINE_REFERENCES:
            row = snapshot[(reference, program)]
            residual = row["residual_db"]
            writer.writerow(
                [
                    program,
                    reference,
                    "" if residual is None else f"{residual:+.2f}",
                    f"{row['shipped_db']:.1f}",
                    str(row["guard_excluded"]).lower(),
                ]
            )
    return out.getvalue()


def write_residual_baseline(refs, path):
    snapshot = residual_snapshot(refs)
    try:
        pathlib.Path(path).write_text(
            serialize_residual_baseline(snapshot), encoding="utf-8", newline="\n"
        )
    except OSError as e:
        raise SystemExit(f"derive_trims: cannot write residual baseline {path}: {e}") from e
    print(f"\n=== residual baseline written for explicit review: {path} ===")


def compare_residual_baseline(refs):
    baseline = load_residual_baseline()
    findings = residual_baseline_findings(baseline, residual_snapshot(refs))
    print(
        f"\n=== cross-run residual oracle (normalized drift > {DRIFT_FLAG_DB:.1f} dB fails; "
        "guard-excluded rows included) ==="
    )
    if not findings:
        print("    all 256 program/reference rows match the accepted baseline.")
        return True
    for finding in findings:
        print(
            f"    GM{finding['program']:<3} {finding['reference']:<5} "
            f"{finding['kind']}: {finding['detail']}"
        )
    print(f"    FAIL: {len(findings)} cross-run baseline difference(s).")
    return False

# --- recorded ear decisions -------------------------------------------------
# A trim of 0.0 is ambiguous: it can mean "nobody has looked at this yet" or "someone
# listened and ruled that 0.0 is right". Those must not be treated the same — the second is
# an ear judgment and belongs under the residual oracle's watch, so that a later run REPORTS
# its disagreement instead of silently re-proposing a change that was already rejected.
#
# The canonical decisions and their rationale live beside the zero-valued assertions in
# engine.rs. Parsing those assertions makes a new pin take effect here without a second list.

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
    """(data, glue) where data = program -> key -> velocity -> trajectory [b0..bK] for
    sounded notes, and glue = program -> {n, viol, max_peak} summarising the per-note
    glue-inertness certificate (`glue_ok`/`peak_abs` from calmeter; absent on old TSVs or
    on the SC-55 side, which has no BusGlue)."""
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
    if "peak_abs" in col:
        maxcol = max(maxcol, col["peak_abs"])
    data, glue = {}, {}
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) <= maxcol:
            continue
        if "peak_abs" in col:
            gp = glue.setdefault(int(f[col["program"]]),
                                 {"n": 0, "viol": 0, "max_peak": 0.0, "smp": 0, "smp_n": 0})
            pk = float(f[col["peak_abs"]])
            gp["n"] += 1
            gp["max_peak"] = max(gp["max_peak"], pk)
            if col.get("glue_ok") is not None and f[col["glue_ok"]] != "1":
                gp["viol"] += 1
            if "sampled" in col and f[col["sampled"]] != "-1":
                gp["smp_n"] += 1
                gp["smp"] += 1 if f[col["sampled"]] == "1" else 0
        if f[col["sounded"]] != "1":
            continue
        p, k, v = int(f[col["program"]]), int(f[col["key"]]), int(f[col["velocity"]])
        traj = [float(f[i]) for i in bidx]
        data.setdefault(p, {}).setdefault(k, {})[v] = traj
    return data, glue


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


def new_trim(shipped, residual):
    """Damped UPDATE of an existing trim. `residual = implied_total - shipped`, so the
    correction is applied to the trim the program already carries.

    Damp the CHANGE, not the total: `DAMP * implied_total` would drag a program that is
    already correctly trimmed (residual 0) 30% back toward zero — for GM6 (+6 dB shipped)
    that is a spurious -1.8 dB. Programs being derived from scratch carry shipped = 0, where
    the two forms coincide, which is why this only bites the ear-vetted entries."""
    if abs(residual) < DEADBAND:
        return shipped  # inside the dead-band: keep the current trim untouched
    return max(-CLAMP, min(CLAMP, float(round(shipped + DAMP * residual))))


def evaluate(ferro, sc, shipped_tbl=None):
    """Run all guards + level for every shared program. Returns a list of row dicts and the
    anchor. Pure over the two loaded tables — the heart of the derivation and the selftest."""
    progs = sorted(set(ferro) & set(sc))
    rows = []
    for p in progs:
        fp, sp = ferro[p], sc[p]
        role, name = GM_FAMILY.get(p, ("?", "?"))
        tbl = SHIPPED if shipped_tbl is None else shipped_tbl
        shipped = tbl[p] if p < len(tbl) else 0.0
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
                "clean": clean, "nkeys": len(keyset), "g": g, "tilt": tilt, "vel": vg,
                "med_shape": med_shape,
            }
        )
    # --- anchor: engine offset K = median RENDERED gap g over a vetted sustained cohort ---
    # The anchor is the ONLY coupling between programs, so one bad member contaminates every
    # derived trim. Admit by MEASUREMENT QUALITY, using family only as a prior. Two passes:
    #
    #   1. provisional frame over every non-excluded sustained program;
    #   2. strict re-selection, then the final frame.
    #
    # The residual is `implied - shipped`, and since implied = anchor + shipped - g that is
    # just `anchor - g`: how far a program's RENDERED output sits from the frame. For a
    # program carrying a nonzero (ear-vetted) shipped trim, residual ~ 0 means the metric
    # agrees with the ear. Admitting on |residual| is outlier rejection around the median,
    # not tuning the frame toward a wanted answer.
    loose = [r for r in rows
             if r["role"] == "sustained" and not r["excluded"] and r["g"] is not None]
    prov = statistics.median([r["g"] for r in loose]) if loose else None
    for r in rows:
        r["residual"] = (prov - r["g"]) if (prov is not None and r["g"] is not None) else None

    cohort = [r for r in loose
              if r["shipped"] != 0.0                       # ear-vetted, not merely untouched
              and r["tilt"] < ADMIT_TILT_DB                # far inside the pitch-tilt guard
              and len(r["clean"]) == r["nkeys"]            # no unmetrable key
              and abs(r["residual"]) <= ADMIT_RESIDUAL_DB] # agrees with its own shipped trim
    if len(cohort) < MIN_COHORT:
        cohort = loose  # too few survived strict admission — fall back and say so loudly
    anchor = statistics.median([r["g"] for r in cohort]) if cohort else None
    mad = (statistics.median([abs(r["g"] - anchor) for r in cohort])
           if anchor is not None else None)

    for r in rows:
        if anchor is not None and r["g"] is not None:
            r["D_p"] = r["g"] - r["shipped"] - anchor
            r["residual"] = anchor - r["g"]  # recompute against the FINAL frame
            # An excluded program keeps whatever trim it already carries: we could not
            # measure it, so we must not change it.
            r["trim"] = r["shipped"] if r["excluded"] else new_trim(r["shipped"], r["residual"])
        else:
            r["D_p"] = None
            r["trim"] = r["shipped"]
        if r["role"] == "never":
            r["trim"] = 0.0
    return rows, anchor, cohort, mad


def run(ferro_path, sc_path):
    (ferro, fglue), (sc, _) = load(ferro_path), load(sc_path)
    only_f, only_s = sorted(set(ferro) - set(sc)), sorted(set(sc) - set(ferro))
    if only_f or only_s:
        print(f"!! programs in one engine only (no differential): ferro-only={only_f} "
              f"sc-only={only_s}")
    rows, anchor, cohort, mad = evaluate(ferro, sc)

    mixed = {}  # programs whose probe straddles their sample-bank edge (certificate 3)

    # --- certificate 1: glue inertness (ferro side only; the SC-55 has no BusGlue) ------
    print("=== glue-inertness certificate (ferro must be LINEAR where we measure) ===")
    if not fglue:
        print("  !! no peak_abs column - this render was metered from a NORMALIZED WAV, so "
              "absolute level is meaningless. Re-render with the raw_dump example.")
    else:
        viol = {p: g for p, g in fglue.items() if g["viol"] > 0}
        # A violation only matters if the program's measurement is actually consumed. The
        # `never` families (SynthFX 96-103, SoundFX 120-127) are never trimmed and never
        # anchor, so glue engagement there cannot reach a shipped number.
        matters = {p: g for p, g in viol.items() if GM_FAMILY.get(p, ("?",))[0] != "never"}
        worst = max(g["max_peak"] for g in fglue.values())
        if matters:
            print(f"  !! {len(matters)}/{len(fglue)} CONSUMED programs have notes at/above the "
                  f"ceiling - their trims are NOT certified:")
            for p, g in sorted(matters.items(), key=lambda kv: -kv[1]["max_peak"])[:12]:
                print(f"     GM{p:<3} {g['viol']}/{g['n']} notes, peak {g['max_peak']:.3f}")
            print("     Fix by lowering mkprobe.PROBE_CC7 (a uniform gain the anchor absorbs).")
        else:
            print(f"  all consumed programs certified inert. The differential is linear where "
                  f"we measure, so the dB back-out is exact.")
        unused = {p: g for p, g in viol.items() if p not in matters}
        if unused:
            names = ", ".join(f"GM{p}({g['max_peak']:.2f})" for p, g in sorted(unused.items()))
            print(f"  (over ceiling but never trimmed/anchored, so harmless: {names})")
        print(f"  worst peak anywhere {worst:.3f}; ceiling is calmeter::GLUE_CEILING.")

    # --- certificate 3: sampled-vs-fallback ground truth -----------------------------
    # From diffing the probe render against its `--no-samples` twin, so it cannot drift from
    # the sampler's real routing. A program metered ENTIRELY on the modelled fallback is
    # usually fine (many GM programs have no sample bank; the model IS the voice). The risk
    # is MIXED: the probe straddles the bank edge, so different keys measure different
    # instruments — which inflates per-key spread and can bias the median.
    mixed = {p: g for p, g in fglue.items() if 0 < g["smp"] < g["smp_n"]}
    if any(g["smp_n"] for g in fglue.values()):
        full = sum(1 for g in fglue.values() if g["smp_n"] and g["smp"] == g["smp_n"])
        none_ = sum(1 for g in fglue.values() if g["smp_n"] and g["smp"] == 0)
        print(f"\n=== sampled/fallback ground truth (probe vs --no-samples twin) ===")
        print(f"  {full} fully sampled, {len(mixed)} MIXED, {none_} fully modelled.")
        if mixed:
            names = ", ".join(f"GM{p}({g['smp']}/{g['smp_n']})"
                              for p, g in sorted(mixed.items()))
            print(f"  MIXED (probe straddles the bank edge - trims LOW-CONFIDENCE): {names}")

    print(f"\n# SHAPE_DB={SHAPE_DB} FLOOR_REL={FLOOR_REL_DB} PITCH_TILT={PITCH_TILT_DB} "
          f"VEL_GUARD={VEL_GUARD} MAX_FAIL_KEYS={MAX_FAIL_KEYS} DAMP={DAMP} CLAMP=+/-{CLAMP}")
    if anchor is None:
        print("!! no sustained-cohort anchor could be formed - cannot derive trims.")
    else:
        print(f"# paired anchor = engine offset K (median rendered ferro-SC gap over "
              f"{len(cohort)} sustained progs): {anchor:.2f} dB   MAD {mad:.2f} dB")
        if len(cohort) < MIN_COHORT:
            print(f"!! cohort {len(cohort)} < MIN_COHORT {MIN_COHORT} - strict admission left "
                  f"too few members, so this fell back to the loose cohort. LOW CONFIDENCE.")
        if mad is not None and mad > MAD_MAX_DB:
            print(f"!! cohort MAD {mad:.2f} > {MAD_MAX_DB} dB - the single-scalar engine-offset "
                  f"model may be false (K family-dependent). Do not ship on this frame.")
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
        # Only percussive rows can be PROPOSED, so printing a computed number for a FROZEN
        # sustained row invites misreading it as a proposal. Show a dash; the residual oracle
        # below is where a sustained program's disagreement is meant to be read.
        new = f"{r['trim']:4.0f}" if r["role"] == "percussive" else "   -"
        print(f"{r['p']:>4} {r['name']:>18} {r['role']:>10} {d} {r['tilt']:5.1f} {r['vel']:5.1f} "
              f"{ms} {r['shipped']:5.1f} {new} {note:<32}")

    print("\n=== proposed percussive-family trim CHANGES (non-excluded) ===")
    any_trim = False
    for r in rows:
        if r["role"] == "percussive" and not r["excluded"] and r["trim"] != r["shipped"]:
            any_trim = True
            # Ground-truthed, not guessed by family: this program's probe measured a MIX of
            # the sampled and modelled voices across keys.
            flag = "  [LOW-CONFIDENCE: probe straddles the sample-bank edge]" if (
                r["p"] in mixed) else ""
            print(f"    GM{r['p']:<3} {r['name']:<18} {r['shipped']:+.0f} -> {r['trim']:+.0f} dB"
                  f"   (residual {r['residual']:+.1f}){flag}")
    if not any_trim:
        print("    (none)")

    # Programs held back ONLY by a moderate pitch tilt. A median trim would be right on
    # average and off by ~tilt/2 at the register extremes — better than the nothing they
    # carry today, but not on metric confidence alone. Surface them for a listening call:
    # whatever Arthur accepts enters SHIPPED as an ear judgment, which the residual oracle
    # then monitors forever.
    print(f"\n=== ear-vet candidates (tilt {PITCH_TILT_DB}-{EARVET_TILT_DB} dB only; a median "
          f"trim is ~+-tilt/2 off at the extremes) ===")
    cands = [r for r in rows
             if r["role"] == "percussive" and r["excluded"] and r["D_p"] is not None
             and all("pitch-tilt" in x for x in r["reasons"])
             and r["tilt"] < EARVET_TILT_DB
             and new_trim(r["shipped"], r["residual"]) != r["shipped"]]
    for r in sorted(cands, key=lambda r: r["tilt"]):
        print(f"    GM{r['p']:<3} {r['name']:<18} {r['shipped']:+.0f} -> "
              f"{new_trim(r['shipped'], r['residual']):+.0f} dB   (tilt {r['tilt']:.1f}, "
              f"so ~+-{r['tilt']/2:.1f} dB across register)")
    if not cands:
        print("    (none)")

    excl = [r for r in rows if r["excluded"]]
    print("\n=== guard-excluded (route to voice-fix / ears) ===")
    for r in excl:
        print(f"    GM{r['p']:<3} {r['name']:<18} {r['role']:<10} {'; '.join(r['reasons'])}")

    # --- certificate 2: the residual oracle ------------------------------------------
    # Every program carrying a NONZERO shipped trim is an ear-judgment someone already made.
    # residual = implied - shipped = anchor - g: how far the program's rendered output sits
    # from the frame. ~0 means the metric agrees with the ear. A large residual is the
    # cheapest detector we have for the class the guards CANNOT see - a voice that is
    # spectrally broken but envelope-clean (it passes shape/tilt/velocity and would other-
    # wise collect a confident trim that merely levels a broken sound).
    # ASCII only - a Greek delta crashes cp1252 stdout when redirected on Windows.
    print(f"\n=== residual oracle (implied - shipped, over ear-vetted trims; "
          f"|d|>{RESIDUAL_FLAG_DB} = metric contradicts the ear) ===")
    # "Ear-vetted" = carries a nonzero trim OR is a recorded decision to stay at 0.0.
    vetted = [r for r in rows
              if (r["shipped"] != 0.0 or r["p"] in EAR_DECIDED)
              and r["residual"] is not None and not r["excluded"]]
    if not vetted:
        print("    (no ear-vetted programs measured in this run)")
    else:
        med = statistics.median([r["residual"] for r in vetted])
        flagged = sorted((r for r in vetted if abs(r["residual"]) > RESIDUAL_FLAG_DB),
                         key=lambda r: -abs(r["residual"]))
        print(f"    median residual over {len(vetted)} vetted programs: {med:+.2f} dB "
              f"(want ~0; a systematic offset means the metric and the ear disagree at scale)")
        for r in flagged:
            print(f"    GM{r['p']:<3} {r['name']:<18} shipped {r['shipped']:+.1f} "
                  f"implies {r['shipped'] + r['residual']:+.1f} (d{r['residual']:+.1f})")
        if not flagged:
            print(f"    no program disagrees by more than {RESIDUAL_FLAG_DB} dB.")
    return 0


def run_panel(ferro_path, ref_paths, write_baseline_path=None):
    """Derive against a PANEL of independent references and gate on their agreement."""
    ferro, fglue = load(ferro_path)
    refs = []
    for rp in ref_paths:
        data, _ = load(rp)
        rows, anchor, cohort, mad = evaluate(ferro, data)
        label = pathlib.Path(rp).name.split("_", 1)[0].lower()
        refs.append({"label": label, "by": {r["p"]: r for r in rows},
                     "anchor": anchor, "cohort": cohort, "mad": mad})

    # ferro's own internal placement: a THIRD, weaker signal. Self-referential, so it is
    # blind to a uniform whole-synth offset and "median over 128 programs" is not a musical
    # truth - it is for spotting defects the panel cannot see, not for setting trims.
    bodies = {p: prog_body(ferro[p], sorted(ferro[p])) for p in ferro}
    fmed = statistics.median([b for b in bodies.values() if b is not None])

    print("=== reference panel ===")
    for r in refs:
        n = len(r["cohort"])
        print(f"  {r['label']:<6} anchor {r['anchor']:+6.2f} dB  cohort {n:>3}  MAD {r['mad']:.2f}"
              + ("   !! cohort below MIN_COHORT" if n < MIN_COHORT else ""))
    print(f"  agreement gate: references must agree within {PANEL_AGREE_DB} dB\n")

    progs = sorted(set.intersection(*[set(r["by"]) for r in refs]))
    out = []
    for p in progs:
        rows_p = [r["by"][p] for r in refs]
        res = [x["residual"] for x in rows_p if x["residual"] is not None]
        excl = [f"{r['label']}: {'; '.join(r['by'][p]['reasons'])}"
                for r in refs if r["by"][p]["excluded"]]
        if len(res) < len(refs):
            consensus = spread = None
        else:
            consensus, spread = statistics.median(res), max(res) - min(res)
        agree = spread is not None and spread <= PANEL_AGREE_DB
        shipped = SHIPPED[p] if p < len(SHIPPED) else 0.0
        role = GM_FAMILY.get(p, ("?", "?"))[0]
        # A recorded ear decision outranks the panel: never auto-change it, however well the
        # references agree. Ears are the final authority; the panel only sets the default.
        held = p in EAR_DECIDED
        trim = (new_trim(shipped, consensus)
                if (agree and not excl and role == "percussive" and not held) else shipped)
        out.append({"p": p, "name": GM_FAMILY.get(p, ("?", "?"))[1], "role": role,
                    "shipped": shipped, "res": res, "consensus": consensus, "spread": spread,
                    "agree": agree, "excl": excl, "trim": trim, "held": held,
                    "int_f": (bodies[p] - fmed) if bodies.get(p) is not None else None})

    labels = " ".join(f"{r['label']:>7}" for r in refs)
    print(f"{'GM':>4} {'name':<18} {'int_F':>6} {labels} {'spread':>7} {'ship':>5} {'new':>4}")
    for o in out:
        res = " ".join(f"{v:+7.2f}" for v in o["res"]) if o["res"] else " " * 7 * len(refs)
        sp = f"{o['spread']:7.2f}" if o["spread"] is not None else "    n/a"
        it = f"{o['int_f']:+6.1f}" if o["int_f"] is not None else "   n/a"
        new = f"{o['trim']:4.0f}" if o["role"] == "percussive" else "   -"
        print(f"{o['p']:>4} {o['name']:<18} {it} {res} {sp} {o['shipped']:5.1f} {new}")

    print("\n=== AUTO-SHIP: references agree, guards clean, trim changes ===")
    ship = [o for o in out if o["agree"] and not o["excl"] and o["role"] == "percussive"
            and o["trim"] != o["shipped"]]
    for o in sorted(ship, key=lambda o: o["p"]):
        print(f"    GM{o['p']:<3} {o['name']:<18} {o['shipped']:+.0f} -> {o['trim']:+.0f} dB   "
              f"(consensus {o['consensus']:+.1f}, refs agree to {o['spread']:.1f} dB)")
    if not ship:
        print("    (none)")

    print("\n=== HELD by a recorded ear decision (panel cannot override) ===")
    for o in [x for x in out if x["held"]]:
        would = (f"panel would say {new_trim(o['shipped'], o['consensus']):+.0f}"
                 if o["consensus"] is not None and o["agree"]
                 else f"panel has no consensus (spread {o['spread']:.1f} dB)"
                 if o["spread"] is not None else "panel could not measure it")
        print(f"    GM{o['p']:<3} {o['name']:<18} held at {o['shipped']:+.0f} dB   ({would})")

    print("\n=== NO CONSENSUS: the references disagree with each other -> ears decide ===")
    dis = [o for o in out if o["spread"] is not None and not o["agree"] and not o["excl"]]
    for o in sorted(dis, key=lambda o: -o["spread"]):
        imp = " / ".join(f"{r['label']} {new_trim(o['shipped'], v):+.0f}"
                         for r, v in zip(refs, o["res"]))
        print(f"    GM{o['p']:<3} {o['name']:<18} spread {o['spread']:5.1f} dB   implies {imp}")
    if not dis:
        print("    (none)")

    print("\n=== guard-excluded on at least one reference (voice work) ===")
    for o in out:
        if o["excl"]:
            print(f"    GM{o['p']:<3} {o['name']:<18} " + " | ".join(o["excl"]))
    if write_baseline_path is not None:
        write_residual_baseline(refs, write_baseline_path)
        return 0
    return 0 if compare_residual_baseline(refs) else 1


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


def _trim_declaration(name, value):
    body = ", ".join([str(value)] * 128)
    return f"pub(crate) const {name}: [f32; 128] = [{body}];\n"


def _zero_pin(program):
    return f"assert_eq!(PROGRAM_TRIM_DB[{program}], 0.0);\n"


def _selftest_engine_parser():
    real = _trim_declaration("PROGRAM_TRIM_DB", 1.25)
    sibling = _trim_declaration("SC55_PROGRAM_TRIM_DB", -9.9)
    assert parse_shipped(sibling + real, "sibling fixture") == [1.25] * 128

    for source, expected_count in [
        (sibling, 0),
        ("// " + real, 0),
        (real + real, 2),
        ("#[cfg(feature = \"alternate\")]\n" + real + real, 2),
    ]:
        try:
            parse_shipped(source, "rejection fixture")
        except SystemExit as e:
            assert f"found {expected_count}" in str(e), e
        else:
            raise AssertionError(
                f"shipped-table parser accepted {expected_count} exact declarations"
            )

    pins = "".join(_zero_pin(program) for program in [0, 1, 3, 11])
    assert parse_ear_decided(pins, "pin fixture") == {0, 1, 3, 11}
    fifth_pin = """assert_eq!(
        PROGRAM_TRIM_DB[99],
        0.0
    );
"""
    assert parse_ear_decided(pins + fifth_pin, "fifth-pin fixture") == {0, 1, 3, 11, 99}

    for source, expected in [
        (real, "found no canonical"),
        (pins + _zero_pin(11), "duplicate ear-decision pins"),
        (_zero_pin(128), "outside GM program 0..127"),
        ("assert_eq!(PROGRAM_TRIM_DB[99], 1.0);", "found no canonical"),
    ]:
        try:
            parse_ear_decided(source, "ear-decision rejection fixture")
        except SystemExit as e:
            assert expected in str(e), e
        else:
            raise AssertionError(f"ear-decision parser accepted invalid fixture: {expected}")


def _selftest_residual_baseline():
    fixture = {}
    for program in range(128):
        for reference in BASELINE_REFERENCES:
            fixture[(reference, program)] = {
                "residual_db": 0.0,
                "shipped_db": 0.0,
                "guard_excluded": False,
            }
    fixture[("sc55", 6)] = {
        "residual_db": 1.46,
        "shipped_db": 6.0,
        "guard_excluded": True,
    }
    fixture[("yxg", 6)] = {
        "residual_db": -1.07,
        "shipped_db": 6.0,
        "guard_excluded": True,
    }
    parsed = parse_residual_baseline(serialize_residual_baseline(fixture), "fixture")
    assert parsed == fixture

    current = {key: dict(value) for key, value in fixture.items()}
    # A newly-applied scalar trim changes residual by its inverse and is not voice drift.
    current[("sc55", 5)]["residual_db"] = -1.0
    current[("sc55", 5)]["shipped_db"] = 1.0
    assert not residual_baseline_findings(parsed, current)

    # The MM-BUG-KILN-00108 hole: excluded GM6 must still report and fail on level drift.
    current[("sc55", 6)]["residual_db"] += 1.25
    findings = residual_baseline_findings(parsed, current)
    assert any(
        finding["program"] == 6
        and finding["reference"] == "sc55"
        and finding["kind"] == "drift"
        for finding in findings
    ), findings

    current = {key: dict(value) for key, value in fixture.items()}
    current[("yxg", 6)]["guard_excluded"] = False
    current[("sc55", 7)]["residual_db"] = None
    findings = residual_baseline_findings(parsed, current)
    assert {finding["kind"] for finding in findings} == {"guard", "measurement"}, findings

    malformed = serialize_residual_baseline(fixture).replace(
        "127,yxg,+0.00,0.0,false\n", ""
    )
    try:
        parse_residual_baseline(malformed, "missing-row fixture")
    except SystemExit as e:
        assert "exactly every program" in str(e), e
    else:
        raise AssertionError("residual baseline parser accepted a missing program/reference row")


# Fixture shipped table - DELIBERATELY independent of the live PROGRAM_TRIM_DB.
# A self-test whose expectations move whenever a production trim changes is not a
# self-test. That coupling is exactly what surfaced when SHIPPED stopped being a
# stale hand-copy and became derived (MM-BUG-KILN-00109): the fixture below had
# silently been asserting against 2026-07-17 production values.
ST_SHIPPED = [0.0] * 128
for _p, _v in {
    # the sustained cohort: nonzero trims, so they are admissible ear judgments
    16: -4.5, 17: -3.0, 18: -1.5, 19: -6.0,
    20: -3.0, 21: -5.0, 22: -1.0, 23: -4.5,
    40: -4.0, 41: -4.0, 42: -3.5, 43: -6.0,
    6: 6.0,    # already-correct percussive trim: must survive untouched
    56: -6.0,  # 5 dB off the frame: rejected from the cohort, still reported
}.items():
    ST_SHIPPED[_p] = _v


def selftest():
    _selftest_engine_parser()
    _selftest_residual_baseline()
    keys = [48, 53, 58, 63, 68, 73]
    ferro, sc = {}, {}

    # Sustained cohort: correctly-calibrated -> RENDERED ferro == SC (engine offset K=0), so
    # g=0, anchor=0, residual=0. Admission needs a NONZERO shipped trim (an ear judgment, not
    # merely an untouched program), so use the organ + solo-strings blocks: 12 members, above
    # MIN_COHORT. Each must come back with its trim UNCHANGED.
    COHORT = (16, 17, 18, 19, 20, 21, 22, 23, 40, 41, 42, 43)
    for p in COHORT:
        ferro[p], sc[p] = _prog({k: (_flat(-20.0), _flat(-20.0)) for k in keys})

    # GM56 Brass (sustained, SHIPPED -6): 5 dB off the frame. Must be REJECTED from the
    # cohort by admission (|residual| > ADMIT_RESIDUAL_DB) yet still reported by the oracle.
    ferro[56], sc[56] = _prog({k: (_flat(-15.0), _flat(-20.0)) for k in keys})

    # GM6 Piano (percussive, SHIPPED +6): already correctly trimmed -> residual 0 -> its trim
    # must stay +6. Guards the damp-the-change fix: damping the TOTAL would return +4.
    ferro[6], sc[6] = _prog({k: (_flat(-20.0), _flat(-20.0)) for k in keys})

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

    rows, anchor, cohort, mad = evaluate(ferro, sc, ST_SHIPPED)
    byp = {r["p"]: r for r in rows}
    inco = {r["p"] for r in cohort}

    assert anchor is not None and abs(anchor) < 1e-6, f"anchor {anchor}"
    assert mad is not None and mad < 1e-6, f"mad {mad}"
    # Strict admission: the 12 clean members in, the 5 dB-off GM56 out.
    assert inco == set(COHORT), f"cohort {sorted(inco)}"
    assert abs(byp[56]["residual"] + 5.0) < 1e-6, ("GM56 residual", byp[56]["residual"])
    # Damp-the-change: an already-correct trim survives untouched.
    assert byp[6]["trim"] == 6.0, ("damp the change, not the total", byp[6]["trim"])
    for p in COHORT:
        assert not byp[p]["excluded"], (p, byp[p])
        assert byp[p]["trim"] == ST_SHIPPED[p], (p, byp[p]["trim"], ST_SHIPPED[p])
    # Fresh derivations (shipped 0) are unaffected by the damping change.
    assert not byp[8]["excluded"] and byp[8]["trim"] == -2.0, byp[8]
    assert not byp[9]["excluded"] and byp[9]["trim"] == -1.0, ("matched one-shot", byp[9])
    assert byp[24]["excluded"] and "shape" in byp[24]["reasons"][0], byp[24]
    assert byp[25]["excluded"] and "shape/short" in byp[25]["reasons"][0], byp[25]
    assert byp[26]["excluded"] and any("pitch-tilt" in r for r in byp[26]["reasons"]), byp[26]
    print(f"selftest OK - exact/unique engine-state and residual-baseline parsers; excluded "
          f"cross-run drift retained; anchor 0.00 MAD 0.00 over "
          f"{len(cohort)} admitted; GM56 (5 dB off) rejected from the cohort; GM6 keeps "
          "+6 (damp the change); GM8 -2, GM9 (matched one-shot) -1; GM24 shape / GM25 "
          "sub-hop / GM26 pitch-tilt excluded.")
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        return selftest()
    args = sys.argv[1:]
    write_baseline_path = None
    if "--write-baseline" in args:
        if args.count("--write-baseline") != 1:
            print("derive_trims: --write-baseline may appear only once.")
            return 2
        option = args.index("--write-baseline")
        if option + 1 >= len(args):
            print("derive_trims: --write-baseline requires an output path.")
            return 2
        write_baseline_path = args[option + 1]
        del args[option : option + 2]
    if len(args) < 2:
        print("usage: derive_trims.py <ferro.levels.tsv> <ref.levels.tsv> [ref2 ...]"
              " [--write-baseline PATH]  |  --selftest")
        print("  two or more references switch on PANEL mode: the consensus is the target and"
              " disagreement between references routes the program to ears.")
        return 2
    if write_baseline_path is not None and len(args) < 3:
        print("derive_trims: --write-baseline requires panel mode with both references.")
        return 2
    if len(args) > 2:
        return run_panel(args[0], args[1:], write_baseline_path)
    return run(args[0], args[1])


if __name__ == "__main__":
    sys.exit(main())
