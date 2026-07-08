# MM-REQ-KILN-00003 — Sustaining synth-FX programs (97/99/101/103) should sustain

- **State:** Implemented
- **Priority:** Could
- **Area:** hollowsynth / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** `fable5/hollowsynth/src/voices.rs::make`, `fable5/hollowsynth/src/voices.rs::tests::synth_fx_97_99_101_103_sustain_as_pads`, `fable5/hollowsynth/src/testutil.rs::guards::gm_routing_pins_voice_kinds`
- **Satisfied-by:** `$null | cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `10cc5b71406f75a5c3de6cdbb67a174e9e29a21a`)

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
$null | cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::synth_fx_97_99_101_103_sustain_as_pads ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 106 filtered out; finished in 0.05s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Additional local gates after rebasing onto `origin/main` at `c0cd5cd`:

```text
$null | deltic timeout 180 cargo test gm_routing_pins_voice_kinds --manifest-path fable5/hollowsynth/Cargo.toml
test testutil::guards::gm_routing_pins_voice_kinds ... ok

deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
ok

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 105 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 6.81s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.89s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 3.91s
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

Post-rebase note: rebased onto `origin/main` at `c0cd5cd` after the hollowsynth
realtime API landed. The implementation commit became
`10cc5b71406f75a5c3de6cdbb67a174e9e29a21a`; the package version was advanced to
`0.8.4` because trunk already carried `0.8.3`.
