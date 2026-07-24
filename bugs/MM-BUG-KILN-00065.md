# MM-BUG-KILN-00065 — Bottle regeneration fails clean-cache runs and routes the source to the wrong crate

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / provenance
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol during the coverage-ledger review of `crates/ferrosintesis-samples-bottle/`)

## Observation

**Symptom.** The documented family selector `prepare.py --only=bottle` has no valid
path to regenerate the active `bottleloop_G3.wav`.

**Expected.** A targeted bottle regeneration should stage its committed source,
reproduce the whole-voice loop asset in
`crates/ferrosintesis-samples-bottle/samples/`, and leave unrelated sample crates
untouched.

**Actual.**

- `D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\tools\ferrosintesis-samples\prepare.py:982-986`
  dynamically includes `bottle_G3.wav` in `FREESOUND_SOURCES`.
- Lines 2553-2554 stage those sources only when Rhodes, dulcimer, or music box was
  selected. On a clean persistent temp cache, `--only=bottle` therefore reaches
  `read_wav(src/bottle_G3.wav)` at line 2653 without the file and fails.
- On a cache populated by an earlier full run, the command continues, but
  `FAMILY_PACKAGE` at lines 991-1021 has no `bottle` entry. The fallback at lines
  1033-1042 writes an onset-style `bottle_G3.wav` into
  `ferrosintesis-samples-orchestral`, not the bottle crate.
- A full run stages the source but takes the same wrong fallback route.
- No checked-in tool emits the active `bottleloop_G3.wav`. The separate branch at
  lines 2598-2609 rebuilds the superseded MuseScore `bottle_C6.wav` onset instead.

The provenance recipe at
`D:\worktrees\midi-music\20260724-REV-CLA@KILN-code-review-065916\crates\ferrosintesis-samples-bottle\PROVENANCE.md:14-24`
does not repair the gap. Static PCM comparison shows the packaged 1.65-second WAV is
the committed source interval approximately 0.100-1.750 seconds, with edge fades and
a 0.94738 normalization factor. The document instead says to trim 0.45-2.10 seconds
from a source it describes as 2.0 seconds long. It also pins only the input hash, not
the generated payload.

The current packaged WAV is valid and its source hash matches the provenance record.
This defect concerns repeatable regeneration and future payload integrity, not a
claim that today's audio is corrupt.

## Fix

Give the whole-voice bottle loop an explicit source manifest and deterministic bake
function. It should verify the committed source SHA-256, encode the exact trim/fades/
normalization, write `ferrosintesis-samples-bottle/samples/bottleloop_G3.wav`, and
verify a pinned output digest. Exclude `bottle_G3.wav` from generic onset discovery.

Remove the retired MuseScore GM 76 producer and bank, or give that onset an explicit
alternate-bank route if it is intentionally retained. Add clean-cache and warm-cache
tests for `--only=bottle`, plus a full-routing test proving no bottle output lands in
the orchestral crate.

## Notes

- No existing Open bug or Draft/Accepted requirement covers this bottle-specific
  ownership and routing failure.
- Security, maintainability, devil's-advocate, and team-lead source passes confirmed
  the control flow. The generator itself was not run because this review was
  intentionally read-only.

