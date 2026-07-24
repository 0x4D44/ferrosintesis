# MM-REQ-KILN-00030 — The amp-control protocol must have one machine-checked definition

- **State:** Draft
- **Priority:** Should
- **Area:** ferrosintesis / amp-lab protocol
- **Raised:** 2026-07-24
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
- **State history:** Draft (2026-07-24, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`)

## Statement

The amp-control protocol's NRPN block identifier, parameter count, parameter
indices, neutral value, and user-facing meanings must come from one authoritative
definition or be protected by a derived cross-crate parity oracle, so the
published synth, amp-lab controls, export, and documentation cannot drift while
their local tests remain green.

## Notes

- `crates/amp-lab/src/amp.rs:7-50` defines MSB `0x30`, six indices, names, and
  neutral value `64`.
- `crates/ferrosintesis/src/engine.rs:417-438` independently defines the same
  protocol for the shipped synth.
- `crates/ferrosintesis/README.md:139-150` is a third hand-maintained description.
- Current values match; this is durable design debt, not a present routing bug.
- The repo's recurring defect pattern is hand-maintained lists that drift. A
  second manually copied expected table is not an adequate oracle.
- Gate 1 should choose between a shared typed/public descriptor and a
  source-derived parity test. The public API/semver implications make this a
  proposed heavy flow.
