# MM-BUG-KIL-00307 — Re-exec cold-cache probes pass vacuously when the child test-name filter matches nothing

- **State:** Closed
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
- **State history:** Open (2026-08-19T09:33:16Z, raised via `deltic bugs new`) -> Fixed (2026-09-14T00:56:35Z, deltic:auto role=fix run=fix-20260914T005509Z-dae62fb8 branch=task/bug-MM-BUG-KIL-00307-run-fix-20260914T005509Z-dae62fb8 code=0517847f846ab227031c56cc04b33ac80a0fdc75 gate=manual) -> Closed (2026-09-14T21:50:03Z, independent verify by Claude Opus 5 on trunk 1d87b00f: both drum-kit re-exec parents now require child evidence in stdout; a drifted child test name fails each parent)

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

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` by an agent other than the fixer. The core-kit half was fixed by `0517847f`; the drumkit2 half (the observation's primary site) had already been changed by `50696dc2`.

**Original observation.** Both parents used to judge the child only by exit status, and libtest exits 0 when `--exact` matches nothing. Both now also require `FERRO_DRUMKIT_PCM_MISS_CHILD_RAN` / `FERRO_DRUMKIT2_PCM_MISS_CHILD_RAN` in the child's stdout, printed by the child test itself.

**Fails-before (method B, the recorded drift).** Renaming the child filter string in each parent to a name that matches no test makes the child print 'running 0 tests ... 0 passed' and exit 0, and each parent now fails: 'the isolated PCM lookup probe did not provide child evidence' (core `lib.rs:1236`, drumkit2 `lib.rs:515`). Before the fix that exact drift passed. Restored.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Estimated effort: Small.
