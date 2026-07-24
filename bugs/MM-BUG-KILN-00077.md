# MM-BUG-KILN-00077 — amp-lab Copy Settings emits a nonexistent album authoring API

- **State:** Fixed
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Export now calls the real `Score` API and is
  proven byte-equal to `Rig::bytes()`. Awaits independent two-eyes closure.)

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

## Resolution

`Rig::export()` now emits the album engines' **actual** surface —
`sc.cc(ch, num, val, beat)` and `sc.program(ch, prog, beat)` — with `SC`, `CH` and `BEAT`
as explicit placeholders, replacing the `amp(idx, val)` helper that exists in no engine.

Chose the report's first option (emit against the existing API) over its second (land a new
helper first). A helper would have to be added to every album's copied `engine.py`
independently — they are per-album copies, not a shared import — so it would multiply
the surface that can drift, for a snippet that is already only three calls per knob.

**Every knob is emitted, including neutral ones.** The old export filtered neutrals out.
That is wrong for a paste target: an album's channel may already carry a non-neutral amp
block from an earlier beat, and eliding neutrals would inherit those rather than reset
them. Writing all six makes the snippet *set* the rig. It is also what makes byte-equality
with `Rig::bytes()` a meaningful check rather than a curated one.

Ordering already matched: `Score.cc`'s own sort key ranks CC0 before a program change
before other CCs, which is exactly `Rig::bytes()`'s bank → program → NRPN order, so
the album writes the same stream the audition sent.

### The oracle

`amp::tests::export_snippet_reproduces_the_rig_bytes` parses the emitted snippet back into
MIDI and requires it to equal `Rig::bytes(ch)` **byte for byte**, so the pasted album and
the live audition cannot disagree about what the rig is.

Parsing in Rust rather than executing Python: the check stays self-contained (no interpreter
on PATH, no album fixture) and deterministic. The parser treats an unrecognised call as a
hard failure rather than skipping it — a line quietly ignored is a line the oracle does
not check — and cross-checks its parsed-line count against the number of `sc.` occurrences
in the whole export, so a malformed line cannot slip past by simply not matching.

Swept over **all four** program/bank combinations x five knob states (all-neutral, all-min,
all-max, mixed-with-extremes, representative) x four channels. The bank flag and program are
precisely what a single hand-checked case would have silently fixed.

Fail-first: restoring the old `amp(...)` line for the bank makes it fail immediately, naming
the rig and printing the offending export.

### Also updated

`crates/amp-lab/README.md` — its "Copy settings" bullet promised `engine.py` calls, which
is the promise this bug says was unmet. It now names the real API, states that all six knobs
are written and why, and points at the oracle, so the claim is checked rather than asserted.

**Not verified:** that a generated snippet was actually pasted into an album and rebuilt.
The equality proven is against `Rig::bytes()`, the same bytes amp-lab sends live; whether an
album's surrounding engine accepts it at a given beat is untested.

**Gate note:** `.deltic-integrate.toml` excludes `amp-lab`, so `cargo test -p amp-lab`
(11 passed) and `cargo clippy -p amp-lab --all-targets -- -D warnings` were run here
directly — the trunk gate will not repeat them.

## Notes

The numeric summary remains useful for manual transcription. It does not satisfy
the README and HLD promise that export is the tool's pasteable deliverable.
