# MM-BUG-CRU-00077 — Sample bank publishers delete their backups on KeyboardInterrupt instead of rolling back

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** tools/ferrosintesis-samples
- **Raised:** 2026-09-14T21:53:09Z
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
- **State history:** Open (2026-09-14T21:53:09Z, raised via `deltic bugs new --land` model=claude-opus-5) -> Fixed (2026-09-14T22:19:58Z, deltic:auto role=fix run=fix-20260914T221446Z-bb4230f6 branch=task/bug-MM-BUG-CRU-00077-run-fix-20260914T221446Z-bb4230f6 code=b62fffadedd17cbd75dfa37f6173bd3f4c769f5d gate=manual) -> Closed (2026-09-14T22:56:40Z, independent verify by Claude Opus 5 on trunk 56ba5184: all three FLAC bank publishers now roll back on KeyboardInterrupt/SystemExit; reverting each to except Exception fails its interrupt test)

## Observation

Split from MM-BUG-CRU-00071 at independent verification (2026-09-14, trunk 011738f6). tools/ferrosintesis-samples/prepare_drumkit.py publish_staged and tools/ferrosintesis-samples/prepare.py _publish_staged_flac_bank move each existing FLAC into a backup directory, then swap the new files in. Rollback runs only in 'except Exception', but the 'finally' removes the backup directories whenever cleanup_backups / cleanup_backup is still True (read in both functions). A KeyboardInterrupt or SystemExit raised during the swap therefore skips the rollback, leaves the flag True, and the finally deletes the moved-aside originals while the bank is half published. A verifier probe that interrupted the second swap left the drumkit core.flac replaced by the new take and the drumkit2 accent.flac gone; the same probe on _publish_staged_flac_bank left a.flac new and b.flac gone. Expected: an interrupted publish restores the previous bank, or at least keeps its backups. Actual: the originals are deleted and the bank is mixed. The committed FLACs can be restored from git, so the loss is limited to the working tree. fretnoise_bake.publish_fretnoise_bank catches BaseException and is not affected (read, not probed). The gong, honky-tonk and bagpipe bakes fixed under MM-BUG-CRU-00070 publish through _publish_staged_flac_bank and share this gap.

Evidence fingerprint: `manual:v1:sample-bank-publishers-delete-their-backups-on--aca7c358e19ce191`


## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `56ba5184` (fix `b62fffad`) by an agent other than the fixer.

**Original observation, root cause.** `prepare_drumkit.publish_staged`, `prepare._publish_staged_flac_bank` and `prepare._publish_ydp_bank` now roll back published files and restore every backup under `except BaseException`. An interrupt mid-swap no longer skips rollback before the `finally` deletes the backups. The fix covers a third publisher (`_publish_ydp_bank`) beyond the two the record named.

**Fails-before (method B), one mutant per publisher.** The new tests `test_prepare_drumkit.DrumkitOutputPlanTests.test_publish_keyboard_interrupt_rolls_back_both_packages`, `test_prepare.GenericFamilyWholeBankPublicationTest.test_keyboard_interrupt_rolls_back_every_selected_file` and `test_prepare.YdpWholeBankPublicationTest.test_keyboard_interrupt_rolls_back_replacements` pass. Reverting each publisher alone to `except Exception` fails its own test on its snapshot assertion:
- drumkit: `b'new-flac' != b'old-flac'`;
- generic: `{'harp_C4.flac': b'new-flac'} != {'harp_C4.flac': b'old harp bank: harp_C4.flac', ...}`;
- YDP: `{... b'new-flac'} != {... b'old-ydpgrand_C2.flac', ...}`.
All restored; worktree clean.

**Coverage scan.** In `prepare.py`, `prepare_drumkit.py`, `fretnoise_bake.py`, `gen_crate_lib.py` and `regen_samples_table.py`, these three are the only functions that pair a backup/rmtree `finally` with an exception handler, and all three now use `BaseException` for rollback. The `except Exception` still present in the two `prepare.py` functions is the inner encode-failure cleanup, which runs before any file is moved aside. `fretnoise_bake.publish_fretnoise_bank` already caught `BaseException`.

**Repo gate.** On `56ba5184` the Python gate step passes ('Ran 284 tests ... OK'). The fix touches only `tools/`, which the cargo steps do not build; those were fully run on `1d87b00f` and `011738f6` earlier in this pass.

## Notes
