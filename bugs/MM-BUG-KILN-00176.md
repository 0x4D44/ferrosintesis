# MM-BUG-KILN-00176 — GM67 high notes expose short recorded-sustain loops

- **State:** Fixed
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
- **State history:** Open (2026-07-29, raised from Arthur's interactive M-CAL audition by GPT-5.6 Codex) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260729T175256Z-p22520-n925390200-c1 branch=task/bug-MM-BUG-KILN-00176-run-fix-20260729T175256Z-p22520-n925390200-c1 code=0798a789f057b04bea1073b30a064611c5b539b8 gate=manual)

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

## Notes

Confirmed in code: `SaxLoopVoice` repeats one loop selected from a 50–130 ms
window in `crates/ferrosintesis/src/sampler.rs:4125-4198`; the runtime reader
wraps it at `crates/ferrosintesis/src/sampler.rs:4322-4345`. Intrinsic vibrato
and drift animate the read rate but do not remove the source-timbre repetition.

Diagnostic capture: Partial. This repository has no `TESTING-GUIDE.md`.
Local ignored artifacts live under `_cal/gm67-diagnostics/`; the durable
reproduction numbers and build identity are recorded above.
