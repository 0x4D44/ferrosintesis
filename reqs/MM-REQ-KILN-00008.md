# MM-REQ-KILN-00008 — Modal & Organ voices must respond to pitch bend and portamento

- **State:** Implemented
- **Priority:** Should
- **Area:** ferrosintesis / voices (Modal, Organ)
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::Modal::set_pitch`, `crates/ferrosintesis/src/voices.rs::Organ::set_pitch`, `crates/ferrosintesis/src/engine.rs::aftertouch_family`, `crates/ferrosintesis/src/engine.rs::tests::modal_organ_pitch_controls_move_sustained_notes`, `crates/ferrosintesis/README.md`
- **Satisfied-by:** `$null | cargo test modal_organ_pitch_controls_move_sustained_notes --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-09, `373e7e1`)

## Statement
The Modal and Organ voice families must honour channel pitch multipliers
(`set_pitch`): pitch bend, RPN bend-range/fine-tune, CC5/CC65 portamento, and
aftertouch vibrato must audibly move their pitch. This covers pianos 0–7, bells
8–15, timpani 47, crystal 96–103 and organs 16–23 — roughly 40 programs that
currently ignore all of them (their `set_pitch` is the no-op trait default while
the engine dutifully calls it).

## Rationale
Highest-leverage expression gap: one capability unlocks ~40 programs. Needs care
(retuning modal partials / organ pipes while a note rings) and per-family design,
hence heavy. Opt-in-safe in principle (a channel that never bends is unchanged),
but must be proven byte-identical for existing albums. 2026-07-08 GM gap audit
(cross-cutting engine gap #1).

## Notes
Implemented in `373e7e1` after Arthur approved the compatibility waiver for
existing Modal/Organ tracks that already authored pitch controls. The waiver set
is `fable5/The Burning Meridian/midi/03 - Meridian.mid` plus all 12
`gpt5-3-spark/midi/*.mid` tracks; every other `render_opus.py::ALBUMS` MIDI
must remain byte-identical old-vs-new.

Oracle command:

```powershell
$null | deltic timeout 180 cargo test modal_organ_pitch_controls_move_sustained_notes --manifest-path fable5/hollowsynth/Cargo.toml
```

Passing output:

```text
running 1 test
test engine::tests::modal_organ_pitch_controls_move_sustained_notes ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 156 filtered out
```

Additional local validation:

```text
$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 153 passed; 0 failed; 4 ignored

$null | deltic timeout 300 cargo clippy --all-targets --manifest-path fable5/hollowsynth/Cargo.toml -- -D warnings
Finished `dev` profile

deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
passed

$null | deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile
```

Waiver-aware render comparison, current `origin/main` v0.9.0 release binary
(`41e49d2`) vs rebased v0.9.1 release binary:

```text
rendered 53 MIDI files with old and new binaries
non-waived byte-identical: 40/40
waived sanity checked: 13/13
largest waived RMS delta: -2.07 dB (gpt5-3-spark/midi/10 - Lightning Over Stone.mid)
peaks remained around -1 dBFS with no clipping samples
```
