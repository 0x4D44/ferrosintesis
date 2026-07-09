# MM-REQ-KILN-00004 — Marimba (12) and xylophone (13) need wood voices, not the vibes preset

- **State:** Implemented
- **Priority:** Should
- **Area:** ferrosintesis / voices
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::MARIMBA`, `crates/ferrosintesis/src/voices.rs::XYLOPHONE`, `crates/ferrosintesis/src/voices.rs::wood_bar`, `crates/ferrosintesis/src/voices.rs::make`, `crates/ferrosintesis/src/voices.rs::tests::marimba_xylophone_have_wood_bar_envelopes`
- **Satisfied-by:** `$null | cargo test marimba_xylophone_have_wood_bar_envelopes --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `b81508e9bfd732eb7e6211a03ce46c7518372a7a`)

## Statement
GM 12 (Marimba) and 13 (Xylophone) must render with wood-bar character — a fast,
key-scaled decay and a band-passed wood-click attack, xylophone with its 1:3
quint tuning — via dedicated `bell()` preset tables, instead of sharing the metal
VIBES table (T60 ~3 s, no click) with GM 11 vibraphone.

## Rationale
One VIBES preset currently serves vibraphone+marimba+xylophone; marimba/xylophone
ring like metal with no mallet click — the defining wood transient is absent. 12
is used by RIVERWAKE. `bell()` is table-driven, so this is data + two match arms.
Byte-identical for existing hollowsynth albums (12/13 unused by them). 2026-07-08
GM gap audit (chromatic percussion).

## Notes

Manual reqs-loop implementation branch:
`task/20260708-TSK-HUM-reqs-loop-mm-req-00004`.

The named oracle was added before implementation and failed red on the old shared
vibes route:

```text
$null | deltic timeout 180 cargo test marimba_xylophone_have_wood_bar_envelopes --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::marimba_xylophone_have_wood_bar_envelopes ... FAILED
marimba should decay like wood, not vibes: marimba 3.00s vs vibes 3.00s
```

Passing oracle for Gate 2:

```text
$null | deltic timeout 180 cargo test marimba_xylophone_have_wood_bar_envelopes --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::marimba_xylophone_have_wood_bar_envelopes ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 107 filtered out; finished in 0.04s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Additional local gates after rebasing onto `origin/main` at `0378038`:

```text
deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
ok

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 106 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 8.17s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.96s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 5.17s
```

The original rationale's "12/13 unused" assumption was wrong for the whole repo:

```text
program_12_13_files=1
opus4-8\amarok\midi\Riverwake.mid: [(15, 12)]
```

Unaffected no-12/13 material stayed byte-identical:

```text
baseline_sha256=2C3046F7B7DC5326123A8F304FDF69707642EAC0D3798C13F4CF7797D10336DE
current_sha256=2C3046F7B7DC5326123A8F304FDF69707642EAC0D3798C13F4CF7797D10336DE
byte_identity=pass
```

Riverwake, the one committed MIDI using GM 12, intentionally changed:

```text
riverwake_baseline_sha256=7F7EA0B95D4ED75CDA8105F077E65B22B0D0A733B92D80B9DA8DED98266BE866
riverwake_current_sha256=A36E46FC7723322AEB9EA7D9892E3D26645F6D93A5DA9CD7BB72EF44874B6AAC
riverwake_expected_diff=pass
```

Three read-only adversarial reviewers ran concrete refutation checks. The
initial oracle gaps around key-scaled decay and click-filter isolation were fixed
and reverified. The Riverwake byte-identity caveat was corrected with the
expected-diff render above. The remaining "dirty tree / req still Accepted"
finding was the expected pre-landing state and is addressed by this commit.

Post-rebase note: rebased onto `origin/main` at `0378038` after
`MM-REQ-KILN-00001` landed. The implementation commit became
`b81508e9bfd732eb7e6211a03ce46c7518372a7a`; the package version was advanced to
`0.8.5` because trunk already carried `0.8.4`.
