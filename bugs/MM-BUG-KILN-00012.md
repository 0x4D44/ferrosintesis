# MM-BUG-KILN-00012 — Contrabass wolf-band (keys 46–50): the waveguide mode-locks to 3·f0

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** voices
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

The stick-slip waveguide contrabass (`BowedString`, `crates/ferrosintesis/src/
voices.rs:~7503`, dispatched for 42|43) mode-locks to 3·f0 across keys 46–50,
producing a "wolf note" — a known pre-existing pitch/timbre defect on the
harmonic-foundation instrument. It was explicitly parked as its own slice in the
round-3 roadmap (`wrk_docs/2026.07.16 - PLN - voice-quality round 3 ... .md`,
Solo-strings section + Stage 5), after the general contrabass darkening shipped.

## Fix

Diagnose the friction-table / loop-gain interaction that lets the third mode
capture the fundamental in that register, and detune or damp the offending mode
(roadmap parks this as a dedicated slice, not part of the darkening work).

## Notes

- Contrabass darkening (refl_sustain, out_lp, body_f) already landed; this is the
  residual.
- Cello 42 is on the same waveguide — verify a fix does not regress it.
