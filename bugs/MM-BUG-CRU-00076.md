# MM-BUG-CRU-00076 — Windows input alias probe still aborts the render when another process holds the MIDI open for writing

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-09-14T21:48:03Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260914T220131Z-078a4888
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00076-run-fix-20260914T220131Z-078a4888
- **Owner base:** f0c85450461bcea3aebb5993bef7ab0c00d9db09
- **Owner fingerprint:** -
- **Owner since:** 2026-09-14T22:01:31Z
- **Owner until:** 2026-09-15T00:01:31Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-14T21:48:03Z, raised via `deltic bugs new --land` model=claude-opus-5)

## Observation

Split from MM-BUG-KILN-00294 at independent verification (2026-09-14, trunk 1d87b00f). That fix (b5bc0ae5) opens the input guard in crates/ferrosintesis-cli/src/output.rs platform_same_file with share_mode(1), FILE_SHARE_READ only, so an ordinary reader no longer aborts the render (verified). A third-party handle that holds the input with WRITE access is still denied by that share mode. Observed on Windows 11 with the debug CLI built from 1d87b00f: with a prior score.wav present, and Python holding score.mid via open(path, 'r+b') (read/write access, share read+write), the command 'ferrosintesis score.mid -o score.wav --tail 0 --no-samples -q' exits 1 with: error: <dir>\score.mid: The process cannot access the file because it is being used by another process. (os error 32). The same command exits 0 with no holder and with a read-only ('rb') holder. Expected, per MM-BUG-KILN-00294: a third-party sharing condition on the input must not abort a render the synthesizer can perform. Actual: an input held open read-write (for example by an editor or DAW) still aborts the render, now with a path-naming diagnostic thanks to MM-BUG-KILN-00298. Inference, not measured: the library's own std::fs::File::open (default share read|write|delete) would read that input, so the abort comes only from the alias probe.

Evidence fingerprint: `manual:v1:windows-input-alias-probe-still-aborts-the-rend-132a19168d39f9bf`


## Fix

<unfixed — raised only>

## Notes
