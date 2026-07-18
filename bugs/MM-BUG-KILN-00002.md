# MM-BUG-KILN-00002 — Showcase audio oracles reject three unchanged tracks

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** testing
- **Raised:** 2026-07-10
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
- **State history:** Open (2026-07-10, raised by Codex GPT-5); Fixed (2026-07-18, b88d381 — corrected stale cross-program audio windows, added level-normalized brightness checks and a matched-window structural guard, and aligned the RMS arc oracle with the authored third-quarter climax/final-drop contour. The committed MIDI remains byte-identical; all five current renders pass.)

## Observation

The synth showcase's full audio runner has four pre-existing oracle failures in
three tracks: track 1 `wah resonance bite` reports an HF delta that is too small;
track 4 `vowel shifts` reports that HF did not drop; and track 5 reports both a
flat dynamic arc and an insufficient `shanai pressure` RMS delta. The cathedral
organ track 2 and brass track 3 pass.

Expected: the committed showcase MIDI rendered by current ferrosintesis passes
its audio-side oracle suite, or the checks accurately identify a real audible
regression. Actual on ferrosintesis v0.13.1: `python analyze.py` reports exactly
four failures after rendering all five committed MIDIs to `build/wav/`:

- `01 - Ignition Court.wav wah resonance bite HF delta too small`
- `04 - Choir of Circuitry.wav vowel shifts HF did not drop`
- `05 - Atlas of Unbuilt Machines.wav dynamic arc too flat:
  [0.08125831622279855, 0.03664808701928576, 0.07698364926183467,
  0.054910448531347786]`
- `05 - Atlas of Unbuilt Machines.wav shanai pressure RMS delta too small`

## Fix

The rendered features were present. The stale measurements compared different
instrument programs or unrelated arrangement sections, while the arc check treated
an intentional mid-track trough as a failure because it compared only the climax
with the intro.

b88d381 moves the lead, soft-piano, brass, pad, and shanai checks onto
same-program windows. Timbre checks can now use high-frequency energy normalized by
RMS, so a dynamic change cannot hide the audible brightness delta. Structural
verification rejects any future matched check that crosses a program boundary.
The RMS arc now requires the authored shape: a distinct third-quarter climax, an
audible final drop, and at least eight percent overall dynamic span.

## Notes

The scratchpad records that these failures reproduced byte-for-byte with the
v0.11 baseline before the cathedral-organ work. The v0.13.1 reproduction confirms
they remain pre-existing and are not caused by the scratchpad-review synth edits,
whose 87-file baseline/candidate render inventory was byte-identical.

Fix evidence on ferrosintesis v0.21.36:

- Before: python analyze.py failed seven current-trunk checks across all five
  tracks, including stale cross-program comparisons introduced by later voice
  changes.
- After: all five rendered tracks pass python analyze.py; all structural,
  feature, matched-window, stereo, arc, program, and controller checks pass
  python build.py --verify.
- python -m unittest test_analyze.py passes four focused regressions for flat or
  malformed arcs and cross-program matched windows.
- Rebuilding the suite changed no committed MIDI file, preserving Cathedral
  Mechanica and Skyline Brass Reactor exactly.
