# MM-REQ-KILN-00007 — Sitar/shamisen/koto (104/106/107) need their own plucked voices

- **State:** Implemented
- **Priority:** Could
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** `fable5/hollowsynth/src/voices.rs::SITAR`, `fable5/hollowsynth/src/voices.rs::SHAMISEN`, `fable5/hollowsynth/src/voices.rs::KOTO`, `fable5/hollowsynth/src/voices.rs::make`, `fable5/hollowsynth/src/voices.rs::tests::sitar_shamisen_koto_have_distinct_pluck_presets`, `fable5/hollowsynth/src/testutil.rs::guards::gm_routing_pins_voice_kinds`, `fable5/hollowsynth/README.md`
- **Satisfied-by:** `$null | cargo test sitar_shamisen_koto_have_distinct_pluck_presets --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `2f36bf142c64cc76a73a4cfbc08b86bbe11836b0`)

## Statement
GM 104 (sitar), 106 (shamisen) and 107 (koto) must render with distinct plucked
character — koto long and mellow (harp-like preset), sitar with a buzzing
jawari/sympathetic quality, shamisen a lightened banjo — instead of all sharing
the single bright/short BANJO preset with GM 105.

## Rationale
104/106/107 are byte-identical to the banjo today; sitar and koto are
character-opposite (koto rings short and bright, opposite of its long mellow
decay). GM 105 (banjo, used by Hollow Hill/RIVERWAKE) stays untouched.
Byte-identical for existing albums (104/106/107 unused). 2026-07-08 GM gap audit
(ethnic).

## Notes

Manual reqs-loop build on branch `task/20260708-TSK-HUM-reqs-loop-mm-req-00007`.

Exact Gate 2 oracle command:

```powershell
$null | cargo test sitar_shamisen_koto_have_distinct_pluck_presets --manifest-path fable5/hollowsynth/Cargo.toml
```

Passing output recorded on 2026-07-08:

```text
running 1 test
test voices::tests::sitar_shamisen_koto_have_distinct_pluck_presets ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 94 filtered out; finished in 0.12s

    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.06s
     Running unittests src\main.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-b8eab23d08065b45.exe)
```

Oracle red proof on baseline claim commit `e0866db`:

```text
test voices::tests::sitar_shamisen_koto_have_distinct_pluck_presets ... FAILED
assertion `left == right` failed: program 104
  left: "BANJO"
 right: "SITAR"
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 94 filtered out
```

Local validation:

```text
deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
PASS

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
PASS: 93 passed; 0 failed; 2 ignored

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
PASS

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
PASS
```

Existing-MIDI and prior-render safety:

```text
tracked_mid_files_scanned=53
program_change_events_scanned=542
program104_106_107_hits=0
program105_banjo_hits=2
  fable5\Hollow Hill\midi\02 - Hollow Hill, Part Two.mid ch15 program105
  opus4-8\amarok\midi\Riverwake.mid ch2 program105

Baseline/current render for fable5\Hollow Hill\midi\02 - Hollow Hill, Part Two.mid:
SHA256 baseline = 8B842ED489EBFD719B3189B62F2EA69B9CA7C1DBC7F02DEB5DA8403FD024C479
SHA256 current  = 8B842ED489EBFD719B3189B62F2EA69B9CA7C1DBC7F02DEB5DA8403FD024C479
cmd /c fc /b req00007-baseline.wav req00007-current.wav
FC: no differences encountered
```

Adversarial self-review:

```text
Oracle-fit reviewer confirmed the oracle passes and checks rendered timbre, not only test-only names. It found one verified weakness: the first oracle compared different random seeds per program. The oracle was strengthened to compare all voices at the same pitch under three shared seeds, then rerun red/green.

Regression reviewers confirmed tracked MIDI has no 104/106/107 hits and that the two GM105 uses are banjo tracks; GM105 remains routed to BANJO and is pinned by the routing guard.

Landing-hygiene reviewer found the expected pre-landing gaps: uncommitted implementation, pending req transition, pending oracle output, pending gates, and generated WAV artifacts. These were addressed before the landing commit except the ignored WAV files, which were removed after evidence capture.
```

Post-rebase note: rebased onto `origin/main` at `c0cd5cd` after the hollowsynth
realtime API landed. The implementation commit became
`2f36bf142c64cc76a73a4cfbc08b86bbe11836b0`; the package version was advanced to
`0.8.4` because trunk already carried `0.8.3`.
