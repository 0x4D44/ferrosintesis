# MM-BUG-KILN-00285 — Core drum-kit cache test can still bypass process isolation

- **State:** Closed
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
- **State history:** Open (2026-08-17T11:40:11Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:15:51Z, deltic:auto role=fix run=fix-20260913T191035Z-0a326789 branch=task/bug-MM-BUG-KILN-00285-run-fix-20260913T191035Z-0a326789 code=0517847f846ab227031c56cc04b33ac80a0fdc75 gate=manual) -> Closed (2026-09-14T21:50:03Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the parent now always re-execs a child that must see PROBE=child; with the pre-fix control flow the new inherited-marker test goes red while the in-process run passes silently)

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

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `0517847f`) by an agent other than the fixer.

**Root cause, read in the code.** `lookup_misses_do_not_initialize_pcm_cache` no longer decides child mode from an inherited marker and a cold-cache snapshot. It always re-executes `lookup_misses_do_not_initialize_pcm_cache_child` (`#[ignore]`, `--exact`, `--test-threads=1`) with `FERRO_DRUMKIT_PCM_MISS_PROBE=child`, and that child asserts the marker is exactly `child` before running the cold-cache assertions. The shared-process path the observation describes no longer exists.

**Fails-before (method B).** The fix's diff was reverse-applied to `crates/ferrosintesis-samples-drumkit/src/lib.rs` (restoring the pristine-snapshot logic), and only the new `inherited_probe_marker_still_runs_the_isolated_child` test was put back. That test then fails with 'the inherited-marker probe did not run an isolated child', and the spawned process's own output shows '1 passed': with an inherited marker and a cold cache, the old code ran the assertions in-process and reported success, which is the recorded hole. Restored.

**Limit of the test.** It identifies the child by a printed token, so it cannot tell a child from an in-process run that printed the same token. Closure rests on the structural removal of the in-process branch, confirmed above, not on the token alone.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets` (`lookup_misses_do_not_initialize_pcm_cache` and `inherited_probe_marker_still_runs_the_isolated_child` pass). Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes
