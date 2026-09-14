# MM-BUG-CRUCIBLE-00036 — ferrosintesis-cli symlink-alias test cannot pass without SeCreateSymbolicLinkPrivilege

- **State:** Open
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
- **State history:** Open (2026-08-17T16:56:43Z, raised via `deltic bugs new`)

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

## Notes

Found incidentally while validating the sample-bank FLAC conversion
(branch `task/20260816-TSK-HUM-remove-the-dark-salamander-alternate-ban`). That branch
does not touch `crates/ferrosintesis-cli/` at all — confirmed with
`git diff origin/main --stat -- crates/ferrosintesis-cli/`, which is empty — so this is
pre-existing and not a regression from it.
