# MM-BUG-KILN-00092 — every NoteOn allocates in the audio callback: voices are `Box<dyn Voice>`

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** engine / realtime
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00082 by Claude Opus 4.8 (1M)
  while fixing it. 00082 fixed the bounded part; this is the part that needs an
  architectural decision. MEASURED, not inferred.)

## Observation

**Measured**, with a counting global allocator armed around the callback
(`crates/amp-lab/src/rtalloc.rs`, added by the 00082 fix):

| Callback shape | Allocations |
|----------------|------------:|
| Steady render block, no events | **0** |
| 64-message CC burst + render | **0** |
| Panic + all-notes-off + render (playback stopped) | **0** |
| One NoteOn + render | **13** |

Everything except voice creation is already allocation-free. The 13 are one voice:
`EngineCore::note_on` builds each voice as `Box<dyn Voice>`
(`crates/ferrosintesis/src/engine.rs`), and the voice models themselves own `Vec`s
(delay lines, mode tables, sample cursors). A dense passage therefore enters the
allocator once per note, on the deadline-bearing thread.

**Expected.** The amp-lab HLD's acceptance criterion is no allocation on the audio thread
after setup.

**Actual.** Bounded and attributable, but non-zero — and it scales with note density, so
the worst case is exactly the busiest moment.

**Audibility is unmeasured.** No xrun has been observed; `LIVE_MAX_VOICES` (128) caps how
many voices can exist, and the allocator is fast on a warm heap. What is certain is the
allocator entry, not a dropout.

## Fix

**This is an architectural decision and needs Arthur, not a fixing pass.** `Box<dyn Voice>`
is how the whole engine is built, and the OFFLINE renderer — the primary surface, where
allocation is free — uses the same path. The options are not local:

1. **A voice pool.** Pre-allocate `LIVE_MAX_VOICES` slots at setup and construct in place.
   Needs every voice model to be constructible into existing storage, or a fixed-size
   enum/union of the concrete voice types. Large, touches every voice.
2. **Accept it, and say so.** Revise the amp-lab HLD's acceptance criterion to "no
   allocation except voice construction, capped at `LIVE_MAX_VOICES`", and keep the
   regression as the ratchet it now is. Cheapest, and defensible if a measurement shows
   the allocation is far inside the deadline.
3. **Measure first.** Time `note_on` on this box against the callback deadline (1024
   frames at 44.1 kHz = 23 ms) and let the number decide between 1 and 2.

Option 3 is the obvious first step and needs no decision.

## Notes

- `the_audio_callback_does_not_allocate_per_block` (`crates/amp-lab/src/audio.rs`) already
  pins every other shape at exactly 0 and bounds NoteOn at 16, so this cannot get quietly
  worse while the decision is pending.
- Do not "fix" this by relaxing that test. The zero-allocation assertions are the part
  worth keeping.
