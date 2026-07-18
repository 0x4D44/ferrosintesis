# MM-BUG-KILN-00006 — No absolute-realism (class-identity) oracle: timbre quality is unverified; only pairwise difference is checked

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** testutil
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

The verification suite (~500 numeric oracles) is strong on *relative* claims —
the perceptual-distinctness matrix (`testutil.rs` `mod perceptual_distinctness`)
answers "do GM40 and GM41 differ?" But **no oracle asserts a voice actually
sounds like the real instrument.** The HLD §5 "Passport" class-range oracles
(church organ sustain ≈0 dB, nylon attack <15 ms, strings FM depth 4–7 Hz) were
designed and accepted (`wrk_docs/2026.07.16 - HLD - perceptual distinctness
oracle.md` §5) but never implemented — grep for passport-range / is_really /
sounds_like returns only comments.

Consequence: a voice can degrade toward a buzz yet stay "distinct" and green.
This is the single place instrument *quality* is unproven — and it is the reason
the viola clone (MM-BUG-KILN-00005) sat unflagged as a defect rather than being
caught by CI. On a box with no ears, this is the highest-leverage verification
gap.

Two sub-gaps in the anti-clone metric itself:
- The full-tier bar `BAR_FULL` (`testutil.rs`) has no proven negative anchor —
  it reds nothing, so it is a drift alarm, not a demonstrated clone-catcher.
- Standing `EarPending` verdicts (40/41 viola, 48/49 ensembles) exert zero
  oracle force and are carried indefinitely awaiting a human A/B.

## Fix

Implement the HLD §5 Passport class-range oracles over the existing per-(program,
key) Passport — the measurement protocol and passport already exist, so this is
additive. Absolute range assertions per instrument class give the first machine
check that a voice belongs to its class, not merely differs from siblings.
Optionally anchor `BAR_FULL` with a synthetic in-test near-clone that must score
below the bar, turning the full tier into a verified gate.

## Notes

- This is an enhancement filed as a bug per the maintainer's routing decision
  (2026-07-18): all audit findings land in `bugs/`.
- Landing this would let future voice changes catch their own realism drift
  without an ear-in-the-loop session — the campaign bottleneck today.
