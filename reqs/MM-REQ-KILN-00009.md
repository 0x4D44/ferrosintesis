# MM-REQ-KILN-00009 — Strings & choir (SawStack) must answer CC1 vibrato and CC68 legato

- **State:** Implemented
- **Priority:** Should
- **Area:** hollowsynth / engine + voices (SawStack)
- **Raised:** 2026-07-08
- **Implemented-by:** `fable5/hollowsynth/src/engine.rs::vibrato_family`, `fable5/hollowsynth/src/engine.rs::tests::strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in`, `fable5/hollowsynth/src/voices.rs::SawStack::legato_to`, `fable5/hollowsynth/src/voices.rs::strings`, `fable5/hollowsynth/src/voices.rs::choir`, `fable5/hollowsynth/src/voices.rs::tests::legato_gated_to_strings_choir_and_leads`, `fable5/hollowsynth/README.md`
- **Satisfied-by:** `$null | cargo test strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `96a8c6b62c16a75965138663a191cfce5987282e`)

## Statement
The string-ensemble (48–51) and choir (52–54) SawStack voices must answer the
CC1 mod-wheel vibrato (add them to `vibrato_family`) and CC68 legato slurs
(extend the lead-gated `SawStack::legato_to`), engaging only on channels that
author those controllers.

## Rationale
The synth-lead build (MM lead voice, GM 80–87) already wired CC1/CC68 into the
SawStack engine and gated legato to leads; extending it to strings/choir is a
small follow-on. Opt-in via the authored-channel pattern → byte-identical for
albums that don't send CC1/CC68 on those channels. Coordinate with the
brass/reed agent, who owns the strings/choir polish. 2026-07-08 GM gap audit
(cross-cutting engine gap #2). A 2026-07-08 implementation scan found some
existing committed MIDI already authors CC1 or CC68 on GM 48; those files are
inside the opt-in exception and are expected to change.

## Notes

Manual reqs-loop build on branch `task/20260708-TSK-HUM-reqs-loop-mm-req-00009`.

Exact Gate 2 oracle command:

```powershell
$null | cargo test strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in --manifest-path fable5/hollowsynth/Cargo.toml
```

Passing output recorded on 2026-07-08:

```text
running 1 test
test engine::tests::strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 105 filtered out; finished in 8.23s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Oracle red proof on baseline claim commit `ef0c5f8`:

```text
$null | deltic timeout 120 cargo test strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in --manifest-path fable5/hollowsynth/Cargo.toml

test engine::tests::strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in ... FAILED
program 48 plain 13.217957 Hz vs mod 13.217957 Hz
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 93 filtered out
```

Local validation:

```text
deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
PASS

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
PASS: 104 passed; 0 failed; 2 ignored

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
PASS: Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.00s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
PASS: Finished `release` profile [optimized] target(s) in 3.76s
```

Existing-MIDI and prior-render safety:

```text
tracked_mid_files=53
parse_errors=0
files_with_program_48_54_notes=53
files_with_cc1_or_cc68_while_program_48_54=13
known opt-in changes: fable5/The Ninth Bell/midi/01 - The Ninth Bell.mid has CC68 on GM 48; gpt5-3-spark/midi/*.mid author CC1 on GM 48.
inherited-controller leak check: 0 files where CC1/CC68 authored under another program later affected GM 48-54 before direct in-program authorship.

No-authored-controller render proof:
baseline/current render target: fable5/Heliopause/midi/01 - Heliopause, Part One.mid
baseline/current render stats: 4.79 min, 12643 events, 6 markers, 4859 voices, peak 1.10, max polyphony 95
baseline SHA256: E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
current  SHA256: E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
cmd /c fc /b req00009-baseline.wav req00009-current.wav
FC: no differences encountered
```

Adversarial self-review:

```text
oracle-fit reviewer confirmed two initial oracle gaps: only GM 48/52 sampled, and CC68 proved one spawned voice but not retuned pitch. The oracle was strengthened to cover every GM 48-54 program and verify the slurred pitch retunes to key 64.
compatibility reviewer confirmed the existing MIDI exception set is non-empty, verified no inherited-controller leak, and reran the focused oracle green.
landing-hygiene reviewer confirmed the expected conflict risk with the parallel v0.9 worktree: this patch conflicts there in Cargo.toml, Cargo.lock, README.md, engine.rs, and voices.rs. That is an integration sequencing risk, not a local correctness blocker.
```

Post-rebase note: rebased onto `origin/main` at `c0cd5cd` after the hollowsynth
realtime API landed. The implementation commit became
`96a8c6b62c16a75965138663a191cfce5987282e`; the package version was advanced to
`0.8.4` because trunk already carried `0.8.3`.
