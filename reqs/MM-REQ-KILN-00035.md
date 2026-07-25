# MM-REQ-KILN-00035 — The render-diff inventory must classify bank-selected voices, not just GM programs

- **State:** Draft
- **Priority:** Should
- **Area:** tooling / render-diff inventory
- **Raised:** 2026-07-25
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-25, promoted from `scratchpad.md` by the scratchpad-review pass; parked 2026.07.25 during the KILN-00049 render-diff; renumbered 00033 -> 00035 at integration, R-SAMEHOST collision with a concurrently-minted req)

## Statement

`tools/render-diff/render_diff.py` must be able to express "this change touched GM
program N *on bank B*", and its MIDI scanner must record the bank a channel had
selected when it sounded a note. A change confined to an alternate bank must then
classify as EXPECTED-changed on exactly the tracks that author that bank, and as
EXPECTED-same everywhere else.

## Notes

CLAUDE.md makes the render-diff inventory mandatory for any `voices.rs` /
`engine.rs` / `drums.rs` / `sampler.rs` change, and warns that the harness lies in
three specific ways. This is a fourth: `scan()` returns `tuple[set[int], set[int]]`
— GM programs and channel-10 drum keys — and its event loop lumps every controller
into the "skip 2 bytes" arm (`render_diff.py:101`), so CC0/CC32 bank selects are
invisible.

The consequence is not theoretical. `engine.rs` routes CC0 into real per-strip
`alt_bank` / `alt_bank_value` state that selects genuinely different voices through
`altbank.rs`, and albums author it — every Slipstream movement sends
`bank_selects=[(10, 1), (11, 1), (13, 1), (14, 1)]`. So when KILN-00049 changed
`DRIVE_LEAD` only on the GM29/30 *alternate* banks, the 124-MIDI diff moved exactly
11 tracks and the tool called all 11 contamination. A hand-written bank-aware scan
then proved those 11 were precisely the complete CC0-nonzero GM29/30 set — i.e. the
change was perfectly targeted and the harness said the opposite.

That is the expensive failure mode: a *correct* change reported as contamination
teaches an agent to distrust the inventory, and the repo's whole verification story
for synth changes rests on trusting it.

Design points Gate 1 should settle rather than an implementer guessing:

- **CLI surface.** `--bank MSB:LSB` as a separate axis, or a qualified program
  (`--program 25@1`)? The latter reads better for the common case (one program, one
  alt bank) but does not express "any bank of program 25".
- **MSB vs LSB.** The repo uses CC0 (`engine.rs`) *and* LSB 96 for the mandolin
  cell, so both must be tracked; they are not interchangeable.
- **Pairing at note-on.** Programs and banks must be recorded as a `(program,
  bank)` pair *at the moment a note sounds*, not as two independent sets — a channel
  that changes bank mid-track otherwise cross-products into combinations it never
  played.

A related defect in the same function is already fixed in this pass (channel-9
program changes were being counted as melodic GM programs); this requirement is the
remaining half.
