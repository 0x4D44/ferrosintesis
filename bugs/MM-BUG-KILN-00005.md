# MM-BUG-KILN-00005 — Viola (GM 41) shares the violin sampled onset; 40 and 41 are near-identical for the first ~380 ms

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** sampler
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

The viola arm in `crates/ferrosintesis/src/voices.rs` (program 41, `make()`
dispatch ~`:10907`) wraps `sampler::violin_bank(vel)` at `LA_VIOLIN` — the same
onset bank and gain the violin (GM 40) uses. No dedicated `viola_bank` exists.
Because the LA layer owns the first ~380 ms, the strongest "which instrument"
cue is bit-shared between the two most-played solo strings.

The round-3 roadmap measured this two ways (`wrk_docs/2026.07.16 - PLN -
voice-quality round 3 (15 voices) roadmap.md`, Solo-strings section):
- Identical onset — windowed diff of the two renders over [0,120 ms) is
  diffRMS/RMS = 0.059 (−24.6 dB) at key 64.
- Tail too subtle — `BODY_VIOLIN` vs `BODY_VIOLA` gives centroid 3812 vs
  3605 Hz (viola only ~6 % darker), where SC-55 makes viola ~33 % darker via a
  1.5–2 kHz formant bump, not a smooth tilt. We separate them ~4–5× too weakly,
  and only in the region the shared sample masks.

The perceptual-distinctness oracle already flags `(40,41)` as an `EarPending`
suspect defect (`testutil.rs`), not an accepted-distinct pair.

Blast radius: GM40 ~51 albums, GM41 ~37 — the highest of any open voice
complaint.

## Fix

Roadmap Stage 3 (the named clean fix): wire a dedicated CC0 `viola_bank` from
the already-pinned VSCO-2-CE Viola Section susvib source, route GM41 to it, and
pair with a darker `BODY_VIOLA` toward the ~0.75× violin centroid ratio (SC-55
target). A darker viola makes the distinctness oracle *more* green, not less —
re-verify it in the same commit rather than relaxing it.

## Notes

- Source is already SHA-pinned (VSCO-2-CE, CC0) — this is incremental, using
  `contrabass_bank` as the wiring template.
- Any `voices.rs`/`sampler.rs` change needs the render-diff inventory from the
  task merge-base; expected diffs only on albums using program 41.
- Related but distinct: the residual contrabass wolf-band is MM-BUG-KILN-00012.
