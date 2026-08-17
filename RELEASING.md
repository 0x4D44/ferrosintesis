# Publishing to crates.io

The publishable workspace contains **27 crates**: 24 sample-asset crates,
`ferrosintesis-flac`, `ferrosintesis`, and `ferrosintesis-cli`. `render-catalog` and the
separate `crates/amp-lab` workspace do not publish.

Publishing is irreversible. A crate version cannot be replaced or reused, and a partial
workspace publish can leave dependency crates live before the parent. Run this procedure
only with explicit release authority, from a clean, integrated `origin/main`.

The `0.0.0` `ferrosintesis` package is a name-reservation stub containing no code.
Real library releases start at `0.21.56`; always inspect crates.io for the current state.

## Dependency order

Cargo derives the order from the manifests. The current graph has four layers:

1. 23 independent sample crates (including `ferrosintesis-samples-drumkit`) plus
   `ferrosintesis-flac`, which depends on nothing.
2. `ferrosintesis-samples-drumkit2`, which depends on `-drumkit`.
3. `ferrosintesis`, which pins all 24 sample crates and `ferrosintesis-flac`.
4. `ferrosintesis-cli`, which depends on `ferrosintesis`.

Do not maintain a second hand-written package list. Confirm the graph with:

```text
cargo publish --workspace --exclude render-catalog --dry-run --locked
```

The dry run prints Cargo's derived publish order and verifies every normalized package.

## Prepare the release

Wait until every intended fix is integrated. Then create a release task from
`origin/main`; this repository uses `version_bump = "release-only"`, so ordinary
integrations do not change crate versions.

In that release task:

1. Choose the library and CLI versions from their manifests. Change a sample crate's
   version only if that already-published sample payload changed. Keep every
   `ferrosintesis` sample dependency pinned with `=`.
2. Run `cargo check --locked` after version edits so `Cargo.lock` changes in lockstep.
3. Replace `## [Unreleased]` in `crates/ferrosintesis/CHANGELOG.md` with the chosen
   library version and release date. Add a fresh empty `Unreleased` section above it.
4. Search the packaged README, NOTICE, licences, provenance files, repository URL,
   version references, and install commands for stale claims.
5. Integrate the release task. Do not package or publish the unintegrated task branch.

Do not use `--allow-dirty` or `--no-verify` for the release.

## Preflight on integrated trunk

First prove that the local checkout is exactly the clean remote trunk:

```text
git fetch origin
git status --short
git rev-parse HEAD
git rev-parse origin/main
```

`git status --short` must be empty, and the two revisions must match.

Run the repository gates with stdin closed:

```text
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings
cargo test -p ferrosintesis --no-default-features --locked
cargo test --workspace --locked
python3 -m unittest discover -s tools/ferrosintesis-samples
cargo +1.87.0 check --workspace --locked
cargo doc -p ferrosintesis --no-default-features --no-deps --locked
```

On PowerShell, prefix each test command with `$null |`. On bash, append `</dev/null`.

Package and dry-run the exact publishable graph:

```text
cargo package --workspace --exclude render-catalog --locked
cargo publish --workspace --exclude render-catalog --dry-run --locked
```

Read every `Packaged ... compressed` line. crates.io rejects an archive over its upload
limit; do not assume an uncompressed directory size is the relevant number. The largest
archive measured on 2026-07-29 was 7.4 MiB compressed.

The library archive's tests must also be self-contained. Repository-wide oracles are
enabled by `.cargo/config.toml` in a checkout and are absent from the archive; crate-local
fixtures under `crates/ferrosintesis/tests/` are packaged. If either boundary changes,
unpack the generated `.crate` outside the repository and run both:

```text
cargo test --locked
cargo test --no-default-features --locked
```

Running the unpacked test from under the repository is not equivalent: Cargo discovers
the ancestor `.cargo/config.toml` and enables repository-only tests.

Finally, check every exact crate name on crates.io. It must either be unclaimed or already
owned by the releasing account. Stop if any name belongs to someone else, if two-factor
authentication is unavailable, or if the token cannot publish all 27 crates. Never print
or commit the token.

## Publish

From the same clean, integrated checkout:

```text
cargo publish --workspace --exclude render-catalog --locked
```

Current Cargo publishes the selected workspace in dependency order. It may pause while a
new dependency becomes visible in the registry, and crates.io may rate-limit a long first
publish. Do not work around either check.

If the command stops after uploading anything, **do not blindly rerun it**. Inspect
crates.io and the command output to identify the exact versions already accepted. Resume
only the missing packages with `cargo publish -p <package> --locked`, preserving the four
dependency layers above. An accepted asset crate is not a rollback condition; finish the
remaining graph with the same reviewed versions.

## Verify the public release

Wait until the versions appear in the crates.io index, then install from the registry into
an empty temporary root:

```text
cargo install ferrosintesis-cli --version <cli-version> --locked --root <temp-root>
<temp-root>/bin/ferrosintesis --help
```

Also prove the modeled-only install advertised in the CLI README:

```text
cargo install ferrosintesis-cli --version <cli-version> --no-default-features --locked --root <another-temp-root>
<another-temp-root>/bin/ferrosintesis --help
```

Confirm that crates.io renders the README, licence, repository link, features, and
dependencies correctly. Confirm that docs.rs builds `ferrosintesis` documentation. Only
after the public artifacts are sound should the release tag or GitHub release be created,
and each remains a separate externally visible action requiring explicit authority.
