# MM-BUG-KILN-00006 — No absolute-realism (class-identity) oracle: timbre quality is unverified; only pairwise difference is checked

- **State:** Fixed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-18, `12b1d78`)

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

Fixed on branch `task/20260718-FIX-HUM-ferrosintesis-passport-class-identity-or`
(U1 harness `aea7ef0` → U7 final `12b1d78`), built under loop-build.

Implemented the HLD §5 Passport class-identity oracle in
`testutil.rs::mod perceptual_distinctness`, over the existing `passports()` render
protocol (no second renderer): a `CLASS_RANGES` table of absolute two-sided ranges on the
probe-key mean of ONE physically-scaled Passport field per family, checked by
`class_identity_ranges_hold`, plus a durable RED-before guard
`class_ranges_reject_wrong_class` (each range must reject a wrong-class exemplar, so no
range is a vacuous always-true bound).

**9 ranges across 8 family groups** — organ (held), keyboard+chrom-perc (decay), plucked
(decay), bowed (held + `fm_depth` vibrato, the §5 example), ensemble/choir (held), brass,
reed, pipe (held). `sustain_db` is the load-bearing axis (sustained ≈0 vs decayed very
negative), separating the classes cleanly with margin.

**Calibration was measured, not guessed** (`print_passport_fields` `#[ignore]` harness):
the existing voices.rs class-oracle numbers use a different estimator, so three planned
ranges (organ flatness, brass/reed harmonic-fraction) were dropped as wrong-in-Passport-
space; and two design carve-outs were corrected by measurement (GM29/30 driven guitar
decay on a plain held note; GM38/39 synth bass hold).

### Verification
- Full ferrosintesis suite green (491 passed, 0 failed); clippy `-D warnings` clean; fmt.
- Every good voice sits inside its physically-correct range — **no F4 voice bug surfaced.**
- Honest limits recorded, not fudged: F1 (synth lead/pad 80-95 too heterogeneous → unasserted
  by design) and F2 (reed↔flute overlap on flat_L → only sustain floors separate the blown
  families).

Test-only change → no version bump. Second-eyes verification pending before `Closed`.

### Deferred sub-items (smaller, separate follow-ups)
- Anchoring `BAR_FULL` with a synthetic in-test near-clone (turn the full anti-clone tier
  into a verified gate) — optional, not built here.
- The standing `EarPending` adjudications: (40,41) was resolved by the viola fix
  (MM-BUG-KILN-00005 — now independent-onset and distinct); (48,49) still awaits one ear A/B.

## Notes

- This is an enhancement filed as a bug per the maintainer's routing decision
  (2026-07-18): all audit findings land in `bugs/`.
- Landing this would let future voice changes catch their own realism drift
  without an ear-in-the-loop session — the campaign bottleneck today.
