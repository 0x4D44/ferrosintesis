# MM-BUG-KILN-00091 — the default V3 kit is measurably weaker than legacy V1 on three velocity/attack behaviours

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** drums / kit voicing
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00054 by Claude Opus 4.8 (1M) while fixing it. 00054 was a coverage gap; extending those oracles to the default kit MEASURED this difference, which nobody had looked at before because no oracle rendered V3.) → Blocked (2026-07-26, GPT-5.6 Codex on KILN-Windows — the measurements cannot decide whether V3's softer kick attack and washier ride are the intended default voicing) → Closed (2026-07-26, Arthur accepted V3's softer coupled kick response and washier ride as intentional default-kit voicing; the existing per-kit oracles already verify all three selected contracts)

## Observation

Three behaviours that the legacy `Kit::V1` satisfies comfortably are satisfied only
marginally by `Kit::V3`, the engine's default. All three still hold **directionally** on
V3 — nothing is inverted — but the margins are much smaller, and the difference had never
been measured because the oracles guarding them rendered V1 only (MM-BUG-KILN-00054).

Measured with `render_drum_kit(key, vel, secs, kit)`, `samples: false`, seed 7:

| Behaviour | Key | V1 bound | V3 measured |
|-----------|-----|----------|-------------|
| Kick beater point superlinear (point ratio vs amplitude ratio) | 36 | > 1.3x | **1.128x** (18.04 vs 16.00) |
| Gain-normalised click grows with velocity | 36 | > 1.3x | **1.097x** (0.0753 vs 0.0686) |
| Ride ping over wash (early/late HF) | 51 | > 3.0x | **2.90x** (0.0947 vs 0.0327) |

The keys involved are exactly the ones V3 re-voices: the kick body band
(`drums.rs` kick voicing) and the `metal_plate` cymbals.

**Expected — unknown, and that is the question.** Either:

- V3's softer beater point, flatter velocity-to-click law and washier ride are the
  *intended* voicing, in which case the per-kit bounds now in the oracles are correct and
  this closes as working-as-intended; or
- the default kit has quietly lost attack definition relative to the kit it replaced, in
  which case it is a voicing regression on the kit every album but Slipstream renders
  with.

Numbers cannot settle it: all three are perceptual claims about attack character.

## Fix

**Needs ears — this box has none.** Route:

1. Arthur listens to kick 36 at v30 vs v120 and ride 51 on V3 against V1.
2. If V3 is right, close this and delete the "measured, not designed" caveats from the
   three oracles in `crates/ferrosintesis/src/drums.rs`, leaving the per-kit bounds as
   deliberate.
3. If V3 is wrong, the fix is in the V3 voicing, and the V3 bounds should then be raised
   to V1's — the oracles are already shaped to make that a one-constant change per kit.

**Do not** close this by relaxing V1's bounds to match V3, or by dropping V3 from those
oracles. Both would discard the only measurement anyone has of the difference.

## Notes

- The per-kit bounds landed with MM-BUG-KILN-00054 are deliberately annotated in-source as
  MEASURED rather than designed, and point here.
- Not a regression report: V3 has presumably always been like this. What changed on
  2026-07-24 is that anything measures it at all.
- Severity Low / Priority Could because nothing is broken or inverted — this is a
  voicing-intent question with a committed measurement attached.

## Blocker — 2026-07-26

Blocking owner: **Arthur**. The three directions are objectively present, but
their desired strength is a product/voicing decision. Raising the V3 thresholds
would change the default kit used by nearly every album; accepting the current
thresholds would deliberately preserve its softer kick and washier ride.

Unblock with dry mono, samples-off renders from exact baseline `623798a`, at
44.1 kHz with seed 7:

- GM drum key 36, velocities 30 and 120, 0.5 seconds, for both `Kit::V1` and
  `Kit::V3`;
- GM drum key 51, velocity 110, 2.0 seconds, for both `Kit::V1` and `Kit::V3`;
- audition each V1/V3 pair once at raw level and once body-level matched, so
  overall loudness does not masquerade as attack definition.

Return these exact inputs:

1. For kick beater superlinearity, choose **keep V3's measured 1.128×
   character** or **raise V3 to V1's >1.3× contract**.
2. For gain-normalised kick click, choose **keep V3's measured 1.097×
   character** or **raise V3 to V1's >1.3× contract**.
3. For ride ping-over-wash, choose **keep V3's measured 2.90× character** or
   **raise V3 to V1's >3.0× contract**.
4. Confirm whether the two kick decisions must move together or may be voiced
   independently.

If all current V3 values are intentional, the follow-up is documentation-only:
remove the “measured, not designed” caveats while retaining the per-kit bounds.
Any raised target requires a Build pass to revoice V3 and prove the selected
contract without changing unrelated drum keys.

## Decision — 2026-07-26

Arthur accepted the current V3 character:

- keep the `1.128×` beater-point response and `1.097×` gain-normalised click
  response together as one intentionally softer kick voicing;
- keep the `2.90×` ride ping-over-wash response as an intentionally washier
  ride;
- retain V1's stronger contracts independently rather than homogenising the
  two kits.

No audio implementation changed. The existing per-kit tests already verify
that every response moves in the designed direction and meets its selected
floor. The provisional “measured, not designed” comments were replaced with
the deliberate kit-specific contracts. This is therefore closed as
working-as-intended, not fixed by revoicing.
