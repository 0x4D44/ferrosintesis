# MM-BUG-KILN-00200 — Cross-crate WAV basename-collision oracle misses ALIASES logical names, so aliases can be silently shadowed

- **State:** Fixed
- **Priority:** Could
- **Severity:** Medium
- **Area:** sampler embedded_wav / oracles
- **Raised:** 2026-08-14T10:21:10Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-14T10:21:10Z, raised via `deltic bugs new` model=claude-fable-5) -> Fixed (2026-08-15T16:43:29Z, deltic:auto role=fix run=fix-20260815T163920Z-p33716-n490348200-c1 branch=task/bug-MM-BUG-KILN-00200-run-fix-20260815T163920Z-p33716-n490348200-c1 code=5f41660 gate=manual)

## Observation

**Symptom.** The cross-crate shadowing oracle
`no_two_asset_crates_ship_the_same_wav_basename`
(`crates/ferrosintesis/src/payload.rs:442-498`) enumerates only **physical**
`samples/*.wav` basenames on disk. But the namespace `embedded_wav`
(`crates/ferrosintesis/src/sampler.rs:205-229`) actually resolves is larger: each
crate's `get()` first rewrites its own **ALIASES logical names** to canonical files
(`crates/ferrosintesis-samples-vcsl-steinway/src/lib.rs:157-166`), so the chain's real
namespace includes 27 steinway + 16 kawai alias names the oracle never sees.

**Failure scenario (both directions), all suites green:**

1. A future crate earlier in the chain (core is 1st; steinway 6th, kawai 7th) adds a
   physical WAV named e.g. `steinwayb_C4_mf.wav`. No physical duplicate exists, so the
   oracle passes — but core now answers that name first, and steinway's alias (which
   maps it to `steinwayb_C4_pp_rr2.wav`) is silently shadowed: the voice plays the
   wrong recording.
2. A steinway/kawai alias name collides with a physical WAV in any crate **after**
   position 6/7: the alias answers first and the later crate's file is unreachable —
   again invisible to the oracle, because the alias name appears in no `samples/`
   directory.

This is exactly the failure the oracle's own doc comment warns about ("wrong TIMBRE on
a voice nobody edited: the hardest kind of bug to trace"), and the enumeration
predicate ("basenames on disk = the lookup namespace") is a hand-maintained assumption
of the KILN-00071/72/73 class — it was correct when written and silently stopped being
complete when MM-BUG-KILN-00165/00162 introduced the ALIASES mechanism. `read_aliases`
(`tools/ferrosintesis-samples/gen_crate_lib.py:62-63`) checks alias-vs-physical
collisions only **within its own crate**.

**Current state is clean** — every steinway/kawai alias name is prefix-disciplined
(`steinwayb_*` / `kawai_*`) and collides with nothing today (verified against the
scan's own corpus, 2026-08-14). Latent oracle gap, not shipped wrongness.

Found by the 2026-08-14 review pass over `crates/ferrosintesis-samples-vcsl-steinway/`
(adversarial verify stage); independently re-verified against `payload.rs` and the
`embedded_wav` chain by the reviewing lead.

## Fix

<unfixed — raised only>

Suggested shape: fold logical names into the scan — for each asset-crate directory,
also parse an `ALIASES` file when present (same `alias canonical` row format
`read_aliases` consumes) and insert the alias names into the same `owner` map the
physical basenames use. That keeps the oracle derived-from-source (the committed
ALIASES manifests) rather than adding a second hand list. Prove it by temporarily
planting a colliding basename in a scratch copy and watching the strengthened test
name both owners.

## Notes

- Sibling of MM-BUG-KILN-00199 (vacuous alias-resolution assertion in the same
  mechanism); separable fixes.
