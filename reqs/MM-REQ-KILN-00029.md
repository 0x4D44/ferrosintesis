# MM-REQ-KILN-00029 — Retain offline-auditable licence evidence for login-gated CC-BY samples

- **State:** Draft
- **Priority:** Should
- **Area:** sample assets / licence provenance
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
- **State history:** Draft (2026-07-24, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-ccby/`)

## Statement

The repository must retain immutable, offline-auditable upstream licence evidence for
each login-gated CC-BY Freesound source embedded by
`ferrosintesis-samples-ccby`.

## Notes

- `crates/ferrosintesis-samples-ccby/PROVENANCE.md:3-4` cites each pack's bundled
  `_readme_and_license.txt` as the evidence for CC-BY 4.0.
- The same document says Freesound downloads are login-gated. No cited licence
  manifest is tracked in the repository; `tools/ferrosintesis-samples/freesound-src/`
  contains only WAVs.
- Acceptable evidence could be the original two manifests, or immutable metadata
  snapshots containing source/pack IDs, author, licence, source URL, and content hash.
- This does not challenge the current `NOTICE`; it preserves the evidence needed to
  audit that notice without a Freesound account or mutable upstream page.

