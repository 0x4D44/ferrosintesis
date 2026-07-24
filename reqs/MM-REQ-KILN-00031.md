# MM-REQ-KILN-00031 — Fret-noise inventory must have one generated source of truth

- **State:** Draft
- **Priority:** Could
- **Area:** fret-noise sample generation / package inventory
- **Raised:** 2026-07-24
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
- **State history:** Draft (2026-07-24, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`)

## Statement

The fret-noise bake and asset crate must derive their contiguous source-cut set,
packaged filenames, file count, lookup table, round-robin count, and generated
inventory assertions from one authoritative inventory. A non-mutating check must
fail when committed outputs or generated Rust drift from that inventory.

## Notes

- `tools/ferrosintesis-samples/fretnoise_bake.py:32,123-137` owns `N = 12` and
  the source/output filename loops.
- `crates/ferrosintesis-samples-fretnoise/src/lib.rs:10-66,90-120` independently
  owns the same count, twelve include rows, round-robin alias, and byte total.
- `tools/ferrosintesis-samples/gen_crate_lib.py` already derives ordinary sample
  crate inventories. It needs a round-robin mode or a custom-tail template so it
  preserves `ROUND_ROBINS` and `take_name`.
- Atomic replacement of generated WAVs is already tracked by
  `MM-BUG-KILN-00063`. Generator-environment byte reproducibility is tracked by
  `MM-BUG-KILN-00095`; neither is duplicated by this inventory requirement.
- Proposed Gate-1 flow is light: the behavior and a source-derived drift oracle
  are bounded, despite touching both Python generation and generated Rust.
