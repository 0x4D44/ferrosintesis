# MM-BUG-KILN-00277 — Pluck legato and tremolo allocate excitation buffers in the realtime callback

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / realtime pluck articulation
- **Raised:** 2026-08-17T09:41:50Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191728Z-94fda33a
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00277-run-verify-20260913T191728Z-94fda33a
- **Owner base:** 8c00fd87cafed92ec6a4fd3fd54e8ae2ca5351e9
- **Owner fingerprint:** sha256:050d848406b770cbce212b4173f48677c108e3165f0ce38b33f887da50c1baa6
- **Owner since:** 2026-09-13T19:17:28Z
- **Owner until:** 2026-09-13T21:17:28Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T09:41:50Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:23:58Z, deltic:auto role=fix run=fix-20260913T181210Z-063c97f3 branch=task/bug-MM-BUG-KILN-00277-run-fix-20260913T181210Z-063c97f3 code=885af17b0dd468d6d535662a4986bfc92cc551e5 gate=manual)

## Observation

Observation: Pluck::legato_to at crates/ferrosintesis/src/voices.rs:5437-5447 collects a new hammer Vec for each accepted CC68 slur. Pluck::retrigger at :5473-5512 allocates both raw and exc Vecs on every accepted tremolo stroke, then replaces hammer. Engine note-event handling calls these methods inside the live callback path at crates/ferrosintesis/src/engine.rs:2671-2684 and :2723-2735; RealtimeSynth applies queued events immediately before rendering at live.rs:397-414. The documented tremolo path runs 10-16 strokes per second, so it repeatedly allocates, initializes, and frees pitch-sized excitation buffers on the deadline-bearing thread.

Expected: intended mid-voice legato and tremolo control paths reuse bounded per-voice storage in realtime. Actual: each slur allocates once and each tremolo stroke allocates twice, even though the voice already owns a reusable hammer buffer.

Concrete fix: retain reusable raw/excitation storage on Pluck, resize or reserve it at construction/setup, and fill it in place without temporary Vec creation. Add a counting-allocator regression covering repeated CC68 legato and same-key tremolo retriggers after realtime setup.

Static review only. Existing retrigger bugs cover routing and round-robin semantics, not callback allocation. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
