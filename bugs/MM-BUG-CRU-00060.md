# MM-BUG-CRU-00060 — Sample container-documentation oracle misses WAV claims after source-context phrases and headings

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample asset crates / container documentation oracle
- **Raised:** 2026-09-13T19:22:42Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T204905Z-553a16f8
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00060-run-verify-20260913T204905Z-553a16f8
- **Owner base:** e539dbb574a56cf71e41f9e0b39cc2a7c2773c49
- **Owner fingerprint:** sha256:92f8782f4b924f7748bce87c9834e132166814521f7fe561e1985c41d96befcb
- **Owner since:** 2026-09-13T20:49:05Z
- **Owner until:** 2026-09-13T22:49:05Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:22:42Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T20:24:45Z, deltic:auto role=fix run=fix-20260913T201450Z-4b649983 branch=task/bug-MM-BUG-CRU-00060-run-fix-20260913T201450Z-4b649983 code=02b8eec294c48d666cf7717f4ab565660483db00 gate=manual)

## Observation

Split at independent verification of MM-BUG-CRUCIBLE-00044 (2026-09-13, trunk 8b6a6f86). payload::tests::sample_crate_documents_match_their_packaged_containers (fix db16a45b) exempts lines that contain source-context phrases or sit under source-ish headings. With the pre-fix text restored it does NOT flag the bug's own cited sentence, clavinet PROVENANCE.md:9 'The 11 WAVs in samples/ are ... extracted from ...', because 'extracted from' marks it as source context. It also accepted an adversarial 'This crate ships 11 WAV files.' planted under '## Extraction and bake'. Expected: a claim about the packaged samples/ container is judged by its subject, not exempted by a nearby phrase or heading.

## Fix

<unfixed — raised only>

## Notes
