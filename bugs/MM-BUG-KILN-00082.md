# MM-BUG-KILN-00082 — amp-lab allocates inside the deadline-bearing audio callback

- **State:** Open
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

## Notes

The allocation itself is confirmed from source. Its wall-clock duration and
audibility are not.
