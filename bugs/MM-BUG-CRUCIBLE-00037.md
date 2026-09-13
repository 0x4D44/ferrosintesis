# MM-BUG-CRUCIBLE-00037 — No guard stops an ungated test reading outside the published crate archive

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** packaging / test boundary
- **Raised:** 2026-08-17T20:48:42Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T200823Z-80317c9b
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00037-run-verify-20260913T200823Z-80317c9b
- **Owner base:** f6c6eadb370a5c1deb4b6fc1a12aa4f927c07c9a
- **Owner fingerprint:** sha256:bff7a29dc67274b2669a70db723b2f121ad0d7b19334e1d065d3451f659b9679
- **Owner since:** 2026-09-13T20:08:23Z
- **Owner until:** 2026-09-13T22:08:23Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T20:48:42Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:45:20Z, deltic:auto role=fix run=fix-20260913T062844Z-33a2e38c branch=task/bug-MM-BUG-CRUCIBLE-00037-run-fix-20260913T062844Z-33a2e38c code=6a582ab29a74011e2e07d8059a3a6527fe0440d0 gate=manual) -> Open (2026-09-13T19:35:03Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: removing the cfg gate from the sax provenance test, the exact recorded escape, leaves repository_source_has_no_ungated_outside_reads green) -> Fixed (2026-09-13T20:02:48Z, deltic:auto role=fix run=fix-20260913T194944Z-b03da02f branch=task/bug-MM-BUG-CRUCIBLE-00037-run-fix-20260913T194944Z-b03da02f code=dac45daaaf96b8adf9b28f10ed5fdb498bd83e8d gate=manual)

## Observation

`RELEASING.md` requires that "the library archive's tests must also be self-contained":
repository-wide oracles are enabled by `--cfg ferrosintesis_repository_tests` from
`.cargo/config.toml`, which is absent from the published `.crate`. Nothing enforces it.
A `#[test]` in `crates/ferrosintesis/src/**` that reads a sibling crate, a repo tool, or
anything above `CARGO_MANIFEST_DIR` is packaged and compiled, and simply panics for a
registry user who runs `cargo test` on the published crate.

That is not hypothetical. `sampler::tests::packaged_sax_takes_outside_the_zone_tables_are_documented`
landed in `80bec63e` (2026-08-15) with no gate, and reads
`CARGO_MANIFEST_DIR/../ferrosintesis-samples-sax/PROVENANCE.md`. Verified against the real
archive by unpacking `ferrosintesis-0.21.58.crate` outside the repository: that path does
not exist, so the test's `.expect("sax PROVENANCE.md is readable")` panics. Because it
landed after the 0.21.57 release, the 0.21.58 release would have been the first to publish
it; it was gated in this release task instead.

Expected: a test that reaches outside the crate cannot land without the cfg gate.
Actual: the invariant is enforced only by a reviewer noticing, and it has already been
missed once.

**Measured: the archive is currently clean — the sax test was the only escape.** A crude
sweep (any `#[test]` whose body mentions `CARGO_MANIFEST_DIR`, `ferrosintesis-samples-`,
`tools/`, or `../` while lacking the gate) flagged 31 candidates across `balance.rs`,
`inventory.rs`, `licensing.rs`, `manifest.rs`, `parse_robustness.rs`, `payload.rs`,
`provenance.rs`, `sampler.rs` and `voices.rs`. Every one turned out to be a false positive:
using `CARGO_MANIFEST_DIR` to read the crate's OWN packaged files is correct, and several
`../` hits are string literals in test data.

Confirmed empirically rather than by reading them. The packaged `ferrosintesis 0.21.58`
tree was copied outside any repository checkout (so no ancestor `.cargo/config.toml` could
set the cfg — verified), its unpublished dependencies patched to local paths so the
ARCHIVE'S OWN source is what runs, and both suites executed:

- `cargo test` — 805 passed, 0 failed, 43 ignored
- `cargo test --no-default-features` — 671 passed, 0 failed, 37 ignored

So this record is about the MISSING ENFORCEMENT, not a backlog of broken tests. The
invariant holds today and nothing keeps it holding.

Repro: `cargo package -p ferrosintesis`, unpack the `.crate` OUTSIDE any repository
checkout, and run `cargo test`. Running it from under the repository is not equivalent —
Cargo discovers the ancestor `.cargo/config.toml` and sets the cfg, which is precisely why
this class survives local testing.

## Fix

<unfixed — raised only>

One part now, since the audit is done and found nothing further:

A guard test that fails when a `#[test]` in `crates/ferrosintesis/src/**` reaches outside
the crate without `#[cfg(ferrosintesis_repository_tests)]`. It should judge by what the
test READS, so `CARGO_MANIFEST_DIR` joined to a packaged path stays legal while a
`.parent()` escape or a sibling-crate name does not. A naive keyword scan is not good
enough — it produced 31 hits and 31 false positives here. Being a source-scanning guard it
belongs in the classes described in the repo's own guard doctrine.

Note the guard cannot be a cross-check against a packaged archive, because the archive is
only built at release time; it has to be a source-shape check to be useful per-landing.

## Notes

Found during the 0.21.58 release preflight, working through `RELEASING.md`'s
"Preflight on integrated trunk" section. The runbook already tells you to unpack and test
the archive "if either boundary changes" — the gap is that a NEW ungated test changes the
boundary without anyone realising it did.

### Verification (reopen) (2026-09-13, Claude Opus 5, independent)

Checked on trunk `8b6a6f86` (fix `6a582ab2`) by an agent other than the fixer. The four guard tests in `crates/ferrosintesis/tests/archive_boundary.rs` are selected and pass on HEAD, but the guard does not stop the escape this bug was raised for.

**Original observation re-run.** Removing `#[cfg(ferrosintesis_repository_tests)]` from `sampler::tests::packaged_sax_takes_outside_the_zone_tables_are_documented` leaves `repository_source_has_no_ungated_outside_reads` green.

**Why it misses (probed in scratch files, all removed).**
1. The tokenizer has no char-literal handling: `'"'` opens a phantom string and desyncs the rest of the file. Such literals exist at `sampler.rs:6841`, inside the sax test at `:8273`, and `engine.rs:4599`. A sibling-read test reported on its own was hidden once a `s.rfind('"')` helper preceded it.
2. The `.parent()`/`.ancestors()` rule looks for an identifier `CARGO_MANIFEST_DIR`, but in `env!("CARGO_MANIFEST_DIR")` it is a string token, so the rule never fires.
3. Paths built with `concat!` or `format!` are not examined.

Of six adversarial ungated escapes only `.join("..")` was caught; `concat!(env!(..), "/../...")`, `format!("{}/../../CLAUDE.md")`, `.parent().unwrap().parent()`, `.ancestors().nth(2)` and `crate::licensing::crates_dir()` all passed.

**Needed to close.** Char-literal lexing, the `env!` string treated as the manifest-dir marker, `concat!`/`format!` path handling, and fixtures for each missed shape, including a `'"'` ahead of an escaping test.
