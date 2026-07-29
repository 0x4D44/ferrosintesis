# MM-BUG-KILN-00176 — GM67 high notes expose short recorded-sustain loops

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** audio / sampled sax sustain
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised from Arthur's interactive M-CAL audition by GPT-5.6 Codex) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260729T175256Z-p22520-n925390200-c1 branch=task/bug-MM-BUG-KILN-00176-run-fix-20260729T175256Z-p22520-n925390200-c1 code=0798a789f057b04bea1073b30a064611c5b539b8 gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `897ff63`; the reported looping is resolved and measured back into the reference band, and three residuals were split out rather than closed with it: MM-BUG-KILN-00177 (keys 64-67 still exposed), MM-BUG-KILN-00178 (the key-58 fartiness half of this observation, never diagnosed), MM-BUG-KILN-00179 (this fix's oracle has no positive control); repo gates green)

## Observation

Arthur's report, verbatim:

> What I did notice is that there are some artifacts on the GM67 channel - a
> combo of "fartiness" on some notes and a noticeable looping on some high
> notes.

Build under test: `d180304d633c5a58cfeee4008263ff997ff285d4`.

Arthur's direct left/right comparison localized the higher-pitched "fartiness"
to notes 5 and 6 (MIDI key 58 at velocities 72 and 110). The sustain oscillation
is most noticeable on notes 11 and 12 (key 73 at velocities 72 and 110).
Ferrosintesis was the left channel in both comparisons, and channel extraction
was hash-verified against the source renders.

Reproduction:

1. Render default-bank GM67 with samples enabled, sends disabled, and the M-CAL
   sustained sequence: MIDI keys 48, 53, 58, 63, 68, and 73, each at
   velocities 72 and 110.
2. Hold each note for 1.3 seconds. Listen especially to keys 68 and 73.
3. The ferrosintesis high notes carry fast repeating timbre. The two reference
   renders do not expose a comparable repetition.
4. Repeat the isolated render with different production voice seeds. The same
   key- and velocity-specific repetition remains.

The high-note spectral-envelope autocorrelation peaks at the exact selected
sample-loop period, or twice that period:

| Note | Rendered loop | First render | Different-seed render |
| --- | ---: | ---: | ---: |
| key 68, velocity 72 | 79.5 ms | 0.695 | 0.705 |
| key 68, velocity 110 | 55.4 ms | 0.353 | 0.310 |
| key 73, velocity 72 | 64.9 ms | 0.900 at 2× period | 0.908 at 2× period |
| key 73, velocity 110 | 63.1 ms | 0.568 | 0.568 |

Across the same four notes, SC-55 and S-YXG50 peak between 0.036 and 0.220.
This confirms the audible-loop report on ferrosintesis. Arthur has localized
the separate "fartiness" description to key 58, but the current probe has not
yet objectively defined or diagnosed it.

**Expected.** A held baritone-sax note varies naturally without exposing the
short source-buffer repetition.

**Actual.** The high notes expose a 12.6–18.1 Hz repeating spectral envelope.

## Fix

No fix attempted during the listening session. Investigate a longer or
multi-segment sustain, loop crossfading or alternation, and whether the A4
source can cover key 73 without making its 63–65 ms loop obvious. Add a
rendered high-register periodicity regression before moving the bug to Fixed.

### Verification summary (2026-07-29, independent two-eyes, Claude Opus 5)

Verified on trunk `897ff63` in a task worktree. The fix was authored by GPT-5.6 Codex,
so the two-eyes rule holds. **Closed with three residual splits.**

**The reported looping is genuinely fixed.** Re-running this Observation's own quantity
- the 8-band log spectral-envelope autocorrelation at the selected source-loop period,
on each note rendered isolated for 1.35 s - reproduced all four loop periods to the
decimal against the table above (79.46 / 55.38 / 64.94 / 63.14 ms vs the recorded
79.5 / 55.4 / 64.9 / 63.1), which confirms the same artifact is being measured:

| key | vel | raw corr pre-fix @1x | post-fix @1x | post-fix @2x |
| ---: | ---: | ---: | ---: | ---: |
| 68 | 72 | 0.932 | -0.019 | -0.059 |
| 68 | 110 | 0.961 | -0.230 | 0.220 |
| 73 | 72 | 0.961 | 0.192 | 0.035 |
| 73 | 110 | 0.938 | -0.046 | -0.026 |

Peak positive periodicity falls to 0.220, inside the 0.036-0.220 band this Observation
records for the SC-55 and S-YXG50 reference modules. (These are this probe's own
numbers on an isolated voice, so the pre-fix column reads higher than the Observation's
0.353-0.900, which was measured on a fuller render; the direction and conclusion agree.)

**The regression genuinely fails without the fix.** Forcing the production gate off
(`program == 67 && key >= 68` -> `false`, restoring the single-slice reader) fails
`baritone_sax_high_hold_does_not_expose_the_source_loop_period` at excess 1.041
(1x 0.963, 2x 1.041) on a loop measured at 0.0795 s - matching this Observation's
recorded 79.5 ms for that note.

**Reach is exactly as claimed.** A census of every MIDI under `albums/` and `demos/`
found only two authoring GM67: `demos/synth_feature_showcase/midi/03 - Skyline Brass
Reactor.mid` (keys up to 81, eight at or above the gate) and
`demos/ferrosintesis_reference/midi/03 - Reed, Pipe, Lead, Pad.mid` (keys 49/53/56,
all below it). The mandated render-diff inventory over `demos/**` then reported
**1 changed, 15 same, 0 contamination**, with one NOT-REACHED row - the low-key GM67
demo, which the `--program` granularity cannot exclude and which my census predicted
would not move. Its non-diff independently confirms the `key >= 68` gate holds from the
other side. Separately, tracing every new mutation confirms the `grain_motion == false`
path is bit-identical (all new state guarded by `if self.grain_motion`, `grain_gain`
stays 1.0, and `choose_next_grain` - the only new `rng.white()` consumer - is
unreachable, so the RNG stream is untouched).

**Gates:** `cargo test --workspace` exit 0 (57 suites, zero failures),
`cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check`
exit 0, 147 Python tests OK.

**Why three residuals rather than a clean close.** The fix resolves the keys Arthur
audited, but its `key >= 68` boundary is that reported key rather than a measured
onset: key 67 selects the *same* source zone as key 68 (root 421.2 Hz) and still
measures 0.946 @1x / 0.988 @2x - more exposed than key 68 was before the fix. That is
MM-BUG-KILN-00177. Arthur's separate "fartiness" at key 58 remains undiagnosed and was
tracked nowhere else, so it is MM-BUG-KILN-00178. And this fix's own oracle asserts
only upper bounds with no positive control, so nothing preserves its demonstrated
sensitivity - MM-BUG-KILN-00179.

## Notes

Confirmed in code: `SaxLoopVoice` repeats one loop selected from a 50–130 ms
window in `crates/ferrosintesis/src/sampler.rs:4125-4198`; the runtime reader
wraps it at `crates/ferrosintesis/src/sampler.rs:4322-4345`. Intrinsic vibrato
and drift animate the read rate but do not remove the source-timbre repetition.

Diagnostic capture: Partial. This repository has no `TESTING-GUIDE.md`.
Local ignored artifacts live under `_cal/gm67-diagnostics/`; the durable
reproduction numbers and build identity are recorded above.
