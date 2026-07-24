# MM-BUG-KILN-00079 — amp-lab's advertised eight-bar loop lasts 32.983 beats

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / backing loop
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
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). The generator now closes the track ON the
  eight-bar line and the parser reads that authored End-of-Track as the loop boundary
  instead of inventing "last event + one beat". Asset regenerated; contract test added.
  Evidence under "Fix landed" below. Awaits independent two-eyes closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

The generator defines eight 4/4 bars (`PPQ=480`, `BAR=PPQ*4`, `BARS=8`) and its
last notes end eight ticks before beat 32
(`crates/amp-lab/tools/make_backing_loop.py:21-25`, `:49-51`, and `:76-114`).
The parser ignores an authored loop boundary and instead sets loop length to
`last_channel_event + PPQ` (`crates/amp-lab/src/seq.rs:139-143`).

The resulting duration is:

`(32 * 480 - 8) + 480 = 15,832 ticks = 32.9833 beats`.

At 104 BPM, the loop runs about 0.567 seconds beyond the exact eight-bar
boundary. The README/HLD call this an eight-bar seamless loop, so its downbeat
period is statically inconsistent with the contract. The parser comment shows
that a tail was intentional, but “last event plus one beat” is not a musical bar
boundary and makes the loop nearly nine beats longer than its final bar onset.
Whether effect tails mask the gap is unverified because no audio was rendered.

## Fix

Author an explicit end boundary in the MIDI and preserve it in parsing. For the
current generator, advance End-of-Track by the remaining eight ticks to
`BARS * BAR`; have the parser use the maximum declared track end (or a dedicated
loop marker) rather than inventing `last event + one beat`.

Add an asset-contract test that proves the committed loop is exactly
`BARS * 4` beats and that the first downbeat after wrap lands on the next bar,
independent of where the last note-off happens.

## Fix landed (2026-07-24)

**Both halves, because either alone leaves the bug.**

1. **The asset now says where it ends.** `make_backing_loop.py` writes End-of-Track at
   `BARS * BAR` (tick 15360) instead of at delta 0 after the last note-off (15352). The
   eight-tick tail inside the final bar stays deliberate; what changes is that the file
   now STATES its boundary.
2. **The parser believes it.** `Loop::parse` records the latest declared End-of-Track and
   uses it as the loop length when it lies past the last event. The old rule — last event
   plus one beat — is not a bar boundary and has nothing to do with the authored meter;
   it produced 15,832 ticks = **32.9833 beats**, so every wrap drifted ~0.567 s past the
   downbeat at 104 bpm.

The fallback is kept for a file that closes its track ON the last event or omits the meta
entirely: a loop still needs somewhere to breathe, and amp-lab should not refuse to play
a hand-made MIDI.

**Regression** — `the_backing_loop_is_exactly_eight_bars` asserts the parsed loop is
within 0.01 beat of eight bars, computed from the METER (4 x 60/104 s per bar), not from
the generator's constants. That distinction matters: asserting against `BARS * BAR` would
let an edit to the generator redefine what "eight bars" means and still pass. It also
pins that the first event sits at frame 0, so a wrap lands on a downbeat rather than
merely being the right length.

**Fails before, each half independently:**

- Parser reverted to `last_tick + ppq`: *"the eight-bar loop is 32.9833 beats long (0.983
  beats off the bar line)"*.
- Parser fixed but the generator reverted (End-of-Track back on the last event, so nothing
  is declared past it and the fallback engages): the identical failure.

Passing requires both, which is why both landed together.

**The regenerated asset was verified byte-identical after the probes** (`cmp` against a
pre-probe copy), so the committed `backing.mid` differs from trunk only by the intended
eight-tick End-of-Track move.

**Gates.** `cargo test -p amp-lab` 18 passed / 0 failed; clippy `-D warnings` clean; `cargo
fmt --check` clean. amp-lab is excluded from the workspace gate, so these were run
explicitly.

## Notes

A deliberate release tail can still exist inside the authored eight bars. If a
non-metric pause is desired instead, document and label that duration rather
than calling the result an eight-bar loop.
