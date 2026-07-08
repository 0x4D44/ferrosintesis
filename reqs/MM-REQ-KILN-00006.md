# MM-REQ-KILN-00006 — SFX programs (GM 120-127) should not emit a pitched guitar note

- **State:** Implemented
- **Priority:** Could
- **Area:** hollowsynth / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** fable5/hollowsynth/src/voices.rs::SfxNoise, fable5/hollowsynth/src/voices.rs::make, fable5/hollowsynth/src/voices.rs::tests::gm_sfx_120_127_are_toneless_noise_fallbacks, fable5/hollowsynth/src/testutil.rs::guards::gm_routing_pins_voice_kinds, fable5/hollowsynth/README.md
- **Satisfied-by:** `$null | cargo test gm_sfx_120_127_are_toneless_noise_fallbacks --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `f762fa68f022601dafcb164a5de49fc9a57a024c`)

## Statement
GM 120–127 (fret noise, breath, seashore, bird, telephone, helicopter, applause,
gunshot) must render as a safe, toneless noise/near-silence fallback rather than
the current in-key steel-guitar pluck, so a composer who hits an SFX program does
not get a wrong pitched note.

## Rationale
These sound-effect programs are rare but currently produce a melodic guitar note
at the written pitch — the loudest possible wrongness. A band-filtered noise
burst (or near silence) is a safer default. Byte-identical for existing albums
(none use 120–127). Lowest-priority family; keep the change proportionate.
2026-07-08 GM gap audit (percussive/SFX).

## Notes

Manual reqs-loop implementation landed on branch
`task/20260708-TSK-HUM-reqs-loop-mm-req-00006`.

Gate 2 oracle command and passing output:

```text
$null | cargo test gm_sfx_120_127_are_toneless_noise_fallbacks --manifest-path fable5/hollowsynth/Cargo.toml
running 1 test
test voices::tests::gm_sfx_120_127_are_toneless_noise_fallbacks ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 94 filtered out; finished in 0.02s

    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.00s
     Running unittests src\main.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-b8eab23d08065b45.exe)
```

Additional local gates run during landing:

```text
$null | deltic timeout 120 cargo test gm_routing_pins_voice_kinds --manifest-path fable5/hollowsynth/Cargo.toml
test testutil::guards::gm_routing_pins_voice_kinds ... ok
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 94 filtered out

deltic timeout 60 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
passed

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 93 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s)
```

Existing-album invariant: tracked MIDI scan found no SFX programs:

```text
tracked_mid_files_scanned=53
program_change_events_scanned=542
program120_127_hits=0
```

Baseline/current renders of `fable5\Heliopause\midi\02 - Heliopause, Part Two.mid`
were byte-identical:

```text
baseline=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
current=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
cmd /c fc /b ...req00006-baseline.wav ...req00006-current.wav
FC: no differences encountered
```

Mandatory adversarial self-review found no confirmed refutation. The oracle-fit
reviewer reran the named oracle and checked raw MIDI program numbering. The
regression reviewer independently scanned 53 tracked MIDI files / 542 program
changes and found zero 120-127 hits and zero 119-127 off-by-one hits. The
landing-hygiene reviewer confirmed the version bump, README update, routing
canary, expected dirty set, gates, and an additional Tuxedo Noir byte-identity
render (`E48CA61B9B435A2E33F81EA418ACEB1E4154D7C9E111655C24A0D899F49052E7`).

Post-rebase note: rebased onto `origin/main` at `c0cd5cd` after the hollowsynth
realtime API landed. The implementation commit became
`f762fa68f022601dafcb164a5de49fc9a57a024c`; the package version was advanced to
`0.8.4` because trunk already carried `0.8.3`.
