# MM-BUG-KILN-00247 — Headroom sample documentation still describes WAV payloads after FLAC conversion

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** headroom sample crate / public package contract
- **Raised:** 2026-08-17T00:04:27Z
- **Discovery source:** Agent
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T00:04:27Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:30:46Z, deltic:auto role=fix run=fix-20260913T162211Z-c54220b4 branch=task/bug-MM-BUG-KILN-00247-run-fix-20260913T162211Z-c54220b4 code=edb66ef8deea05b93b1efb872863364dada43363 gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: headroom docs separate 45 FLAC payloads from 54 logical names; pre-fix docs fail the contract test)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fixes `edb66ef8`, `a1df1ab7`) by an agent other than the fixer.

**Original observation re-derived.** Headroom holds 45 FLACs, 9 FLAC-to-FLAC aliases and `LOGICAL_FILE_COUNT = 54`; README, PROVENANCE and NOTICE match, and the package list ships ALIASES and NOTICE.

**Fails-before (method A).** With README, PROVENANCE and NOTICE from `edb66ef8^`, `tests::package_docs_match_the_embedded_flac_contract` fails. The crate's 4 tests pass on HEAD.

**Coverage note.** The guard matches literal phrases rather than deriving 45/9/54 from `SAMPLES`/`ALIASES`, as the record suggested; logged in `scratchpad.md`.

## Notes
