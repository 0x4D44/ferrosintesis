# MM-REQ-KILN-00010 — CC70 vowel morph should extend beyond the choir

- **State:** Satisfied
- **Priority:** Could
- **Area:** ferrosintesis / engine
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/engine.rs::vowel_family`, `crates/ferrosintesis/src/engine.rs::EngineCore::note_on`, `crates/ferrosintesis/src/engine.rs::EngineCore::render_block_add`, `crates/ferrosintesis/src/engine.rs::tests::choir_pad_91_cc70_vowel_morph_opens_formants`, `crates/ferrosintesis/src/voices.rs::SawStack::set_vowel`, `crates/ferrosintesis/src/voices.rs::pad`, `crates/ferrosintesis/README.md`
- **Satisfied-by:** `$null | deltic timeout 180 cargo test choir_pad_91_cc70_vowel_morph_opens_formants --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `df0ae7daa90a8f3b4f9fa13bce4aa13346e8ada3`) → Satisfied (2026-07-25, verified)

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
$null | deltic timeout 180 cargo test choir_pad_91_cc70_vowel_morph_opens_formants --manifest-path fable5/hollowsynth/Cargo.toml
```

Passing output recorded on 2026-07-08:

```text
running 1 test
test engine::tests::choir_pad_91_cc70_vowel_morph_opens_formants ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 113 filtered out; finished in 0.98s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Compiling hollowsynth v0.8.12 (D:\worktrees\midi-music\20260708-TSK-HUM-reqs-loop-mm-req-00010\fable5\hollowsynth)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 1.56s
     Running unittests src\lib.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-dbc2a0c85c370b4c.exe)
     Running unittests src\main.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-e095bab3fbaf2821.exe)
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
passed (no output)

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 112 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 8.58s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.00s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 3.61s
```

Existing-MIDI and prior-render safety:

```text
No tracked `.mid` files changed between the original scan base `4696cdb` and the current trunk base `2c60131`, so the original MIDI scan remains applicable:
tracked_mid_files_scanned=53
parse_errors=0
program91_files=0
program91_noteons=0
cc70_files=11
cc70_on_program91_events=0

Baseline/current render for fable5\Heliopause\midi\01 - Heliopause, Part One.mid, rerun after rebasing onto `c0cd5cd`:
SHA256 baseline = E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
SHA256 current  = E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
cmd /c fc /b req00010-baseline-rebased.wav req00010-current-rebased.wav
FC: no differences encountered
```

Adversarial self-review:

```text
Oracle-fit reviewer found a real temporal bug in the first implementation: whole-song lookahead made a program-91 note use the formant path before CC70 arrived. The implementation was changed so program 91 starts as the old lowpass pad and converts inside SawStack::set_vowel only when CC70 is actually authored. The oracle now bit-compares the pre-CC70 window against a no-CC70 render, and the reviewer confirmed the issue fixed.

Compatibility reviewer confirmed the previous 53-MIDI scan still applies because no tracked `.mid` files changed between the scan base and `c0cd5cd`, then reran a baseline/current Heliopause render against `c0cd5cd`; `fc /b` reported no differences. Before this integration push, `git diff --name-only 4696cdb origin/main -- "*.mid"` was empty, so the scan still applies to current trunk.

Rebase reviewer checked that no conflict markers remain, `EngineCore::note_on` and `EngineCore::render_block_add` both use `vowel_family(program)`, and the reset-controller path still does not convert program 91 without CC70 authoring.

Landing-hygiene reviewer confirmed the rebased implementation SHA, version bump, clean gates, no staged generated artifacts, and a real future integration conflict with the parallel v0.9 branch.
```

Post-integration rebase note: rebased onto `origin/main` at `2c60131` after
`MM-REQ-KILN-00007` landed. The implementation commit became
`df0ae7daa90a8f3b4f9fa13bce4aa13346e8ada3`; the package version was advanced to
`0.8.12` because trunk already carried `0.8.11`. The rebase kept the accumulated
GM voice/routing additions and merged the README SawStack table row.
