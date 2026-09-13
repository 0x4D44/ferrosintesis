# MM-BUG-KILN-00274 — Bounded MIDI files can expand into an unbounded decoded event flood

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / SMF parser resource bounds
- **Raised:** 2026-08-17T09:41:16Z
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
- **State history:** Open (2026-08-17T09:41:16Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:54:48Z, deltic:auto role=fix run=fix-20260913T173220Z-8a0f7670 branch=task/bug-MM-BUG-KILN-00274-run-fix-20260913T173220Z-8a0f7670 code=4951e6ed6e747b0c11fd2054cd248b64e43cb5c0 gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: 48 MiB zero-delta flood rejected as TooManyEvents; regressions fail with limits disabled; residual clippy gate failure in the fix's test helpers split to MM-BUG-CRU-00055)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:303-305 and :334-439 append every decoded event to raw without a cardinality budget. A valid format-0 SMF under load()'s 64 MiB byte cap can encode roughly 16-22 million zero-delta running-status channel events while song.seconds remains zero. raw and the final events vector coexist during the conversion at midi.rs:494-501; engine.rs:4268-4272 later creates another full event vector before rendering. The file-size and duration guards therefore still permit hundreds of MiB to more than 1 GiB of transient allocation plus O(E log E) sorting, which can exhaust memory on a hostile bounded input.

Expected: the public path-based parser, which documents the path as untrusted and bounds its input bytes, also bounds decoded event work and memory. Actual: a compact event flood expands far beyond the input cap before any typed error.

Concrete fix: add a documented decoded-event/resource budget checked before each retained push and a typed TooManyEvents error; include retained marker text in the budget or bound it separately. Add a compact zero-delta flood regression proving rejection before vector growth. Avoid the extra render-time event copy where practical.

Static review only. Three independent lenses confirmed the control flow and the existing MM-BUG-CRUCIBLE-00027 covers only file-read bytes, not decoded event cardinality. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `4951e6ed`, message "Bound decoded MIDI resources", which does not cite this ID) by an agent other than the fixer.

**Original observation re-run.** A 48 MiB format-0 file (under the 64 MiB cap) with 16 million zero-delta running-status note-ons is rejected by the CLI: "retains 1000001 decoded event-like records, exceeding the 1000000 record limit".

**Fails-before (method B).** Disabling the checks in `reserve_event_budget` and `reserve_text_budget` fails `zero_delta_event_flood_is_rejected` and `retained_marker_text_is_bounded`. Restored; `git diff` empty; the regressions and both `TooManyEvents`/`TooMuchText` robustness cases pass on HEAD.

**Residual split to MM-BUG-CRU-00055.** The fix's test helpers use `repeat(b'x').take(marker_len)` at `midi.rs:1068` and `parse_robustness.rs:173`; that is the cause of the current clippy `manual_repeat_n` gate failure on rustc/clippy 1.95. The behavioural fix is sound, so the lint is tracked as its own defect.


## Notes
