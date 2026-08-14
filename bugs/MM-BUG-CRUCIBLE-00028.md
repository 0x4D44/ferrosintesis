# MM-BUG-CRUCIBLE-00028 — Overlong MIDI VLQs panic in checked builds and silently wrap in release

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** ferrosintesis / MIDI parser
- **Raised:** 2026-08-14T11:47:22Z
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
- **State history:** Open (2026-08-14T11:47:22Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

## Observation

SMF variable-length quantities are limited to four bytes. `Cursor::vlq` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\midi.rs:198`
loops until it sees a clear continuation bit and performs `v = (v << 7) | ...` without a
byte count or checked shift.

A complete otherwise-valid track beginning with the five-byte delta
`90 80 80 80 00`, followed by a valid channel event and End-of-Track, overflows `u32` on
the fifth shift in checked builds. Release builds wrap and accept a different tick value.
Other five-byte encodings are silently accepted even when the shift does not overflow.

Expected: malformed overlong VLQs return a `MidiError`. Actual: public `offline::parse`
can panic or silently change timing. Existing robustness fixtures prove truncation, not
the four-byte semantic limit; MM-BUG-KILN-00101 covered separate `usize` range arithmetic.

## Fix

Count VLQ bytes and reject a fifth byte before shifting. Use checked arithmetic and a
specific malformed-VLQ error. Add a complete five-byte negative fixture plus four-byte
boundary fixtures for zero and `0x0FFF_FFFF`; prove the new test fails against this parser.
Estimated effort: Small.

## Notes
