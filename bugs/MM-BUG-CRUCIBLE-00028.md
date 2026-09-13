# MM-BUG-CRUCIBLE-00028 — Overlong MIDI VLQs panic in checked builds and silently wrap in release

- **State:** Closed
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
- **State history:** Open (2026-08-14T11:47:22Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T10:17:39Z, deltic:auto role=fix run=fix-20260815T100751Z-p34060-n822582500-c1 branch=task/bug-MM-BUG-CRUCIBLE-00028-run-fix-20260815T100751Z-p34060-n822582500-c1 code=a462a88 gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: the bug's five-byte VLQ file is rejected as OverlongVlq; both regressions fail with the unbounded loop restored)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `a462a882`) by an agent other than the fixer.

**Original observation re-run.** The exact file (delta `90 80 80 80 00`, note-on, End-of-Track) is rejected by the CLI: "a variable-length quantity is longer than the four bytes SMF allows".

**Fails-before (method B).** Restoring the unbounded VLQ loop fails `vlq_honours_the_four_byte_limit_at_both_ends` and the `OverlongVlq` case of `every_error_variant_is_reachable_with_its_payload` ("expected OverlongVlq, but the file parsed cleanly"). Restored; `git diff` empty; both pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
