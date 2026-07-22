# MM-BUG-KILN-00047 — GM0 upright attacks thump across short piano phrases

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-22, raised by OpenAI Codex from Arthur's FRA report)

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

Pending.

## Notes

- Reproduction and calibration evidence will be kept in
  `wrk_journals/2026.07.22 - JRN - piano envelope and release.md`.
- Scope is the default GM0 VSCO upright and its piano voice release. Other piano
  banks, other LA instruments, MIDI scheduling, and pedal semantics are not part of
  this defect.
