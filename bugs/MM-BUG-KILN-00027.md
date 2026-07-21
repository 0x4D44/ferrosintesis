# MM-BUG-KILN-00027 — `--solo 8` render of Hollow Hill Pt 1 hangs (>400 s vs ~2 min full mix)

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** engine / sampler
- **Raised:** 2026-07-20
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-20, promoted from the 2026-07-19 scratchpad entry — Claude Fable 5, GM sweep audit) → Fixed (2026-07-21, `85d215c`+`a2e6700`+`90f43f2`, bumped `58e487e`) → Closed (2026-07-21, two-eyes verified by an independent Claude Opus 4.8 session: root cause understood, byte-transparency confirmed, regression guard green on trunk)

## Observation

`ferrosintesis "<Hollow Hill Pt 1>.mid" --solo 8 -o x.wav` (channel 8 = nylon,
program 24) runs >400 s and had to be killed, while the FULL-mix render of the
same file finishes in ~2 min and `--solo 7/10/14` also finish in ~2 min. Only
`--solo 8` is pathologically slow.

Reproduces on BOTH the pre-Phase-1 pluck baseline binary AND with
`--peak-normalize` — so it is not the LUFS normalizer and not the pluck redesign.
A >200× slowdown on a solo path is a real engine/sampler defect even though
full-mix renders are unaffected.

Suspect a stuck / never-reaping voice or an LA-sample loop interaction specific to
that channel: `crates/ferrosintesis/src/engine.rs` (solo path / voice reap) +
`crates/ferrosintesis/src/sampler.rs`.

Repro: Hollow Hill Pt 1, `--solo 8`.

## Fix

**Root cause.** The "hang" was a ~10× crawl (14-min render in 456 s wall) of a
*completing* render, not a true hang. IIR feedback tails in the always-running buses
(hall/cathedral reverbs, chorus/echo, sympathetic resonance) decay past ~1e-20 and park
there as denormals; a sparse `--solo` mix leaves almost no live voices, so those buses churn
denormal arithmetic for the whole render.

**Fix.** A per-block `flush_denormal` snapping bus-owned feedback state to exactly 0, called
by the bus owners only (`85d215c` flush; `a2e6700` narrowed it to bus-owned state after a
byte-transparency sweep caught in-primitive flushing nudging voice KS loops). The flush floor
was then lowered `1e-20 → 1e-34` (`90f43f2`): 1e-20 is a *normal* f32 (subnormals start
~1.18e-38), so flushing there was not byte-transparent — the sub-floor δ surfaced via an f32
rounding-tie and `BusGlue` amplified it to a ~2 LSB, −84 dBFS, 4.8 s self-healing burst on
"Atlas of Becoming / Wire and Wake". 1e-34 keeps the perf fix (state × smallest coefficient
stays normal) while dropping the per-add tie hazard ~1e-12 → ~1e-26.

**Verification.** `--solo 8` of Hollow Hill Pt 1: 456 s → ~43 s, identical output stats.
"Wire and Wake" (default + `--peak-normalize`) renders byte-identical to the unflushed
baseline. Regression guard `reverb::tests::tanks_do_not_park_below_the_flush_floor` observed
red → green and confirmed green on trunk in the 598-test ferrosintesis suite. Integrated at
`58e487e`. Diagnosis with Fable 5 and gpt-5.6-sol (rounding-tie mechanism); flush-site bisect
localized the seed (Sympathetic, PingPong exonerated). Full detail in
`wrk_journals/2026.07.21 - JRN - U5 solo8 hang rounding-tie resolution.md`.

## Notes

- Promoted from scratchpad.md (2026-07-19 entry) during the 2026-07-20 GM
  instrument sweep so it is tracked as a defect rather than parked; diagnosis
  session planned.
- Player-correctness issue (the solo path is the documented verification-stem
  workflow), not a voicing issue.
