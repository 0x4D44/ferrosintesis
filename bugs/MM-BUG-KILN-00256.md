# MM-BUG-KILN-00256 — Concurrent MuseScore-grand regenerations race fixed shared intermediates

- **State:** Open
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
- **State history:** Open (2026-08-17T02:30:29Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Every worktree selects the same system-temp directory `tempfile.gettempdir()/musescore_general` for this bake at tools/ferrosintesis-samples/prepare.py:5695-5698. `_bake_musescore_grand` then rewrites fixed `msgrand_<root>.ogg` and `msgrand_<root>.wav` intermediate paths at :4650-4655: the Ogg open with `wb` truncates the shared file, ffmpeg overwrites the shared WAV with `-y`, and `read_wav` immediately consumes that same path. Two concurrent documented `--only=musescoregrand` runs can therefore read an intermediate while the peer truncates or replaces it, causing a spurious failure or publishing data produced from a peer's partial/mismatched intermediate. The pinned SF3 input is authenticated; the race is in mutable decode intermediates. Expected: identical concurrent regenerations safely share immutable cached input, serialize, or use isolated intermediates. Actual: all runs mutate the same fixed names without locking. Concrete fix: use a process-unique decode directory, or lock the cache and atomically publish authenticated intermediates. Add a two-process regression that overlaps Ogg extraction, ffmpeg output, and WAV consumption. MM-BUG-KILN-00221 covers fixed clavinet intermediates in a different MuseScore path; it does not exercise or fix this MuseScore_General function. Static review only; no concurrent run occurred. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
