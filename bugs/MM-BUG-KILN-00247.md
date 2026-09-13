# MM-BUG-KILN-00247 — Headroom sample documentation still describes WAV payloads after FLAC conversion

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** headroom sample crate / public package contract
- **Raised:** 2026-08-17T00:04:27Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T195910Z-997375c7
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00247-run-verify-20260913T195910Z-997375c7
- **Owner base:** 389b8db6c1a8a4513ca79d5207edff597ce1bddc
- **Owner fingerprint:** sha256:98509932921e72927da2dc86f9a3ec1a9584667089f4298530af51b98e6a5949
- **Owner since:** 2026-09-13T19:59:10Z
- **Owner until:** 2026-09-13T21:59:10Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T00:04:27Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:30:46Z, deltic:auto role=fix run=fix-20260913T162211Z-c54220b4 branch=task/bug-MM-BUG-KILN-00247-run-fix-20260913T162211Z-c54220b4 code=edb66ef8deea05b93b1efb872863364dada43363 gate=manual)

## Observation

Static inspection found that the published package documentation still describes
the pre-migration WAV bank. `crates/ferrosintesis-samples-headroom/README.md:8-10`
says 54 mono WAVs are embedded, `PROVENANCE.md:10-18,61` calls the 45 physical
outputs WAVs, and `NOTICE:4` calls the embedded samples WAVs. The committed crate
instead embeds 45 FLAC files at `src/lib.rs:15-196`; the other nine logical names
are `.wav` aliases at `src/lib.rs:198-208` that return canonical FLAC bytes.

Expected: the shipped README, provenance, and notice distinguish 45 physical FLAC
payloads from 54 logical names and explain the nine compatibility aliases. Actual:
package users and auditors receive the wrong container and inventory contract.
Current runtime lookup is internally consistent; this is a published documentation
defect, not evidence of payload corruption. Concrete fix: update all three package
documents together and add a source-derived documentation guard tied to the actual
inventory/container set. Static review only; no app, test, decoder, generator,
package command, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
