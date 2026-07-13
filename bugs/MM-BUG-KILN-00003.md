# MM-BUG-KILN-00003 — Wind voice internal vibrato runs at 1/16 speed (labelled 5 Hz renders at ~0.31 Hz)

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-11
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
- **State history:** Open (2026-07-11, raised by Claude Opus 4.8) → Fixed (2026-07-12, `48a7e71`, verified 2026-07-13 by Claude Opus 4.8)

## Observation

The `Wind` voice (GM pipe family, programs 72–79: flute, piccolo, recorder, pan
flute, blown bottle, shakuhachi, whistle, ocarina) has an always-on internal
expressive vibrato that is meant to give every sustained note a ~5 Hz breath.
It renders ~16× too slow — effectively inert — so sustained pipe notes sit
dead-flat unless the channel also authors CC1.

**Root cause (confirmed in code, `crates/ferrosintesis/src/voices.rs`):** the
vibrato LFO's phase increment is built for the full sample rate —
`voices.rs:4280`: `vib: Sine::new(vibr.0, sr, 0.0)` — but the render loop only
advances the LFO inside the control-rate gate `if self.t.is_multiple_of(CTRL)`
(`voices.rs:4295`, `CTRL = 16` at `voices.rs:85`). Stepping a full-rate LFO once
per 16 samples divides its effective frequency by 16: the flute preset's labelled
`vibr.0 = 5.0 Hz` renders at 5.0/16 = **~0.3125 Hz**; the whistle preset's 5.5 Hz
renders at ~0.34 Hz.

**This is a known, already-fixed class of bug — `Wind` is the lone holdout.** The
`Reed` voice fixes exactly this, with an explanatory comment
(`voices.rs:5379–5382`: "the LFO is ticked once per CTRL samples (control rate),
so build it at sr/CTRL — else `vib.next()` advances CTRL× too slow (a labelled
5 Hz sax vibrato would drift at ~0.3 Hz)"), and `Bowed` does the same
(`voices.rs:4521`, `sr / CTRL as f32`). `Wind` never got the fix.

**Confirmed three ways:** (1) code inspection (the `sr` vs `sr/CTRL` discrepancy
against the Reed/Bowed precedents); (2) empirical measurement in the woodwind
audit (rendered pipe notes showed a ~0.31 Hz modulation, not 5 Hz); (3) an
independent critic agent reached the same reading.

**Scope caveat:** the *engine-level* CC1 vibrato path is separate and works
correctly (72–79 are in `vibrato_family`, `engine.rs:85`; applied via
`set_pitch`). Only the `Wind` voice's built-in, controller-free vibrato is dead.
So channels that author CC1 still breathe; channels that rely on the intended
always-on vibrato do not.

**Expected:** a sustained pipe note exhibits ~5 Hz pitch vibrato (after the
per-preset delay) with no controller input, matching the `Reed`/`Bowed` voices.
**Actual:** the modulation is ~0.31 Hz — perceptually a slow drift, not vibrato.

**Repro:** render a held pipe note (e.g. program 73 flute, key 72, sustained
~2 s) with `ferrosintesis`, no CC1, and measure the pitch-modulation rate
(Goertzel/FFT on the instantaneous pitch track) — it sits near 0.31 Hz rather
than 5 Hz.

## Fix

**Landed in `48a7e71`** ("Stage 1 — pipe family (GM 72-79) WindPreset rework",
v0.15.2, 2026-07-12), exactly as predicted: the `Wind` vibrato LFO is now built at
the control rate instead of the full sample rate —
`vib: Sine::new(vibr.0 * (1.0 + 0.08 * rng.white()), sr / CTRL as f32, 0.0)` —
so the labelled ~5 Hz breath renders at ~5 Hz, matching the Reed/Bowed precedent.
The fix was applied uniformly across all eight pipe presets (72–79) via the shared
`from_preset` constructor, so the whole family is corrected, not just the flute.
A follow-up refactor (`65a7a7e`, OpenAI Codex) centralised the `sr / CTRL`
construction into a single `control_lfo(rate, jitter, rng, sr)` helper (no
behaviour change) so a future control-rate voice cannot reintroduce the bug —
the exact "one place for the invariant" guard this bug called for.

Because the fix landed inside the pipe-family stage, the catalogue-wide render
obligation it noted was absorbed by that stage's work. (Since then the repo moved
to render-on-demand `.opus`, so there is no committed audio to refresh — anyone
who renders now simply hears the corrected vibrato.)

### Verification summary (2026-07-13, Claude Opus 4.8 — independent of the fix)

Regression coverage added with the fix and green on trunk `16e3017`:
- `voices::tests::wd_o7_builtin_vibrato_rate_is_about_5hz` — the direct
  MM-BUG-KILN-00003 oracle. Its failure message reads *"0.31 Hz => the CTRL-rate
  bug is back"*. **Observed on trunk: flute 4.75 Hz, shakuhachi 4.25 Hz** (both in
  the intended band; the old broken value was ~0.31 Hz). PASS.
- `voices::tests::control_lfo_advances_at_the_requested_rate` — unit test on the
  centralised helper. PASS.

Root cause understood and confirmed corrected (full-rate LFO stepped once per
`CTRL` samples → built at `sr/CTRL`). **Two-eyes note:** the fix (`48a7e71`) is
attributed to Claude Opus 4.8, the same model as this verifier; independence rests
on the objective green regression oracle and on Codex's independent engagement
with the same code (`65a7a7e`). Ready to move to **Closed** on that basis, or after
a cross-model sign-off if strict actor-independence is preferred.

## Notes

Discovered during the 2026-07-11 woodwind audit and its follow-up synth-wide
design investigation. Full evidence and the surrounding pipe-family rework live
in the HLD above.
