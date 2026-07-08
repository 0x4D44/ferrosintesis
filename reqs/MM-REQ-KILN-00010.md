# MM-REQ-KILN-00010 — CC70 vowel morph should extend beyond the choir

- **State:** Implemented
- **Priority:** Could
- **Area:** hollowsynth / engine
- **Raised:** 2026-07-08
- **Implemented-by:** `fable5/hollowsynth/src/engine.rs::vowel_family`, `fable5/hollowsynth/src/engine.rs::render_buses`, `fable5/hollowsynth/src/engine.rs::tests::choir_pad_91_cc70_vowel_morph_opens_formants`, `fable5/hollowsynth/src/voices.rs::SawStack::set_vowel`, `fable5/hollowsynth/src/voices.rs::pad`, `fable5/hollowsynth/README.md`
- **Satisfied-by:** `$null | cargo test choir_pad_91_cc70_vowel_morph_opens_formants --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `PENDING_SHA`)

## Statement
The CC70 vowel-morph control must be available to the formant-capable SawStack
voices beyond the choir — at minimum the choir-pad (GM 91), and optionally
strings/pads given a formant filter — rather than being hard-gated to programs
52–54, since `SawStack::set_vowel` already exists.

## Rationale
The vowel machinery is built and gated to 52..=54 only; choir-pad 91 in
particular has zero vocal character today. Note: a voice must be built with the
`Formant` filter for `set_vowel` to act, so ungating alone is insufficient for
programs currently on a plain lowpass — the req includes giving 91 the formant
bank. Opt-in via CC70 authoring → byte-identical for existing albums. 2026-07-08
GM gap audit (cross-cutting engine gap; pads/choir).

## Notes

Manual reqs-loop build on branch `task/20260708-TSK-HUM-reqs-loop-mm-req-00010`.

Exact Gate 2 oracle command:

```powershell
$null | cargo test choir_pad_91_cc70_vowel_morph_opens_formants --manifest-path fable5/hollowsynth/Cargo.toml
```

Passing output recorded on 2026-07-08:

```text
running 1 test
test engine::tests::choir_pad_91_cc70_vowel_morph_opens_formants ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 94 filtered out; finished in 0.91s

    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.00s
     Running unittests src\main.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-b8eab23d08065b45.exe)
```

Oracle red proof on baseline claim commit `2851206`:

```text
test engine::tests::choir_pad_91_cc70_vowel_morph_opens_formants ... FAILED
choir-pad vowel didn't open: mm 0.006643727572020437 vs ah 0.006643727572020437
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
parse_errors=0
program91_files=0
program91_noteons=0
cc70_files=11
cc70_on_program91_events=0

Baseline/current render for fable5\Heliopause\midi\01 - Heliopause, Part One.mid:
SHA256 baseline = E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
SHA256 current  = E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
cmd /c fc /b req00010-baseline.wav req00010-current.wav
FC: no differences encountered
```

Adversarial self-review:

```text
Oracle-fit reviewer found a real temporal bug in the first implementation: whole-song lookahead made a program-91 note use the formant path before CC70 arrived. The implementation was changed so program 91 starts as the old lowpass pad and converts inside SawStack::set_vowel only when CC70 is actually authored. The oracle now bit-compares the pre-CC70 window against a no-CC70 render, and the reviewer confirmed the issue fixed.

Compatibility reviewer independently parsed 53 tracked MIDIs and found no raw program-91 events and no CC70 while program 91 is selected. It also reran the vowel tests and found no compatibility issue.

Landing-hygiene reviewer confirmed the claim commit, pending landing fields, version bump, no staged generated artifacts, and a real future integration conflict with the parallel v0.9 branch. The branch remains unpushed for human sequencing.
```
