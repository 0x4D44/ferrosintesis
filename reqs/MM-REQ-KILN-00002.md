# MM-REQ-KILN-00002 — Kalimba (GM 108) should have a tine voice, not a guitar

- **State:** Implemented
- **Priority:** Could
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** fable5/hollowsynth/src/voices.rs::KALIMBA, fable5/hollowsynth/src/voices.rs::make, fable5/hollowsynth/src/voices.rs::tests::kalimba_108_has_tine_decay_not_pluck, fable5/hollowsynth/src/testutil.rs::guards::gm_routing_pins_voice_kinds, fable5/hollowsynth/README.md
- **Satisfied-by:** `$null | cargo test kalimba_108_has_tine_decay_not_pluck --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `PENDING_SHA`)

## Statement
A NoteOn on GM program 108 (Kalimba) must render as a plucked-tine timbre — a
short-decay inharmonic partial set with a soft thumb-contact transient — via a
new `bell()` preset table, not the steel-guitar catch-all.

## Rationale
The `bell()` modal primitive is fully table-driven, so a KALIMBA partial table
(~2.8x/5.4x overtones, short T60, low-level contact noise) plus one match arm
suffices. Byte-identical for existing albums (108 unused). 2026-07-08 GM gap
audit (percussive/ethnic).

## Notes

Manual reqs-loop implementation landed on branch
`task/20260708-TSK-HUM-reqs-loop-mm-req-00002`.

Gate 2 oracle command and passing output:

```text
$null | cargo test kalimba_108_has_tine_decay_not_pluck --manifest-path fable5/hollowsynth/Cargo.toml
running 1 test
test voices::tests::kalimba_108_has_tine_decay_not_pluck ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 94 filtered out; finished in 0.00s

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

Existing-album invariant: tracked MIDI scan found `program108_hits=0`.
Baseline/current renders of `fable5\Heliopause\midi\02 - Heliopause, Part Two.mid`
were byte-identical:

```text
baseline=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
current=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
cmd /c fc /b ...req00002-baseline.wav ...req00002-current.wav
FC: no differences encountered
```

Mandatory adversarial self-review found no confirmed refutation. The oracle-fit
reviewer reran the named oracle and confirmed the routing/timbre clauses. The
regression reviewer scanned 53 tracked MIDI files and found zero program-108 or
program-107 events. The landing-hygiene reviewer confirmed the expected files,
version bump, README update, routing canary, gates, and req claim; the only
actionable point was that the implementation was still uncommitted before this
landing commit.
