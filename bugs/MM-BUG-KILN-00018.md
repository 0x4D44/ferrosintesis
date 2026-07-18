# MM-BUG-KILN-00018 — Natural brass (56–61) secondary spectral balance: h2–h5 ~17 dB below real brass's low-mid formant ring

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** voices
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

The round-3 brass "holds synthetic" liveness fix landed (living-breath modulator),
but a deeper spectral-balance miss remains: our h2–h5 are ~17 dB weaker than real
brass's low-mid formant ring (`wrk_docs/2026.07.16 - PLN - voice-quality round 3
... .md`, Brass section — parked behind the liveness fix as "a bigger, riskier
body-EQ change"). This is the residual realism gap for natural brass 56–61 once
the frozen-hold issue is addressed.

## Fix

A body-EQ change in the brass model (`Brass`, `crates/ferrosintesis/src/
voices.rs:~9544`) to lift the h2–h5 low-mid formant ring toward the measured SC-55
target, gated by its own oracle (recalibrated from hardware, not weakened) and the
render-diff inventory.

## Notes

- The liveness fix recovered most of the "synthetic" perception; this is the next
  tranche of natural-brass fidelity.
- Higher risk than the liveness change — measure against SC-55 before/after and
  keep synth brass 62/63 untouched.
