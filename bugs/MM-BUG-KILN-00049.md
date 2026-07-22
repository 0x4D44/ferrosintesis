# MM-BUG-KILN-00049 — the e-bow sustainer pins its hold level in the LOOP domain but is calibrated against an OUTPUT measurement, so any damper change breaks its pitch invariance (+12.9 dB at key 88)

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-22
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
- **State history:** Open (2026-07-22, raised by Claude Opus 4.8 (1M) — surfaced while fixing KILN-00042; it is the reason DRIVE_LEAD had to be excluded from that fix)

## Observation

**Symptom.** `DRIVE_LEAD` is the only preset carrying the e-bow sustainer (`sustain > 0`).
Its design claim, stated in `sus_headroom` (`crates/ferrosintesis/src/voices.rs`), is that
the hold level is **pitch-invariant by construction**:

> "PROPORTIONALLY supercritical — k = SUS_K_OVER × the loop's per-trip deficit at the
> fundamental… Keeping k/deficit constant pins the saturator's equilibrium amplitude at the
> SAME multiple of the knee L at every pitch — the hold level is calibrated by construction
> instead of trimmed at runtime."

The algebra holds in the loop domain. Loss per trip is `deficit·A`; the driver contributes
`k·l·tanh(A/l) → k·l` once saturated; equilibrium is therefore

```
deficit·A = k·l = SUS_K_OVER·deficit·l   ⟹   A_eq = SUS_K_OVER·l
```

— independent of `deficit`, hence of pitch. **But the oracles measure the rendered OUTPUT,
and the loop→output mapping is itself pitch-dependent** (body resonators, `out_lp`, pickup
RLC, and how many partials the loop is currently carrying). Nothing pins that half.

**Measured**, with the KILN-00042 damper hold enabled on `DRIVE_LEAD` (velocity 100,
seed 0xD8, held 8 s), held level relative to the note's own spoken reference:

| key | f | fc | deficit | knee `l` | held level rel-ref |
|---|---|---|---|---|---|
| 64 | 329.6 | 10734 | 0.00387 | 0.1129 | **−6.1 dB** |
| 70 | 466.2 | 16713 | 0.00323 | 0.1277 | −3.3 dB |
| 76 | 659.3 | 19845 | 0.00284 | 0.1137 | −1.6 dB |
| 82 | 932.3 | 19845 | 0.00277 | 0.1227 | +4.4 dB |
| 88 | 1318.5 | 19845 | 0.00304 | 0.0891 | **+12.9 dB** |

`deficit`, `k` and `l` are all near-constant across the register exactly as the design
intends — and the audible hold level still climbs **19 dB**. The design's invariant is real
but it is the wrong invariant, because it is not the quantity anyone hears.

**Expected.** Held level within the oracle's ±5 dB band at every pitch, per the design claim.

**Actual.** A 19 dB spread across two octaves; `sustain_holds_high_notes` fails at key 88.

**Reproduce.** On a build where `DRIVE_LEAD` is `DamperHold::Derived` (remove its opt-out
in `voices.rs`):

```
cargo test -p ferrosintesis --release -- sustain_holds_high_notes </dev/null
```

```
key 88: windows outside [-13.3, -3.3]: [(2, 8.03), (3, 9.79), (4, 10.79), (5, 11.40), (6, 11.78), (7, 12.02)]
```

## Root cause

Two halves of one calibration live in different domains and only one is pinned:

1. `sus_headroom` pins the **loop** equilibrium at `SUS_K_OVER × knee`, correctly and
   pitch-independently.
2. `SUS_HOLD_REF_OFFSET_DB` (in the test module) absorbs the **loop → output** mapping as a
   single measured scalar — "the crest-vs-RMS, the smoothed window-max envelope statistic,
   and the saturator equilibrium multiple" — with the tacit assumption that the mapping is
   flat enough in pitch for one number to cover it.

That assumption held while the damper's corner sat a fixed multiple above the fundamental.
Once the corner moves (as KILN-00042 makes it), the loop carries a different partial
structure at each pitch, the mapping tilts, and no single scalar can absorb it. The comment
on `SUS_HOLD_REF_OFFSET_DB` already records the constant being re-captured twice for exactly
this class of change ("the brighter damper shrinks the high-key loop deficit so the
SUS_K_MAX clamp no longer caps E6…") — but a re-capture only re-centres a spread, it cannot
remove one.

## Fix direction

Pin the invariant in the domain where it is claimed. Options, in preference order:

1. **Close the loop on the output.** Derive the knee `l` (or a per-note correction to it)
   from a measurement that already includes the loop→output mapping, rather than from the
   spoken-level reference alone.
2. **Model the mapping.** Make `SUS_HOLD_REF_OFFSET_DB` a function of pitch fitted against
   the same probe harness KILN-00042 uses, instead of a scalar. Cheaper, but it re-fits
   every time the damper law changes — which is what just went wrong.
3. **Bound the regime.** Cap how far the damper corner may sit above the fundamental so the
   loop's partial structure stays in the band the sustainer was calibrated for. Interacts
   with 00042's ceiling and would partly undo it.

**Oracle to add:** the existing `sustain_holds_high_notes` asserts a band per key; add an
explicit assertion that the *spread across keys* is small, so a future change that tilts the
mapping fails on the invariant itself rather than on whichever key happens to leave the band
first.

## Notes

- **Blocks MM-BUG-KILN-00042 for DRIVE_LEAD.** That preset is `DamperHold::Off` purely
  because of this. The cost is low — DRIVE_LEAD's sustainer already holds notes at constant
  level, so the f³ decay collapse 00042 fixes is masked there anyway — which is why the
  exclusion was the right call rather than a workaround.
- Above key ~76 the derived corner saturates the `sr * 0.45` clamp, so the loop is nearly
  undamped; that is where the mapping tilts hardest.
- Same underlying habit as MM-BUG-KILN-00048: a loop-internal quantity calibrated against an
  output-domain measurement. Worth fixing them with one another in mind.
