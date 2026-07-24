# MM-BUG-KILN-00082 — amp-lab allocates inside the deadline-bearing audio callback

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / realtime audio
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/amp-lab/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Built the allocation counter the bug asks
  for and MEASURED the callback: everything except voice creation was already at zero,
  and the reservations took the rest to zero. The per-voice `Box` residual needs an
  architectural decision and is split to MM-BUG-KILN-00092. Evidence under "Fix landed"
  below. Awaits independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

The amp-lab HLD acceptance criterion requires no allocation on the audio thread
after setup. The callback completes both UI and sequencer MIDI messages through
`RealtimeSynth::write_byte()` (`crates/amp-lab/src/audio.rs:75-111`).

`RealtimeSynth` constructs `pending` as `Vec::new()`
(`crates/ferrosintesis/src/live.rs:161-189`), and a completed MIDI message pushes
a command into it (`live.rs:456-469`). The first tick-zero backing message
therefore grows a zero-capacity vector inside the first callback. Later command
bursts can reallocate when they exceed retained capacity. NoteOn handling also
constructs boxed voices and grows the active-voice vector
(`crates/ferrosintesis/src/engine.rs:2540-2589` and `:2640`).

`prewarm_samples()` only decodes lazy sample banks; it does not reserve command
or voice storage. Expected: callback work is allocation-free after setup.
Actual: allocator entry is statically certain. Whether it causes an audible
xrun on KILN is unverified because no timing probe or application run occurred.

## Fix

Provide bounded setup-time reservation/fixed-capacity storage for pending
commands and a realtime-safe voice allocation strategy or pool. Size and define
overflow behavior against the maximum command burst and live voice cap. If the
underlying live synth intentionally permits allocation, revise the amp-lab
design only after measuring and explicitly accepting that weaker contract.

Add an allocation-counting callback-core regression after setup. Exercise the
initial rig, tick-zero backing burst, note creation, panic/all-notes-off, A/B
recall, and the maximum bounded command backlog; require zero callback
allocations if the HLD contract remains.

## Fix landed (2026-07-24)

**The measurement came first, and it changed the picture.** The bug reasons from source
that allocation is "statically certain"; it does not say how much or where. A test-only
counting global allocator (`crates/amp-lab/src/rtalloc.rs`), armed per thread around the
measured call only, gives the actual numbers. Pre-fix:

| Callback shape | Before | After |
|----------------|-------:|------:|
| Steady render block | **0** | 0 |
| 64-message CC burst | **0** | 0 |
| Panic + all-notes-off | **17** | **0** |
| One NoteOn | 13 | 13 |

So two of the bug's four concerns were already fine. `pending` growing from `Vec::new()`
is real but ONE-SHOT — the first message the audio thread ever completes — and invisible
by the second callback, which is why a CC burst measures zero. The recurring cost is
voice creation, and panic was paying it too through vector growth.

**Fixes (bounded, setup-time):**

- `RealtimeSynth::new` builds `pending` with `Vec::with_capacity(LIVE_MAX_VOICES)`, so the
  first completed message does not allocate.
- New `RealtimeSynth::reserve_realtime_storage()` reserves the voice vector to
  `LIVE_MAX_VOICES` via a new `EngineCore::reserve_voices`. Deliberately separate from
  `prewarm_samples()` — it is not about samples, and a `--no-samples` build needs it just
  as much. amp-lab calls both at setup.
- Offline is untouched: it is unbounded by design and pays nothing for growth amortised
  over a whole render.

**Regression** — `the_audio_callback_does_not_allocate_per_block` asserts **exactly 0**
for a steady block, a 64-message CC burst, and panic + all-notes-off, and bounds a single
NoteOn at 16. The counter carries its own self-test (it must see a known `Vec` allocation
and report zero when nothing allocates), because a broken counter would make every "0"
above vacuous.

**Two measurement traps worth recording**, both of which produced wrong numbers first:

- Panic initially measured 13 even after the fix. It was not panic: `Cmd::Panic` rewinds
  the loop, the tick-0 NoteOn spawns a voice, and that voice was being attributed to
  panic. Measured with playback stopped, panic is 0.
- The NoteOn case then measured 26 — two voices, because the resumed sequencer spawned one
  as well. Isolated, it is 13 per voice.

**What is NOT fixed, and why.** The 13 are one `Box<dyn Voice>` plus the `Vec`s inside the
voice model. Removing that needs a voice pool in the shared engine — every voice model
constructible into existing storage — which is an architectural change to code the
OFFLINE renderer uses too. That is not a fixing pass's call, so it is split to
**MM-BUG-KILN-00092** with the measurements attached and a cheap first step (time
`note_on` against the 23 ms callback deadline before choosing between a pool and revising
the HLD criterion).

**Gates.** `cargo test -p amp-lab` 17 passed; `cargo test --release -p ferrosintesis` 661
passed / 0 failed / 26 ignored (+4 doc-tests); clippy `-D warnings` clean on both crates;
`cargo fmt --check` clean. The allocator is `#[cfg(test)]` — release builds are untouched.

## Notes

The allocation itself is confirmed from source. Its wall-clock duration and
audibility are not.
