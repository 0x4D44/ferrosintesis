# MM-BUG-KILN-00024 — GM 48/49 ensemble identity remains EarPending and unenforced

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** testutil
- **Raised:** 2026-07-18
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260727T000102Z-p9812-n317020100-c28
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00024-run-fix-20260727T000102Z-p9812-n317020100-c28
- **Owner base:** cc5bd986cd7191dcbaeb39cb7ed1e82e76e10c3b
- **Owner fingerprint:** -
- **Owner since:** 2026-07-27T00:01:02Z
- **Owner until:** 2026-07-27T00:46:02Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-18, raised via `deltic bugs new` model=gpt-5@xhigh) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — the oracle deliberately cannot decide whether GM48/49's shared-onset tail difference is perceptually sufficient; Arthur must supply the one planned same/different A/B verdict) → Open (2026-07-26, unblocked by Arthur's blinded A/B verdict on `175b594`: “the _A & _B samples sound pretty much the same to me (for both pairs)”; requires a durable GM49 Slow Strings identity)

## Observation

Observation: perceptual_distinctness still carries GM 48/49 as an EarPending pair, so the oracle exerts no pass/fail force over whether string ensemble 1 and 2 are acceptably distinct. Expected: one human A/B adjudication records a durable verdict and converts it into an enforced positive or collapse expectation. Actual: the standing EarPending entry remains indefinitely non-binding. Repro: inspect the GM 48/49 adjudication and run print_perceptual_matrix. Split from MM-BUG-KILN-00006 during independent closure.

## Fix

The code already routes this exact pair through the design's human-adjudication
seam. The measured shared-onset tail score is 0.0602, below the frozen 0.76 bar,
but that metric only says numeric distinctness is unproven. It cannot decide
whether String Ensemble 1 and Slow Strings sound acceptably different.

### Blocker — 2026-07-25

Blocking owner: **Arthur**. Unblock after one level-matched, same-note A/B of
GM48 and GM49 at the oracle's two probe registers (keys 48 and 72) answers:

1. **Different enough:** record the pair as ear-accepted and add a positive
   assertion so it cannot collapse later.
2. **Too similar:** replace the `EarPending` entry with a voice-fix requirement
   for a durable Slow Strings identity, then implement and prove that change in
   a separate Build pass.

The listening question is specifically whether GM49's slower swell reads as a
real identity difference after its sampled-onset/model handover, not merely
whether the files differ numerically. Choosing either route unattended would
invent the product verdict this bug exists to preserve.

### Adjudication — 2026-07-26

Codex rendered a blinded, dry, level-matched A/B on `origin/main`
`175b59444f0d623d7da83d720cfc12cd1c2a6531`: keys 48 and 72, velocity 100,
three-second held notes, embedded samples enabled, each clip normalized to
−18.00 LUFS. The order was independently randomized by register; it happened
to be A=GM49 and B=GM48 in both pairs.

Arthur's observation, verbatim:

> Is A GM48 and B GM49? I'm not sure what I'm listening for - the _A & _B
> samples sound pretty much the same to me (for both pairs)

This is the planned **too similar** verdict at both probe registers. Correctly
labelling A/B was not required; the inability to hear a durable identity
difference is the decision. The detailed probe record is
`wrk_journals/2026.07.26 - JRN - GM48-GM49 blinded ensemble adjudication.md`.

### Confirmed cause and autonomous fix requirement

`crates/ferrosintesis/src/voices.rs::strings` gives GM49 a velocity-scaled
0.45-second base attack, about 0.42 seconds at the adjudicated velocity. The
shared sampled-onset handover lasts about 0.40 seconds. Most of the intended
slow swell is therefore hidden beneath the common onset; once settled, both
programs are the same five-player `SawStack` with only modest filter/release
differences. That fits both the 0.0602 tail score and Arthur's two-register
verdict.

The autonomous fixer must:

1. Leave GM48's accepted normal-attack identity intact.
2. Give GM49 a clearly slower, durable section identity that emerges through
   and remains audible after the sampled-onset handover at keys 48 and 72,
   velocity 100. Prefer the smallest change to the existing envelope/filter/
   `SawStack` voicing; do not add a new dependency or synthesis architecture.
3. Add samples-on failing-before/passing-after coverage for the real handover,
   not only the existing model-only attack comparison.
4. Remove GM48/49's `Why::EarPending` exemption from
   `perceptual_distinctness::ALLOW`. The pair must clear the frozen tail-tier
   `BAR_TAIL` without lowering the bar, changing JNDs/weights, reclassifying the
   shared onset, or substituting a different probe.
5. Preserve the GM48/49 seam-level, class-identity, deterministic-render, and
   wider ensemble-family guards. Produce the same level-matched A/B evidence
   for independent verification, then leave the bug `Fixed`.

## Notes

- `crates/ferrosintesis/src/testutil.rs::print_perceptual_matrix` remains the
  metric diagnostic. Run it with
  `cargo test -p ferrosintesis print_perceptual_matrix -- --ignored --nocapture`
  when recording the adjudication.
- The original listening queue is
  `wrk_journals/2026.07.16 - JRN - round3 voice-quality build.md`, lines
  119–124. It explicitly calls for one same/different listen and then either an
  ear-accepted assertion or voice work.
