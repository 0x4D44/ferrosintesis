# MM-REQ-KILN-00033 — Dark Salamander must remain a verified projection of the source grand bank

- **State:** Draft
- **Priority:** Should
- **Area:** sample assets / dark-grand generation
- **Raised:** 2026-07-26
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-26, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-dark-salamander/`)

## Statement

The dark-Salamander bank must be a complete, deterministic projection of every
tracked `ferrosintesis-samples-grand` WAV, preserve each paired file's note
identity, duration and canonical PCM format, and measurably attenuate treble
relative to that paired source.

## Notes

The current 54 payloads are unique, valid PCM mono 44.1 kHz/16-bit files, and
each differs from its raw-grand counterpart. That is a one-time observation, not
a durable oracle.

The generated tests at
`crates/ferrosintesis-samples-dark-salamander/src/lib.rs:246-278` and
`tools/ferrosintesis-samples/gen_crate_lib.py:79-114` check filenames, aggregate
bytes and RIFF/WAVE magic. They do not prove the committed payloads are the
defined high-shelf transform or that the transform still darkens the bank.
Same-length silence, swapped notes, raw-grand copies, or a broken 0 dB shelf can
pass those checks.

A suitable Gate-1 oracle would rebake all 54 pairs without mutating tracked
files, compare the canonical output bytes, and independently measure the
high-band attenuation so a self-consistent bad transform cannot redefine the
expectation.

Proposed priority: Should. Proposed flow: light. Estimated effort: Medium.
