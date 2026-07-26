# MM-REQ-KILN-00137 — Album channel balance must be re-verifiable against the current synth

- **State:** Draft
- **Priority:** Should
- **Area:** albums / balance
- **Raised:** 2026-07-26
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-26, raised via `deltic reqs new`)

## Statement

An album engine sets its channel levels (velocity, CC7/CC11) against the voice
levels of the day it was composed. The synth has moved a long way under them —
hundreds of commits of voice work plus the `PROGRAM_TRIM_DB` table — so a
committed `.mid` can now render with a balance its composer never intended, and
nothing detects that.

**The system must be able to say, per album track, which channels have drifted
from the in-mix level they were authored to sit at.** The reproducible artifact is
the `.mid`, so the drift is not in the source but in the render, and it needs a
render-side oracle rather than an eyeball.

Two parts, and Gate 1 should decide whether they split:

1. **The check.** A per-channel in-mix level census across the catalogue,
   comparable over time — e.g. per-channel momentary loudness at the track's own
   normalization, stored as a committed baseline and diffed, the way
   MM-BUG-KILN-00118 asked for a per-program residual baseline. Without a stored
   baseline this can only ever be found by someone listening, which is how it was
   found this time.
2. **The rebalance.** Fix the albums the check flags. That tail is one-shot work,
   not a durable requirement, and it is potentially large — every album is its own
   engine, and a rebalance edits committed `.mid` output.

Flagged `heavy`: cross-cutting, touches every album, needs a design decision on
what "the level it was authored to sit at" even means for a generative engine
whose output is the only record of intent.

## Notes

Raised 2026-07-26 out of MM-BUG-KILN-00107. Arthur, judging GM6 harpsichord in
album mixes, found the trim unjudgeable there because the mix already encodes the
composer's balance; on a flat Reference-Audition peer comparison the same voice at
the same trim was the *quietest* in its family. His conclusion: "so some of our
tracks will need rebalancing (but I think we knew that already)".

Concrete first instance: `albums/gpt5-6/Atlas of Becoming/midi/11 - Clockwork
Orchard.mid`, where the harpsichord reads as prominent in the mix while measuring
2.6 LUFS below its peers on the audition. That gap is an arrangement/level
decision in the album, not a synth defect — KILN-00107 settled the synth side.

Related: MM-REQ-KILN-00018 (Retired) covered keeping committed *listening assets*
current, which the move to git-ignored renders solved. This is the different and
still-open problem: the committed `.mid` itself encodes a balance that has aged.
