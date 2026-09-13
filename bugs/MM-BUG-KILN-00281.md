# MM-BUG-KILN-00281 — Catalog overlap oracle rejects production-valid long MIDI timelines

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/render-catalog / MIDI overlap oracle
- **Raised:** 2026-08-17T10:31:46Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T193403Z-e9355a11
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00281-run-verify-20260913T193403Z-e9355a11
- **Owner base:** 26bf8dc6ea58eaffa21ac0081f53712c3c0fa8a4
- **Owner fingerprint:** sha256:bb5da0d6b658e93bf7bf25be418fb9fae44080e24250e8ab9b5120d4beb42c88
- **Owner since:** 2026-09-13T19:34:03Z
- **Owner until:** 2026-09-13T21:34:03Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T10:31:46Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:36:13Z, deltic:auto role=fix run=fix-20260913T183200Z-99b08c83 branch=task/bug-MM-BUG-KILN-00281-run-fix-20260913T183200Z-99b08c83 code=cca859fbfb85165b6aed05ecdf55699ebf445ca3 gate=manual)

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

## Notes

Found by a bounded static review of `crates/render-catalog/`. The arithmetic and
production-width mismatch were independently source-confirmed. No application, test,
render, or exploratory harness ran.
