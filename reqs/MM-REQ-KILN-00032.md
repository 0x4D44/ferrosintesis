# MM-REQ-KILN-00032 — Render entry points must share one machine-checked default profile

- **State:** Draft
- **Priority:** Should
- **Area:** ferrosintesis CLI/catalog render policy
- **Raised:** 2026-07-25
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-25, captured by Codex GPT-5.6-Sol from the coverage review of `crates/ferrosintesis-cli/`)

## Statement

The shipping CLI, catalog renderer, and raw measurement renderer must derive
their shared render defaults and tempo-derived echo policy from one
authoritative definition, or from a parity oracle that actually observes each
entry point's effective configuration.

## Notes

- Current values match; this is structural drift risk, not a present sound
  mismatch.
- `crates/ferrosintesis-cli/src/main.rs:28-37,112-140` defines rate, wetness,
  tail, normalization, and tempo-derived echo policy locally.
- `crates/ferrosintesis-cli/examples/raw_dump.rs:65-80` copies the same profile
  because calibration requires it to match the shipping renderer.
- `crates/render-catalog/src/main.rs:26-39,264-280` carries a third copy.
- `crates/render-catalog/src/main.rs:911-931` is named
  `synth_options_match_ferrosintesis_cli_defaults`, but it checks catalog
  constants and options against literals from that same file. A CLI-only
  default change leaves it green.
- `deltic reqs --json` and the open requirement files showed no requirement
  covering this render-profile parity gap.
- Gate 1 should choose a shared typed profile/formula consumed by all entry
  points, or a genuinely derived cross-entry-point oracle. Another copied
  literal table would inherit the same defect.
