# MM-BUG-CRU-00071 — Drum-kit publish_staged swaps files one at a time with no rollback

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** drum-kit sample generation / failure atomicity
- **Raised:** 2026-09-13T19:26:12Z
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
- **State history:** Open (2026-09-13T19:26:12Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:56:01Z, deltic:auto role=fix run=fix-20260913T214837Z-82ee938b branch=task/bug-MM-BUG-CRU-00071-run-fix-20260913T214837Z-82ee938b code=df7b03d4dff0b84d138620d4f15cad89df1c5e6f gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 011738f6: drum-kit publication now swaps both packages as one transaction with rollback; bypassing rollback fails the swap-failure test; the KeyboardInterrupt gap is split to MM-BUG-CRU-00077)

## Observation

Residual found at independent verification of MM-BUG-KILN-00283 (2026-09-13, trunk 8b6a6f86), by reading the code. Fix 82e6b571 makes tools prepare_drumkit.py publish FLAC-only banks and reject stale WAVs, but publish_staged moves each staged take into place with os.replace one file at a time and has no rollback. A failure mid-swap leaves a partly published two-package kit (drumkit and drumkit2). No committed test checks that a successful publish writes .flac names either. Expected: whole-kit transactional publication with rollback, like _publish_staged_flac_bank.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `00990a87` and `011738f6` (fix `df7b03d4`) by agents other than the fixer: a verifier worker ran the mutation and the interrupt probe, and the lead re-ran the tests and read the code.

**Original observation.** `publish_staged` in `prepare_drumkit.py` now encodes and verifies every take for both packages first. It then moves the old files into backup directories, swaps the new ones in, and on failure removes what it published and restores every backup. `DrumkitOutputPlanTests.test_publish_swap_failure_rolls_back_both_packages_and_cleans_temps` and `test_publish_success_uses_packaged_flac_names_for_both_packages` pass.

**Fails-before (method B).** Bypassing the rollback fails the swap-failure test: `AssertionError: b'new-flac' != b'old-flac'`. Restored.

**Residual split to MM-BUG-CRU-00077.** Rollback runs only under `except Exception`, but the `finally` still removes the backup directories while `cleanup_backups` is True. A KeyboardInterrupt or SystemExit mid-swap therefore skips rollback and deletes the originals. The worker's probe, interrupting the second swap, left drumkit `core.flac` new and drumkit2 `accent.flac` gone. The committed FLACs are recoverable from git.

**Repo gate.** The Python suite on `1d87b00f` and `00990a87` ends 'Ran 281 ... FAILED (errors=4)', all four in the MM-BUG-CRU-00068 classes (reopened), none in `test_prepare_drumkit.py`. The cargo gate steps do not build `tools/`.

## Notes
