# MM-BUG-KILN-00274 — Bounded MIDI files can expand into an unbounded decoded event flood

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / SMF parser resource bounds
- **Raised:** 2026-08-17T09:41:16Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191249Z-3ad85db7
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00274-run-verify-20260913T191249Z-3ad85db7
- **Owner base:** 3006a1b272d3627677d9a12775b93e6df96a9c53
- **Owner fingerprint:** sha256:72f79c27dff5856b7fa6d91fe1bbe1093e7b9314c65411c2e55470c685a895c1
- **Owner since:** 2026-09-13T19:12:49Z
- **Owner until:** 2026-09-13T21:12:49Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T09:41:16Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:54:48Z, deltic:auto role=fix run=fix-20260913T173220Z-8a0f7670 branch=task/bug-MM-BUG-KILN-00274-run-fix-20260913T173220Z-8a0f7670 code=4951e6ed6e747b0c11fd2054cd248b64e43cb5c0 gate=manual)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:303-305 and :334-439 append every decoded event to raw without a cardinality budget. A valid format-0 SMF under load()'s 64 MiB byte cap can encode roughly 16-22 million zero-delta running-status channel events while song.seconds remains zero. raw and the final events vector coexist during the conversion at midi.rs:494-501; engine.rs:4268-4272 later creates another full event vector before rendering. The file-size and duration guards therefore still permit hundreds of MiB to more than 1 GiB of transient allocation plus O(E log E) sorting, which can exhaust memory on a hostile bounded input.

Expected: the public path-based parser, which documents the path as untrusted and bounds its input bytes, also bounds decoded event work and memory. Actual: a compact event flood expands far beyond the input cap before any typed error.

Concrete fix: add a documented decoded-event/resource budget checked before each retained push and a typed TooManyEvents error; include retained marker text in the budget or bound it separately. Add a compact zero-delta flood regression proving rejection before vector growth. Avoid the extra render-time event copy where practical.

Static review only. Three independent lenses confirmed the control flow and the existing MM-BUG-CRUCIBLE-00027 covers only file-read bytes, not decoded event cardinality. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
