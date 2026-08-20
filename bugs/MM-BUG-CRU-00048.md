# MM-BUG-CRU-00048 — Mandolin regeneration can publish a partial mixed bank after a late failure

- **State:** Open
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
- **State history:** Open (2026-08-20T12:21:13Z, raised via `deltic bugs new`)

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

<unfixed — raised only>

Generate all 40 final FLACs in an empty per-family staging directory, validate exact
names and decoded PCM there, then publish the complete bank with rollback. Add
late-transform and late-replacement failure injections; each must leave the previous bank
byte-for-byte unchanged.

## Notes
