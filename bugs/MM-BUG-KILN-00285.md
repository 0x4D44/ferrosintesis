# MM-BUG-KILN-00285 — Core drum-kit cache test can still bypass process isolation

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** core drum-kit sample crate / cache regression
- **Raised:** 2026-08-17T11:40:11Z
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
- **State history:** Open (2026-08-17T11:40:11Z, raised via `deltic bugs new`)

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
