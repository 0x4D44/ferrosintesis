# MM-BUG-CRUCIBLE-00036 — ferrosintesis-cli symlink-alias test cannot pass without SeCreateSymbolicLinkPrivilege

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** cli / test environment
- **Raised:** 2026-08-17T16:56:43Z
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
- **State history:** Open (2026-08-17T16:56:43Z, raised via `deltic bugs new`) -> Fixed (2026-09-14T01:17:50Z, deltic:auto role=fix run=fix-20260914T010621Z-09bfbef0 branch=task/bug-MM-BUG-CRUCIBLE-00036-run-fix-20260914T010621Z-09bfbef0 code=2799d1d468dd2bb33f504562cff6e8464b487305 gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 258e957b: the symlink-alias test now skips only on OS error 1314, so the CLI suite passes on unelevated Windows and any other failure still goes red; the skip itself is silent)

## Observation

`output::tests::rejects_supported_symbolic_link_alias`
(`crates/ferrosintesis-cli/src/output.rs:153`) creates a symbolic link in its own setup
to build the fixture it then asserts on. Creating a symlink on Windows requires
`SeCreateSymbolicLinkPrivilege`, which an unelevated process does not hold unless
Developer Mode is enabled, so on a default fleet Windows box the test panics before it
reaches any assertion:

```
thread 'output::tests::rejects_supported_symbolic_link_alias' panicked at
crates\ferrosintesis-cli\src\output.rs:153:13:
create symbolic link: A required privilege is not held by the client. (os error 1314)
```

Expected: the test either exercises the alias-rejection path, or reports honestly that
it cannot. Actual: `cargo test --workspace` fails on this one target
(`-p ferrosintesis-cli --bin ferrosintesis`, 4 passed / 1 failed) on every unelevated
Windows run, so the workspace suite has a permanently red step that masks real
regressions behind a known-noise failure.

Classification: test-infrastructure defect, not a product defect — the code under test
is fine and the other three alias-rejection tests (normalized path, hard link,
identical contents) pass. It is the same class as the mddosem repo's
MDD-BUG-CRUCIBLE-00750 (Windows-impossible tests).

Repro: `cargo test -p ferrosintesis-cli --bin ferrosintesis` from an unelevated shell
on Windows without Developer Mode.

## Fix

<unfixed — raised only>

Likely shape: attempt the symlink and `skip`/return early when it fails with a
privilege error, so the coverage loss is visible rather than a hard failure — matching
how `test_banjo_extract.py` and `test_fretnoise_bake.py` degrade to `SkipTest` when an
optional prerequisite is absent. A silent `#[ignore]` would be wrong: it must stay
runnable on an elevated box or in CI where the privilege is held.

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `258e957b` by an independent verifier worker in this pass, other than the fixer (fix `2799d1d4`).

**Original observation.** This box holds no `SeCreateSymbolicLinkPrivilege`: `whoami /priv` lacks it, Developer Mode is off, and an unprivileged symlink creation fails. `cargo test -p ferrosintesis-cli --locked --all-targets` passes with 7 bin tests and 0 failures, so the recorded permanent red step is gone. The test takes its skip branch here, confirmed by temporarily turning the early return into a panic ('A required privilege is not held by the client. (os error 1314)').

**Narrowness (method B).** `rejects_supported_symbolic_link_alias` and `skips_only_missing_symlink_privilege` pass. Changing `ERROR_PRIVILEGE_NOT_HELD` from 1314 to 1315 fails both: the first with the recorded message 'create symbolic link: A required privilege is not held by the client. (os error 1314)', the second on `is_missing_symlink_privilege(... 1314)`. The unit test also asserts that raw error 5 and a synthetic `PermissionDenied` are not skipped, so any other symlink failure still goes red. Before this fix, trunk already skipped on any `PermissionDenied` (`b3627a98`); this fix narrows that. The test still runs in full on a privileged box, as the record required. Restored.

**Limit, noted rather than split.** The record hoped the coverage loss would be visible. The skip is a silent `return`, so libtest reports 'ok' on an unelevated box, and the alias-rejection assertion never runs here. libtest has no runtime skip, so this is close to the ceiling; a message would show only under `--nocapture`.

**Repo gate.** On `258e957b`: `cargo test -p ferrosintesis-cli --locked --all-targets` 32 passed, and the CLI no-default run 27 passed. On `1d87b00f`: fmt, all three clippy steps and `cargo test --workspace --all-targets` green. Still red on trunk, not caused by this fix: 4 `test_prepare.py` errors (MM-BUG-CRU-00068, reopened).

## Notes

Found incidentally while validating the sample-bank FLAC conversion
(branch `task/20260816-TSK-HUM-remove-the-dark-salamander-alternate-ban`). That branch
does not touch `crates/ferrosintesis-cli/` at all — confirmed with
`git diff origin/main --stat -- crates/ferrosintesis-cli/`, which is empty — so this is
pre-existing and not a regression from it.
