# MM-BUG-CRUCIBLE-00030 — GS drum-mode transitions leave melodic effect state derived from the old routing

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / GS channel routing
- **Raised:** 2026-08-14T11:47:24Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T102800Z-p13352-n472573600-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00030-run-fix-20260815T102800Z-p13352-n472573600-c1
- **Owner base:** aa7eca7ed6cbc98b52f77a52accdef211419776c
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T10:28:00Z
- **Owner until:** 2026-08-15T12:28:00Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-14T11:47:24Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

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

## Notes
