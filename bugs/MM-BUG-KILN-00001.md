# MM-BUG-KILN-00001 — Ghost brush slap re-strike dominates soft notes

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-10, raised by Codex GPT-5)

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

Pending. Recalibrate the burst against velocity with a regression oracle before
updating the pinned brush render and affected listening assets.

## Notes

The current equal-velocity brush oracle uses velocity 100 and does not cover
ghost notes. Any fix changes the `brush_render_is_frozen` fingerprint and must
follow the repo's synth render-diff inventory and asset-refresh policy.
