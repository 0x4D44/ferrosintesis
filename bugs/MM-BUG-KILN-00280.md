# MM-BUG-KILN-00280 — Catalog overlap oracle accepts invalid high-bit GM reset

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / MIDI overlap oracle
- **Raised:** 2026-08-17T10:31:44Z
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
- **State history:** Open (2026-08-17T10:31:44Z, raised via `deltic bugs new`)

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
