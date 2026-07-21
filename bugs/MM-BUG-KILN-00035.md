# MM-BUG-KILN-00035 — GM System On means different things offline (XG-effect-only) vs live (full hard_reset); the live path's 4-byte SysEx buffer ignores XG/GS messages the offline parser decodes

- **State:** Open
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the cross-agent MIDI/GM support audit — both Fable 5 and gpt-5.6-sol-xhigh confirmed the entry-point split; the 4-byte live-buffer parity gap from Fable 5)

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

<to be filled by the fixer>

Sketch: (1) settle one GM System On semantic across both entry points — recommended: keep
offline soft + documented, keep live `hard_reset` (the spec-faithful live behaviour), or
factor a shared explicit GM-reset helper; (2) grow the live SysEx capture to recognise the
XG System On / GS Reset / GS rhythm-part patterns the offline parser already handles.

## Notes

- Lowest priority of the four review defects: the dominant offline path at tick 0 is benign,
  and the live path is not the album-render workflow.
- Related to but distinct from MM-BUG-KILN-00033 (ordinary per-channel controller
  persistence).
