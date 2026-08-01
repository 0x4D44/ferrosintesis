# MM-BUG-CRUCIBLE-00008 — Catalog MIDI overlap oracle misses cross-track, equal-tick, and unbalanced ambiguity

- **State:** Closed
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
- **State history:** Open (2026-07-31, raised by Codex GPT-5.6-Sol during static code review) -> Fixed (2026-07-31T22:29:17Z, deltic:auto role=fix run=fix-20260731T220807Z-p75660-n943457900-c1 branch=task/bug-MM-BUG-CRUCIBLE-00008-run-fix-20260731T220807Z-p75660-n943457900-c1 code=3fbe77f110af25a5473aacff01296acee93e40a6 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 789baed; fixer was Codex GPT-5.6-Sol)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `789baed` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-8-11`.

**Original observation reproduced against the pre-fix tree.** Both oracle versions
were compiled standalone (`rustc --test`, the file is std-only) with
`CARGO_MANIFEST_DIR` pointed at the pre-fix `albums/` tree extracted from
`3fbe77f^`:

- the pre-fix oracle returns **clean** on that corpus (`1 passed`) — the blindness
  in the report;
- the post-fix oracle **fails** on the same corpus, naming 25 files and 7 243
  same-pitch overlaps (e.g. `The Long Turning` 1 528, `Meridian` 1 328,
  `Riverwake` 902), plus unmatched note-on/off lifecycles.

That is the fails-before evidence for both the oracle and the committed MIDI it
now rejects.

**Post-fix tree green.** `cargo test -p render-catalog`: 21 unit tests pass
(1 ignored helper) and all 5 overlap tests pass, including the three adversarial
controls that map one-to-one onto the reported shapes — cross-track overlap,
same-tick on-before-off vs off-before-on, and the unbalanced `on/on/off`
lifecycle — plus the balanced-repeat negative control.

**Regenerated MIDI is reproducible.** `python3 build.py` in
`albums/fable5/The Burning Meridian` (3 MIDIs rewritten by the fix) reproduced the
committed `.mid` and `album_manifest.json` byte-identically (`git status` clean),
and `build.py --verify` reports `RESULT: PASS - all oracles green`.

**Gates.** `cargo clippy -p render-catalog --all-targets -- -D warnings` clean;
`cargo fmt --all -- --check` clean.

## Notes

Static review only. The pass did not execute the application or tests.

This is a residual oracle defect, not a reopening of
`MM-BUG-KILN-00056`: that bug repaired the known album writers and independently
confirmed their then-current outputs, while this report concerns event shapes the
standing regression oracle cannot detect.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-220343\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-220343.md`.
