# MM-BUG-KILN-00240 — Packaged-sample onset sweep excludes every converted FLAC bank

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / committed onset continuity oracle
- **Raised:** 2026-08-16T21:54:31Z
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
- **State history:** Open (2026-08-16T21:54:31Z, raised via `deltic bugs new`)

## Observation

Observation: crates/ferrosintesis-samples-gong/PROVENANCE.md:121-128 says the two committed gong layers are pinned by test_committed_gong_bank_starts_with_continuous_pcm, but no such test exists on this baseline. Its derived replacement, tools/ferrosintesis-samples/test_prepare.py::test_every_packaged_bank_starts_without_a_discontinuity at lines 1056-1092, enumerates sample crates but skips every name not ending in .wav at lines 1073-1075 and then calls a RIFF-only read_wav helper. The gong crate now packages only gong_ageng_soft.flac and gong_ageng_loud.flac, so the oracle that should prevent the previously shipped soft-strike onset click never examines either current payload. The same filter drops all other banks converted to FLAC. Expected: the continuity oracle derives and decodes every supported packaged container, proves both gong layers are in its checked set, and keeps a non-vacuous per-format inventory floor. Concrete fix: move the sweep to a format-aware path using the shipped FLAC decoder or another repository-supported offline decoder; update the stale provenance test reference; add negative FLAC fixtures for a one-shot first-frame jump and loop wrap discontinuity, plus a guard proving a converted bank cannot disappear from coverage. Static review only; the test suite and decoder were not run.

## Fix

<unfixed — raised only>

## Notes
