# MM-BUG-CRU-00078 — drumkit2 velocity-split oracle still pins CHINA's first boundary on one side only

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-samples-drumkit2
- **Raised:** 2026-09-14T22:58:47Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260915T001713Z-6be1fb97
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00078-run-fix-20260915T001713Z-6be1fb97
- **Owner base:** c5b9aa6ca36333c85411d2a76ace081a898f7a1d
- **Owner fingerprint:** -
- **Owner since:** 2026-09-15T00:17:13Z
- **Owner until:** 2026-09-15T02:17:13Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-14T22:58:47Z, raised via `deltic bugs new --land` model=claude-opus-5)

## Observation

Split from MM-BUG-KIL-00306 at independent verification (2026-09-14, trunks 81252a3e and 56ba5184). The fix (091b98f8) pins every interior velocity boundary the record listed on both sides and adds the structural vel_hi invariants (last == 127, strictly ascending). CHINA's first boundary is the exception: tests::layer_for_velocity_respects_the_sfz_splits in crates/ferrosintesis-samples-drumkit2/src/lib.rs probes velocity 25 but never asserts CHINA.layer_for_velocity(26) == 1. Observed: changing CHINA.vel_hi from [25, 51, 76, 101, 127] to [30, 51, 76, 101, 127] keeps the list ascending and ending at 127, and 'cargo test -p ferrosintesis-samples-drumkit2 --locked --lib' stays green (11 passed, 0 failed, 1 ignored). With that table, velocities 26-30 would play the softest china take instead of layer 2. Expected: the SFZ-derived split table is pinned on both sides of every boundary, as MM-BUG-KIL-00306 required. Actual: one boundary is free. The committed values are correct today; this is a false-green oracle gap. The record's own boundary list also omitted this boundary.

Evidence fingerprint: `manual:v1:drumkit2-velocity-split-oracle-still-pins-china-1c39f7feec758add`


## Fix

<unfixed — raised only>

## Notes
