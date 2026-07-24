# MM-BUG-KILN-00065 — Bottle regeneration fails clean-cache runs and routes the source to the wrong crate

- **State:** Closed
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The bottle loop now has one owner:
  `bake_bottle_loop`, wired to `--only=bottle`, with the source SHA-256 pinned, its own
  crate routing, and the whole-voice source excluded from onset discovery. The recipe was
  RECOVERED by measurement and is machine-pinned. The retired MuseScore onset is
  deliberately NOT removed — see "Fix landed". Awaits independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

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

## Fix landed (2026-07-24)

**Four defects, four fixes** (`tools/ferrosintesis-samples/prepare.py`):

1. **Wrong crate.** `FAMILY_PACKAGE` gained `bottle` and `bottleloop`, both routing to
   `ferrosintesis-samples-bottle`. Before, family `bottle` matched nothing and fell back
   to `-orchestral`.
2. **Swept into onset discovery.** `FREESOUND_SOURCES` now excludes
   `BOTTLE_LOOP_SOURCE`. It is a whole-voice loop; the generic loop would trim it to an
   attack. Excluding it at discovery beats special-casing it in five downstream places.
3. **Clean-cache staging.** `--only=bottle` now stages the committed Freesound sources
   (the condition listed only rhodes / dulcimer / musicbox), so it no longer reaches
   `read_wav` on a file that was never copied.
4. **No producer.** New `bake_bottle_loop()` verifies the pinned source SHA-256, applies
   the trim/fades/normalisation, and writes the asset to the bottle crate. It is wired
   into `main()` under `want("bottle")`, gated like the gong so `--only=<other>` can
   never rewrite the tracked WAV.

**The recipe was recovered by measurement, not read from the note.** The provenance text
said "trimmed 0.45–2.10 s" of a 2.0 s source — an interval that does not exist. Measuring
the committed WAV against the committed source gives, exactly: trim frames 4411–77176
(0.1000 s – 1.7500 s, NCC 1.000000 at that alignment), 131-sample linear fade-in, 2647-sample
quadratic fade-out, peak normalised to 0.9. `PROVENANCE.md` now carries that table and
records the correction.

**What this does NOT achieve, stated plainly.** The bake reproduces the committed asset to
within **24 LSB** (worst sample; peak 29490, so ≈ −71 dBFS) but **not** byte-for-byte. The
original bake was never checked in, so its exact float path is unknown — the residual is a
uniform ~2e-5 gain difference plus rounding, spread evenly across the file, not a shape
error. I did not overwrite the shipped WAV to force a match: that would change a tracked
asset and the GM 76 render on a guess about the original pipeline, which is Arthur's call,
not a fixer's. So the pinned digest the bug asks for is a pinned **tolerance** instead, and
the test proves the bound is tight rather than slack: a ONE-SAMPLE trim error moves the
output 1045 LSB, 43x the bound.

**Deliberately not done: removing the retired MuseScore GM 76 onset.** The bug offers
"remove it, or give it an explicit alternate-bank route". CLAUDE.md is explicit that a
voice is judged by whether it is correct and reachable, not by in-repo usage, and that a
suspected-dead feature is Arthur's call rather than a tidy-up. It is also still prewarmed
(`bottle_bank`). Left in place and flagged.

**Regression** — four tests in `tools/ferrosintesis-samples/test_prepare.py`:

- the whole-voice source is not in generic onset discovery;
- neither `bottleloop_G3.wav` nor `bottle_G3.wav` routes to `-orchestral`;
- the bake reproduces the committed asset within the bound (writing to a temp root — it
  never touches the tracked WAV);
- a tampered source is refused by the SHA-256 pin.

**Fails before / passes after.** Reverting the routing and discovery fixes fails two of
them, naming `bottleloop_G3.wav routes to ferrosintesis-samples-orchestral`. Shifting the
trim start by one sample fails the recipe pin at 1045 LSB.

**Gates.** `python -m unittest test_prepare` — 31 passed (27 pre-existing + 4 new). No Rust
code changed, and no tracked WAV was rewritten.

## Notes

- No existing Open bug or Draft/Accepted requirement covers this bottle-specific
  ownership and routing failure.
- Security, maintainability, devil's-advocate, and team-lead source passes confirmed
  the control flow. The generator itself was not run because this review was
  intentionally read-only.

