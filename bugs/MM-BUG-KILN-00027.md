# MM-BUG-KILN-00027 — `--solo 8` render of Hollow Hill Pt 1 hangs (>400 s vs ~2 min full mix)

- **State:** Open
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
- **State history:** Open (2026-07-20, promoted from the 2026-07-19 scratchpad entry — Claude Fable 5, GM sweep audit)

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

<unfixed — raised only>

## Notes

- Promoted from scratchpad.md (2026-07-19 entry) during the 2026-07-20 GM
  instrument sweep so it is tracked as a defect rather than parked; diagnosis
  session planned.
- Player-correctness issue (the solo path is the documented verification-stem
  workflow), not a voicing issue.
