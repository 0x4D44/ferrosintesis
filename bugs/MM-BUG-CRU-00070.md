# MM-BUG-CRU-00070 — Gong, honky-tonk and bagpipe bakes write straight into the live crate and convert per file, so a late failure leaves a mixed bank

- **State:** Closed
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
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:47:48Z, deltic:auto role=fix run=fix-20260913T214019Z-23fbd881 branch=task/bug-MM-BUG-CRU-00070-run-fix-20260913T214019Z-23fbd881 code=ffd22d054ab0bc6c9aaa6e84608902e415884b6f gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 011738f6: gong, honky-tonk and bagpipe bakes now stage and publish through the rollback publisher; pointing each write back at the live crate fails its late-failure test; interrupt gap tracked in MM-BUG-CRU-00077)

## Observation

Residual found at independent verification of MM-BUG-KILN-00265, 00239, 00251 and 00287 (2026-09-13, trunk 8b6a6f86), by reading the code (not fault-injected). The generic, grand, clavinet, onset, MuseScore-grand, mandolin, bass, YDP and sax bakes now stage and publish through a transactional FLAC publisher. Three writers still do not: _bake_honkytonk writes os.path.join(out_dir, ...) per zone (tools/ferrosintesis-samples/prepare.py:5555); the bagpipe/chanter bake writes sample_output_path(fn) per file (prepare.py:4801); _bake_gong_bank writes each output directly (prepare.py:6392). Their WAVs land in the live crate samples/ and are converted to FLAC one file at a time by the pending-bank publish at the end of main. A failure mid-run leaves mixed WAV and FLAC or partially refreshed packages. Expected: stage and publish these banks through the same whole-bank transaction.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `00990a87` and `011738f6` (fix `ffd22d05`) by agents other than the fixer: a verifier worker ran the mutations, and the lead re-ran the tests and read the publisher.

**Original observation.** The gong, honky-tonk and bagpipe bakes no longer write into the live crate one file at a time. They stage, then publish through `_publish_staged_flac_bank`, which encodes and verifies every FLAC before moving any old file aside. `LocalWholeBankAtomicityTest` covers each bake with a late failure (`test_gong_...`, `test_honkytonk_...`, `test_bagpipe_late_failure_never_touches_the_previous_bank`); all pass.

**Fails-before (method B).** For each bake, pointing its write back at the live crate fails that bake's test on its snapshot assertion. Restored.

**Residual, tracked in MM-BUG-CRU-00077.** `_publish_staged_flac_bank` rolls back only under `except Exception`, and its `finally` deletes the backup directory. A KeyboardInterrupt during the swap therefore deletes the moved-aside originals. This bug's recorded failure (an ordinary late error) is fixed.

**Repo gate.** The Python suite on `1d87b00f` and `00990a87` ends 'Ran 281 ... FAILED (errors=4)', all four in the MM-BUG-CRU-00068 classes (reopened), none touching these bakes. The cargo gate steps do not build `tools/`.

## Notes
