# MM-BUG-KILN-00051 — after the plucked t60 re-fit, the LA guitar sample→model crossfade seam blooms (~5%): the sample onset fades out before the now-hotter model sustain peaks

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sampler
- **Raised:** 2026-07-23
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
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) — surfaced by the plucked-family t60 re-fit; `la_level_continuity` now carries a bounded exception for the guitar labels)

## Observation

**Symptom.** The nylon/steel guitars (GM24/25) carry an LA sample layer that crossfades a
recorded pick onset into the modelled string. The 2026.07.23 plucked-family t60 re-fit
(nylon 3.8 → 7.7, steel 4.5 → 7.0) raised the MODEL sustain level, so at the crossfade
seam — where the sample onset has faded out but before the (now hotter) model fully takes
over — the envelope dips and then blooms ~5 % (≈ 0.4 dB) a few 50 ms windows into the note.
`la_level_continuity` caught it: `steel-guitar-low: attack is not the peak — late window
0.04411 above attack 0.04223`.

**Expected.** The attack (the pick) owns the peak; the sample→model handoff is seamless in
level.

**Actual.** A small mid-note bloom at the crossfade seam. Small (0.4 dB) and unlikely to be
audible, but the attack is no longer strictly the peak.

**Reproduce.** `cargo test -p ferrosintesis --release -- la_level_continuity` — the guitar
labels now take a bounded exception (`bloom <= 1.15`, `sampler.rs`); remove the `guitar`
branch to see the raw failure.

## Root cause

`crates/ferrosintesis/src/sampler.rs` — the LA guitar layer's onset gain / fade
(`LA_GUITAR`, `LA_STEEL` and the crossfade to `[fade_end, ∞): the MODEL owns the sustain`)
was level-matched to the pre-re-fit model, which decayed faster. With the model now
sustaining ~1.5–2 dB louder, the fade schedule leaves a dip-then-bloom at the seam.

## Fix direction

Re-match the LA guitar crossfade to the new model sustain level: either raise the sample
fade-out tail slightly or trim the model level at the seam so the handoff is monotone.
Then remove the bounded `guitar` exception in `la_level_continuity` (it is bounded on both
sides precisely so the fix cannot pass silently). Needs the render-diff inventory.

## Notes

- Cosmetic today (0.4 dB, mid-note). Filed so the exception is not permanent.
- Same class as MM-BUG-KILN-00030 (the harpsichord LA onset not tracking a `vel_sense`
  model) — both are LA-onset-vs-model level tracking gaps.
