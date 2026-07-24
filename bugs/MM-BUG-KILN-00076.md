# MM-BUG-KILN-00076 — amp-lab silently reverts the selected program and bank at every loop wrap

- **State:** Open
- **Priority:** Must
- **Severity:** High
- **Area:** amp-lab / audition state
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

**Static reproduction.** Select GM30 or the main bank in amp-lab, then let the
backing sequence cross a loop boundary.

The committed backing generator authors `CC0=1` and Program 29 on the
UI-controlled channel 1 at tick zero
(`crates/amp-lab/tools/make_backing_loop.py:62-65`). `Player::advance()` resets
its event index to zero at every wrap (`crates/amp-lab/src/seq.rs:188-191`), and
the audio callback forwards those tick-zero messages to the synth
(`crates/amp-lab/src/audio.rs:99-111`). UI rig changes are one-shot messages
(`crates/amp-lab/src/main.rs:88-100`), so the repeated backing messages win.

Expected: the selected program and bank remain active until the user changes
them. Actual: every wrap restores GM29 lead while the UI and copied export still
show the selected rig. Authored amp-knob offsets survive Program Change and CC0;
the voice and bank are the state that reverts.

This was confirmed from the source and the committed MIDI's tick-zero bytes. The
application was not run, so the audible transition itself remains unmeasured.

## Fix

Remove channel 1's CC0 and Program Change from the generated backing sequence,
regenerate `assets/backing.mid`, and initialize that channel solely from the
current `Rig`. Alternatively, filter UI-owned channel state from repeated
backing events and reapply the current rig deterministically.

Add a two-wrap regression that selects a non-default program/bank and proves the
effective state still matches the UI after the second tick-zero boundary. Also
derive an asset census that rejects CC0/Program Change on the UI-owned channel.

## Notes

The rhythm guitar, bass, drums, and their setup messages remain backing-owned.
Only channel 1's program/bank ownership conflicts with the GUI.
