# MM-BUG-CRU-00069 — Honky-tonk bake decodes to fixed intermediates in the shared honkytonk_fb temp directory

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** sample tooling / concurrent cache isolation
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
- **State history:** Open (2026-09-13T19:26:11Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:39:08Z, deltic:auto role=fix run=fix-20260913T213306Z-f78d849d branch=task/bug-MM-BUG-CRU-00069-run-fix-20260913T213306Z-f78d849d code=d3cd6cd2ad352c761c2c52a094e21a5f010395ff gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 011738f6: honky-tonk decodes now go to a per-run temp directory; pointing the decode back at the shared cache fails the two-process regression test)

## Observation

Residual found at independent verification of MM-BUG-KILN-00261 (2026-09-13, trunk 8b6a6f86), by reading the code. The onset fix (9170b41b) moved MuseScore onset decode intermediates into per-run staging, but _bake_honkytonk (tools/ferrosintesis-samples/prepare.py:5543-5546) still decodes to the fixed name htsrc_<note>.wav inside the host-global gettempdir()/honkytonk_fb and reads it back immediately. Two concurrent honky-tonk regenerations can read each other's decoded WAV. The MuseScore-grand sibling is tracked separately as MM-BUG-KILN-00256. Expected: per-run private decode intermediates, as the clavinet and onset bakes now use.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `00990a87` and `011738f6` (fix `d3cd6cd2`) by agents other than the fixer: a verifier worker ran the mutation, and the lead re-ran the tests.

**Original observation.** The decoded honky-tonk WAV is now written into a per-run `TemporaryDirectory`, and the shared `honkytonk_fb` cache holds only the input FLACs. `HonkytonkConcurrentExtractionTest.test_two_bakes_use_isolated_decode_intermediates` runs two worker processes that meet at a barrier on the shared cache, which is the recorded race. It passes on both trunks.

**Fails-before (method B).** Pointing the decoded WAV path back at the shared `src` directory fails the test: 'worker A failed: RuntimeError: A: read another process's decoded WAV ...\honkytonk_fb\htsrc_C2.wav'. Restored.

**Repo gate.** The Python suite on `1d87b00f` and `00990a87` ends 'Ran 281 ... FAILED (errors=4)', all four in the MM-BUG-CRU-00068 classes (reopened), none touching this bake. The cargo gate steps do not build `tools/`.

## Notes
