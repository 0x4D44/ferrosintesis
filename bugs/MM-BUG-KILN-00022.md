# MM-BUG-KILN-00022 — GM2 extended percussion (keys 27–34, 83–87) render as a generic 1 kHz tick

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-18, `055a849` — keys 27–34 and 83–87 aliased to their nearest modeled voices (sticks→side stick, slap→clap, scratch→guiro, clicks→side stick, high-Q/metro-bell→muted triangle, jingle bell→tambourine, belltree→open triangle, castanets→claves) via a key remap applied after the sampled-kit check; surdos 86/87 get a dedicated ~82 Hz membrane (mute damped / open ringing ~85 Hz) since no GM tom sits low enough. Regression `gm2_extended_percussion_not_generic_tick`: each key renders as its nearest voice, never the generic tick; surdos low and mute≠open. render-diff: 0 album renders move (no album sounds these keys).)

## Observation

The `_` arm in the drum dispatch emits a generic ~1 kHz tick
(`crates/ferrosintesis/src/drums.rs:~2064`) for unmapped keys. The GM2 extended
percussion keys 27–34 (high-Q, slap, scratch push/pull, sticks, square click,
metronome) and 83–87 (jingle bell, belltree, castanets, mute/open surdo) fall
through to it. The in-repo albums are protected by program whitelists, but
ferrosintesis is advertised as a faithful player of *any* GM file, and a foreign
file using these keys gets a toneless click instead of the instrument.

## Fix

Map keys 27–34 and 83–87 to the nearest existing voices (e.g. sticks → side stick,
castanets → claves, surdo → low tom, jingle bell / belltree → tambourine+triangle
blend) instead of the generic tick.

## Notes

- Matters for the "plays any GM file" goal (CLAUDE.md), not the committed catalog.
- Low musical urgency; a batch of nearest-neighbour mappings, each cheap.
