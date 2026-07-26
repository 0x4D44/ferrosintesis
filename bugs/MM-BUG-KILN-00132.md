# MM-BUG-KILN-00132 — Gong provenance oracle pins the velocity boundary as a literal, so it can drift again

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** testing / provenance
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** The oracle added to keep the gong provenance honest pins the boundary as a LITERAL string, so the documented velocity and the shipped velocity can drift apart again while it stays green.

`crates/ferrosintesis/src/sampler.rs:5065` asserts:

    provenance.contains("hard switch at velocity 84")

but the shipped boundary is `const GONG_LOUD_VEL: u8 = 84;` (`sampler.rs:4675`), consumed by `gong_layer` at `:4694`. The two `ptr::eq` clauses in the same test correctly derive from the constant (`GONG_LOUD_VEL - 1` and `GONG_LOUD_VEL`), so they follow any change; only the documentation clause does not.

**Reproduced, not inferred.** On this tree I changed `GONG_LOUD_VEL` to 90, left `crates/ferrosintesis-samples-gong/PROVENANCE.md` untouched (still saying "hard switch at velocity 84"), and ran the test:

    cargo test -p ferrosintesis --locked -- gong_provenance_describes_the_shipped_velocity_boundary
    test sampler::tests::gong_provenance_describes_the_shipped_velocity_boundary ... ok

Green, with the packaged provenance now describing a boundary the synth does not use. The constant was restored afterwards.

**Expected.** Moving the shipped boundary turns the oracle red until the packaged provenance is updated to match.

**Actual.** Only a boundary move to a velocity that also removes the substring "hard switch at velocity 84" would be caught, which is no part of the change.

**Provenance.** Split out of MM-BUG-KILN-00129 during its independent two-eyes verification. That bug's reported observation is genuinely fixed - the false "velocity-crossfades between soft and loud" claim is gone, the wording now states the hard switch and preserves the comb-filter rationale, and reintroducing the crossfade sentence does turn the oracle red. This is the residual half of its own fix direction, which asked for the boundary in the oracle "so the corrected statement remains true".

**Fix direction.** Build the expected string from the constant, matching the pattern this repo already uses for exactly this job: MM-BUG-KILN-00122's documentation guard derives its selector with `format!("CC0={slot}")` from the shipped dispatch (`crates/ferrosintesis/src/altbank.rs:1342`). Here that is:

    provenance.contains(&format!("hard switch at velocity {GONG_LOUD_VEL}"))

and the same for the "soft through velocity {GONG_LOUD_VEL - 1}" clause the provenance also states. Keep the negative `velocity-crossfades` clause as is - it is already correct.

Estimated effort: Extra small.

## Fix

<unfixed — raised only>

## Notes
