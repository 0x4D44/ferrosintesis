# MM-BUG-KILN-00092 — every NoteOn allocates in the audio callback: voices are `Box<dyn Voice>`

- **State:** Blocked
- **Priority:** Should
- **Severity:** Medium
- **Area:** engine / realtime
- **Raised:** 2026-07-24
- **Owner:** Arthur
- **Owner role:** human
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
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00082 by Claude Opus 4.8 (1M) while fixing it. 00082 fixed the bounded part; this is the part that needs an architectural decision. MEASURED, not inferred.) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — option 3 measured ample 1024-frame deadline margin; Arthur must choose the bounded construction exception or authorize a whole-engine voice-pool design)

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

### Option 3 measurement — 2026-07-25

A temporary ignored release-profile probe swept every GM melodic program after
`prewarm_samples()` and `reserve_realtime_storage()`. Each timing covered one Program
Change, one NoteOn, and the full 1024-frame callback; an untimed Panic removed the voice
between samples. The probe was removed before this ledger-only commit.

| 1,536 warmed callbacks | Time | Share of 23.220 ms deadline |
|------------------------|-----:|-----------------------------:|
| p50 | 0.438 ms | 1.89% |
| p95 | 0.704 ms | 3.03% |
| p99 | 0.973 ms | 4.19% |
| maximum (GM52) | 2.566 ms | 11.05% |

This is one-host evidence, not a hard realtime proof, but it finds a large margin and still
no observed xrun. The existing allocation ratchet keeps NoteOn at most 16 allocations
and every other measured callback shape at zero.

**Blocked decision for Arthur:**

1. **Recommended — accept the bounded voice-construction exception.** Amend
   `wrk_docs/2026.07.23 - HLD - amp lab (live knob GUI for Part B).md` acceptance criterion
   7 to permit voice construction capped by `LIVE_MAX_VOICES`, retain the current
   allocation ratchet, then close this as an accepted design constraint.
2. **Authorize the voice-pool build.** This is a major engine refactor: pre-allocate 128
   heterogeneous voice slots and make every concrete voice constructible in place, while
   preserving the unbounded offline renderer and all render identities.

## Notes

- `the_audio_callback_does_not_allocate_per_block` (`crates/amp-lab/src/audio.rs`) already
  pins every other shape at exactly 0 and bounds NoteOn at 16, so this cannot get quietly
  worse while the decision is pending.
- Do not "fix" this by relaxing that test. The zero-allocation assertions are the part
  worth keeping.
