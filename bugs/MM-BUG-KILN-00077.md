# MM-BUG-KILN-00077 — amp-lab Copy Settings emits a nonexistent album authoring API

- **State:** Open
- **Priority:** Must
- **Severity:** Medium
- **Area:** amp-lab / export
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

`Rig::export()` labels its output as `engine.py` authoring code but emits bare
calls such as `amp(0, 72)` (`crates/amp-lab/src/amp.rs:107-139`). A repository-wide
source lookup found no `def amp(...)` in any album engine. The existing fable5
surface is `Score.cc(ch, num, val, beat)` (for example
`albums/fable5/Big Weather/engine.py:173-176`), so the copied snippet also lacks
the score object, channel, and event time. The separately labelled “raw NRPN”
section contains `index:value` summaries, not MIDI messages.

Expected: Copy Settings produces code that can be pasted into an album and
authors the same complete rig. Actual: the advertised `engine.py` calls raise
`NameError` unless the user first invents an undocumented helper, and the output
does not carry enough context to call the existing API directly.

The current unit test checks knob names and neutral prose only
(`crates/amp-lab/src/amp.rs:171-184`), so it cannot detect an unusable export.

## Fix

Export concrete calls against an existing album API, with explicit placeholders
for score, channel, beat, bank, and program. For fable5 that means the three
NRPN CC messages per non-neutral knob using
`sc.cc(ch, 99, 0x30, beat)`, `sc.cc(ch, 98, index, beat)`, and
`sc.cc(ch, 6, value, beat)`, plus the selected CC0 and Program Change in a form
the engine actually supports. If a new helper is preferred, land and document
the helper before emitting it.

Add an export oracle that executes or parses the supported snippet and proves
its MIDI bytes equal `Rig::bytes()` for all four program/bank combinations and
representative knob states.

## Notes

The numeric summary remains useful for manual transcription. It does not satisfy
the README and HLD promise that export is the tool's pasteable deliverable.
