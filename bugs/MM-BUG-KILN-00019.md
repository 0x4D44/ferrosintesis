# MM-BUG-KILN-00019 — Per-program loudness match is damped 0.70×; residuals remain and older album mixes were tuned to the old balance

- **State:** Blocked
- **Priority:** Should
- **Severity:** Medium
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Blocked (2026-07-25, Codex GPT-5.6-Sol; current balance spread matches the reference modules, while changing the 0.70 damping/±6 dB clamp and retouching album controllers require Arthur's listening decision)

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

## Note (2026-07-25, re-ranked)

Re-ranked Could/Low -> Should/Medium. Not because the 0.70x damping is wrong — a
control measurement on 2026-07-25 found ferrosintesis's program-to-program spread
statistically indistinguishable from the reference modules' own (within +/-1 dB of
own median: ferro 11-16%, SC-55 14%, S-YXG50 14%), so the residual is not a defect.

The re-rank is because this ONE entry silently carries three separable pieces of
work, and Could/Low is why a subject Arthur raises repeatedly never gets selected:

  1. The un-taken decision on the damping and clamp. The 2026.07.20 HLD ordered a
     "Full reappraisal — not anchored by the past; the 0.70x damping and +-6 dB
     clamp are re-examined, not inherited", to be settled "once the full D_p
     distribution is in". The distribution arrived 2026-07-22 and DAMP=0.7
     CLAMP=+-6.0 were carried forward unchanged. Arthur's "go undamped" steer was
     honoured for the DERIVATION (both committed reports print raw undamped
     proposals); the follow-on "then decide how much to apply" conversation is what
     never happened. A missing decision, not a disobeyed instruction.
  2. The album CC7/CC11 re-touch — step 2 of the original two-step plan, never
     started.
  3. The residual itself, which is the part that is arguably working as designed.

Split these if any is picked up independently. The staleness of the table is
tracked separately as MM-BUG-KILN-00107; the standing guard is the within-family
spread oracle from MM-BUG-KILN-00045.

## Blocker (2026-07-25)

There is no unattended correctness fix to apply. The current control measurement says the
shipped program-to-program spread is statistically indistinguishable from the SC-55 and
S-YXG50 references, so increasing trim strength is a taste choice rather than a measured
defect. The album CC7/CC11 retouch likewise needs listening against any chosen trim law.

Unblock when Arthur chooses whether to retain or change the 0.70 damping and ±6 dB clamp
after listening to the raw proposals, and identifies the album renders that need a
controller-balance pass under that choice. Implementation and render-diff validation can
then proceed against a concrete target.
