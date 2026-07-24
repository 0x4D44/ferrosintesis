# MM-BUG-KILN-00088 — Mandolin round-robin phase splits across engine spawns and voice retriggers

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / mandolin round robin
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-mandolin/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). One bank-scoped strike phase: the engine
  counter now advances only for a variation that rotates takes, and a retriggered voice
  hands its sounding take back through the new `Voice::rr_phase`. Engine-level oracle
  added; both defects proved independently. Evidence under "Fix landed" below. Awaits
  independent two-eyes closure.)

## Observation

**Symptom.** A mandolin phrase boundary can immediately replay a round-robin
take and break the recorded down/up pick order.

The source-level sequence is:

1. A fresh mandolin NoteOn consumes engine `pitched_rr == 0`, plays `rr1`, and
   advances the engine counter to 1.
2. A same-key NoteOn within 100 ms retriggers the existing `LaVoice`, which
   rotates its private index and plays `rr2`. The early return does not advance
   the engine counter.
3. After a gap longer than 100 ms, the next fresh voice consumes the still-1
   engine counter and plays `rr2` again.

The heard sequence is therefore take 0, take 1, take 1 rather than take 0,
take 1, take 2. Because the recorded takes encode alternating pick direction,
this gives down/up/up and repeats identical onset PCM at the phrase boundary.

There is a second manifestation of the same ownership defect.
`crates/ferrosintesis/src/engine.rs:2565-2587` advances `pitched_rr` for every
non-alt melodic spawn, not only mandolin. A base steel or unrelated LSB voice
on the same channel/key can therefore perturb the next mandolin take.

**Expected.** One bank-scoped source of truth advances exactly once for every
accepted mandolin stroke, including a fast retrigger, and unrelated voices do
not consume its phase.

**Actual.** Fresh spawns advance `pitched_rr` at
`crates/ferrosintesis/src/engine.rs:2567-2586`. Fast strokes return at
`crates/ferrosintesis/src/engine.rs:2491-2501` after advancing only
`LaVoice::rr` at `crates/ferrosintesis/src/sampler.rs:3377-3413`.

This review was source-only by contract; the application, tests, and audio were
not run.

## Fix

Make one bank-scoped strike phase authoritative. Advance it exactly once for
every mandolin stroke, whether the stroke spawns or successfully retriggers a
voice, and do not advance it for base/undefined/other variation voices.

Add an engine-level state oracle covering:

- fresh take 0 → fast retrigger take 1 → gap → fresh take 2;
- multiple fast strokes followed by a fresh phrase;
- base steel and unrelated LSB notes on the same channel/key before mandolin;
- counter wrap after take 3.

Estimated effort: Small–Medium.

## Fix landed (2026-07-24)

**Code.** The phase now has exactly ONE owner at a time.

- `voices::variation_round_robins(program, bank_lsb)` is the single table of which
  variations own a strike phase. Both `make_variation`'s construction and the engine's
  counter read it, so the two cannot disagree about who consumes a take.
- `crates/ferrosintesis/src/engine.rs` advances `pitched_rr` only when that table says the
  variation rotates. It used to advance on every melodic spawn, on the theory that the
  counter is inert elsewhere — true of the voice it builds, false of the phase.
- New `Voice::rr_phase()` (default `None`, implemented by `LaVoice`) reports the take
  currently SOUNDING. On a successful retrigger the engine mirrors it as `sounding + 1`, so
  the next fresh spawn resumes the sequence. Mirroring the sounding take rather than adding
  one per stroke is deliberate: `LaVoice::retrigger` declines the rotation when the next
  take would repitch outside 0.5..=2.05, and a blind increment would desync there.

**Regression** — `the_mandolin_strike_phase_is_bank_scoped_and_survives_a_retrigger`
(`engine.rs`). It asserts on the SOUNDING take, not on the counter, so it measures what a
listener hears: fresh 0 → fast retrigger 1 → gap → fresh 2; a tremolo run that wraps past
the last take continues rather than restarting; and neither base steel (LSB 0) nor an
undefined LSB on the same channel and key consumes the phase.

**Fails before, each defect independently.** Removing only the retrigger hand-back:
"the fresh voice after the gap replayed a take the retrigger already played" (left 1, right
2). Restoring only the advance-on-every-spawn: "base steel guitar (LSB 0) consumed the
mandolin's strike phase" (left 3, right 0).

**Blast radius — predicted, then falsified against the renders.** A census of all 141
committed MIDIs finds three files using the mandolin bank, and predicts which can move:
Hollow Hill Pt 1 (4 mandolin key-pairs, no fast restrikes, no keys shared with other
voices) cannot; Pt 2 (3 shared keys) and The Signal Fire (459 fast restrikes, 2 shared
keys) must. Rendering against a baseline built at `31468cd` matched the prediction exactly
— Pt 1 identical, Pt 2 and The Signal Fire differing, and both controls (Big Weather 01, a
GM-sweep demo) identical.

**Where the diff sits.** A whole-file `cmp` is misleading here: the renders are
loudness-normalized, so any local change shifts the global gain and every sample differs.
Removing that gain (median per-second RMS ratio 1.000046) localizes the real change — the
12 worst-affected seconds of Hollow Hill Pt 2 are ALL inside the 718–747 s mandolin
passage (3.5–4.2% residual) against a median second of 0.014%. The change reached the
mandolin and nothing else, which is the intended improvement: the takes rotate in the
recorded down/up pick order instead of replaying at phrase boundaries.

**Gates.** `cargo test --release -p ferrosintesis` 659 passed / 0 failed / 26 ignored (+4
doc-tests); clippy `-D warnings` clean; `cargo fmt --check` clean.

## Notes

The existing sampler oracle proves strict rotation inside one continuously
retriggered `LaVoice`. It cannot see the hand-off back to the engine-owned
counter at a fresh-spawn boundary.

