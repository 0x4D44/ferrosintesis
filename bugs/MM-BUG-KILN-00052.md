# MM-BUG-KILN-00052 — the KILN-00042 register-tilt oracle checks the closed-form corner helper, not the rendered path, so a rewiring that drops the damper hold in `Pluck::new` would pass unguarded

- **State:** Closed
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
- **State history:** Open (2026-07-23, raised by Claude Opus 4.8 (1M) from the independent two-eyes closure of KILN-00042 by gpt-5.6-sol — a genuine test-coverage gap, not a defect in shipped behaviour) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — added a rendered register-tilt oracle with a forced-off non-vacuity control) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: the coverage gap the bug reports - no oracle exercising the RENDERED decay path - is closed by `rendered_ks_decay_tilt_holds_across_register` (`voices.rs:15524`), which renders the shipped `NYLON` preset through `Pluck::new` at keys 48 and 76 and bounds the measured tilt to 1.0-3.5x. Critically it also renders a `DamperHold::Off` twin and requires that control to stay above 5.25x, so the test cannot silently go vacuous if the hold stops reaching the loop - exactly the regression the bug said would slip past the closed-form helper. Test green; the closed-form oracle it complements is retained (belt-and-braces).)

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

## Resolution — 2026-07-26

The settled, seed-averaged f0-band decay estimator previously local to the
velocity-invariance test is now a shared test helper. The new
`rendered_ks_decay_tilt_holds_across_register` oracle renders the shipped
`NYLON` preset at keys 48 and 76 through `Pluck::new`, then bounds the measured
high/low decay-rate tilt to 1.0–3.5×.

The same test renders an otherwise identical `DamperHold::Off` twin and requires
its tilt to remain at least 5.25×. That negative control proves the chosen span
would turn red if the Derived branch stopped reaching the loop; the test cannot
silently become vacuous as the voicing evolves.

## Verification — 2026-07-26

- Fail-first with the forced-off twin standing in for the shipped preset read
  key 48 at 13.4 dB/s and key 72 at 47.5 dB/s, failing at 3.55×.
- Register-span scoping selected the more robust key 76: the shipped Derived
  path reads `13.4 → 20.4 dB/s` (1.52×), while the Off control reads
  `13.4 → 84.3 dB/s` (6.31×).
- The rendered tilt, closed-form tilt, and rendered velocity-invariance tests
  pass together.
- The complete default suite passed (727 tests, 27 ignored), the model-only
  suite passed (626 tests, 22 ignored), and both doc-test sets passed (4 each).
- Strict workspace clippy and true model-only clippy passed with warnings
  denied; formatting and `git diff --check` passed.
- Fresh release binaries from exact baseline `4831afe`, full 124-MIDI inventory
  at 11.025 kHz: all 124 stayed byte-identical, with zero contamination and zero
  missed paths, confirming the test-only change does not alter shipped output.
