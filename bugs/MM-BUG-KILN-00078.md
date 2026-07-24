# MM-BUG-KILN-00078 — amp-lab quantizes every MIDI event to an audio-callback boundary

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** amp-lab / sequencer
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Player reports offsets; the callback renders
  in spans; the callback core is factored out of the cpal closure so it is testable without
  a device. Residual is the synth's own 64-frame block, as the report anticipated. Awaits
  independent two-eyes closure.)

## Observation

The sequencer claims frame-accurate playback, but `Player::advance()` emits every
event due anywhere before `pos + frames` without returning its within-block
offset (`crates/amp-lab/src/seq.rs:170-185`). The callback sends all those bytes
to `RealtimeSynth` and only then renders the entire host block
(`crates/amp-lab/src/audio.rs:99-125`).

`RealtimeSynth::write_byte()` buffers completed commands until its next internal
64-frame fill (`crates/ferrosintesis/src/live.rs:223-243` and `:279-296`).
Consequently events are applied at callback/internal-block boundaries rather
than at `Event.frame`. A note may start early by almost one host callback; an
on/off pair due in the same callback is submitted before any of that callback's
audio is rendered.

Expected: scheduled drums and notes land at their declared frame offsets.
Actual: all events due in one callback collapse onto the start of a render
quantum. Exact audible jitter on Arthur's device is unverified because this
review did not run the application.

## Fix

Change the player interface to expose the next event's offset. Render the host
buffer in spans, inject each event immediately before its span, then render the
remainder. If 64-frame residual quantization is still unacceptable, add a
timestamped command surface to the realtime synth rather than discarding offsets
in amp-lab.

Add a device-independent callback-core test with variable host block sizes. Pin
the first changed output frame for several events, an on/off pair, and a loop
boundary instead of merely counting emitted events.

## Resolution

Three changes, in the order they matter:

1. **`Player::advance` now reports each event's offset within the caller's span**
   (`emit(off, msg)`). It had the information and threw it away.
2. **The callback renders in SPANS** — audio up to the next event, that event's bytes,
   then on. Submitting everything up front collapsed the whole block onto its first sample.
3. **The callback core is factored out of the cpal closure** into `audio::Core`. This is
   the change that makes the other two provable: the closure captures a device and can only
   run on real hardware, which is why a `Must`-severity scheduling defect existed with no
   failing test. `Core::process` takes a buffer and a frame count, so a test drives it at
   any block size with no audio device.

Residual quantization is `RealtimeSynth`'s own 64-frame internal block (~1.5 ms at
44.1 kHz). The report anticipated this and offered a timestamped synth command surface as
the follow-up; that is **not** done here. What the fix removes is the dependence on the
HOST buffer — previously up to 23 ms at a 1024-frame block, and it scaled with whatever
the device chose.

Realtime safety preserved: `pending` is pre-allocated to `MAX_EVENTS_PER_BLOCK` and an
overflow is counted as an xrun rather than growing on the audio thread; `fill_device` moves
the scratch out and back with `mem::take`, which swaps a pointer.

### Oracles, and three failed attempts worth recording

Landed:

- `audio::note_starts_at_its_own_frame_not_the_block_boundary` — pins the FIRST CHANGED
  OUTPUT FRAME across block sizes 64/128/256/512/1024. Red pre-fix at 1024 with the note
  543 frames (12 ms) early.
- `audio::an_on_off_pair_inside_one_callback_still_sounds` — red pre-fix: the pair
  collapsed and the note started 1567 frames early.
- `seq::advance_reports_offsets_within_the_callers_span_across_a_wrap` — exact integer
  offsets across a wrap.

The wrap case was attempted **three times as an audio test** and each version was defeated
by a different measurement artifact, all of which passed while the bug was present:

1. "is there a sound after the wrap" — true either way.
2. energy before vs after the scheduled onset — when collapsed, the note has decayed to
   near-silence by its slot, so both windows are ~0 and the ratio is noise.
3. first sample above an absolute gate — defeated twice over: the previous note's release
   tail sat above the gate at the wrap, and once that was fixed with a longer loop, the
   note's own ATTACK RAMP displaced the detected onset by ~230 frames.

The reason none worked is worth keeping: **collapsing quantizes an event to the start of the
callback CONTAINING it, not to the wrap.** The error is therefore at most one block, and any
audio window wider than a block sees the two behaviours as identical. The offsets are exact
integers, so measuring them as integers is both stronger and honest about the claim. That is
what landed.

**Not verified:** audible jitter on Arthur's device. amp-lab holds a live cpal output device
and was not run — the report had the same limit. The claim proven is that a scheduled
event's first changed output frame is within 64 frames of its declared frame, independent of
host block size.

**Gate note:** `.deltic-integrate.toml` excludes `amp-lab`, so `cargo test -p amp-lab`
(14 passed) and `cargo clippy -p amp-lab --all-targets -- -D warnings` were run here
directly — the trunk gate will not repeat them.

## Notes

Keeping the sequencer on the audio thread avoids UI repaint jitter, but thread
placement alone does not make the current delivery sample-accurate.
