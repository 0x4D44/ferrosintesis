# MM-BUG-KILN-00091 — the default V3 kit is measurably weaker than legacy V1 on three velocity/attack behaviours

- **State:** Open
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
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00054 by Claude Opus 4.8 (1M)
  while fixing it. 00054 was a coverage gap; extending those oracles to the default kit
  MEASURED this difference, which nobody had looked at before because no oracle rendered V3.)

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
