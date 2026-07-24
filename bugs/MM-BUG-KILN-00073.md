# MM-BUG-KILN-00073 — prewarm oracle enumerates only pub *_bank, missing four realtime lazy caches

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler / realtime
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
- **State history:** Open (2026-07-24 — split from MM-BUG-KILN-00059 on its independent
  two-eyes closure. Found by Codex gpt-5.6-sol; each item independently re-confirmed by
  Claude Opus 4.8 (1M), who wrote the oracle.)

## Observation

**Symptom.** Four realtime-reachable lazy caches still decode on first use, inside the
audio callback, and the KILN-00059 oracle cannot see any of them.

**Root cause.** `every_public_bank_accessor_is_exercised` enumerates the wrong set. It
scans for `pub fn *_bank`, but that predicate is narrower than "realtime lazy cache" in
three separate ways:

| Cache | Why the scan misses it |
|---|---|
| `bottle_loop_bank` (`sampler.rs:3342`) | private `fn`, not `pub` |
| `chanter_rr2` (`sampler.rs:2254`) | private `fn`, a round-robin variant with no public `*_bank` wrapper |
| `rain_loop` (`sampler.rs:86`) | `pub fn`, but not named `*_bank`, and returns `&[f32]` |
| `GONG_LAYERS` (`sampler.rs:3958`) | a bare `static OnceLock<(Vec<f32>, Vec<f32>)>` — not built by `bank!`, so the `BANK_INITS` counter never even counts it |

Confirmed present, and confirmed absent from `prewarm()`:

```
$ sed -n '/^pub fn prewarm()/,/^}/p' crates/ferrosintesis/src/sampler.rs \
    | grep -c "bottle_loop_bank\|chanter_rr2\|GONG_LAYERS\|rain_loop"
0
```

`GONG_LAYERS` is the worst of the four: because it is not a `bank!` construction, it is
invisible to *both* oracles — the counter cannot count it and the source scan cannot
name it. A future cache of that shape would be equally invisible.

**Relation to KILN-00059.** That fix is sound as far as it goes — it took prewarm from
24 of 80 caches to complete coverage of every `bank!`-built `Zone` bank, and its
"56 uninitialized" measurement stands. This bug is the part its enumeration predicate
could never reach, and it is why the KILN-00059 entry's scope claim should be read as
"every `bank!`-built Zone bank", not "every cache".

## Fix

Add the four to `sampler::prewarm()`, then widen what the oracles enumerate so the
predicate matches the actual invariant — *every lazily-initialized cache reachable from
a realtime NoteOn* — rather than a naming convention:

- Count initializations at the `OnceLock` level rather than only inside `bank!`, so
  non-`Zone` caches like `GONG_LAYERS` are counted too. A small helper wrapping
  `get_or_init` that every cache is required to use would make the counter total, and
  the source scan could then assert that no `OnceLock` is initialized by a bare
  `get_or_init` bypassing it.
- Failing that, scan for `static …: OnceLock<…>` declarations instead of `pub fn *_bank`
  and require each enclosing function to be reachable from the exercise sweep. Less
  elegant, but it keys off the thing that actually makes a cache lazy.

Whichever route, prove it the same way KILN-00059 was proven: the strengthened oracle
must fail on today's tree, naming these four, before the prewarm additions are made.

## Notes

- `MM-BUG-KILN-00064` separately covers GM 76's per-NoteOn loop search and notes that
  `prewarm()` points at the retired `bottle_bank()` rather than `bottle_loop_bank()`.
  That overlaps this bug's `bottle_loop_bank` item; whichever lands second should check
  the other's work rather than duplicating it.
- Reinforces the CLAUDE.md convention added today: a derived oracle is only as good as
  its enumeration predicate. Deriving from `pub fn *_bank` was still a hand-maintained
  assumption wearing a source-scan's clothing.
