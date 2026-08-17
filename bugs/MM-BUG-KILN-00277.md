# MM-BUG-KILN-00277 — Pluck legato and tremolo allocate excitation buffers in the realtime callback

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / realtime pluck articulation
- **Raised:** 2026-08-17T09:41:50Z
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
- **State history:** Open (2026-08-17T09:41:50Z, raised via `deltic bugs new`)

## Observation

Observation: Pluck::legato_to at crates/ferrosintesis/src/voices.rs:5437-5447 collects a new hammer Vec for each accepted CC68 slur. Pluck::retrigger at :5473-5512 allocates both raw and exc Vecs on every accepted tremolo stroke, then replaces hammer. Engine note-event handling calls these methods inside the live callback path at crates/ferrosintesis/src/engine.rs:2671-2684 and :2723-2735; RealtimeSynth applies queued events immediately before rendering at live.rs:397-414. The documented tremolo path runs 10-16 strokes per second, so it repeatedly allocates, initializes, and frees pitch-sized excitation buffers on the deadline-bearing thread.

Expected: intended mid-voice legato and tremolo control paths reuse bounded per-voice storage in realtime. Actual: each slur allocates once and each tremolo stroke allocates twice, even though the voice already owns a reusable hammer buffer.

Concrete fix: retain reusable raw/excitation storage on Pluck, resize or reserve it at construction/setup, and fill it in place without temporary Vec creation. Add a counting-allocator regression covering repeated CC68 legato and same-key tremolo retriggers after realtime setup.

Static review only. Existing retrigger bugs cover routing and round-robin semantics, not callback allocation. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
