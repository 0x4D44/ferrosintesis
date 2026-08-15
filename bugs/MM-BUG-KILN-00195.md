# MM-BUG-KILN-00195 — B1 upright crate-side asset validator never checks fmt/data/pad, so a consumer-panicking asset publishes green

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** samples-b1-upright / oracles
- **Raised:** 2026-08-14T07:06:13Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T034422Z-p27896-n097946200-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-KILN-00195-run-fix-20260815T034422Z-p27896-n097946200-c1
- **Owner base:** 16be7cf47636b6249bee455ccdfdc25bef5b9c26
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T03:44:22Z
- **Owner until:** 2026-08-15T05:44:22Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-14T07:06:13Z, raised via `deltic bugs new` model=claude-fable-5)

## Observation

**Symptom.** At `cargo publish` time the asset crate's own tests are the only gate, and
its handwritten validator (`crates/ferrosintesis-samples-b1-upright/src/lib.rs:246`,
`b1_tail`) validates only the `b1t ` natural-tail chunk. It never inspects the `fmt `
chunk, the `data` chunk, or pad bytes. The runtime parser
(`crates/ferrosintesis/src/sampler.rs:95`, `parse_b1_tail`) rejects all of those — and
`b1_bank!` turns any rejection into a panic at bank build
(`crates/ferrosintesis/src/sampler.rs:347-348`), which prewarm reaches on every
samples-on run.

**Checks the runtime does that the crate test does not** (line-by-line diff, verified):

1. odd-length chunks must carry a zero pad byte (`sampler.rs:126-128`);
2. exactly one `fmt ` chunk: PCM format 1, mono, 44 100 Hz, block-align 2, 16-bit
   (`sampler.rs:131-143,195`);
3. a unique, nonzero, even-length `data` chunk (`sampler.rs:144-151,195`) whose frame
   count matches the independently decoded body (`sampler.rs:198-199`);
4. `entry_frame < pcm_frames` (`sampler.rs:178-180`). The crate test pins
   `entry == 59_535` (`lib.rs:269-273`) but never parses `data`, so it cannot relate
   the entry point to the body it enters.

**Failure scenario.** A bake defect (or manual edit) that rewrites one WAV's `fmt ` to
stereo/8-bit, drops its `data` chunk into a same-sized junk chunk, or truncates `data`
below frame 59 535 with the RIFF size fixed up passes `cargo test -p
ferrosintesis-samples-b1-upright` (structure, tail, and both aggregate byte pins can all
stay green) and publishes clean — then every ferrosintesis consumer panics in
`b1_bank!` on first prewarm. The workspace's strict-parse tests
(`sampler.rs:9711-9764`) do catch it, but they live in `ferrosintesis`'s suite and do
not run at asset-crate publish.

**Correlated blindness.** The regen tool's validator
(`tools/ferrosintesis-samples/regen_samples_table.py:51-99`, `b1_tail_payload_size`) is
a faithful mirror of the same tail-only predicate, so tool and test share the identical
blind spot and cannot fail independently — the correlated-oracle failure mode
MM-BUG-KILN-00071/72/73 documented for the licensing/manifest/prewarm oracles.

Found by an adversarial defeat-the-oracle review pass (2026-08-14 code review,
`crates/ferrosintesis-samples-b1-upright/`); finding independently re-verified against
source by the reviewing lead.

## Fix

<unfixed — raised only>

Suggested shape: teach the crate-side `b1_tail` test validator (and the shared regen
predicate) the runtime's checks — one strict `fmt `, one even nonzero `data` whose
frame count the tail entry must fall inside, zero pad bytes — or, better, derive both
from one shared strict predicate so they cannot drift apart again. Prove it the
KILN-00073 way: mutate one embedded WAV in each defeated direction and watch the
strengthened crate test go red before trusting it.

## Notes

- The runtime parser itself is sound; this is purely the publish-time gate on the asset
  crate being weaker than what the consumer requires.
- Same-class precedent: MM-BUG-KILN-00071/72/73 (oracle predicates holed by an
  adversarial pass, all Closed).
