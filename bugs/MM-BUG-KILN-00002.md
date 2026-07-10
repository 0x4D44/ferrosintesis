# MM-BUG-KILN-00002 — Showcase audio oracles reject three unchanged tracks

- **State:** Open
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
- **State history:** Open (2026-07-10, raised by Codex GPT-5)

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

Pending. Determine per check whether the rendered feature or its measurement is
wrong, then recalibrate the oracle or correct the track with focused audio
evidence. Keep the passing cathedral-organ and brass tracks unchanged.

## Notes

The scratchpad records that these failures reproduced byte-for-byte with the
v0.11 baseline before the cathedral-organ work. The v0.13.1 reproduction confirms
they remain pre-existing and are not caused by the scratchpad-review synth edits,
whose 87-file baseline/candidate render inventory was byte-identical.
