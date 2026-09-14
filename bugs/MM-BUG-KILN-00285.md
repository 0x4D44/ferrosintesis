# MM-BUG-KILN-00285 — Core drum-kit cache test can still bypass process isolation

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** core drum-kit sample crate / cache regression
- **Raised:** 2026-08-17T11:40:11Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213848Z-4c356e79
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00285-run-verify-20260914T213848Z-4c356e79
- **Owner base:** 3d9970cf2687c8cce8374de7b90baff8a71fb61f
- **Owner fingerprint:** sha256:1d1700198115424546bf3b70b9a294f000a784e9fef2b938ba39d354d36401cb
- **Owner since:** 2026-09-14T21:38:48Z
- **Owner until:** 2026-09-14T23:38:48Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T11:40:11Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:15:51Z, deltic:auto role=fix run=fix-20260913T191035Z-0a326789 branch=task/bug-MM-BUG-KILN-00285-run-fix-20260913T191035Z-0a326789 code=0517847f846ab227031c56cc04b33ac80a0fdc75 gate=manual)

## Observation

The cold-cache regression can still run in the shared libtest process when its
probe marker is inherited and the cache happens to be cold at one instant.

At `crates/ferrosintesis-samples-drumkit/src/lib.rs:1015-1028`, the test treats
`FERRO_DRUMKIT_PCM_MISS_PROBE` being present plus
`pcm_cache_initializations() == 0` as proof that it is the re-executed child. If a
caller or CI environment already exported that marker while the parent cache is
cold, the test skips re-exec. Other tests initialize the same process-global
`PCM_CACHE` at `:904-923` and `:966-1000`, so a peer can warm it after the snapshot
and before the cold-cache assertions at `:1045-1059`.

Expected: the cold-cache assertions always run in a fresh isolated process,
independent of inherited environment and parallel test order. Actual: inherited
state can select child mode in the shared parent, producing a schedule-dependent
false failure or a pass that never proved isolation. Production miss ordering at
`:757-770` is correct; this is a regression-test defect.

This is the core-crate counterpart of Open `MM-BUG-KILN-00202`, which covers the
same residual control flow in `ferrosintesis-samples-drumkit2`. Closed
`MM-BUG-CRUCIBLE-00035` covered only the earlier already-warm inherited-marker
case. Static control flow confirms the hole; an observed flaky execution is
unverified because this pass did not run tests.

## Fix

<unfixed — raised only. Put the cold-cache assertions in a dedicated ignored
child test, re-exec that exact test with `--ignored --exact --test-threads=1`, and
require evidence that the child ran. Add an inherited-marker, initially-cold
parent regression that remains isolated while another test initializes the
cache. Estimated effort: Small.>

## Notes
