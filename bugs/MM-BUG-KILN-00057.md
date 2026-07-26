# MM-BUG-KILN-00057 — non_guitar_la_render_is_pinned freezes a raw-f32 FNV hash: the last un-migrated bit-exact render golden, no diagnostic on failure and fragile across codegen

- **State:** Closed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised via `deltic bugs new` by Claude Opus 4.8 (1M), from a `lessons_learnt.md` pruning pass; the original "will flip in release" premise was EMPIRICALLY TESTED here and found FALSE, and the bug re-scoped accordingly) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — replaced the raw-f32 hash with a portable, diagnostic render signature) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run at source: the raw cross-commit FNV pin is gone. `non_guitar_la_render_is_pinned` and its `0xaa11_bc63_b298_af8e` constant no longer exist anywhere in `sampler.rs`; the test is now `non_guitar_la_render_signature_is_stable` (`sampler.rs:7144`), rendering the same GM56/key 69/velocity 100/seed 5 canary and freezing it through `testutil::assert_render_signature` (rms -16.398 dB, centroid 1767.767 Hz, late/early 13.049 dB) under the shared relative tolerances. Both defects the bug names are addressed: a failure now reports WHICH audible dimension moved, and the metric no longer depends on float-op ordering. Test green in the debug gate and in my focused run.)

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

Replace the cross-commit FNV pin with the existing `RenderSignature` oracle. Preserve the
same GM56 render and guard its level, spectrum, and envelope shape using the shared
cross-machine tolerances.

## Resolution — 2026-07-26

`non_guitar_la_render_is_pinned` is now
`non_guitar_la_render_signature_is_stable`. It renders the same GM56/key 69/velocity
100/seed 5 canary, then freezes:

- body RMS over 0.00–0.50 s: -16.398 dB;
- spectral centroid over 0.00–0.50 s: 1767.767 Hz;
- late/early level over 0.35–0.50 s versus 0.00–0.10 s: 13.049 dB.

The oracle now reports which audible dimension moved and uses the shared ±0.15 dB /
±2% tolerances instead of requiring every floating-point bit to match.

## Verification — 2026-07-26

- A fail-first zero signature reported the measured values and each tolerance failure:
  `-16.398323 dB`, `1767.7667 Hz`, and `13.048706 dB`.
- The focused oracle passed in debug and release profiles.
- The complete default suite passed (727 tests, 27 ignored), the true model-only suite
  passed (626 tests, 22 ignored), and both doc-test sets passed (4 each).
- Strict workspace clippy and true model-only clippy passed with warnings denied;
  formatting and `git diff --check` passed.
- Fresh release binaries from exact baseline `d37b8ca`, full 124-MIDI inventory at
  11.025 kHz: all 124 stayed byte-identical, with zero contamination and zero missed
  paths, confirming the test-only migration does not alter shipped output.

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
