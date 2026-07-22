# MM-BUG-KILN-00047 — GM0 upright attacks thump across short piano phrases

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synthesis
- **Raised:** 2026-07-22
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-22, raised by OpenAI Codex from Arthur's FRA report) → Fixed (2026-07-22, default GM0 bank and release implementation by OpenAI Codex; independent verification pending)

## Observation

The default GM0 VSCO upright re-articulates each note of the opening piano figure in
the Ferrosinthesis Reference Audition instead of carrying the phrase across its
62.5 ms note gaps. The second and third notes sound especially thumpy compared with
the SC-55 and S-YXG50 renders.

The MIDI has no pedal or legato controller: D4, F#4, and A4 each last 312.5 ms and
start 375 ms apart at 96 BPM. The currently delivered Ferro render loses 16–23 dB
inside those gaps; a matched retained SC-55 piano probe loses about 6 dB. The
source-bank forte takes also have a 32.5 dB spread in their 0–30 ms versus
120–280 ms RMS ratio, including large same-zone round-robin differences. The
second and third FRA notes select different G4 round robins, exposing that
inconsistency as changing attack weight.

Expected: adjacent keys and round robins retain their individual timbre and natural
register decay, but have a coherent macro-envelope; lifting an unpedalled piano key
should leave enough piano-only release to bridge FRA's short gaps without turning
longer separations into sustain-pedal behaviour.

## Fix

Fixed on `task/20260722-TSK-HUM-piano-envelope-and-release`. The sample generator
now conditions all 54 default-upright takes against one slope-bounded whole-bank
attack/body envelope and one shared absolute body-level trend. It preserves the
first 40 ms hammer event, post-140 ms decay slope, spectra, pitch, and common
headroom. Two consecutive bakes are hash-identical; no non-piano sample changes.

The default GM0 route now gives its sample and model owners the same 0.45 s key-up
T60. Its conditioned-bank handoff uses gain 4.0 and a 180–450 ms fade. A matched
4.9 dB forte-owner trim preserves the repository's square perceived-velocity law.
The override is explicit and default-bank-only: GM0 alternates, undefined-CC0
fallbacks, GM1, GM3, and non-piano LA routes retain their legacy release and render
identity.

Direct sampled fixtures now lose 4.13–6.77 dB through the FRA 62.5 ms gaps;
modeled fixtures lose 7.32–8.12 dB. Every path is at least 28.53 dB down 250 ms
after note-off and reaps by 2 s. The exact dry three-note engine regression stays
within the 10 dB gap ceiling. Full validation passed: 18 generator tests, workspace
format/lint, 615 passing library tests plus every other workspace target, and a
141-MIDI exact-base render comparison with 83 expected GM0 changes and zero
contamination. Left Fixed pending independent two-eyes closure.

## Notes

- Reproduction and calibration evidence will be kept in
  `wrk_journals/2026.07.22 - JRN - piano envelope and release.md`.
- Scope is the default GM0 VSCO upright and its piano voice release. Other piano
  banks, other LA instruments, MIDI scheduling, and pedal semantics are not part of
  this defect.
