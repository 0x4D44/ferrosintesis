# MM-REQ-CRUCIBLE-00007 — Centralize sampled-drum and tom descriptors

- **State:** Draft
- **Priority:** Could
- **Area:** ferrosintesis / drum routing metadata
- **Raised:** 2026-07-31
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-31, raised via `deltic reqs new` model=gpt-5.6-sol@xhigh)

## Statement

The system must derive sampled-drum routing, level, repitch, jitter, and hybrid modeled-tom parameters from one typed descriptor set, so a routed key cannot lack a level and modeled/sample tom pitches cannot drift between tables.

## Notes

Current metadata is internally consistent, so this is technical debt rather
than a live defect:

- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\drums.rs:1383-1395`
  duplicates the high-tom pitch, decay, noise, lifetime, and gain values from
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\drums.rs:1874-1902`
  and explicitly says to keep the two mappings synchronized.
- Sample playback repeats all six tom pitches at
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\sampler.rs:5099-5109`.
- Sample routing and per-key levels are separate key sets at
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\sampler.rs:4831-4853`
  and
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\sampler.rs:5099-5128`.
  A future routed key omitted from `DRUM_LEVEL` reaches the `unwrap` at line 5128.
- Two rendered tom tests restate the ladder again at
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\drums.rs:3151-3175`
  and
  `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-014814\crates\ferrosintesis\src\drums.rs:3200-3222`.

Gate 1 should define an oracle that derives the routed sampled-key set from the
descriptor, proves each key has a level without an `unwrap`, and iterates the
same tom descriptors for modeled, sampled, and hybrid pitch checks. Because
this refactor touches audio routing, the implementation must preserve current
renders unless a separate voicing change is explicitly approved.

No open requirement or bug covers this runtime descriptor split.
