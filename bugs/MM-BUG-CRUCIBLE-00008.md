# MM-BUG-CRUCIBLE-00008 — Catalog MIDI overlap oracle misses cross-track, equal-tick, and unbalanced ambiguity

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/render-catalog / MIDI overlap oracle
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
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review) -> Fixed (2026-07-31T22:29:17Z, deltic:auto role=fix run=fix-20260731T220807Z-p75660-n943457900-c1 branch=task/bug-MM-BUG-CRUCIBLE-00008-run-fix-20260731T220807Z-p75660-n943457900-c1 code=3fbe77f110af25a5473aacff01296acee93e40a6 gate=manual)

## Observation

The catalog-wide overlap oracle can return clean for three ambiguous event
shapes:

- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\crates\render-catalog\tests\album_midi_overlaps.rs:42-47`
  creates fresh `(channel, key)` note maps for each `MTrk`, and `:141-155`
  sums those independent results. A format-1 overlap split across two tracks is
  therefore invisible even though the renderer merges all tracks into one event
  stream at
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\crates\ferrosintesis\src\midi.rs:238-245,423-432`.
- `album_midi_overlaps.rs:92-114` stores only ticks. If a second note-on is
  serialized before a note-off at the same tick, `end > next_start` is false and
  the policy-dependent handoff passes.
- `album_midi_overlaps.rs:102-109` skips the key entirely when note-on and
  note-off counts differ. The concrete stream `on@0, on@10, off@20` therefore
  returns zero despite a real overlap from tick 10 to tick 20.

**Expected:** the committed-MIDI gate models the file-wide merged event stream,
preserves deterministic same-tick order, and cannot return clean for an
overlap-bearing unbalanced lifecycle.

**Actual:** each of the three streams above can produce `Ok(0)`, and the catalog
test consumes that as a pass at `album_midi_overlaps.rs:181-184`.

## Fix

Parse every track into one ordered stream keyed by absolute tick plus a stable
event ordinal. Check active `(channel, key)` state across the whole SMF. Treat a
note-on while the key is active as an overlap, including same-tick on-before-off,
and report unmatched note lifecycles separately rather than skipping them.

Add adversarial positive controls for a cross-track overlap; same-tick
off-before-on (clean) and on-before-off (ambiguous); two ons with one off; and a
normal repeated note. The controls must fail against the current implementation.

## Notes

Static review only. The pass did not execute the application or tests.

This is a residual oracle defect, not a reopening of
`MM-BUG-KILN-00056`: that bug repaired the known album writers and independently
confirmed their then-current outputs, while this report concerns event shapes the
standing regression oracle cannot detect.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
