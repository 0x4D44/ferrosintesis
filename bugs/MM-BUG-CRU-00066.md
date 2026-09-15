# MM-BUG-CRU-00066 — Five more packaged one-shots start far from silence and pass the continuity sweep

- **State:** Blocked
- **Priority:** Should
- **Severity:** Low
- **Area:** sample assets / onset continuity
- **Raised:** 2026-09-13T19:23:43Z
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
- **State history:** Open (2026-09-13T19:23:43Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:20:32Z, deltic:auto role=fix run=fix-20260913T205331Z-55b12432 branch=task/bug-MM-BUG-CRU-00066-run-fix-20260913T205331Z-55b12432 code=4f4f6d9e30eb903612b828e84352fd56e32830c3 gate=manual) -> Open (2026-09-14T22:56:40Z, independent verify by Claude Opus 5 on trunk 56ba5184: the rebake only zeroed frame 0, so steel_E4 and cellosolo_A3_f still open with a larger step (2138 and 2243 LSB), and the frame-zero oracle passes any one-shot whose first sample is zero) -> Blocked (2026-09-15T00:14:07Z, fix drain by Claude Opus 5 on trunk a8caf6f0: the requested opening-slope bound cannot separate the flagged files from ordinary sharp attacks (tubular_*, cellosolo_A4_p), so it needs Arthur's listening/design decision; evidence in Notes)

## Observation

Residual split at independent verification of MM-BUG-KILN-00215 (2026-09-13, trunk 8b6a6f86). The dulcimer fix (24807679) rebaked two assets and added a dulcimer-only frame-zero test, but the general packaged-onset sweep still lets a large attack mask a frame-zero step, as the record itself noted. A decode census of every packaged one-shot (1015 files, clavinet excluded) found frame-zero values far from silence in: headroom_C4_pp (-1235), headroom_F#3_pp (-1087), orchestral steel_E4 (-1402), strings cellosolo_A3_f (+1882), strings cellosolo_C4_f (+1654). All pass the general sweep and none is in any bug record. They end at silence, so they look like one-shots rather than loops. Expected: packaged one-shots enter from silence, and a general frame-zero oracle covers every bank.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `81252a3e` (verifier worker) and `56ba5184` (lead) by agents other than the fixer (fix `4f4f6d9e`). **Reopened.**

**What the fix gets right.** Frame zero of all five named files is now 0: `headroom_C4_pp` -1235 -> 0, `headroom_F#3_pp` -1087 -> 0, `steel_E4` -1402 -> 0, `cellosolo_A3_f` +1882 -> 0, `cellosolo_C4_f` +1654 -> 0. `test_every_packaged_bank_starts_without_a_discontinuity` is a general sweep over every `crates/*/samples` bank except clavinet, and it passes. Putting the five pre-fix FLACs back fails it, naming exactly those five files.

**Why reopened.** The record expects packaged one-shots to enter from silence. For two of the five files they still do not, and the opening jump got larger. The lead decoded frames 0-3 with `prepare.read_wav` at `4f4f6d9e^` and at trunk:
- `steel_E4`: [-1402, -2138, -3279, -2534] -> [0, -2138, -3279, -2534]. Only frame 0 changed, so the largest opening step grew from 1402 to 2138 LSB.
- `cellosolo_A3_f`: [1882, 3521, 4003, 4455] -> [0, 1760, 4003, 4455]. The largest opening step grew from 1882 to 2243 LSB.
- `headroom_C4_pp` did improve: [-1235, -1285, -1334, -1359] -> [0, -428, -889, -1359], a largest step of 470.
The worker measured the other two as improved too: `headroom_F#3_pp` 1087 -> 607 and `cellosolo_C4_f` 1727 -> 1205.

**The oracle cannot see this.** The one-shot check bounds only sample 0 against an absolute 3-LSB limit. Driven through the test's own `_onset_continuity` / `_onset_limit`, a one-shot starting [0.8, 0.8, ...] is flagged, but [0.0, 0.8, ...] gives step 0.00000 and passes. Zeroing the first sample therefore satisfies it whatever follows.

**To close.** Bound the opening slope over the first N samples from silence (not just sample 0), confirm that oracle flags the current `steel_E4` and `cellosolo_A3_f`, and re-fade those two files properly.

**Repo gate.** On `56ba5184` the Python gate step passes ('Ran 284 tests ... OK'). The cargo steps were fully run on `1d87b00f` and `011738f6` earlier in this pass.

## Notes

### Blocked (2026-09-15, Claude Opus 5, fix drain) — needs a listening/design decision

**Missing input:** Arthur's call on what opening slope a tightly trimmed one-shot may
have, and whether the attack-preservation contract in `declick_fade_in` may be relaxed
to meet it. No oracle available to an agent can settle this; it needs ears.

**Why a fixer cannot just pick a bound (observed, on trunk `a8caf6f0`):**
- The verifier's close criterion is "bound the opening slope over the first N samples
  from silence". A decode of all 994 packaged one-shots shows no gap between the flagged
  openings and ordinary sharp attacks. `steel_E4` opens `[0, -2138, -3279, -2534]` and
  `cellosolo_A3_f` opens `[0, 1760, 4003, 4455]`. But `tubular_G4` opens
  `[0, 198, 1827, 3542, 5550, 8830]` and `cellosolo_A4_p` opens `[0, 974, 3162, 4113]`.
  Neither of those is in any record, and both are at least as steep by N = 3-6.
- The two named files are not the worst. Worse zero-lead openings include
  `eastpick_E3` (first step 3689), `cellosolo_C5_f` (3331), `pickbass_F#1` (1709),
  `cellosolo_A2_f` (1795) and `dulcimer_F#4` (1793). A fix that re-fades only the two
  named files would repeat the hand-maintained-list defect CLAUDE.md warns about.
- Four packaged-side oracle shapes were tried, and each failed to separate the defect from
  real attacks: the frame-zero bound (defeated by zeroing frame 0), steps relative to the
  first 10 ms of motion (`steel_E4` passes, because its 2138 step is ordinary for a pick
  attack), a ramp-scaled step bound (flags quiet, well-faded files such as
  `gong_ageng_soft`), and an amplitude ramp (overlaps `tubular_*`).
- A source-side rule, "the de-click ramp may never step further than the jump it removes
  or the source's own motion at that sample", was simulated on the 23 zero-lead sources
  cached locally. It softens `steel_E4` (first step 2139 -> 535) and `cellosolo_A3_f`,
  but leaves `dulcimer_F#4` (1793) and `eastpick_E2` (1897) unchanged. It also cannot be
  checked from the packaged file alone. Most other affected sources (`cellosolo_*`,
  `pickbass`, `steel_E2`) are not cached, so any rule change also means a network
  re-fetch and a multi-family rebake.

**To unblock:** decide (a) the acceptable opening, as a slope or fade-length floor, for
sources with less than 2 ms of lead-in, and (b) whether `test_fade_in_never_exceeds_available_lead_in`
and `test_fade_in_cap_actually_bites_on_the_measured_steel_geometry` may give up attack
energy to meet it. Then reopen with `deltic bugs reopen`.
