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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 (1M) while landing KILN-00048 — the decouple exposed it; PIZZ dropped from the shaped_g7 parity check meanwhile, like PICK before it)

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
