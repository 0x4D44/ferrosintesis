# MM-BUG-CRUCIBLE-00023 — Failed core drum PCM lookups initialize the entire cache

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / core drum-kit PCM API
- **Raised:** 2026-08-11T08:30:10Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T120005Z-p20964-n399449000-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00023-run-fix-20260815T120005Z-p20964-n399449000-c1
- **Owner base:** a907b969af6a0ffbaaf090c84851b05c41b8beb1
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T12:00:05Z
- **Owner until:** 2026-08-15T14:00:05Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-11T08:30:10Z, raised via `deltic bugs new`)

## Observation

The public core drum-kit PCM miss paths initialize the package-wide cache before
they determine that the requested take does not exist.

At
`D:\worktrees\ferrosintesis\20260811-REV-MM-CDX@CRUCIBLE-code-review-083323\crates\ferrosintesis-samples-drumkit\src\lib.rs:751`,
`pcm(name)` calls `decoded_samples()` on line 752, then searches `SAMPLES` and
returns `None` on lines 753-756. `pcm_by_index(index)` repeats the ordering at
lines 761-762. `decoded_samples()` converts all 128 WAVs at lines 780-782.

The committed inventory contains 9,627,358 PCM data bytes. A typo, availability
probe, or out-of-range diagnostic therefore converts and permanently retains the
whole cache before returning `None`.

Expected: an absent name or invalid index returns `None` while `PCM_CACHE`
remains cold.

Actual: lookup failure has the same package-wide initialization and residency
cost as a valid first take. Package-wide decode for a valid take and explicit
`prewarm()` remain intentional; this report covers only the miss path. The
ordering and byte count were confirmed statically. Decode time and peak RSS were
not measured because this was a read-only review pass.

## Fix

Resolve and validate the name or index before calling `decoded_samples()`.
Preserve the intentional eager decode after a valid lookup.

Port the pristine-process regression from
`D:\worktrees\ferrosintesis\20260811-REV-MM-CDX@CRUCIBLE-code-review-083323\crates\ferrosintesis-samples-drumkit2\src\lib.rs:401`:
prove missing-name and out-of-range lookups leave
`pcm_cache_initializations()` at zero, then prove a valid lookup initializes the
cache once.

## Notes

Closed `MM-BUG-KILN-00174` fixed the same ordering defect in the companion
`ferrosintesis-samples-drumkit2` crate only. Its implementation at
`D:\worktrees\ferrosintesis\20260811-REV-MM-CDX@CRUCIBLE-code-review-083323\crates\ferrosintesis-samples-drumkit2\src\lib.rs:226`
validates both miss paths before touching the cache. The core crate retains the
pre-fix ordering and has no equivalent regression. Estimated effort: Small.
