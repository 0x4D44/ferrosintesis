# MM-BUG-CRU-00076 — Windows input alias probe still aborts the render when another process holds the MIDI open for writing

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-09-14T21:48:03Z
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
- **State history:** Open (2026-09-14T21:48:03Z, raised via `deltic bugs new --land` model=claude-opus-5) -> Fixed (2026-09-14T22:13:47Z, deltic:auto role=fix run=fix-20260914T220131Z-078a4888 branch=task/bug-MM-BUG-CRU-00076-run-fix-20260914T220131Z-078a4888 code=80fcde2f864ba0bcb3259a33b095f3435286e851 gate=manual) -> Closed (2026-09-14T22:23:56Z, independent verify by Claude Opus 5 on trunk f44966c6: an input held open for writing no longer aborts the render; hard-link aliases are still rejected unless a writer holds the input, where the guard is advisory and the source stays intact)

## Observation

Split from MM-BUG-KILN-00294 at independent verification (2026-09-14, trunk 1d87b00f). That fix (b5bc0ae5) opens the input guard in crates/ferrosintesis-cli/src/output.rs platform_same_file with share_mode(1), FILE_SHARE_READ only, so an ordinary reader no longer aborts the render (verified). A third-party handle that holds the input with WRITE access is still denied by that share mode. Observed on Windows 11 with the debug CLI built from 1d87b00f: with a prior score.wav present, and Python holding score.mid via open(path, 'r+b') (read/write access, share read+write), the command 'ferrosintesis score.mid -o score.wav --tail 0 --no-samples -q' exits 1 with: error: <dir>\score.mid: The process cannot access the file because it is being used by another process. (os error 32). The same command exits 0 with no holder and with a read-only ('rb') holder. Expected, per MM-BUG-KILN-00294: a third-party sharing condition on the input must not abort a render the synthesizer can perform. Actual: an input held open read-write (for example by an editor or DAW) still aborts the render, now with a path-naming diagnostic thanks to MM-BUG-KILN-00298. Inference, not measured: the library's own std::fs::File::open (default share read|write|delete) would read that input, so the abort comes only from the alias probe.

Evidence fingerprint: `manual:v1:windows-input-alias-probe-still-aborts-the-rend-132a19168d39f9bf`


## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `f44966c6` (fix `80fcde2f`) by an agent other than the fixer.

**Original observation, re-run live on Windows.** Same debug CLI, a prior `score.wav` present, and `score.mid` held open for writing (Python `open(path, 'r+b')`). `ferrosintesis score.mid -o score.wav --tail 0 --no-samples -q` now exits 0 with the input bytes unchanged; before the fix it exited 1 with os error 32.

**Root cause check.** If the input guard's `share_mode(1)` open hits a sharing violation, `platform_same_file` now returns 'not the same file' and lets the renderer's own input open decide, instead of aborting. Other open errors still return a path-naming error.

**Fails-before (method B).** `read_write_shared_distinct_input_does_not_abort_render` passes, along with all 9 `output_safety` tests. Deleting the sharing-violation arm fails it: 'distinct output failed with a read/write-shared input: error: ...\score.mid: The process cannot access the file because it is being used by another process. (os error 32)'. Restored.

**Alias protection, probed with a fresh hard link each time.**
- No holder, and a reader-held input: `-o alias.wav`, where `alias.wav` is a hard link to `score.mid`, is still rejected with 'aliases the input ... refusing to overwrite the source MIDI'. The link and the MIDI are untouched.
- Writer-held input: the same command exits 0. The guard is skipped, so the render replaces the `alias.wav` name with a WAV and breaks the link. `score.mid` still holds the original MIDI bytes.
The fix commit states this advisory behaviour on purpose, and no source bytes were lost, so it is recorded here as a limit rather than a new bug.

**Repo gate.** On `f44966c6`: `python3 -m unittest discover -s tools/ferrosintesis-samples` ends 'Ran 284 tests ... OK', so the Python gate step is green again, and `cargo test -p ferrosintesis-cli --locked --test output_safety` passes 9 of 9. The cargo steps were fully run on `1d87b00f` and `011738f6` earlier in this pass (fmt, all clippy steps, both no-default test steps, `cargo test --workspace --all-targets`); they were not re-run in full on `f44966c6`.

## Notes
