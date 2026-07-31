# MM-BUG-CRUCIBLE-00005 — SMF event reads can cross declared track boundaries

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / SMF parser
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-07-31, deltic:auto role=fix run=fix-20260731T064404Z-p95088-n720289300-c1 branch=task/bug-MM-BUG-CRUCIBLE-00005-run-fix-20260731T064404Z-p95088-n720289300-c1 code=a6e209bce42fdf8ffec0295c027e3af2b7958a70 gate=manual) -> Closed (2026-07-31, claude-opus-5; independent two-eyes verification on trunk `ddd71e6`. The fixer was `deltic:auto role=fix` with GPT-5.6 as the authoring model on `a6e209b`; I did not fix it. ORIGINAL OBSERVATION re-run VERBATIM through the public CLI: the report's format-1 reproducer, with track 0 declared as exactly two bytes `00 C0` and a valid `MTrk` placed immediately after it. Pre-fix binary (`c86f850`) accepts the file and reports THREE events — the phantom Program Change built from the next chunk's `M` (0x4D) plus track 1's note pair — then renders 1 live voice, which is the reported cross-boundary read followed by a clean rewind. Fix-bearing binary returns `error: unexpected end of file`, i.e. `MidiError::UnexpectedEof`, which is the report's stated expectation. TWO-SIDED at unit level: on the pre-fix source with the fix-bearing tests spliced in, `event_reads_cannot_cross_the_declared_track_boundary` FAILS ("an event truncated by its MTrk boundary borrowed bytes from the next chunk"); it passes on the fix-bearing tree. ROOT CAUSE addressed at the layer the report preferred, not the narrower one it warned would rot: the fix reads the declared payload once with `c.bytes(len)?` and parses it through a track-local `Cursor`, so the chunk boundary is now STRUCTURAL for fixed-size fields, VLQs, meta payloads and SysEx payloads alike, and the `c.pos = end` rewind is gone. I checked the interaction the rewrite could have broken: the MM-BUG-KILN-00101 protection against a declared length beyond the whole file is preserved — `c.bytes(len)?` rejects it up front — and its oracle in `parse_robustness.rs` passes in the suite. Repo gate green on the exact tree (fmt, both clippy configurations, `cargo test -p ferrosintesis --no-default-features` 714 passed, `cargo test --workspace` 849 passed in the lib, Python suite). No residual.)

## Observation

The parser computes a declared track end at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:236-245`,
but the event loop checks only whether an event *starts* before that end. Every
`Cursor` read remains bounded by the whole file, not by the current `MTrk`
chunk. After the event finishes, line 358 assigns `c.pos = end`, rewinding any
cross-boundary read.

A format-1 source-level reproducer can declare track 0 as exactly two bytes,
`00 C0`, and place a valid `MTrk` chunk immediately after it. The Program Change
arm at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\midi.rs:332-334`
reads the next header's `M` byte (`0x4D`) as the missing program, creates a
phantom Program Change, then rewinds to the `M` so track 1 parses normally.

**Expected:** an event truncated by its declared track boundary returns
`MidiError::UnexpectedEof` even when more bytes exist elsewhere in the file.

**Actual:** the parser consumes bytes owned by the next chunk, accepts the
malformed track, and may expose phantom events or metadata.

## Fix

Read the declared track payload once with `c.bytes(len)?`, then parse it through
a track-local `Cursor`. This makes the chunk boundary structural for fixed-size
data, VLQs, meta payloads, and SysEx payloads. A narrower post-read
`c.pos <= end` check can detect the symptom, but it is easier to regress at new
read sites.

Add a format-1 regression where track 0 ends inside a Program Change and track 1
is otherwise valid. Require `UnexpectedEof`, not a phantom event plus a
successful second-track parse.

## Notes

Static review only; the pass did not execute the application or tests.

The existing malformed-input oracle at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\parse_robustness.rs:351-360`
covers a declared length beyond the whole file, not an event that crosses a
shorter `MTrk` boundary into another valid chunk.

Reported in
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\wrk_docs\2026.07.31 - CR - 20260731-REV-CLA@CRUCIBLE-code-review-014814.md`.
