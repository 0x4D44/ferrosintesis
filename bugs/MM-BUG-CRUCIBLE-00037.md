# MM-BUG-CRUCIBLE-00037 — No guard stops an ungated test reading outside the published crate archive

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** packaging / test boundary
- **Raised:** 2026-08-17T20:48:42Z
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
- **State history:** Open (2026-08-17T20:48:42Z, raised via `deltic bugs new`)

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

A crude sweep (any `#[test]` whose body mentions `CARGO_MANIFEST_DIR`, `ferrosintesis-samples-`,
`tools/`, or `../` while lacking the gate) flags 31 candidates across `balance.rs`,
`inventory.rs`, `licensing.rs`, `manifest.rs`, `parse_robustness.rs`, `payload.rs`,
`provenance.rs`, `sampler.rs` and `voices.rs`. Most are expected to be false positives —
using `CARGO_MANIFEST_DIR` to read the crate's OWN packaged files is correct, and a `../`
inside a string literal may be test data. The real count is unknown and needs the audit
this record asks for; it was out of scope for a release task.

Repro: `cargo package -p ferrosintesis`, unpack the `.crate` OUTSIDE any repository
checkout, and run `cargo test`. Running it from under the repository is not equivalent —
Cargo discovers the ancestor `.cargo/config.toml` and sets the cfg, which is precisely why
this class survives local testing.

## Fix

<unfixed — raised only>

Two parts, and the guard is the important one:

1. A guard test that fails when a `#[test]` in `crates/ferrosintesis/src/**` reaches
   outside the crate without `#[cfg(ferrosintesis_repository_tests)]`. It should judge by
   what the test READS, so `CARGO_MANIFEST_DIR` joined to a packaged path stays legal
   while a `.parent()` escape or a sibling-crate name does not. Being a source-scanning
   guard it belongs in the classes described in the repo's own guard doctrine.
2. Audit the 31 candidates and gate the genuine escapes.

Note the guard cannot be a cross-check against a packaged archive, because the archive is
only built at release time; it has to be a source-shape check to be useful per-landing.

## Notes

Found during the 0.21.58 release preflight, working through `RELEASING.md`'s
"Preflight on integrated trunk" section. The runbook already tells you to unpack and test
the archive "if either boundary changes" — the gap is that a NEW ungated test changes the
boundary without anyone realising it did.
