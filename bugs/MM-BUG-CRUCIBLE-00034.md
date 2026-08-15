# MM-BUG-CRUCIBLE-00034 — Catalog overlap oracle ignores GM System On voice resets

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / MIDI overlap oracle
- **Raised:** 2026-08-14T12:51:04Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-14T12:51:04Z, raised via `deltic bugs new`) -> Fixed (2026-08-15T11:11:28Z, deltic:auto role=fix run=fix-20260815T110711Z-p34000-n736568800-c1 branch=task/bug-MM-BUG-CRUCIBLE-00034-run-fix-20260815T110711Z-p34000-n736568800-c1 code=fe1fb49 gate=manual)

## Observation

The catalog-wide overlap gate skips every SysEx event at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-132701\crates\render-catalog\tests\album_midi_overlaps.rs:102-105`.
Its active-note state machine at `album_midi_overlaps.rs:183-208` therefore does not
observe GM System On.

The production path does observe it. The SMF parser recognizes the complete universal
GM System On payload as `EvKind::GmReset` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-132701\crates\ferrosintesis\src\midi.rs:304-315`,
orders the reset before other events at the same tick at `midi.rs:423-425`, and the
engine clears all active voices at `engine.rs:2213-2217` and `engine.rs:2449`.

A valid stream shaped as `NoteOn(k) -> GM System On -> NoteOn(k) -> NoteOff(k)` is
therefore clean in the renderer: the reset ends the first voice before the second starts.
The audit ignores the reset, counts the second start as an overlap, and finishes with an
unmatched first note-on. A stale note-off emitted after a reset is likewise harmless to
the renderer but can be counted as unmatched by the audit.

**Expected:** the committed-MIDI oracle models every production event that changes note
lifecycle, including the renderer's same-tick reset ordering.

**Actual:** GM System On is invisible to the oracle, so valid reset-bearing MIDI can fail
the repository gate as overlapping or unbalanced.

## Fix

Decode the exact GM System On shape in the audit, place it before other same-tick events
as the production parser does, and reset the audit's active-note epoch. Define how
post-reset note-offs from the old epoch are ignored without hiding genuinely unmatched
note-offs in the new epoch.

Add controls for a held note cleared by GM System On, a same-tick reset plus replacement
note, and a stale post-reset note-off. Demonstrate each new control red against the
current audit before landing the fix.

## Notes

Found by a static, multi-lens review of `crates/render-catalog/`. No application, test,
render, or exploratory harness ran. The production reset semantics and the audit's SysEx
skip were independently confirmed from source; no runtime claim is made.
