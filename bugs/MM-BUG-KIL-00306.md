# MM-BUG-KIL-00306 — drumkit2 velocity-split oracle pins too few boundaries and lacks the structural vel_hi invariant

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drumkit2 test oracles
- **Raised:** 2026-08-19T09:33:16Z
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
- **State history:** Open (2026-08-19T09:33:16Z, raised via `deltic bugs new`)

## Observation

`layer_for_velocity_respects_the_sfz_splits`
(`crates/ferrosintesis-samples-drumkit2/src/lib.rs:406-413`) pins only CRASH's
42/43 boundary, CHINA's outer edges (25→0, 102→4), SPLASH at one velocity, and the
last CRASH layer. Every interior split is unconstrained, and the crate never
asserts the structural `vel_hi` invariants its sibling enforces for every bank
(`crates/ferrosintesis-samples-drumkit/src/lib.rs:899-900`: last == 127, strictly
ascending).

Two mutations stay green across the whole workspace:

1. `CRASH.vel_hi` (`lib.rs:189`) `[42,85,127]` → `[42,120,127]`: the test's three
   CRASH probes (42→0, 43→1, 127→2) all still hold, while GM 49/57 hits at
   velocity 86..120 now play the middle-layer take instead of the hard take.
2. `CHINA.vel_hi` (`lib.rs:206`) `[25,51,76,101,127]` → `[25,51,40,101,127]`
   (non-ascending): `layer_for_velocity`'s `position(|&hi| v <= hi)` can then never
   return index 2, so all four `china_vl3_rr*` takes become unreachable at any
   velocity. The probes 25→0 and 102→4 still pass.

Nothing else covers this: the resolution and audio oracles iterate layer *indices*,
never velocities, and the only downstream velocity-layer test
(`crates/ferrosintesis/src/sampler.rs` `sampled_drum_velocity_selects_layer`) uses
a core-crate bank, not a kit2 bank. Expected: the SFZ-derived split table is pinned
on both sides of every boundary and structurally valid. Actual: interior bounds and
monotonicity are free. Current committed values are correct (checked against
PROVENANCE's SFZ-derived table); this is a false-green oracle defect, same class as
MM-BUG-KILN-00203.

## Fix

Assert both sides of every interior boundary (CRASH 85→1/86→2; CHINA 51→1, 52→2,
76→2, 77→3, 101→3, 102→4; SPLASH 0→0 and 127→0), and port the sibling's structural
loop over `BANKS` (`*vel_hi.last().unwrap() == 127` and
`vel_hi.windows(2).all(|w| w[0] < w[1])`). Prove each added assertion can fail by
applying the two mutations above before landing.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Estimated effort: Small.
