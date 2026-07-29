# MM-BUG-KILN-00174 — Missing drum PCM lookup decodes and retains the full package

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drum-kit2 PCM API
- **Raised:** 2026-07-29
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260729T141553Z-p52900-n828035100-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00174-run-fix-20260729T141553Z-p52900-n828035100-c1
- **Owner base:** 37a9c4aa452aaf12674156276c04fe261093f4b8
- **Owner fingerprint:** -
- **Owner since:** 2026-07-29T14:15:53Z
- **Owner until:** 2026-07-29T16:15:53Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

The public exact-name PCM lookup initializes the full package cache before it
checks whether the requested name exists.

At
`D:\worktrees\midi-music\20260729-REV-CLA@KILN-code-review-141004\crates\ferrosintesis-samples-drumkit2\src\lib.rs:286`,
`pcm(name)` calls `decoded_samples()` on line 287, then searches `SAMPLES` and
returns `None` for a miss on lines 288–291. `pcm_by_index()` has the same ordering
for an out-of-range index at lines 294–298. `decoded_samples()` converts all 48
WAVs at lines 315–317.

The committed inventory totals 10,619,904 file bytes, of which 10,617,792 bytes
are PCM data. A typo, availability probe, or out-of-range diagnostic call
therefore performs the whole conversion and permanently retains roughly
10.62 MB before returning `None`.

Expected: an absent name or invalid index returns `None` without initializing
unrelated PCM.

Actual: lookup failure has the same package-wide startup and residency cost as a
valid first sample. Package-wide decode for a valid take and explicit `prewarm()`
remain intentional; this report covers only the miss path. The ordering and byte
count were confirmed statically; decode time and peak RSS were not measured.

## Fix

Resolve and validate the name/index before calling `decoded_samples()`. Preserve
the intentional eager decode after a valid lookup.

Add a pristine-process regression proving missing-name and out-of-range lookups
leave `pcm_cache_initializations()` at zero, then prove a valid lookup initializes
the cache once.

## Notes

No existing bug or open requirement covers this public API miss cost. Estimated
effort: Small.
