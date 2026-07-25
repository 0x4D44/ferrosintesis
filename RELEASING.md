# Releasing ferrosintesis to crates.io

The synth ships as **25 crates**: `ferrosintesis` plus **24 sample-asset crates** it pins
at exact versions. Publishing is irreversible — a version can be *yanked* but never
removed, and the name/version pair is burned forever. A half-finished publish leaves the
registry holding asset crates that no released parent uses.

So this is a runbook, not a habit. Read it end to end before the first `cargo publish`.

> **Status as of 2026-07-25: nothing real has been published.** `crates.io/crates/ferrosintesis`
> holds only a name-reservation stub `0.0.0`, pushed 2026-07-09. All 24 sample-crate names
> are **unregistered** — see "Name reservation" below, because that is the one genuinely
> urgent item here.

---

## The constraint that dictates everything: publish order

`crates/ferrosintesis/Cargo.toml` pins every asset crate with `=0.1.0`:

```toml
ferrosintesis-samples-core = { path = "../ferrosintesis-samples-core", version = "=0.1.0", optional = true }
```

Those are **real registry dependencies**, not just path dependencies. `cargo publish`
resolves them against the index, so:

1. Every sample crate must be on crates.io **before** `ferrosintesis` can be published at all.
2. `ferrosintesis-samples-drumkit2` depends on `ferrosintesis-samples-drumkit` (it shares the
   `Bank` type), so **drumkit must precede drumkit2**.
3. Everything else is order-independent among the samples.

Until then, `cargo package -p ferrosintesis` fails with
`no matching package named ferrosintesis-samples-<x> found` — that is expected and is not a
defect in the manifest.

`ferrosintesis-cli`, `render-catalog` and `amp-lab` are `publish = false` and never ship.

## Hard limits you will hit

| Limit | Value | Where it bites |
|---|---|---|
| `.crate` tarball size | **10 MiB** | The drum kit. See below. |
| Rate limit, new crates | ~1 per 10 min (burst 5) | Publishing 24 new names in one sitting. |
| Yank ≠ delete | — | You cannot take a bad version back. |

**The size limit is why the drum kit is two crates.** The combined kit packaged at 15.8 MiB
and would have been rejected outright. It was split on 2026-07-25 into
`-drumkit` (7.5 MiB) and `-drumkit2` (8.4 MiB). Check headroom before adding samples:

```powershell
cargo package -p <crate> --no-verify --allow-dirty   # prints "Packaged N files, X (Y compressed)"
```

`Y compressed` is the figure crates.io measures. Crates that depend on an unpublished
sibling cannot be measured this way until that sibling is up; estimate with
`tar -cf - samples src Cargo.toml README.md PROVENANCE.md LICENSE-CC0 | gzip -6 | wc -c`.

## Name reservation — do this first, separately

The parent name is held; **the 24 asset-crate names are not**. Anyone can take
`ferrosintesis-samples-core` today, and if they do, the pinned dependency graph cannot be
published under these names at all. Reserving them is cheap and reversible in a way that
publishing real content is not.

This is a deliberate decision point, not a step to run on autopilot — reserving 24 names is
itself an irreversible public act. Get Arthur's explicit go.

## Pre-flight

Run from a **clean checkout of `origin/main`** (never a task branch — an artifact built off
an un-integrated branch silently lags the trunk while carrying an identical version string):

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings
cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings
$null | cargo test --workspace --exclude amp-lab --locked
```

Then rehearse the packaging without touching the network:

```powershell
foreach ($c in (cargo metadata --no-deps --format-version 1 | ConvertFrom-Json).packages |
         Where-Object { $_.name -like 'ferrosintesis-samples-*' }) {
  cargo package -p $c.name --no-verify --allow-dirty
}
```

Confirm every crate reports **under 10 MiB compressed**.

Checklist before the first real publish:

- [ ] Version numbers are deliberate. `.deltic-integrate.toml` sets
      `version_bump = "release-only"`, so integration never bumps: the number you see is
      the number that ships. Bump it as a conscious release act.
- [ ] `CHANGELOG.md` has an entry for this version.
- [ ] Every crate has `description`, `license`, `repository`, `readme`, `rust-version`.
- [ ] Each attribution-bearing crate ships its `NOTICE` **in its `include` list**
      (`cargo test -p ferrosintesis --lib licensing` proves this).
- [ ] The payload prose matches reality
      (`cargo test -p ferrosintesis --lib payload`).
- [ ] `cargo +1.87 check --workspace` passes — the declared MSRV is only real once a
      toolchain at that version has compiled it.

## Publishing

**Dry run the whole set first.** `--dry-run` performs everything except the upload:

```powershell
cargo publish -p ferrosintesis-samples-core --dry-run
```

Then, for real, samples first. `--locked` keeps the resolved graph identical to what you
tested. After each, wait for the index to update before the crate that depends on it:

```powershell
# 1. drumkit BEFORE drumkit2 (drumkit2 depends on it)
cargo publish -p ferrosintesis-samples-drumkit --locked
# ...wait for the index, then:
cargo publish -p ferrosintesis-samples-drumkit2 --locked

# 2. the remaining 22, any order, minding the rate limit
cargo publish -p ferrosintesis-samples-core --locked
# ... etc

# 3. only once all 24 are live and indexed:
cargo publish -p ferrosintesis --locked
```

Publishing the parent is the point of no return: it is the version the world resolves.

## Verify after

- `cargo install ferrosintesis-cli` will NOT work (it is `publish = false`); instead, in a
  scratch directory outside the workspace: `cargo add ferrosintesis && cargo build`, to
  prove the published graph resolves without any path dependency.
- Check docs.rs built. It is configured with `no-default-features = true`
  (`crates/ferrosintesis/Cargo.toml`); without that it would try to compile ~104 MiB of PCM
  and likely time out, leaving the crate with no documentation.
- Confirm the README renders on the crates.io page and its repository links resolve.

## If it goes wrong

- **A bad version is live.** `cargo yank --version X.Y.Z -p <crate>`. Yank does not delete;
  it stops *new* dependents resolving to it. Existing `Cargo.lock`s keep working. Publish a
  fixed version afterwards — you cannot reuse the yanked number.
- **A sample crate published but the parent failed.** Harmless. Fix the parent and publish
  it; the asset crates are already where they need to be.
- **A crate is over 10 MiB.** Split it (follow `ferrosintesis-samples-drumkit2`: keep the
  shared type in the original crate and give the new one its own `BankSource`), or ask
  crates.io for a limit increase. Do NOT trim samples to fit — that changes the render, and
  a size-driven re-voicing is exactly the kind of change nobody will remember making.
