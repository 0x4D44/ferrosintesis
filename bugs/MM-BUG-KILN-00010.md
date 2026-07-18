# MM-BUG-KILN-00010 — Cabasa, maracas and shaker (keys 69/70/82) render as one identical voice

- **State:** Fixed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-18, `f0e32b0`)

## Observation

Keys 69 (cabasa), 70 (maracas) and 82 (shaker) share a single high-passed
noise-burst arm (`crates/ferrosintesis/src/drums.rs:~1949`); no sampled bank
exists for these keys, so this is the only voicing. Three distinct shaken
instruments render bit-identically apart from seed jitter, so a latin groove that
alternates cabasa and shaker gets no timbral contrast.

## Fix

Fixed in `f0e32b0` (branch `task/20260718-FIX-HUM-ferrosintesis-split-cabasa-maracas-shake`).

Split the shared `69 | 70 | 82` arm (`drums.rs`) into three distinct arms, **level-neutral**
(all g = 0.40, so kit balance is untouched), differing by HP corner + decay + length:
- **cabasa 69** — bright, sustained steel-bead rasp (HP 5500 Hz, t60 0.08 s, longest wash);
- **maracas 70** — sharp, quick, woodier seed rattle (HP 3600 Hz, t60 0.030 s, fast decay);
- **shaker 82** — the original smooth hiss, kept EXACTLY (HP 4200 Hz, t60 0.055 s) → renders
  bit-identical, so shaker-only tracks are unaffected.

### Verification
- New oracle `cabasa_maracas_shaker_are_distinct` (drums.rs): none bit-identical; brightness
  ordered cabasa > shaker > maracas (centroids 7221 / 6658 / 6411 Hz); cabasa sustains longer
  than the quick maracas.
- Full ferrosintesis suite green (498 passed); clippy `-D warnings` clean.
- Render-diff: only 5/109 tracks use note 69/70 (aux perc); the two tested users differ, the
  two non-users are bit-identical (shaker 82 + all other drums untouched — zero contamination).

Shipped code → one version bump owed at integration. Second-eyes pending before `Closed`.

## Notes

- Purely modeled (no sampled bank involved), so no asset sourcing needed.
- Adds new voice character → render-diff inventory; expected diffs only on albums
  using these keys.
