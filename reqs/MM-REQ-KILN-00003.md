# MM-REQ-KILN-00003 — Sustaining synth-FX programs (97/99/101/103) should sustain

- **State:** Implemented
- **Priority:** Could
- **Area:** ferrosintesis / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::make`, `crates/ferrosintesis/src/voices.rs::tests::synth_fx_97_99_101_103_sustain_as_pads`, `crates/ferrosintesis/src/testutil.rs::guards::gm_routing_pins_voice_kinds`
- **Satisfied-by:** `$null | deltic timeout 180 cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `a3eecb96c93646fb382867f14d250ac3f9eadb81`)

## Statement
GM 97 (soundtrack), 99 (atmosphere), 103 (sci-fi) must render as sustaining pad
textures (route to `pad()`), and 101 (goblins) to the LFO-swept sweep-pad path,
rather than the one decaying `bell(CRYSTAL)` chime that all eight FX programs
currently share and which fades to silence in ~3 s on a held note.

## Rationale
These are sustained-texture programs; a struck chime is structurally wrong. The
SawStack pad voice already provides the right character; this is dispatch-arm
work. Byte-identical for existing albums (only FX 98/crystal is used, and it
stays on the bell path). 2026-07-08 GM gap audit (synth FX).

## Notes

Manual reqs-loop implementation branch:
`task/20260708-TSK-HUM-reqs-loop-mm-req-00003`.

The named oracle was added before implementation and failed red on the old shared
crystal route:

```text
$null | deltic timeout 180 cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::synth_fx_97_99_101_103_sustain_as_pads ... FAILED
assertion `left == right` failed: program 97 should route to pad
  left: "modal"
 right: "sawstack"
```

Passing oracle for Gate 2:

```text
$null | deltic timeout 180 cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::synth_fx_97_99_101_103_sustain_as_pads ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 109 filtered out; finished in 0.05s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Additional local gates after rebasing onto `origin/main` at `112d3b9`:

```text
$null | deltic timeout 180 cargo test gm_routing_pins_voice_kinds --manifest-path fable5/hollowsynth/Cargo.toml
test testutil::guards::gm_routing_pins_voice_kinds ... ok
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 109 filtered out; finished in 0.00s

deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
passed (no output)

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 108 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 8.80s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.89s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 3.55s
```

MIDI scan:

```text
changed_fx_files=0
unchanged_crystal_fx_files=6
```

Unaffected GM-98 material stayed byte-identical:

```text
baseline_sha256=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
current_sha256=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
byte_identity=pass
```

Three read-only adversarial reviewers ran concrete refutation checks. The oracle
and regression reviewers found no defects. The remaining dirty-tree/Accepted
state finding was the expected pre-landing state and is addressed by this
commit.

Post-integration rebase note: rebased onto `origin/main` at `112d3b9` after
`MM-REQ-KILN-00002` landed. The implementation commit became
`a3eecb96c93646fb382867f14d250ac3f9eadb81`; the package version was advanced to
`0.8.8` because trunk already carried `0.8.7`.
