# MM-BUG-KILN-00280 — Catalog overlap oracle accepts invalid high-bit GM reset

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / MIDI overlap oracle
- **Raised:** 2026-08-17T10:31:44Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T193314Z-04bb33d5
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00280-run-verify-20260913T193314Z-04bb33d5
- **Owner base:** b197e1c2be0bcf061de9ae11dfb0b0baff30033f
- **Owner fingerprint:** sha256:33a4e4130af16ef8588feb05455293689b6a8f015b8ce371f8ab05278d0942c3
- **Owner since:** 2026-09-13T19:33:14Z
- **Owner until:** 2026-09-13T21:33:14Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T10:31:44Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:30:26Z, deltic:auto role=fix run=fix-20260913T182523Z-acac18d4 branch=task/bug-MM-BUG-KILN-00280-run-fix-20260913T182523Z-acac18d4 code=b4ba3f7af8b20b8fe7e7cc728b381981141b7f62 gate=manual)

## Observation

The overlap audit's GM System On recognizer at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-111645\crates\render-catalog\tests\album_midi_overlaps.rs:73-78`
matches the device byte with `_`. It therefore accepts the malformed payload
`F0 05 7E FF 09 01 F7` as a reset. The production decoder first rejects every SysEx
body byte at or above `0x80` at
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-111645\crates\ferrosintesis\src\midi.rs:97-104`,
so it ignores the same message.

A stream shaped as `NoteOn(60) -> malformed reset -> NoteOn(60) -> NoteOff(60)`
therefore clears the audit's first note and reports clean. Production keeps the first
voice active, so the second start is a same-pitch overlap and one note remains unmatched.

**Expected:** the catalog oracle and production decoder recognize the same complete,
seven-bit GM System On payloads.

**Actual:** one high-bit device byte makes the oracle clear note state that production
retains, allowing ambiguous committed MIDI through the repository gate.

## Fix

Require every SysEx body byte before the terminating `F7` to be below `0x80` before
recognizing GM System On. Add a red-before-fix control with the exact high-bit payload
between two same-pitch note-ons; assert that the audit reports the overlap and unmatched
note-on.

## Notes

Found by a bounded static review of `crates/render-catalog/`. The production/audit
mismatch was independently source-confirmed by correctness, security, reliability, test,
and adversarial reviewers. No application, test, render, or exploratory harness ran.
