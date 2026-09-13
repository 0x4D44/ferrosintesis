# MM-BUG-CRUCIBLE-00030 — GS drum-mode transitions leave melodic effect state derived from the old routing

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / GS channel routing
- **Raised:** 2026-08-14T11:47:24Z
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
- **State history:** Open (2026-08-14T11:47:24Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T10:42:44Z, deltic:auto role=fix run=fix-20260815T102800Z-p13352-n472573600-c1 branch=task/bug-MM-BUG-CRUCIBLE-00030-run-fix-20260815T102800Z-p13352-n472573600-c1 code=ac54258 gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: routing regression fails with re-derivation removed from the DrumMode and GsReset handlers)

## Observation

GS rhythm-part routing changes immediately, but the strip state derived from that routing
changes only on a later Program Change. `DrumMode` and `GsReset` only flip `gs_drum` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:2441`.
`program_change` separately chooses drum kits, program FX sends, and guitar `Drive` at
`engine.rs:3145-3197`.

Reproducer: declare channel 11 a GS rhythm part, select program 29, then send GS Reset and
play a note without another Program Change. Program 29 was selected while the channel was
a drum part, so its sends were set to zero and `drive` to `None`. GS Reset makes the next
note melodic, but it retains those drum-derived values instead of program 29's melodic
FX profile and drive. The inverse transition can retain melodic state on a newly declared
drum part. The existing test at `engine.rs:5787-5804` issues Program Change 0 after reset,
which masks the stale state.

Expected: the modeled routing flag and all unauthored state derived from it agree after the
transition. Actual: the next note uses a mixed melodic/drum configuration. This does not
ask for unmodeled full Roland GS Reset semantics; it repairs state derived from the routing
effect the engine already models.

## Fix

After `DrumMode`, and for every channel changed by `GsReset`, rederive kit-independent
program defaults and `Drive` while preserving authored controller values. Centralize that
transition so both directions use one invariant. Add no-follow-up-Program-Change tests for
program 29/30 and for an ordinary program with nonzero default sends. Estimated effort:
Small/Medium.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `ac54258c`) by an agent other than the fixer.

`gs_routing_changes_rederive_program_state_without_a_program_change` drives the bug's sequence at engine-event level (drum part, program 29 or 52, GS Reset, note, no second Program Change, both directions) against a known-correct reference render. It was not re-run as a SysEx file through the CLI.

**Fails-before (method B).** Removing the `rederive_routing_derived_state` calls from the `DrumMode` and `GsReset` handlers fails it: "prog 29: after GS Reset the channel is melodic again but kept drum-derived sends/drive". Restored; `git diff` empty; passes on HEAD.

One derivation now serves Program Change, DrumMode, GsReset and CC0. GM/System reset rebuild the whole core and XG reset does not touch drum routing, so no other transition keeps the defect.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
