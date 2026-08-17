# MM-BUG-KILN-00274 — Bounded MIDI files can expand into an unbounded decoded event flood

- **State:** Open
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
- **State history:** Open (2026-08-17T09:41:16Z, raised via `deltic bugs new`)

## Observation

Observation: crates/ferrosintesis/src/midi.rs:303-305 and :334-439 append every decoded event to raw without a cardinality budget. A valid format-0 SMF under load()'s 64 MiB byte cap can encode roughly 16-22 million zero-delta running-status channel events while song.seconds remains zero. raw and the final events vector coexist during the conversion at midi.rs:494-501; engine.rs:4268-4272 later creates another full event vector before rendering. The file-size and duration guards therefore still permit hundreds of MiB to more than 1 GiB of transient allocation plus O(E log E) sorting, which can exhaust memory on a hostile bounded input.

Expected: the public path-based parser, which documents the path as untrusted and bounds its input bytes, also bounds decoded event work and memory. Actual: a compact event flood expands far beyond the input cap before any typed error.

Concrete fix: add a documented decoded-event/resource budget checked before each retained push and a typed TooManyEvents error; include retained marker text in the budget or bound it separately. Add a compact zero-delta flood regression proving rejection before vector growth. Avoid the extra render-time event copy where practical.

Static review only. Three independent lenses confirmed the control flow and the existing MM-BUG-CRUCIBLE-00027 covers only file-read bytes, not decoded event cardinality. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
