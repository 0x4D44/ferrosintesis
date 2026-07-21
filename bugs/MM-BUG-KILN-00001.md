# MM-BUG-KILN-00001 — Ghost brush slap re-strike dominates soft notes

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synthesis
- **Raised:** 2026-07-10
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
- **State history:** Open (2026-07-10, raised by Codex GPT-5) → Fixed (2026-07-19, `7328c70`, by Claude Opus 4.8 (1M)) → Closed (2026-07-21, independently verified by Codex GPT-5: actual trunk fix `77cf02f`; red-before 2.336/1.590, green-after 1.238/1.290; workspace tests and clippy green)

## Observation

`crates/ferrosintesis/src/drums.rs:975` gives the brush-slap re-excitation burst
an absolute amplitude of `0.50`. At ghost-note velocity 30, the 12 ms second
contact renders louder than the first contact.

Expected: the second strand contact remains audible without dominating the
soft initial slap. Actual: in a focused test at velocity 30, high-passed RMS
was `0.006718` in the 4–11 ms first-contact window and `0.015692` in the
13–22 ms second-contact window, a 2.336× ratio.

Reproduction: render `render_drum_kit(39, 30, 0.3, Kit::Brush)` and compare
`hp_win(..., 800.0, 0.004, 0.011)` with
`hp_win(..., 800.0, 0.013, 0.022)`. The latter currently wins.

## Fix

Fixed in `7328c70`. Root cause: `brush_slap` re-struck the noise bands with a
fixed absolute burst amplitude (`0.50` in `with_bursts`), but the first-contact
noise scales with velocity (`membrane_velocity`'s `nf(vn) = 0.5 + 0.5·vn²`), so
the second/first energy ratio ∝ `0.50/nf(vn)` blew up as velocity fell. The
velocity-100 oracle and the frozen render never exercised low velocity
(`nf→0.81` there bounds the ratio), so it went uncaught.

Extracted `fn noise_vel_gain(vn) = 0.5 + 0.5·vn²` (also used by
`membrane_velocity`, byte-identical) and scaled the burst by it
(`reexcite = 0.50 · noise_vel_gain(velnorm)`), anchored so full velocity keeps
the calibrated `0.50`. The ratio is now velocity-invariant: ghost(30)
2.336→1.238, loud(100) 1.590→1.290.

Verification: new regression oracle `brush_slap_reexcite_tracks_velocity`
(fails pre-fix at 2.336, passes post-fix); `brush_slap_accent_and_double_contact`
still green; re-froze the key-39 `brush_render_signatures_are_stable` fingerprint;
render-diff reported 1 expected change (GM40 + key39) and zero contamination;
549 lib tests + `clippy -D warnings` green. Diagnosis + fix confirmed 3-of-3 by
an adversarial skeptic panel (which also caught a misplaced `#[allow]`, repaired
pre-commit). Left **Fixed**, not Closed — awaiting independent two-eyes verify.

### Verification summary (2026-07-21 — Codex GPT-5)

Independent of the Claude Opus 4.8 fixer. On a throwaway worktree at the actual trunk
fix's parent (`77cf02f^`), the transplanted regression failed with the recorded
ghost/loud re-strike ratios 2.336/1.590. Current trunk passed
`brush_slap_reexcite_tracks_velocity` at 1.238/1.290. Source review confirmed the fix
applies the same `noise_vel_gain` law to the first-contact noise and the re-strike, which
directly removes the fixed-amplitude mismatch. `cargo test --workspace` and
`cargo clippy --workspace --all-targets -- -D warnings` were green. No residual gap.

## Notes

The equal-velocity brush oracle (velocity 100) did not cover ghost notes — the
new regression oracle does. The fix changes the `brush_render_signatures_are_stable`
key-39 fingerprint (updated); the `.opus`/`.wav` renders are git-ignored build
output, so there are no committed listening assets to refresh.
