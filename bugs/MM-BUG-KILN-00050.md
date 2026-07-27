# MM-BUG-KILN-00050 — above its crossover the KILN-00042 damper hold orders held corners by the preset's t60, not its bright, so plucked instruments re-order in brightness in the top register (ukulele drifts to/under nylon above ~key 64; koto's held corner exceeds nylon's)

- **State:** Fixed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) — the acknowledged residual of the KILN-00042 relative-budget damper hold, surfaced by a rendered identity scan and confirmed against both experts' analyses) → Blocked (2026-07-26, GPT-5.6 Codex on KILN-Windows — both shared laws trade one identity defect for another and the recorded fix requires Arthur to judge the current plucked-family contrast before any per-instrument revoicing) → Open (2026-07-26, Arthur approved a focused, level-matched per-instrument revoicing pass with comparative A/B renders) → Fixed (2026-07-27, GPT-5.6 Codex on KILN-Windows — source candidate `0acc6f7baa81d8ae0243a6012d0ce3e55d050123` restores the required steel/ukulele/koto held-brightness order with preset-local controls, level parity, focused regression coverage, and zero catalog contamination)

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

### Blocker — 2026-07-26

Blocking owner: **Arthur**. Current trunk still uses the relative-budget
`DamperHold::Derived` law, and the record already establishes that its global
alternative restores corner ordering only by failing the vetted rendered
ukulele identity. Choosing either shared law or new per-preset constants without
listening would repeat the trade this bug exists to preserve.

Unblock with one level-matched, same-note comparative pass using the recorded
seeds `0x6510`, `0x76A1`, and `0x1250` at keys 55, 60, and 64:

1. Compare **UKULELE vs NYLON** and decide whether the ukulele remains
   perceptually brighter at every key.
2. Compare **KOTO vs NYLON** and decide whether the koto remains perceptually
   darker at every key.
3. Return one product verdict:
   - **Current contrast is acceptable:** record the residual as ear-accepted
     and close the bug without changing the shared physics.
   - **Revoice the outlier(s):** identify ukulele, koto, or both and confirm the
     target ordering above. A Build pass can then tune only those presets,
     extend the rendered identity oracle across all three keys, and return the
     exact candidate A/B for final sign-off.

The question is mutual identity in the held 30–420 ms window, not whether an
isolated instrument sounds pleasant. The existing centroid evidence cannot
decide that perceptual comparison.

### Decision and implementation contract — 2026-07-26

Arthur approved the **per-instrument revoicing** route. Preserve the shared
`DamperHold::Derived` law and `KS_DAMP_BUDGET`; do not substitute the rejected
global bright-anchor law.

The autonomous Build should:

1. Reproduce the trunk baseline for NYLON, STEEL, UKULELE, and KOTO at keys
   55, 60, and 64, using seeds `0x6510`, `0x76A1`, and `0x1250` and the existing
   `[0.030, 0.420]` second measurement window.
2. Tune only preset-local voicing parameters. Prefer the narrowest control that
   restores held brightness identity without changing the family-wide damper
   equation. Do not shorten an instrument's validated ring merely to improve
   centroid ordering; if `bright` alone cannot retain both ring and identity,
   add a bounded preset-local held-corner scale rather than another shared law.
3. Preserve these perceptual relationships across all three keys:
   UKULELE brighter than NYLON; STEEL brighter than NYLON; KOTO darker than
   NYLON. Require a stable margin above seed/measurement noise, not only the
   correct sign in one render.
4. Extend `damper_hold_preserves_instrument_identity` to cover the three keys
   and all affected comparisons. Keep the existing plucked decay, variation,
   jawari, determinism, and finite-output oracles green.
5. Produce level-matched, same-note **trunk versus candidate** A/B renders for
   each affected comparison. The listening target is mutual brightness in the
   held 30–420 ms region, not isolated pleasantness.
6. Run the required full catalog render diff because the change touches shared
   plucked-voice presets, and inspect every changed program for unintended
   loudness, decay, or register effects.

Land a green implementation as **Fixed**, not Closed. Independent verification
must check the objective ordering and the A/B pack; Arthur retains the final
perceptual sign-off if the candidate changes audible identity materially.

## Fix evidence — 2026-07-27

Source candidate `0acc6f7baa81d8ae0243a6012d0ce3e55d050123` keeps
`DamperHold::Derived` and `KS_DAMP_BUDGET` unchanged. It adds a bounded
`PluckPreset::damper_hold_scale` (clamped to 1.0–2.5), leaves the default at
1.0, and opens only UKULELE (2.2) and STEEL (2.4). STEEL's existing excitation
trim moves from -1.51 dB to -2.18 dB to remove the measured +0.67 dB mean-energy
side effect; NYLON and KOTO receive no voicing change.

The new rendered regression uses the required keys 55/60/64, velocity 100,
seeds `0x6510`, `0x76A1`, and `0x1250`, and the 0.030–0.420 s body. Four
consecutive Hann-windowed 4096-sample DFT centroids avoid the large
phase/seed noise in the old sparse full-window estimator. Every individual
seed clears the contract's stable 4% margin:

- STEEL / NYLON ranges 1.373–2.626.
- UKULELE / NYLON ranges 1.303–2.297.
- KOTO / NYLON ranges 0.685–0.834.

The aggregate centroids (NYLON, STEEL, UKULELE, KOTO) are respectively
455.5/721.8/984.2/354.1 Hz at key 55,
559.0/1134.9/913.9/411.0 Hz at key 60, and
714.9/1526.8/962.0/512.6 Hz at key 64. The former shared-law controls fail at
least two comparisons, proving the oracle detects the defect. The legacy
sparse estimator also retains the correct aggregate sign for all four
instruments at all three keys.

Focused validation passed:

- `cargo fmt --all -- --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- `cargo clippy --workspace --all-targets --no-default-features -- -D warnings`
- `cargo test -p ferrosintesis pluck -- --nocapture` (16 passed; 2 diagnostics ignored)
- `cargo test -p ferrosintesis damper_hold_preserves_instrument_identity`
- `cargo test -p ferrosintesis plucked_hold_preserves_brightness_order_across_identity_keys`
- `cargo test -p ferrosintesis ukulele_variation_is_brighter_and_shorter_than_nylon`
- `cargo test -p ferrosintesis sitar_shamisen_koto_have_distinct_pluck_presets`
- `cargo test -p ferrosintesis shaped_g7_mean_parity_and_seed_bound`
- `cargo test -p ferrosintesis --no-default-features --locked`
  (677 passed, 35 ignored; 4 doctests passed)

The first integration gate exposed that the local STEEL opening canceled the
pre-existing wound-string attenuation (`wound_strings_darker`: wound 467 Hz
versus plain 456 Hz). The final source carries that attenuation into the local
held-corner multiplier. The canary then passes without changing the required
key-55/60/64 ordering measurements above.

Fresh release `raw_dump --no-samples` probes over keys 55/60/64 show NYLON and
KOTO are byte-identical to trunk. Only STEEL and UKULELE change. Native
integrated loudness moves -0.17 LU for STEEL (-50.18 to -50.35 LUFS) and
-0.15 LU for UKULELE (-42.69 to -42.84 LUFS), so the brightness repair is not
a level increase. Same-note raw and -18 LUFS level-matched comparisons are in
`C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00050-candidate`.

The required release-binary render inventory covered all 124 album MIDIs and
17 demo MIDIs:

- albums: 16 expected changed, 105 expected same, 0 contamination, 3 reported
  not reached;
- demos: 5 expected changed, 12 expected same, 0 contamination, 0 not reached.

All 21 changed tracks use GM25 STEEL and/or GM24. The three album
`NOT REACHED` rows declare GM24 but render unchanged bank-0 NYLON; the
bank-blind inventory cannot distinguish those from the actually changed
bank-LSB-96 UKULELE. Their unchanged hashes agree with the isolated NYLON
proof, so they are expected false positives rather than missing wiring.

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
