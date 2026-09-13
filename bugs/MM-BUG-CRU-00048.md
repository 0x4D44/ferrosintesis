# MM-BUG-CRU-00048 — Mandolin regeneration can publish a partial mixed bank after a late failure

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** mandolin sample generation / failure atomicity
- **Raised:** 2026-08-20T12:21:13Z
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
- **State history:** Open (2026-08-20T12:21:13Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T14:57:33Z, deltic:auto role=fix run=fix-20260913T144902Z-b45c3bda branch=task/bug-MM-BUG-CRU-00048-run-fix-20260913T144902Z-b45c3bda code=53a2586d8f7fb8eae1db081556a0bf9d5df1a371 gate=manual) -> Closed (2026-09-13, independently verified by Codex: staged mandolin publication preserves the previous bank on late failures; no residual gap)

## Observation

Static review found that the documented mandolin bake writes a new bank directly into
the live package directory one file at a time. The generic loop reads the 40 mandolin
sources and calls `write_wav_mono(sample_output_path(...))` at
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-124001\tools\ferrosintesis-samples\prepare.py:5904`
and `:5911-5944`. `write_wav_mono` makes each logical WAV individually atomic at
`:4372-4403`, but it writes beside the previous FLAC bank and registers that final
directory for later conversion.

`publish_pending_banks()` at `prepare.py:4412-4452` then encodes, verifies, replaces,
and deletes each file independently. A late transform failure leaves a prefix of new WAVs
beside the old FLACs. A late encode, decode, replacement, removal, or process failure
leaves a prefix of new FLACs, an old-FLAC suffix, and any unconverted WAVs. A rerun can
repair the directory, and inventory checks can reject the mixed file count, but the failed
command has already destroyed the invariant that the tracked bank is one coherent
generation.

Expected: any failed regeneration preserves the previous 40-file mandolin bank
byte-for-byte. Actual: failure publishes a partial generation into the live package.
This is the mandolin counterpart of open `MM-BUG-KILN-00245`, whose observation and fix
are explicitly scoped to the separate 54-file grand bank; it does not ensure the
mandolin path becomes atomic. Static review only; no generator, test, build, decoder,
package, app, render, or exploratory harness ran. Estimated effort: Medium.

## Fix

Fixed by `53a2586d8f7fb8eae1db081556a0bf9d5df1a371`. Mandolin generation now stages the
complete logical bank in a private per-family directory, validates the staged inventory, and
publishes through the shared rollback transaction. A transform or publication failure leaves
the previous bank byte-for-byte unchanged.

### Verification summary (2026-09-13 — Codex)

`$null | deltic timeout 300 python -m unittest
test_prepare.MandolinWholeBankPublicationTest` passed both regression cases: a third-sample
transform failure and an injected late publication failure, each preserving the old bank and
leaving no transaction artifacts.

For the required mutation check, I temporarily changed `_bake_mandolin` to write each WAV
directly into the live package directory. The late-transform regression failed because the
previous FLAC bank gained new WAV files. I restored the staging write and verified its source
diff is empty.

The full `test_prepare` module ran 228 tests with one unrelated Steinway alias-manifest
failure. The complete sample-tooling suite ran 264 tests with the same single failure. Those
gates also emitted an existing unclosed-file `ResourceWarning`; neither issue is in the
mandolin transaction path. The shared publication helper has separate records for other bank
families and ffmpeg/documentation concerns; those are distinct from this mandolin atomicity
defect.

## Notes
