# MM-BUG-KILN-00126 — Published drum-kit inventory and kick provenance are stale

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** drum-kit package documentation / provenance
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`)

## Observation

The core crate's published README still describes the pre-split cymbal bank.

`crates/ferrosintesis-samples-drumkit/README.md:3-10` claims 109 WAVs and lists
crash, sizzle crash, splash, and china as core contents sourced partly from Big Rusty
Drums. The core crate actually embeds 140 ride/hat/kick/snare/tom WAVs
(`crates/ferrosintesis-samples-drumkit/src/lib.rs:27-33`), while those four accent
banks moved to the companion crate
(`crates/ferrosintesis-samples-drumkit/PROVENANCE.md:19-32`).

The tooling overview repeats the old ownership at
`tools/ferrosintesis-samples/README.md:3-7`.

The core provenance has a second, independent factual error. It says every bank uses
the `mid` mic set and names the kick source stem `mid_kick_snon` at
`crates/ferrosintesis-samples-drumkit/PROVENANCE.md:36-52,60-72`. The generator
intentionally sources all sixteen kick takes from the `kickmic` close-mic set at
`tools/ferrosintesis-samples/prepare_drumkit.py:97-101`. Commit history confirms the
kick payloads and generator changed together when the kick was re-sourced.

Expected: packaged documentation accurately identifies the crate's contents and the
recording source behind each shipped family.

Actual: crates.io consumers and provenance auditors receive the old package boundary
and the wrong kick microphone. The sources are CC0, so this is not an attribution
breach; it is inaccurate published inventory and provenance.

## Fix

Update the core crate description and README to describe its 140-file core-kit
inventory and point to `ferrosintesis-samples-drumkit2` for the 48 accent WAVs.
Update the tooling overview to describe both destinations.

In core `PROVENANCE.md`, document `mid` for every family except the kick, and record
the kick's `kickmic_kick_snon` source stem and close-mic rationale.

Add an adversarial documentation oracle only if this drift recurs: derive crate
ownership and source stems from one generator manifest rather than maintaining the
same facts in several prose files.

Estimated effort: Small.

## Notes

No existing bug or open requirement covered these current drum-kit documentation
errors.
