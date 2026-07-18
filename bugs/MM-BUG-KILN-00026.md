# MM-BUG-KILN-00026 — GM42/43 brightness is guarded by the wrong struct: the brightness oracles render `Bowed::new` (CC0 alt-bank), not the shipping `BowedString`, and assert no direction — a recurrence of MM-BUG-KILN-00004's trap

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 via overnight code-review pass, deep-review workflow)

## Observation

Commit `41d2bc8` ("deepen GM42/43 vibrato, fix brightness, de-chorus solo strings")
has as one headline the correction of a spectral inversion: the contrabass (GM43) was
rendering ~55% **brighter** than the cello (GM42), backwards for the family. The fix
is pure parameter edits inside `BowedString::new`
(`crates/ferrosintesis/src/voices.rs:7662-7671`: cello `out_lp` 2100→2600, contrabass
`refl_sustain` 2600→2200 and a new `out_lp` 1800). The commit message states oracles
were "recalibrated to the intended new reference", but **no oracle observes the voice
that actually ships**, so the headline fix is unverified and a reversed-ordering
regression passes the whole suite green.

**The wrong-struct gap (independently confirmed by reading the source):**

- `make()` routes GM `42 | 43` to `Box::new(BowedString::new(...))` as the DEFAULT
  bank — `voices.rs:11161-11162`. `BowedString` is the shipping voice.
- The brightness/body oracles render through `render_default_bowed`
  (`voices.rs:16248-16254`), which builds `Bowed::new(program, key, vel, sr, seed)`
  — `voices.rs:16250`. `Bowed` is a **different struct**, the CC0 alt-bank preset
  (see altbank.rs), which the commit never touched. So
  `default_bowed_bodies_and_onsets_are_distinct` (`voices.rs:16272`) and
  `default_bowed_body_bands_and_fiddle_identity` (`voices.rs:16317`) measure a voice
  GM42/43 do not render through.

**The no-direction gap:** even on the right struct, the one brightness assertion that
touches 42/43 (`voices.rs:16285-16294`) computes
`relative = (pair[0]/pair[1]).max(pair[1]/pair[0])` and asserts only `relative >= 1.05`
— it checks that adjacent programs *differ* by ≥5%, never *which* is brighter. A full
cello↔contrabass reversal passes it. The `out_lp` levers are post-loop and
tuning-neutral (`voices.rs:7650`), so reverting the brightness edits leaves the tuning
oracle (`bowedstring_gm43_pitch_bounded`, engine.rs) and every other test green.

**This is the exact trap MM-BUG-KILN-00004 documented** ("the guarding oracle tests
the wrong voice"). That bug (Closed 2026-07-18) fixed the 1/16-speed vibrato AND
migrated the *vibrato* oracle `default_bowed_natural_vibrato_runs_at_named_rate` onto
`make()` so it exercises the shipped `BowedString`. The **brightness** oracles were
left on `Bowed::new` — so the class was closed on one oracle and remained open on
another, and today's brightness commit walked straight into it. The repo's oracle-first
doctrine treats green oracles as the definition of done, so a false-green/absent guard
for a shipped intent is a genuine verification defect (this is why 00004 was filed High
for the guard, not the audible symptom).

- **Expected (oracle-first):** an oracle renders GM42/43 through `make()` and asserts
  the cello is spectrally brighter than the contrabass; it fails if the
  `out_lp`/`refl_sustain` brightness edits are reverted or over-corrected.
- **Actual:** the brightness oracles measure `Bowed::new` and assert only a
  direction-agnostic ≥5% difference; a reversed 42/43 brightness ordering ships green.

No current audible defect — the shipped `BowedString` is correct today. The risk is a
future silent timbre regression (renders are git-ignored build output, so nothing in
the committed source would flag it).

## Fix

Add a brightness-ordering oracle that renders GM42 and GM43 **through `make()`** (as
`bowed_string_tuning_is_pitch_independent` already does) at a pitch inside both
compasses (cello 36–76, contrabass 28–55; e.g. key 43 or 48; samples off so the
waveguide body is measured directly). Compute an HF fraction
`hp_rms(settled_sustain, sr, ~2200-2500) / rms(settled_sustain).max(1e-9)` for each
and assert the cello's clearly exceeds the contrabass's (e.g. `h42 > h43 * 1.15`, or
`h43 < h42 * 0.85`), with a message naming the backwards +55% inversion. Model it on
the vibrato oracle migrated off `Bowed` in the 00004 fix. It must be red if the
`out_lp`/`refl_sustain` edits are reverted, green as shipped.

Consider, while there, whether `render_default_bowed` / the two body oracles should
also move to `make()` for 42/43 (they currently give false coverage for those two
programs) — but scope carefully: those oracles also cover GM40/41/110, which do use
the `Bowed`/model path.

## Notes

- Found by the overnight code-review pass (`crates/ferrosintesis/` area) via the
  `deep-review` workflow (test-coverage + devil's-advocate lenses, both survived the
  three-skeptic verify); see `wrk_docs/2026.07.18 - CR - overnight review pass
  (ferrosintesis core).md`.
- Verify skeptics corrected the finder severity High → **Medium**: no live defect, but
  a documented named-trap recurrence that defeats the oracle-first definition-of-done
  for the very change the commit is about.
- Related, lower-severity oracle-coverage gaps around the same commit are documented in
  the CR report (not separately filed): the GM43 vibrato-depth floor was widened not
  raised so a bass-only re-shallowing passes (engine.rs:5295); GM42 has no cents-depth
  oracle (engine.rs:5282; partially covered by the rate oracle); the GM42/43 chorus
  de-send is unpinned (engine.rs:390); and a stale comment claims the contrabass
  `out_lp` is `None` while the code sets 1800 Hz (voices.rs:7650-7651).
