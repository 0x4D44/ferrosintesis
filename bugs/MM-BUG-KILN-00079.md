# MM-BUG-KILN-00079 — amp-lab's advertised eight-bar loop lasts 32.983 beats

- **State:** Open
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

## Notes

A deliberate release tail can still exist inside the authored eight bars. If a
non-metric pause is desired instead, document and label that duration rather
than calling the result an eight-bar loop.
