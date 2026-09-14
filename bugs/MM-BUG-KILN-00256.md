# MM-BUG-KILN-00256 — Concurrent MuseScore-grand regenerations race fixed shared intermediates

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore grand sample generation / concurrent cache isolation
- **Raised:** 2026-08-17T02:30:29Z
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
- **State history:** Open (2026-08-17T02:30:29Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-14T01:31:25Z, deltic:auto role=fix run=fix-20260914T012002Z-b63c0f51 branch=task/bug-MM-BUG-KILN-00256-run-fix-20260914T012002Z-b63c0f51 code=305f6fb6b560c4dee23d10c90d49f55e14ba4cd7 gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 011738f6: MuseScore-grand Ogg/WAV decodes are now per-run; pointing them back at the shared cache fails the concurrent-bake test)

## Observation

Every worktree selects the same system-temp directory `tempfile.gettempdir()/musescore_general` for this bake at tools/ferrosintesis-samples/prepare.py:5695-5698. `_bake_musescore_grand` then rewrites fixed `msgrand_<root>.ogg` and `msgrand_<root>.wav` intermediate paths at :4650-4655: the Ogg open with `wb` truncates the shared file, ffmpeg overwrites the shared WAV with `-y`, and `read_wav` immediately consumes that same path. Two concurrent documented `--only=musescoregrand` runs can therefore read an intermediate while the peer truncates or replaces it, causing a spurious failure or publishing data produced from a peer's partial/mismatched intermediate. The pinned SF3 input is authenticated; the race is in mutable decode intermediates. Expected: identical concurrent regenerations safely share immutable cached input, serialize, or use isolated intermediates. Actual: all runs mutate the same fixed names without locking. Concrete fix: use a process-unique decode directory, or lock the cache and atomically publish authenticated intermediates. Add a two-process regression that overlaps Ogg extraction, ffmpeg output, and WAV consumption. MM-BUG-KILN-00221 covers fixed clavinet intermediates in a different MuseScore path; it does not exercise or fix this MuseScore_General function. Static review only; no concurrent run occurred. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `00990a87` and `011738f6` (fix `305f6fb6`) by agents other than the fixer: a verifier worker ran the mutation, and the lead re-ran the test.

**Original observation.** Concurrent MuseScore-grand regenerations no longer share fixed decode intermediates. `MuseScoreGrandWholeBankPublicationTest.test_concurrent_bakes_isolate_decode_intermediates_and_reads` runs two concurrent bakes against one shared cache and passes.

**Fails-before (method B).** Pointing the Ogg/WAV intermediates back at the shared `src` fails it: 'worker B failed: RuntimeError: B: consumed another process's decoded WAV ...\shared-cache\msgrand_40.wav'. Restored.

**Repo gate.** The Python suite on `1d87b00f` and `00990a87` ends 'Ran 281 ... FAILED (errors=4)', all four in the MM-BUG-CRU-00068 classes (reopened); none touch this bake. The cargo gate steps do not build `tools/`.

## Notes
