# MM-BUG-KILN-00076 — amp-lab silently reverts the selected program and bank at every loop wrap

- **State:** Fixed
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Took the asset route: channel 1's bank +
  program removed from the generator and `backing.mid` regenerated, guarded by two oracles.
  Awaits independent two-eyes closure.)

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

## Resolution

Took the report's **first** route — fix the asset — rather than the runtime-filter
alternative, because `backing.mid` is `include_bytes!`d (`main.rs:20`) and is therefore the
tool's *only* input. There is no user-supplied sequence for a filter to defend against, so
a filter would have been dead code guarding a case that cannot arise.

`crates/amp-lab/tools/make_backing_loop.py` no longer authors `CC0` or Program Change on
`LEAD`; `assets/backing.mid` regenerated (2494 → 2487 bytes, the two removed events).
Safe because `Lab::new` already calls `send_rig()` at startup, so the channel is
initialized from the current `Rig` either way — the backing was never the only source.

CC7 (volume) and CC10 (pan) stay backing-owned: they place the guitar in the mix, they do
not choose which guitar it is. Only voice state conflicted with the GUI.

Two oracles, both proven red against the pre-fix asset:

- `seq::tests::backing_asset_leaves_the_ui_channel_voice_alone` — the asset census the
  report asked for. It parses the same `include_bytes!` blob the binary ships and rejects
  the whole class (Program Change, Bank Select MSB **and** LSB) on the GUI-owned channel,
  rather than checking for the two specific messages the generator happened to write. So
  neither an edited generator nor a hand-edited asset can quietly reintroduce it. Red at
  **2** offending messages.
- `seq::tests::two_wraps_never_re_send_the_ui_channel_voice` — the two-wrap regression,
  read through `Player::advance` rather than off the asset, so a future `advance()` that
  re-emitted setup state at a boundary would be caught even with a clean asset. Red at
  **6** messages: `[B1 00 01]` and `[C1 1D]` replayed three times across two wraps, which
  is the reported defect exactly.

Both are needed. The census alone would miss a player bug; the wrap test alone would pass
on a clean player with a dirty asset that some other path replays.

**Not verified:** the audible transition. amp-lab is a GUI holding a live cpal output
device, so running it is not something to do unattended — the same reason the report
says the application was not run. The claim proven here is the deterministic one: those
bytes no longer exist in the asset and are never emitted across two wraps.

**Gate note:** `.deltic-integrate.toml` excludes `amp-lab` from the integration gate, so
`cargo test -p amp-lab` (10 passed) and `cargo clippy -p amp-lab --all-targets -- -D
warnings` were run here directly — the trunk gate will not repeat them.

## Notes

The rhythm guitar, bass, drums, and their setup messages remain backing-owned.
Only channel 1's program/bank ownership conflicts with the GUI.
