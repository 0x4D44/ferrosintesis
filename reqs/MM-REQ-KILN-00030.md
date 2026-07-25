# MM-REQ-KILN-00030 — The amp-control protocol must have one machine-checked definition

- **State:** Satisfied
- **Priority:** Should
- **Area:** ferrosintesis / amp-lab protocol
- **Raised:** 2026-07-24
- **Implemented-by:** `crates/ferrosintesis/src/engine.rs::AMP_NEUTRAL` (new named constant), `crates/ferrosintesis/src/engine.rs::tests::amp_protocol_has_one_definition`
- **Satisfied-by:** `engine::tests::amp_protocol_has_one_definition`
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
- **State history:** Draft (2026-07-24, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`) → Accepted (2026-07-25) → Implemented (2026-07-25) → Satisfied (2026-07-25, verified)

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

## Implementation (2026-07-25)

Gate 1 chose the **derived cross-crate parity oracle**, which the Statement
offers as the alternative to a shared descriptor. That avoids the public
API/semver implications that made this a proposed heavy flow: nothing is
published, moved, or re-exported. The work turned out light.

`engine::tests::amp_protocol_has_one_definition` derives all three statements of
the protocol from source and requires them to agree:

| source | how it is read |
|---|---|
| this crate | the real `AMP_NRPN_MSB` / `AMP_PARAM_COUNT` / `AMP_NEUTRAL` constants, plus a scan of `engine.rs` for every `const AMP_*: usize` index |
| `crates/amp-lab/src/amp.rs` | text scan of `AMP_NRPN_MSB`, `NEUTRAL`, and the `KNOBS` table's `idx` / `name` |
| `crates/ferrosintesis/README.md` | text scan of the documented MSB and the NRPN table rows |

Three design points, each answering a note on this requirement:

- **No fourth copied table.** The note warned that "a second manually copied
  expected table is not an adequate oracle". Nothing here restates the protocol;
  every value is read from one of the three existing sources. Knob names are
  compared by prefix after normalising to letters only, because this crate's
  identifiers are abbreviations of the published names (`AMP_TIGHT` /
  "Tightness", `AMP_PRES` / "Presence", `AMP_CABTONE` / "Cab Tone") — a derived
  relationship rather than a mapping table.
- **It lives in `ferrosintesis`, not `amp-lab`.** `amp-lab` is excluded from the
  integration gate (`.deltic-integrate.toml` — it drags in egui + cpal, ~200
  crates), so a parity test living there would not run when it matters. Reading
  amp-lab's source as TEXT keeps the check on the gated side without taking the
  dependency.
- **The neutral got a name.** It was a bare `64` literal in five places in
  `engine.rs` while `amp-lab` published it as `amp::NEUTRAL` and the README
  stated it — a protocol value with no single definition to compare against.
  `AMP_NEUTRAL` now names it and the amp paths use it.

Refutations — one per field the Statement names, each applied and each RED:

| adversarial change | result |
|---|---|
| amp-lab renumbers a knob (Presence 4 -> 5) | red |
| amp-lab renames a knob (Body -> Bottom) | red |
| amp-lab changes the NRPN MSB (0x30 -> 0x31) | red |
| amp-lab changes the neutral (64 -> 63) | red |
| README documents a different MSB | red |
| README drops a knob row | red |
| a 7th knob added to the synth without `AMP_PARAM_COUNT` following | red |

Values were already in agreement, so this changes no behaviour — it is the
regression alarm the requirement asked for, and it now cannot stay green while
the three drift.
