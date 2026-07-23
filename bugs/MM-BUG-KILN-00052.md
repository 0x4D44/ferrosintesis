# MM-BUG-KILN-00052 — the KILN-00042 register-tilt oracle checks the closed-form corner helper, not the rendered path, so a rewiring that drops the damper hold in `Pluck::new` would pass unguarded

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
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) from the independent two-eyes closure of KILN-00042 by gpt-5.6-sol — a genuine test-coverage gap, not a defect in shipped behaviour)

## Observation

**Symptom.** The KILN-00042 damper-hold fix is guarded by two oracles, and neither
exercises the **rendered** decay path end-to-end:

- `ks_decay_law_holds_across_register` asserts the register tilt using the closed-form
  `corner_scale` / `min_corner` helper directly — it is a unit test of the *math*, not of
  what `Pluck::new` actually wires into the KS loop. If a future change stopped applying
  the hold in the render path (removed the `DamperHold::Derived` branch, changed the loop
  order, regressed the `bright` derivation) the helper would still return the correct
  numbers and this oracle would stay green.
- `damper_hold_preserves_instrument_identity` *does* render real voices, but it only
  checks the **sign** of early spectral-centroid contrast (it no longer checks magnitude,
  post-KILN-00050 rescope), so it is a collateral-safety oracle that would plausibly pass
  even with the hold absent.

So the property "a plucked note's rendered decay-rate tilt across register stays within
the reference-bracketed bound" — the actual thing KILN-00042 fixed — is **not** pinned by
any rendered oracle.

**Expected.** A regression that silently stops applying the hold in `Pluck::new` should
turn a test red.

**Actual.** It would not. Flagged by the independent verifier (gpt-5.6-sol) during the
KILN-00042 two-eyes closure.

## Root cause

The tilt regression oracle was written against the closed-form helper for speed and
determinism, leaving the render path covered only indirectly.

## Fix direction

Add a **rendered** decay-tilt integration oracle: render a plucked preset (e.g. `KOTO` or
`NYLON`) held at a low key and a high key, measure the actual dB/s decay from the rendered
buffer (peak block → last block within 40 dB, or the b0..b8 momentary trajectory as the
M-CAL probe does), and assert the top/bottom ratio is within the reference-bracketed bound
(references sit ~1.7–1.8×; today's held law lands ~3.4× median, so a bound of ~3.5× is the
honest ceiling that a fixed-cutoff regression — 5–12× — would break). Keep it alongside
the closed-form oracle (belt-and-braces), and keep it debug-fast (short render, one preset,
two keys). Exclude the `DamperHold::Off` opt-outs (GM6/GM7 modeled paths; GM33/35) or pick
a preset that is `Derived`.

## Notes

- Pure test-hardening: no shipped-code behaviour changes, so this is a synth-area defect in
  *coverage*, not in output. Landing it should not move any render (render-diff clean).
- Related: KILN-00048/00049/00050 (the KILN-00042 follow-up couplings). This one is
  orthogonal — it hardens the guard rather than extending the fix.
