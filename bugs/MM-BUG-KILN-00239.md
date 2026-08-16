# MM-BUG-KILN-00239 — Gong regeneration command leaves the embedded FLAC bank stale

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** gong sample crate / deterministic regeneration
- **Raised:** 2026-08-16T21:53:11Z
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
- **State history:** Open (2026-08-16T21:53:11Z, raised via `deltic bugs new`)

## Observation

Observation: README.md:15-18 and PROVENANCE.md:130-140 publish python3 tools/ferrosintesis-samples/prepare.py --local-only as the complete gong regeneration command. That path selects LOCAL_SOURCES whose output names are .wav at tools/ferrosintesis-samples/prepare.py:1091-1098 and writes them with write_wav_mono at :5444-5462. The crate instead embeds only .flac at crates/ferrosintesis-samples-gong/src/lib.rs:12-20. Following the documented command therefore creates two extra WAVs while leaving both shipped FLAC payloads unchanged; the crate inventory test then sees four bank files against FILE_COUNT=2, and Cargo.toml:10 would package both container sets. The separate tools/ferrosintesis-samples/to_flac.py conversion is not named by either regeneration document and describes itself as a one-time bake. Expected: the documented regeneration workflow atomically refreshes the exact packaged FLAC assets and leaves a testable clean two-file inventory. Concrete fix: integrate verified FLAC emission/conversion into the selected gong recipe or publish and test a complete two-step workflow; refresh provenance sizes/names; add a negative regression that starts from the committed FLAC-only bank, runs the workflow in an isolated tree, and proves both embedded payloads were replaced with no duplicate WAVs. Static review only; the command was not run under this pass contract.

## Fix

<unfixed — raised only>

## Notes
