# MM-BUG-KILN-00010 — Cabasa, maracas and shaker (keys 69/70/82) render as one identical voice

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** drums
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

Keys 69 (cabasa), 70 (maracas) and 82 (shaker) share a single high-passed
noise-burst arm (`crates/ferrosintesis/src/drums.rs:~1949`); no sampled bank
exists for these keys, so this is the only voicing. Three distinct shaken
instruments render bit-identically apart from seed jitter, so a latin groove that
alternates cabasa and shaker gets no timbral contrast.

## Fix

Split 69/70/82 into three arms with distinct burst envelopes, decay and rate — a
cabasa's steel-bead rasp, maracas' seed rattle and a shaker's tighter hiss are
separable with a few parameters each.

## Notes

- Purely modeled (no sampled bank involved), so no asset sourcing needed.
- Adds new voice character → render-diff inventory; expected diffs only on albums
  using these keys.
