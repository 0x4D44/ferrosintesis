# MM-BUG-KILN-00078 — amp-lab quantizes every MIDI event to an audio-callback boundary

- **State:** Open
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

## Notes

Keeping the sequencer on the audio thread avoids UI repaint jitter, but thread
placement alone does not make the current delivery sample-accurate.
