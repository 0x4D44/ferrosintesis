# MM-BUG-KILN-00050 — above its crossover the KILN-00042 damper hold orders held corners by the preset's t60, not its bright, so plucked instruments re-order in brightness in the top register (ukulele drifts to/under nylon above ~key 64; koto's held corner exceeds nylon's)

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
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
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) — the acknowledged residual of the KILN-00042 relative-budget damper hold, surfaced by a rendered identity scan and confirmed against both experts' analyses)

## Observation

**Symptom.** KILN-00042 fixes the plucked register-decay collapse with a *relative*
damper budget: the in-loop corner is opened until the damper contributes
`KS_DAMP_BUDGET` (0.30) of the preset's own authored `t60` loss. The held corner is
therefore `fc_min = f·√(4.343·f / (ρ·A))` with `A = 60/t60` — it is ordered by **t60**,
not by the preset's authored `bright`. Two presets with the same `t60` get the same held
corner regardless of how bright or dark they were voiced; a longer-ringing preset (larger
t60, smaller A) gets a *wider* held corner.

Measured on a rendered scan (vetted broadband `centroid`, [0.030, 0.420] s, seeds
aggregated, key = C4 unless noted):

- **Ukulele vs nylon** (uke `bright` 4800 > nylon 3800, but uke t60 1.8 < nylon 3.8): the
  uke stays brighter through key 60 (653 vs 514) but crosses under around key 64 (700 vs
  736) and drifts darker above it.
- **Koto vs nylon** (koto `bright` 1900 ≪ nylon 3800, koto t60 7.0 ≫ nylon 3.8): the
  koto's long t60 gives it a *wider* held corner than nylon (fc_min ≈ 5518 Hz vs 4083 Hz
  at key 60). By the vetted centroid the audible effect is mild in the playing register
  (koto 533 vs nylon 514 at key 60 — within ~4%, and koto is darker at keys 55 and 64),
  but the corner ordering is inverted and a higher-band metric reads it as a clear
  inversion.

**Expected.** A preset's *brightness ordering* relative to its neighbours should not
change across the register: a ukulele should read brighter than a concert guitar wherever
both are played, a koto darker.

**Actual.** In the held region (above each preset's crossover) the brightness ordering is
set by t60, so instruments re-order. The effect is small-to-inaudible in the mid register
by the ear-correlated broadband centroid (which is why the vetted `ukulele_variation` and
`sitar_jawari` oracles pass, and why the change was approved by ear), but it is real and
grows with pitch.

**Reproduce.** On the KILN-00042 branch, render UKULELE (GM24 bank LSB 96), NYLON (GM24),
KOTO (GM107) at keys 55/60/64, seeds [0x6510, 0x76A1, 0x1250], and compare the
[0.030, 0.420] s broadband `centroid`. Or read the rendered identity oracle
`damper_hold_preserves_instrument_identity` (which passes at key 60) and note it is
deliberately scoped to the identity keys, not the top register.

## Root cause

`crates/ferrosintesis/src/voices.rs`, `DamperHold::Derived` / `min_corner`: the held
corner is derived from the preset's `t60`-implied loss `A`, so `fc_min ∝ √(f/A)` carries
no `bright` term. Above the crossover the corner is therefore t60-ordered. This is the
known trade of the relative-budget law: it was chosen over a `bright`-ordered global-anchor
law (`fc = bright·(f/F_A)^1.5`) because the global anchor, while it provably preserves
`bright` ordering, opens the ukulele's damper enough to fail the *vetted* rendered
`ukulele_variation_is_brighter_and_shorter_than_nylon` oracle (uke ≈ nylon when both held,
1222 vs 1253 at key 60) — i.e. the ukulele's rendered brightness is not primarily
corner-driven, so forcing corner-ratio preservation does not restore it. Neither single
shared law preserves both the decay fix and the full-register brightness ordering; this
entry tracks the residual of the law that was shipped.

## Fix direction

Not a shared-law tweak (both shared laws trade one defect for another — see root cause).
The likely correct lever is **authored, per-instrument voicing** (Fable's recommendation):
where a preset's held-region brightness ordering matters, adjust that preset's `bright` /
`t60` by ear so it holds its place, rather than bending the shared law. Candidates: nudge
UKULELE brighter or shorter so it stays above nylon when held; if the koto's wider held
corner is audible on a real piece, lower its held reach specifically. Any change here needs
the render-diff inventory and an ear pass, and should extend
`damper_hold_preserves_instrument_identity` to the newly-guaranteed keys.

## Notes

- **Not a blocker for KILN-00042.** The effect is mild-to-inaudible in the playing register
  by the ear-correlated metric; the owner approved the change by ear. This is the
  "iterate on trunk" residual, tracked so it is not forgotten.
- The rendered `damper_hold_preserves_instrument_identity` oracle guards the identity keys
  (≈ key 60) against a *convergent* law regressing in; it intentionally does not assert the
  top register, which is this bug.
- Depends indirectly on MM-BUG-KILN-00048: if the velocity→brightness coupling is moved
  out of the loop damper (as 00048 proposes), the held corner's relationship to timbre
  changes and this ordering question should be re-derived.

## Amplified by the 2026.07.23 plucked t60 re-fit

The plucked-family t60 re-fit (matching the SC-55/S-YXG50 ring; nylon 3.8→7.7, steel
4.5→7.0, etc.) makes this residual materially worse. A longer `t60` lowers the KILN-00042
hold's crossover (smaller `A` → larger `fc_min`), so the hold now engages at the PLAYING
register (key ~60), not just the top octave — and where it engages, the bright-independent
held corner compresses the brightness SPREAD between neighbours. Measured (key 60, early
window): steel-vs-nylon authored contrast 0.39 → shipped ~0.08 under the hold. Consequences
already visible in the oracles:
- `damper_hold_preserves_instrument_identity` was re-scoped from a 55%-magnitude-retention
  bar to sign-preservation only, because no honest magnitude bound survives the re-fit's
  range of hold engagement.
- `sitar_shamisen_koto_have_distinct_pluck_presets`: the ringing banjo's upper partials now
  rival the sitar's jawari; the sitar assertion dropped to a marginal cent/t60 edge.

So this is now a **playing-register** brightness-homogenisation of the whole modelled
plucked family, not just a top-octave curiosity. Bumping Severity considerations: still
Low-ish audibly (the owner approved the re-fit's rings by ear, with each instrument in
isolation), but it is the reason the family's *mutual* contrast has narrowed. The fix is
unchanged (per-instrument voicing, or a bright-dependent held corner); its value rose.
