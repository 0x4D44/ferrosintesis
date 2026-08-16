# MM-BUG-KILN-00202 — Inherited cold-cache marker still bypasses process isolation

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drumkit2 cache regression
- **Raised:** 2026-08-16T07:16:52Z
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
- **State history:** Open (2026-08-16T07:16:52Z, raised via `deltic bugs new`)

## Observation

The cold-cache regression can still run in the shared libtest process when the
probe marker is inherited and the cache happens to be cold at one instant.

At
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-075555\crates\ferrosintesis-samples-drumkit2\src\lib.rs:414`,
the test treats `FERRO_DRUMKIT2_PCM_MISS_PROBE` being present plus
`pcm_cache_initializations() == 0` as proof that it is the child. If a caller or
CI environment already exported that marker while the parent cache is cold, the
test skips the re-exec at lines 415-430. Another parallel test can then initialize
`PCM_CACHE` between the snapshot at line 414 and the assertions at lines 432-438.

Expected: the cold-cache assertions always run in a fresh, isolated process,
independent of inherited environment and parallel test order.

Actual: an inherited marker plus a cold-at-snapshot cache selects child mode in
the shared parent. The test can then fail with `left: 1, right: 0` even though the
production miss path is correct, or pass without proving process isolation.

This is the residual schedule that closed `MM-BUG-CRUCIBLE-00035` did not cover.
That fix handles a marker inherited into an already-warm parent, but a one-time
cold snapshot cannot prove that no peer will warm the cache later. The failure was
confirmed from the control flow and adversarial scheduling; this read-only review
did not run the test suite.

## Fix

Remove marker-presence recursion from the isolation decision. Put the cold-cache
assertions in a separate ignored child test, have the outer test re-exec that
exact child with `--ignored --exact --test-threads=1`, and require explicit
evidence that the child ran before accepting its status. An equally strong
per-invocation nonce/handshake is acceptable if inherited values cannot select
child mode.

Add a regression for the inherited-marker, initially-cold parent case and prove
it remains isolated while another test initializes `PCM_CACHE`.

## Notes

Raised by the 2026-08-16 static review of
`crates/ferrosintesis-samples-drumkit2/`. This affects the regression only; the
public `pcm` and `pcm_by_index` miss ordering is correct. Estimated effort: Small.
