# MM-BUG-KIL-00307 — Re-exec cold-cache probes pass vacuously when the child test-name filter matches nothing

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drum-kit test oracles
- **Raised:** 2026-08-19T09:33:16Z
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
- **State history:** Open (2026-08-19T09:33:16Z, raised via `deltic bugs new`)

## Observation

The re-exec parent in `lookup_misses_do_not_initialize_pcm_cache`
(`crates/ferrosintesis-samples-drumkit2/src/lib.rs:448-464`) judges its child only
by `output.status.success()` (line 457). libtest exits 0 when a `--exact` filter
matches zero tests, so if the hardcoded
`NAME = "tests::lookup_misses_do_not_initialize_pcm_cache"` (line 437) ever drifts
from the real test path — a rename of the test or its module compiles fine, since
`NAME` is a plain string literal — the child runs nothing, prints
"0 passed … 1 filtered out", exits 0, and the parent reports success. The
cold-cache assertions at lines 466-482 then execute in no process at all, and the
MM-BUG-CRUCIBLE-00023 / MM-BUG-KILN-00174 miss-path oracle is silently disabled.

Stacked repro: rename the test but not `NAME`, then revert `pcm()`
(lib.rs:226-231) to the pre-00023 ordering (decode before name lookup). Every test
in the crate stays green while a missing-name lookup again decodes and retains the
whole package.

The ported twin in `crates/ferrosintesis-samples-drumkit/src/lib.rs:1032-1037` has
the identical exit-status-only judgment. Distinct from open MM-BUG-KILN-00202,
which is about the parent mis-selecting *child mode* on an inherited env marker;
this is the parent trusting a child that ran nothing.

Expected: the parent proves the child actually executed the probe. Actual: it
proves only that a process exited 0. False-green oracle defect; the current NAME
strings are correct today.

## Fix

Assert on the captured stdout in addition to exit status — require `"1 passed"`
(or the exact `test <NAME> ... ok` line) in the child output, in both crates. Prove
it fails first by pointing `NAME` at a non-existent test. Fixing MM-BUG-KILN-00202
in the same pass is natural, since both live in the same dozen lines.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Estimated effort: Small.
