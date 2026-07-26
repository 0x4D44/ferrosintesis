# MM-BUG-KILN-00058 — GM45 pizzicato's Shaped-vs-Legacy loudness parity broke KEY-DEPENDENTLY after the KILN-00048 decouple (offsets span ~7.5 dB, unfittable by the scalar exc_trim)

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 (1M) while landing KILN-00048 — the decouple exposed it; PIZZ dropped from the shaped_g7 parity check meanwhile, like PICK before it) → Blocked (2026-07-26, GPT-5.6 Codex on KILN-Windows — the required key-aware excitation re-fit needs Arthur to choose whether level or spectral slope should carry the audible correction) → Open (2026-07-26, Arthur approved preserving the Shaped timbre and restoring Legacy level parity with a smooth key/velocity gain correction)

## Observation

**Symptom.** GM45 pizzicato's `shaped_g7` migration parity — Shaped excitation vs the frozen
Legacy reference — was ~0 dB pre-decouple (its `exc_trim` was fit for it). After KILN-00048
(which anchors the KS loop-damper corner at its vel-100 value), the parity is
**key-dependent**. Measured offset (Shaped − post-decouple Legacy, the two re-captured on the
same build):

```
PIZZ  key vel   offset dB
      40  50    -2.95
      40 100    -0.56
      40 120    +0.45
      52  50    -4.58
      52 100    -1.59
      52 120    -0.68
      64  50    -1.75
      64 100    +1.74
      64 120    +2.91
```

A ~7.5 dB spread (−4.58 to +2.91). A single scalar `exc_trim` cannot fit it: (40,50) needs
δ ≥ +0.02 to clear its tol while (64,120) needs δ ≤ −0.41 — an empty intersection (same
impossibility class as GM42/43's turnover and PICK's deferral).

**Expected.** Shaped ≈ Legacy across the range (the migration didn't re-level), which
`shaped_g7_mean_parity_and_seed_bound` guards.

**Actual.** Key-dependent divergence up to ±4.5 dB, so PIZZ was removed from `SHAPED_MIGRATED`
(`crates/ferrosintesis/src/testutil.rs`) to keep the oracle honest.

**Reproduce.** Re-add `"PIZZ"` to `SHAPED_MIGRATED` and run
`cargo test -p ferrosintesis shaped_g7_mean_parity_and_seed_bound`, or
`... print_shaped_loudness_offset -- --ignored --nocapture` for the per-cell offsets above.

## Root cause

The Shaped excitation (natural-rolloff harmonic build) and the Legacy excitation
(peak-normalized noise burst) respond to a loop-corner (`bright`/`pick_lp`) change
DIFFERENTLY, and KILN-00048's corner change is itself key-dependent (via the hold/anchor
interaction). So the Shaped-vs-Legacy differential — zero when `exc_trim` was fit for the old
corner — is now a key-dependent function. `exc_trim` is a per-preset SCALAR and cannot track
it.

## Fix direction

Re-fit PIZZ's Shaped excitation for the post-decouple corner — a per-key or slope adjustment
(`slope`/`exc_trim` are the levers; a scalar `exc_trim` alone won't do it, mirroring PICK).
Needs ears (this box has none) and re-inclusion in `SHAPED_MIGRATED` as the acceptance test.

## Notes

- **Low priority / not a gross defect:** PIZZ still ships its Shaped voice; the issue is that
  its loudness now drifts up to ±4.5 dB from its Legacy reference across the range, a
  calibration/parity gap, not an audible break in a single note. Pizzicato is rarely the
  exposed melodic line.
- **Same class as PICK's deferral** (already out of `SHAPED_MIGRATED` for a key-dependent
  offset) and GM42/43's square-law exclusion (a scalar cannot fit a non-scalar curve).
- Raised while landing KILN-00048; the decouple is the trigger, not the whole cause (the
  underlying Shaped/Legacy corner-response asymmetry pre-existed, latent).

## Blocker — 2026-07-26

Blocking owner: **Arthur**. The nine measured cells prove a scalar trim cannot
restore parity, but they do not choose the audible repair. A key/velocity gain
surface would preserve the current Shaped spectrum while matching Legacy level;
changing the excitation slope would also alter brightness and attack character.
Choosing between them is a product/voicing decision, not a numerical inference.

Unblock with paired 1.0 s renders of current Shaped PIZZ and an otherwise
identical forced-Legacy twin. Use:

- keys **40, 52, and 64**;
- velocities **50, 100, and 120**;
- matched seeds **5, 21, and 99**;
- one raw-level comparison for parity, then a body-level-matched comparison to
  isolate timbre.

Return these exact product inputs:

1. Choose **retain Shaped timbre with key/velocity gain** or **re-fit the
   excitation slope**.
2. If retaining timbre, confirm that the acceptance target is mean
   Shaped-minus-Legacy body level within **±0.5 dB at all nine cells**.
3. If re-fitting slope, identify whether keys 40, 52, and 64 should each sound
   **darker**, **unchanged**, or **brighter** than the current Shaped render.
4. Confirm whether Legacy parity is the desired level contract, or provide the
   preferred dB offset at each of the three keys.

Those answers are enough for a Build pass to implement the narrowest
key-aware law, restore PIZZ to `SHAPED_MIGRATED`, and present a bounded final
A/B. Without them, changing `slope` or gain would silently invent the voice.

### Decision and implementation contract — 2026-07-26

Arthur selected **retain Shaped timbre with key/velocity gain**. Legacy's
captured body level remains the zero-offset calibration contract.

The autonomous Build should:

1. Preserve PIZZ's current Shaped excitation slope, harmonic rolloff, attack,
   loop corner, and decay. Apply the correction only in the PIZZ Shaped gain
   path; do not use spectral or envelope changes to solve level parity.
2. Fit the smallest smooth key/velocity correction that brings the mean
   Shaped-minus-Legacy body level within **±0.5 dB** at all nine anchor cells:
   keys 40, 52, and 64 × velocities 50, 100, and 120, using matched seeds 5,
   21, and 99.
3. Interpolate continuously between anchors and clamp safely beyond the
   measured key/velocity range. Do not introduce a discontinuous nine-cell
   lookup or extrapolate an unbounded gain curve.
4. Add intermediate-key and intermediate-velocity checks so an anchor-perfect
   fit cannot hide overshoot between cells. Retain the existing finite-output,
   velocity-ordering, decay, and determinism oracles.
5. Re-add `"PIZZ"` to `SHAPED_MIGRATED` and make
   `shaped_g7_mean_parity_and_seed_bound` pass honestly across the expanded
   grid. Add a level-matched spectral/attack regression proving the correction
   did not materially change the current Shaped timbre.
6. Produce both raw-level and body-level-matched trunk-versus-candidate A/B
   renders for the nine anchors, then run the required full catalog render
   diff and inspect every affected program.

Land a green implementation as **Fixed**, not Closed. Independent verification
must confirm parity, smooth interpolation, and unchanged level-matched timbre.
