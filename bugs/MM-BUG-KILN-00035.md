# MM-BUG-KILN-00035 — GM System On means different things offline (XG-effect-only) vs live (full hard_reset); the live path's 4-byte SysEx buffer ignores XG/GS messages the offline parser decodes

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** parser / engine / live
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the cross-agent MIDI/GM support audit — both Fable 5 and gpt-5.6-sol-xhigh confirmed the entry-point split; the 4-byte live-buffer parity gap from Fable 5) → Fixed (2026-07-22, `c26dfff` on `main`, OpenAI Codex; shared live/SMF decoder, full GM reset semantics, and live XG/GS capture/recovery regressions — branch SHA before the integration rebase was `384e88d`) → Closed (2026-07-22, Claude Opus 4.8, independent two-eyes verification on `b63bd51`: both facets of the Observation reproduced pre-fix on `5605e67` and resolved post-fix via a public-API repro; gates green; catalog renders provably unaffected)

## Observation

Two entry-point inconsistencies in reset / SysEx handling.

- **GM System On has two semantics.** Offline, the SMF parser decodes GM System On to
  `EvKind::XgReset` → `xg_reset()`, which resets only the XG effect block and explicitly
  never routes through `hard_reset` (midi.rs:243-250; engine.rs:1769-1782). Live, the
  byte-stream parser emits `ResetKind::GmSystemOn` and `fill_ring` maps any `Reset(_)` to
  `self.core.hard_reset()` — a full engine rebuild (live.rs:274, 380-386; engine.rs:1531).
  Same wire bytes, two behaviours. GM System On means "initialise to GM state" regardless of
  transport, and SMFs are expected to carry it; the offline soft interpretation is
  spec-equivalent only in the dominant tick-0 case (a fresh engine is already at GM defaults
  — `Strip::new` seeds CC7=100, pan centre, bend range 2) and observably wrong for a
  mid-file reset (medley/mix files).

- **Live SysEx capture is 4 bytes.** The live parser buffers only the first 4 SysEx bytes
  (`sysex: [u8; 4]`, live.rs:320; longer messages set `sysex_overflow`), so the live path
  matches GM System On but **ignores** XG System On, GS Reset, and GS "Use for Rhythm Part"
  — messages the offline parser fully decodes (midi.rs:211-280). A live GS stream cannot
  route a second channel to drums; the identical file rendered offline can.

Offline rendering is the primary path and mostly unaffected (GM Reset at t=0). This is an
entry-point-consistency / live-fidelity defect, not an offline-render correctness bug. No
in-repo album is affected.

## Fix

Fixed in `c26dfff` (the integrated commit; `384e88d` was the pre-rebase branch SHA —
same `git patch-id`, but it is not an ancestor of `origin/main`).

- `midi.rs::decode_sysex_payload` now strictly recognizes the complete fixed GM,
  XG, and GS payloads once. Both SMF and live input use it, so message shapes and
  event semantics cannot drift between entry points.
- GM System On has its own `EvKind::GmReset`. `EngineCore::gm_system_on` restores
  fresh synthesis, channel, voice, and effect state for both transports while
  retaining whole-render public `Stats`. A private resettable seed position keeps
  the existing live reset behavior without coupling synthesis state to diagnostics.
- The live parser captures the longest modeled nine-byte payload, lets realtime
  messages pass through an open SysEx, handles raw `FF` immediately, and recovers
  another non-realtime status instead of swallowing later channel traffic.
- GM reset events sort before same-tick setup across SMF tracks, so authored setup at
  that tick overrides the newly established defaults regardless of track order.

Verification:

- Regressions cover exact/malformed SMF shapes, all modeled live XG/GS messages,
  live overflow/status recovery, full live/core GM reset, same-tick ordering, and a
  parsed mid-file reset that proves the old held voice is gone while Stats remain
  cumulative.
- `cargo fmt --check`, workspace Clippy with warnings denied, and
  `cargo test --workspace` all passed.
- The mandatory exact-base render inventory found all 124 catalog MIDIs
  byte-identical: zero changed and zero contamination.

### Verification summary (2026-07-22, Claude Opus 4.8 — independent, two-eyes)

Verified on `b63bd51` (contains the fix as `c26dfff`); pre-fix baseline `5605e67`.

**Independent repro, not the fixer's tests.** Both facets of the Observation are
reachable from the *public* API, so the check used a purpose-written repro
(`offline::{parse, render}` + `live::RealtimeSynth`) that touches no `pub(crate)`
item and therefore compiles unchanged on both trees. That matters: the fixer's own
tests reference `EvKind::GmReset`, `decode_sysex_payload` and `voice_seed_index`,
none of which exist pre-fix, so they cannot be run against the old code at all. The
repro asserts *parity between entry points* — the exact property the bug claims is
broken — rather than an absolute threshold.

| facet | pre-fix `5605e67` | post-fix |
|---|---|---|
| GM System On, voice held across a mid-file reset | offline survived=**true**, live survived=**false** — FAIL | both false — PASS |
| GS "Use for Rhythm Part" (block `0x1A` → ch 10) changes the render | offline differs=**true**, live differs=**false** — FAIL | both true — PASS |

That is the Observation verbatim: "Same wire bytes, two behaviours", and "a live GS
stream cannot route a second channel to drums; the identical file rendered offline can."

**Root cause addressed at the right layer.** `midi::decode_sysex_payload` is now the
single definition of every modeled system-SysEx shape and both entry points call it,
so the two paths cannot drift again by construction. All seven added regression tests
pass in the gate run.

**Render safety proved structurally, not sampled.** (1) A SysEx census over every
committed MIDI: **140 files, zero SysEx events of any kind**, so no committed MIDI can
reach a changed decode path. (2) The load-bearing risk is the new `voice_seed_index`:
if it ever diverged from `Stats::voices_spawned`, every render would change. All three
`voices_spawned += 1` sites (engine.rs:1608, 1951, 2104) are paired 1:1 with a
`voice_seed_index += 1`, both start at 0, and both seed consumers (engine.rs:1578, 1986)
read the new field — so absent a `GmReset` the counters are provably equal.

**Deliberate strictness, accepted — no residual split.** The shared recognizer requires
a complete, exact, seven-bit payload in a terminated `F0` event, so three shapes the old
prefix-matching SMF parser accepted are now ignored: a GS Reset missing its checksum, a
System On with trailing bytes, and a System On split across `F0`/`F7` packets. All are
out-of-spec or vanishingly rare, none appears in-repo, the live path behaves identically,
and `system_sysex_rejects_malformed_shapes` codifies it as intended. This is the bug's own
goal (one shape definition, no drift), not a gap.

**Gates** on the verification worktree: `cargo fmt --check` clean, `cargo clippy
--workspace --all-targets -- -D warnings` clean, `cargo test --workspace` 609 passed /
0 failed / 20 ignored.

## Notes

- Lowest priority of the four review defects: the dominant offline path at tick 0 is benign,
  and the live path is not the album-render workflow.
- Related to but distinct from MM-BUG-KILN-00033 (ordinary per-channel controller
  persistence).
