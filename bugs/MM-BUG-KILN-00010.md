# MM-BUG-KILN-00010 — Cabasa, maracas and shaker (keys 69/70/82) render as one identical voice

- **State:** Closed
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-18, `f0e32b0`) → Closed (2026-07-18, independently verified by OpenAI Codex on `55c829e`)

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

### Independent closure verification (2026-07-18, OpenAI Codex)

- Re-ran `drums::tests::cabasa_maracas_shaker_are_distinct` on trunk build
  `55c829e`: centroids measured 7221/6658/6411 Hz for cabasa/shaker/maracas,
  and cabasa's late/early decay ratio remained above maracas.
- Confirmed the original observation at pre-fix `e364471`: keys 69, 70, and 82
  entered one shared arm with HP 4200 Hz, t60 0.055 s, and gain 0.40. That shared
  parameterization cannot satisfy the regression's ordered brightness and decay
  traits; the focused test passes after the three-way dispatch split.
- The independent workspace gate on the same build passed: `cargo test --workspace`,
  `cargo clippy --workspace --all-targets -- -D warnings`, and `cargo fmt --all -- --check`.
  All three voices are distinct at equal level and no residual gap was found.

## Notes

- Purely modeled (no sampled bank involved), so no asset sourcing needed.
- Adds new voice character → render-diff inventory; expected diffs only on albums
  using these keys.
