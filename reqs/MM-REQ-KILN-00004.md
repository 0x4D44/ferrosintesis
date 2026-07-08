# MM-REQ-KILN-00004 — Marimba (12) and xylophone (13) need wood voices, not the vibes preset

- **State:** Implemented
- **Priority:** Should
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** `fable5/hollowsynth/src/voices.rs::MARIMBA`, `fable5/hollowsynth/src/voices.rs::XYLOPHONE`, `fable5/hollowsynth/src/voices.rs::wood_bar`, `fable5/hollowsynth/src/voices.rs::make`, `fable5/hollowsynth/src/voices.rs::tests::marimba_xylophone_have_wood_bar_envelopes`
- **Satisfied-by:** `$null | cargo test marimba_xylophone_have_wood_bar_envelopes --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `0efd750575902f455c10eb93f7ea2957253c75f6`)

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

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 94 filtered out; finished in 0.02s
```

Additional local gates:

```text
deltic timeout 120 cargo fmt --check
ok

$null | deltic timeout 600 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 93 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 6.34s

$null | deltic timeout 600 cargo clippy --all-targets --manifest-path fable5/hollowsynth/Cargo.toml -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.44s
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

Post-rebase note: rebased onto `origin/main` at `c0cd5cd` after the hollowsynth
realtime API landed. The implementation commit became
`0efd750575902f455c10eb93f7ea2957253c75f6`; the package version was advanced to
`0.8.4` because trunk already carried `0.8.3`.
