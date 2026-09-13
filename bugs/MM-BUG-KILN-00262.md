# MM-BUG-KILN-00262 — Orchestral2 required preflight and non-banjo rebakes still target WAV after FLAC migration

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** orchestral2 sample generation / final-format regeneration
- **Raised:** 2026-08-17T04:25:53Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T203024Z-cd09d866
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00262-run-verify-20260913T203024Z-cd09d866
- **Owner base:** d80165ff792121cce074ef9bcb0daf4062cb52f9
- **Owner fingerprint:** sha256:3c9ce21f49d3e8901b39e7bc1ce9e98c9751bdc45d4814572913a33e9274b41d
- **Owner since:** 2026-09-13T20:30:24Z
- **Owner until:** 2026-09-13T22:30:24Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T04:25:53Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T04:19:01Z, deltic:auto role=fix run=fix-20260913T041638Z-3cc10e4f branch=task/bug-MM-BUG-KILN-00262-run-fix-20260913T041638Z-3cc10e4f code=55298fb16c0f370149bafafb7e518685cafa4443 gate=manual)

## Observation

The published non-banjo recipe at
`crates/ferrosintesis-samples-orchestral2/PROVENANCE.md:7-8` tells maintainers to
run `prepare.py --only=<family>`. Its source tables still name WAV outputs, and
`tools/ferrosintesis-samples/prepare.py:5342-5352` carries those names into the
expected inventory. The validator at `prepare.py:5402-5424` inspects only WAVs,
and the generic bake loop at `prepare.py:5733-5779` writes those WAV names. The
active crate instead embeds 132 FLAC files at
`crates/ferrosintesis-samples-orchestral2/src/lib.rs:17-405`, and the synth asks
for FLAC keys (for example `crates/ferrosintesis/src/sampler.rs:2565-2644`).

Following the documented command therefore creates fresh, unconsumed WAVs beside
unchanged FLACs. Runtime keeps using the stale FLAC payloads, while the crate's
inventory sees both containers. The required preflight is also deterministically
red: `tools/ferrosintesis-samples/test_prepare.py:2823-2851` compares the WAV
expectations with only on-disk WAV names, so every migrated family disagrees with
its FLAC-only directory. That unittest discovery is a required workspace and
fallback gate at `.deltic-integrate.toml:59,71`.

Expected: each scoped recipe stages, validates, and replaces the exact final-format
bank consumed at runtime, and the required preflight derives the same inventory.
Concrete fix: separate source names from canonical output names, encode and verify
the final FLAC set in empty staging, reject mixed same-stem containers before
publication, refresh the embedded inventory, and add a current-FLAC-tree negative
fixture. Static source review only; no generator, test, decoder, app, render, or
exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes

Open `MM-BUG-KILN-00240` covers the separate onset-continuity sweep that skips
FLAC. Open `MM-BUG-KILN-00241` covers the syntactically broken crate-lib generator.
