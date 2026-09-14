# MM-BUG-CRU-00077 — Sample bank publishers delete their backups on KeyboardInterrupt instead of rolling back

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** tools/ferrosintesis-samples
- **Raised:** 2026-09-14T21:53:09Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T225328Z-3d72a71d
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00077-run-verify-20260914T225328Z-3d72a71d
- **Owner base:** a967b394c04ab92ed0b326f2ff9d0d5f96a56b6c
- **Owner fingerprint:** sha256:39ed016ec8217b31e689b510fb409eeed5ee332b41bf88323eba1934906cb98a
- **Owner since:** 2026-09-14T22:53:28Z
- **Owner until:** 2026-09-15T00:53:28Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-14T21:53:09Z, raised via `deltic bugs new --land` model=claude-opus-5) -> Fixed (2026-09-14T22:19:58Z, deltic:auto role=fix run=fix-20260914T221446Z-bb4230f6 branch=task/bug-MM-BUG-CRU-00077-run-fix-20260914T221446Z-bb4230f6 code=b62fffadedd17cbd75dfa37f6173bd3f4c769f5d gate=manual)

## Observation

Split from MM-BUG-CRU-00071 at independent verification (2026-09-14, trunk 011738f6). tools/ferrosintesis-samples/prepare_drumkit.py publish_staged and tools/ferrosintesis-samples/prepare.py _publish_staged_flac_bank move each existing FLAC into a backup directory, then swap the new files in. Rollback runs only in 'except Exception', but the 'finally' removes the backup directories whenever cleanup_backups / cleanup_backup is still True (read in both functions). A KeyboardInterrupt or SystemExit raised during the swap therefore skips the rollback, leaves the flag True, and the finally deletes the moved-aside originals while the bank is half published. A verifier probe that interrupted the second swap left the drumkit core.flac replaced by the new take and the drumkit2 accent.flac gone; the same probe on _publish_staged_flac_bank left a.flac new and b.flac gone. Expected: an interrupted publish restores the previous bank, or at least keeps its backups. Actual: the originals are deleted and the bank is mixed. The committed FLACs can be restored from git, so the loss is limited to the working tree. fretnoise_bake.publish_fretnoise_bank catches BaseException and is not affected (read, not probed). The gong, honky-tonk and bagpipe bakes fixed under MM-BUG-CRU-00070 publish through _publish_staged_flac_bank and share this gap.

Evidence fingerprint: `manual:v1:sample-bank-publishers-delete-their-backups-on--aca7c358e19ce191`


## Fix

<unfixed — raised only>

## Notes
