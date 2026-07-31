# MM-BUG-CRUCIBLE-00004 — Equal-tick tempo changes lose authored order

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / SMF tempo map
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-07-31, deltic:auto role=fix run=fix-20260731T063651Z-p33684-n469525500-c1 branch=task/bug-MM-BUG-CRUCIBLE-00004-run-fix-20260731T063651Z-p33684-n469525500-c1 code=2043bf1ce98b1321a874188389d5d9fb903a227b gate=manual)

## Observation

Tempo changes are stored only as `(tick, microseconds_per_quarter)` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:230-231`
and pushed at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:270-280`.
`tempos.sort_unstable()` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:361-362`
orders equal-tick entries by their numeric tempo value, discarding authored
event order.

For a valid format-0 track that authors tick-zero tempos of 1,000,000 then
500,000 microseconds per quarter, the second event should win and subsequent
events should render at 120 BPM. Sorting produces `(0, 500000), (0, 1000000)`,
so the cumulative loop at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:375-383`
instead leaves 1,000,000 active and renders at 60 BPM. Meanwhile
`initial_bpm` at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:416`
reads the first sorted entry and reports 120 BPM, contradicting the timeline.

**Expected:** zero-delta Set-Tempo events retain encounter order; the last
authored change governs the following interval and agrees with `initial_bpm()`.

**Actual:** the numerically largest microseconds-per-quarter value always
governs, regardless of source order.

## Fix

Retain an encounter sequence for tempo events and order them by
`(tick, sequence)`, or use a stable tick-only ordering. Collapse equal-tick
changes with explicit last-authored-wins semantics before building the
cumulative map. Derive `initial_bpm` from the effective tick-zero tempo, not
the first uncollapsed tuple.

Add a regression that authors the same two tick-zero tempos in both value
orders. Assert that reversing source order reverses the effective tempo and
that `initial_bpm()` matches the tempo used for later events.

## Notes

Static review only; the pass did not execute the application or tests.

No existing bug or open requirement covers same-tick tempo ordering.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-014814.md`.
