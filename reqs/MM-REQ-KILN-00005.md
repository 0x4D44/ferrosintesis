# MM-REQ-KILN-00005 — Orchestra hit (GM 55) should be a real stab, not a guitar note

- **State:** Satisfied
- **Priority:** Could
- **Area:** ferrosintesis / voices
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::OrchHit`, `crates/ferrosintesis/src/voices.rs::orch_hit`, `crates/ferrosintesis/src/voices.rs::make`, `crates/ferrosintesis/src/voices.rs::tests::orchestra_hit_55_is_short_layered_stab`, `crates/ferrosintesis/README.md`
- **Satisfied-by:** `$null | deltic timeout 180 cargo test orchestra_hit_55_is_short_layered_stab --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `6cc4a25d357d839ebb1ec83e8ef0c4ddb46aab03`) → Satisfied (2026-07-25, verified)

## Statement
A NoteOn on GM program 55 (Orchestra Hit) must render as a short, layered
stab — octave-stacked ensemble chord with a percussive thump and a fast decay —
plus the appropriate engine wiring, not the steel-guitar catch-all.

## Rationale
55 falls in the 55–71 seam: the brass/reed effort wires 55–71 into the
expressive features but designs no voice for 55 itself. 55 is unused by every
committed album, so a new voice here is byte-identical-safe. 2026-07-08 GM gap
audit (low-strings/hit). Note: coordinate with the brass/reed agent on the
55–71 engine wiring to avoid a collision.

## Notes

Manual reqs-loop build on branch `task/20260708-TSK-HUM-reqs-loop-mm-req-00005`.

Exact Gate 2 oracle command:

```powershell
$null | deltic timeout 180 cargo test orchestra_hit_55_is_short_layered_stab --manifest-path fable5/hollowsynth/Cargo.toml
```

Passing output recorded on 2026-07-08:

```text
running 1 test
test voices::tests::orchestra_hit_55_is_short_layered_stab ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 110 filtered out; finished in 0.01s

    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.01s
     Running unittests src\lib.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-ba4185fbc9b0bac1.exe)
     Running unittests src\main.rs (fable5\hollowsynth\target\debug\deps\hollowsynth-5ef3fec99e2e91ba.exe)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Oracle red proof on baseline claim commit `1f40ad1`:

```text
$null | deltic timeout 120 cargo test orchestra_hit_55_is_short_layered_stab --manifest-path fable5/hollowsynth/Cargo.toml

test voices::tests::orchestra_hit_55_is_short_layered_stab ... FAILED
assertion `left == right` failed: GM 55 must not route to steel
  left: "STEEL"
 right: "orch_hit"
test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 94 filtered out
```

Local validation:

```text
deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
passed (no output)

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 109 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 9.05s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.99s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 3.94s
```

Existing-MIDI and prior-render safety:

```text
tracked_mid_files=53
parse_errors=0
files_with_program55_changes=0
files_with_program55_noteons=0

No-program-55 render proof:
baseline commit: origin/main `c0cd5cd`
baseline/current render target: fable5/Heliopause/midi/01 - Heliopause, Part One.mid
baseline/current render stats: 4.79 min, 12643 events, 6 markers, 4859 voices, peak 1.10, max polyphony 95
baseline SHA256: E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
current  SHA256: E6595EEB10020827C7B422463DD0B93F59C6C806B57F1213B1157AC310C69F6D
cmd /c fc /b req00005-baseline.wav req00005-current.wav
FC: no differences encountered
```

Adversarial self-review:

```text
oracle-fit reviewer found no confirmed issue, reran the named oracle, verified the engine path stores raw program 55 and passes it into voices::make, and ran an end-to-end generated-MIDI render probe showing program 55 has fast decay, 220/880 Hz octave layers, and a much stronger low thump than program 25 steel.
compatibility reviewer found no confirmed issue, scanned 53 tracked MIDI files, confirmed zero program-55 events, and verified the only runtime routing change is voices::make's program-55 arm.
landing-hygiene reviewer confirmed the expected overlap with the parallel v0.9 worktree, whose branch already contains an orchestra-hit implementation. That is an integration sequencing risk; whichever branch lands second needs deliberate reconciliation.
```

Post-integration rebase note: rebased onto `origin/main` at `35f6c40` after
`MM-REQ-KILN-00003` landed. The implementation commit became
`6cc4a25d357d839ebb1ec83e8ef0c4ddb46aab03`; the package version was advanced to
`0.8.9` because trunk already carried `0.8.8`. The rebase kept the existing
wood-bar, kalimba, sustained-FX, and fiddle dispatch/tests, and reused the
existing `render_voice` helper to avoid a duplicate test helper.
