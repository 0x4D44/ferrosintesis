# MM-BUG-CRU-00070 — Gong, honky-tonk and bagpipe bakes write straight into the live crate and convert per file, so a late failure leaves a mixed bank

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / failure atomicity
- **Raised:** 2026-09-13T19:26:11Z
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
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Residual found at independent verification of MM-BUG-KILN-00265, 00239, 00251 and 00287 (2026-09-13, trunk 8b6a6f86), by reading the code (not fault-injected). The generic, grand, clavinet, onset, MuseScore-grand, mandolin, bass, YDP and sax bakes now stage and publish through a transactional FLAC publisher. Three writers still do not: _bake_honkytonk writes os.path.join(out_dir, ...) per zone (tools/ferrosintesis-samples/prepare.py:5555); the bagpipe/chanter bake writes sample_output_path(fn) per file (prepare.py:4801); _bake_gong_bank writes each output directly (prepare.py:6392). Their WAVs land in the live crate samples/ and are converted to FLAC one file at a time by the pending-bank publish at the end of main. A failure mid-run leaves mixed WAV and FLAC or partially refreshed packages. Expected: stage and publish these banks through the same whole-bank transaction.

## Fix

<unfixed — raised only>

## Notes
