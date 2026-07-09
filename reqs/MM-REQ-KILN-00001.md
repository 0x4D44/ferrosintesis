# MM-REQ-KILN-00001 — Fiddle (GM 110) should render as a bowed string, not a guitar

- **State:** Implemented
- **Priority:** Should
- **Area:** ferrosintesis / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::make`, `crates/ferrosintesis/src/engine.rs::vibrato_family`, `crates/ferrosintesis/src/engine.rs::fx_profile`, `crates/ferrosintesis/src/engine.rs::tests::gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato`
- **Satisfied-by:** `$null | cargo test gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `073ea2c7348a25de62f927a7b4bbf09809196ec1`)

## Statement
A NoteOn on GM program 110 (Fiddle) must render through the bowed-string voice
(the `Bowed` model already used for GM 40–45, LA violin-bank included), not the
steel-guitar catch-all it currently falls through to.

## Rationale
110 is a lead voice on RIVERWAKE and is character-opposite to a plucked guitar.
`Bowed::new` takes no program parameter, so this is a one-arm dispatch change
(duplicate the 40..=45 arm) plus adding 110 to `vibrato_family` and the fiddle
`fx_profile` arm. Byte-identical for every existing hollowsynth album (110 is
unused by them). From the 2026-07-08 GM gap audit (ethnic family).

## Notes

Manual reqs-loop implementation branch:
`task/20260708-TSK-HUM-reqs-loop-implement-first-light`.

The named oracle was added before the implementation and failed red on the old
steel-guitar fallback:

```text
$null | deltic timeout 180 cargo test gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato --manifest-path fable5/hollowsynth/Cargo.toml
test engine::tests::gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato ... FAILED
assertion `left == right` failed: GM 110 must use the bowed/LA fiddle path
  left: "STEEL"
 right: "bowed"
```

Passing oracle for Gate 2:

```text
$null | cargo test gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato --manifest-path fable5/hollowsynth/Cargo.toml
test engine::tests::gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 106 filtered out; finished in 0.50s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Additional local gates after rebasing onto `origin/main` at `c0cd5cd`:

```text
deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
ok

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 105 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 7.71s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.94s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 4.09s
```

Authored-channel compatibility check:

```text
baseline_sha256=2C3046F7B7DC5326123A8F304FDF69707642EAC0D3798C13F4CF7797D10336DE
current_sha256=2C3046F7B7DC5326123A8F304FDF69707642EAC0D3798C13F4CF7797D10336DE
byte_identity=pass
```

Three read-only adversarial reviewers ran concrete refutation checks. Two
confirmed the oracle and regression evidence. The third found the expected
pre-landing dirty-tree/ledger state; the actionable stale README GM table was
fixed before landing.

Post-rebase note: rebased onto `origin/main` at `c0cd5cd` after the hollowsynth
realtime API landed. The implementation commit became
`073ea2c7348a25de62f927a7b4bbf09809196ec1`; the package version was advanced to
`0.8.4` because trunk already carried `0.8.3`.
