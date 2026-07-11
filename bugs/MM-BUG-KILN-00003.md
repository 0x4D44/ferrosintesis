# MM-BUG-KILN-00003 — Wind voice internal vibrato runs at 1/16 speed (labelled 5 Hz renders at ~0.31 Hz)

- **State:** Open
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
- **State history:** Open (2026-07-11, raised by Claude Opus 4.8)

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

Pending. The fix is a one-token change mirroring the Reed/Bowed precedent:
`voices.rs:4280` → `vib: Sine::new(vibr.0, sr / CTRL as f32, 0.0)`.

It is **default-on** (changes the sound of every album using programs 72–79 —
34 tracks across 12 albums, 32 committed `.opus`), so it carries a render-diff
inventory + opus-refresh obligation and must land inside the pipe-family stage,
not as a standalone edit (fixing it alone would pay the same catalogue-wide
refresh twice). It is scheduled as **Stage 1** of
`wrk_docs/2026.07.11 - HLD - woodwind and synthwide LA synthesis comprehensive
design.md` (§7.1.6). Regression coverage: a `Wind`-vibrato-rate oracle asserting
~5 Hz (the analogue of the existing Reed vibrato oracle), added with the fix.

## Notes

Discovered during the 2026-07-11 woodwind audit and its follow-up synth-wide
design investigation. Full evidence and the surrounding pipe-family rework live
in the HLD above.
