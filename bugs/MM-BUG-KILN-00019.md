# MM-BUG-KILN-00019 — Per-program loudness match is damped 0.70×; residuals remain and older album mixes were tuned to the old balance

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** engine
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

The SC-55-referenced per-program trim (`PROGRAM_TRIM_DB`, `crates/ferrosintesis/
src/engine.rs:~441`) is deliberately damped to 0.70× strength (`wrk_docs/
2026.07.17 - CR - instrument level audit + SC-55 trim.md`), leaving ~1–2.5 dB
family residuals by design (Ensemble +2.5, Organ −1.4, Pipe −1.6…). A knock-on:
sections/choir now sit ~+5 dB louder than when several album mixes were hand-tuned
to the *old* balance, so a few album mixes may want a CC7/CC11 re-touch on
re-listen.

## Fix

Optional second pass to tighten the 0.70× damping toward a closer SC-55 match
(after Arthur listens), paired with a CC7/CC11 re-touch audit of the album mixes
that were tuned to the old balance. Both are ear-in-the-loop calls.

## Notes

- Explicitly flagged as a follow-up in the level-audit CR — not a defect so much as
  a deliberate stopping point awaiting a listening pass.
- Any trim change is level-only/timbre-neutral but still triggers the master
  bus-glue by ~0.5 dB (benign) → render-diff expected on trimmed programs.
