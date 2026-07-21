# MM-BUG-KILN-00013 — Live/realtime path has no global polyphony cap: a dense stream can blow the audio-callback deadline

- **State:** Closed
- **Priority:** Could
- **Severity:** Medium
- **Area:** live
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-19, `a0df299`, by Claude Opus 4.8 (1M)) → Closed (2026-07-21, independently verified by Codex GPT-5: actual trunk fix `121d4fd`; 168 voices red-before, capped at 128 green-after; workspace tests and clippy green)

## Observation

`EngineCore` keeps `active: Vec::new()` unbounded (`crates/ferrosintesis/src/
engine.rs:~1149`); the only voice steal is per-channel
`DRIVEN_GUITAR_VOICE_LIMIT = 8` (`engine.rs:~205`,
`make_room_for_driven_guitar`). There is no global `MAX_VOICES` / oldest-quietest
steal in either path. Harmless offline (no deadline), but a live stream that
stacks hundreds of un-released voices can push `render_block_add` past the
audio-callback budget and cause xruns/dropouts. A realtime synth normally caps
total polyphony and steals the oldest/quietest.

## Fix

Fixed in `a0df299`. Added `EngineCore::enforce_voice_cap(cap)`: while over the
cap, steal the oldest **released** voice (the quietest available proxy — the
`Voice` trait exposes no level query — and `active` is push-ordered so the front
is the oldest), else the oldest voice overall. Called **only** from
`RealtimeSynth::fill_ring` (after draining pending events, before
`render_block_add`) with a new `LIVE_MAX_VOICES = 128` ceiling. Offline never
calls it, so its polyphony stays unbounded and its goldens bit-identical **by
construction** (not merely by a flag check).

Verification: `live_polyphony_is_capped` (168 spawned → 128),
`live_under_cap_steals_nothing` (40 → 40), `offline_polyphony_is_unbounded`
(300 → 300), and `enforce_voice_cap_steals_oldest_released_first` (checks victim
identity, not just count). An adversarial 3-skeptic panel confirmed the fix 3-of-3,
including a dangling-state audit: no structure indexes `active` positionally (all
voice access is a predicate re-scan; `drum_rr`/`key_on_at` are `(ch,key)`-keyed;
choke groups and the driven-guitar count are recomputed; a stolen voice's
`note_off` simply no-ops), so `active.remove()` cannot corrupt engine state.
fmt + `clippy -D warnings` + 553 lib tests green. Left **Fixed**, not Closed —
awaiting independent two-eyes verify.

### Verification summary (2026-07-21 — Codex GPT-5)

Independent of the Claude Opus 4.8 fixer. On `121d4fd^`, a public-realtime-path
transplant reproduced the original unbounded count: 168 live voices survived, failing the
128 ceiling. Current trunk passed `live_polyphony_is_capped`,
`live_under_cap_steals_nothing`, `offline_polyphony_is_unbounded`, and
`enforce_voice_cap_steals_oldest_released_first`. Source review confirmed the cap runs
after pending events and before realtime block rendering, while offline has no caller.
`cargo test --workspace` and clippy with warnings denied were green. The documented hard-cut
tradeoff is overload policy, not a residual of the unbounded-render defect.

## Notes

- Hard cut on steal can click under genuine overload — the safety valve's cost
  versus xruns/dropouts. `LIVE_MAX_VOICES` is documented and tunable.
- Scoped to the realtime surface; offline determinism/goldens untouched.
- `live` is the secondary surface — this is robustness, not a render-quality defect.
