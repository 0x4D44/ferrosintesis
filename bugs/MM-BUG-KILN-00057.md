# MM-BUG-KILN-00057 — non_guitar_la_render_is_pinned freezes a raw-f32 FNV hash: the last un-migrated bit-exact render golden, no diagnostic on failure and fragile across codegen

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** synth
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
- **State history:** Open (2026-07-24, raised via `deltic bugs new` by Claude Opus 4.8 (1M), from a `lessons_learnt.md` pruning pass; the original "will flip in release" premise was EMPIRICALLY TESTED here and found FALSE, and the bug re-scoped accordingly)

## Observation

**Symptom.** `non_guitar_la_render_is_pinned` (`crates/ferrosintesis/src/sampler.rs:5282`)
freezes a bit-exact FNV-1a hash of a raw f32 render and asserts it equals a hard-coded
constant:

```rust
let mut v = voices::make(56, 69, 100, 44100.0, 5, true);
let mut buf = vec![0f32; 22050]; v.render(&mut buf);
let mut h: u64 = 0xcbf2_9ce4_8422_2325;
for x in &buf { for b in x.to_bits().to_le_bytes() { h = (h ^ b as u64).wrapping_mul(0x0000_0100_0000_01b3); } }
assert_eq!(h, 0xaa11_bc63_b298_af8e, "non-guitar LA render changed (fnv {h:#x}) ...");
```

This is the last surviving cross-commit bit-exact float-render golden in the workspace — the
`drums.rs` goldens of this class were already migrated to `testutil::assert_render_signature`
(aggregate rms/centroid/envelope with relative tolerance), and `sawstack_v1_canary_frozen`
(the historical offender that flipped debug↔release and was re-pinned for months) was removed.
Two problems remain with the raw-hash form:
1. **No diagnostic on failure** — it reports only "fnv 0x… ≠ 0x…", giving a future engineer no
   idea whether the change was a benign codegen reorder or real contamination.
2. **Inherently non-portable** — a `to_bits()` FNV over a summed-oscillator render is sensitive
   to optimizer/CPU/opt-flag float-op reordering by construction.

**Empirical check (this is the part that corrects the seeding claim).** The original premise
was "latent — will flip the moment anyone runs `cargo test --release`." I ran it:

```
$ cargo test --release -p ferrosintesis non_guitar_la_render_is_pinned
test sampler::tests::non_guitar_la_render_is_pinned ... ok   (1 passed)
```

It is **green in release as well as debug on this box** — the GM56 render is bit-identical
across profiles here, so the "flips in release" claim is **false as stated**. The gate itself
only ever runs debug (`.deltic-integrate.toml` runs `cargo test --workspace --locked`, no
`--release`; no CI), so a release flip would be invisible if it ever did occur — but none is
demonstrated today.

**Expected.** Contamination detection (the test's real intent — "did guitar-only variation
leak into a non-guitar voice?") via a metric that (a) survives benign float-reorder noise and
(b) reports *what* changed. `assert_render_signature` already provides exactly this and is used
by 8 other call sites.

## Fix

<unfixed — raised only>

## Notes

- **Severity Could/Low, and NOT "latent red".** The empirical release run above disproves the
  "will flip" inference; the case for change is test *quality* (no diagnostic; wrong tool for
  a float render), plus consistency — it is the last raw-float-hash golden after the `drums.rs`
  migration. Do not file or fix it as an active failure.
- **The `drums.rs` half of the original claim is simply false.** `drums.rs:2661`
  (`v1_drum_render_signatures_are_stable`) and `drums.rs:4890`
  (`brush_render_signatures_are_stable`) are *already* `RenderSignature` freezes with relative
  tolerance (`testutil.rs:138-140`, `:171-175`) — the exact remedy. The claim was a verbatim
  restatement of a stale lesson line.
- **Fix shape:** convert `non_guitar_la_render_is_pinned` to `testutil::assert_render_signature`.
  Intent is preserved: contaminating voices differ 30–130%, far outside the signature's
  ±0.15 dB / ±2% tolerances, so it still catches a real leak while shedding the last-bit
  fragility and gaining a readable failure.
- **Do not sweep up the ~40 other `to_bits()` sites** (engine.rs, voices.rs, altbank.rs,
  sampler.rs:5157/5161, testutil.rs). They are same-binary A-vs-B self-comparisons
  (determinism / controller-inertness) and are immune to cross-profile reordering — explicitly
  blessed by the repo's own lessons. Only the *cross-commit frozen* hash is the target.
- **Docs fix (no ledger entry needed):** the `lessons_learnt.md` frozen-hash nugget still points
  its "green today, latent" tail at `drums.rs`; it should point at this `sampler.rs` test
  instead, and drop the "will flip in release" implication given the measurement above. Being
  corrected in the same lessons pass.
- **Class precedent:** `MM-BUG-KILN-00020` (the perceptual anti-clone oracle vanishes under
  `--no-default-features`) — same shape of "the gate silently stops guarding under a different
  build configuration", though that is a feature gate rather than a profile-dependent float.
