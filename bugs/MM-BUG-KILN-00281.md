# MM-BUG-KILN-00281 — Catalog overlap oracle rejects production-valid long MIDI timelines

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/render-catalog / MIDI overlap oracle
- **Raised:** 2026-08-17T10:31:46Z
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
- **State history:** Open (2026-08-17T10:31:46Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:36:13Z, deltic:auto role=fix run=fix-20260913T183200Z-99b08c83 branch=task/bug-MM-BUG-KILN-00281-run-fix-20260913T183200Z-99b08c83 code=cca859fbfb85165b6aed05ecdf55699ebf445ca3 gate=manual) -> Closed (2026-09-13T19:35:03Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: seventeen maximum VLQ deltas audit clean; reverting ticks to u32 reproduces absolute tick overflow)

## Observation

`NoteEvent.tick` and the per-track cumulative tick in
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-111645\crates\render-catalog\tests\album_midi_overlaps.rs:53,86-92`
are `u32`. The audit returns `absolute tick overflow` when a legal sequence crosses
`u32::MAX`. Production deliberately carries absolute ticks as `u64` at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-111645\crates\ferrosintesis\src\midi.rs:303,323,340`.

Seventeen legal maximum four-byte deltas total 4,563,402,735 ticks. With division 32,767
and the default 500,000 microseconds per quarter note, that is about 69,634 seconds
(19.34 hours), below production's 24-hour limit. Production accepts the small file; the
catalog audit refuses it at the seventeenth delta.

**Expected:** every production-valid committed MIDI within the supported duration can be
checked for overlaps.

**Actual:** the repository gate rejects a valid long timeline before examining its note
lifecycle.

## Fix

Use `u64` for `NoteEvent.tick` and the cumulative per-track tick, matching production.
Add a red-before-fix boundary control with seventeen maximum deltas and a clean note
lifecycle; assert that it audits successfully.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `cca859fb`) by an agent other than the fixer.

**Original observation re-run.** Seventeen maximum four-byte deltas with a balanced note, crossing `u32::MAX` ticks, audit clean on HEAD.

**Fails-before (method B).** Reverting both tick fields and the `checked_add` to `u32` fails `accepts_seventeen_maximum_vlq_deltas_before_note_off` with "absolute tick overflow", the recorded failure. Restored; passes on HEAD. The audit now matches the production parser's `u64` tick width.

## Notes

Found by a bounded static review of `crates/render-catalog/`. The arithmetic and
production-width mismatch were independently source-confirmed. No application, test,
render, or exploratory harness ran.
