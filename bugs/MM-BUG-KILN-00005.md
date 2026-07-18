# MM-BUG-KILN-00005 — Viola (GM 41) shares the violin sampled onset; 40 and 41 are near-identical for the first ~380 ms

- **State:** Fixed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-18, `9d34950`)

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

Fixed on branch `task/20260718-FIX-HUM-ferrosintesis-viola-bank-gm41-dedicated`
(commits `079a7c9` bake, `602f09a` bank+embed, `9d34950` route+oracle), built
under loop-build.

A dedicated CC0 `viola_bank` was baked from the (already-pinned) VSCO-2-CE **Viola
Section susvib** source and routed to GM 41, so 40 and 41 no longer share the
solo-violin onset:

- `prepare.py`: added the viola source — 7 zones C3–D6, p/f dynamic layers,
  sounding-pitch dest names over the octave-down section labels (VSCO string-section
  labels sound ~1 octave above the label), viola in `TWO_F_STRONG` for the per-note
  2f cap, routed to the CC0 `-orchestral2` crate. Baked 14 onset WAVs; **measured
  roots** (conf 0.86–0.98, ≤10 cents): C3 130.5, G3 195.5, D4 292.7, A4 439.9,
  E5 659.8, B5 987.2, D6 1172.4 Hz.
- `sampler.rs`: `viola_f()`/`viola_p()` + `viola_bank(vel)` (mirrors `violin_bank`)
  registered in `prewarm`; `orchestral2/src/lib.rs`: 14 `include_bytes!`.
- `voices.rs:10916`: GM 41 arm wraps `viola_bank` instead of `violin_bank`. Kept
  `LA_VIOLIN` gain/fade (`la_level_continuity` green — the section level fits the
  seam, no `LA_VIOLA` needed). **`BODY_VIOLA` left unchanged**: the roadmap suggested
  darkening it, but every distinctness/centroid oracle is green without it, so the
  minimal fix stands (the *onset* was the defect the ear judges).
- `testutil.rs`: `onset_tier_classification_is_stable` `SHARED_ONSET_PAIRS` dropped
  `(40,41)` — the pair is now independent-onset (its own bank) and scores on the full
  perceptual metric. This is the deliberate GREEN transition, re-pinned per the test's
  own T9 instruction, not a weakening.

### Verification

- **`every_gm_family_sounds_free_of_unexpected_clones` passes with (40,41) on the
  full metric** — the dedicated viola onset genuinely separates them (verified
  distinct, not masked). All 6 perceptual/routing oracles + LA seam oracles green.
- **Full workspace suite green** (488 + all crates, 0 failed) — no other oracle moved.
- **clippy `-D warnings` clean; fmt applied.**
- **Render-diff** (baseline = task merge-base vs new release binary): a GM41-using
  track (`Windowlit Water`) differs on samples-on and is **bit-identical under
  `--no-samples`** (confinement); two non-GM41 tracks are **samples-on bit-identical**
  (zero contamination). GM41-only reach confirmed.

Shipped code → one version bump owed at integration. Second-eyes verification pending
before `Closed` (two-eyes rule).

## Notes

- Source is already SHA-pinned (VSCO-2-CE, CC0) — this is incremental, using
  `contrabass_bank` as the wiring template.
- Any `voices.rs`/`sampler.rs` change needs the render-diff inventory from the
  task merge-base; expected diffs only on albums using program 41.
- Related but distinct: the residual contrabass wolf-band is MM-BUG-KILN-00012.
