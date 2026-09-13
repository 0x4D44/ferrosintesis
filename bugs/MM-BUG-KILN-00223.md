# MM-BUG-KILN-00223 — Core single-take aliases are decoded twice during prewarm

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** core piano sample runtime / memory
- **Raised:** 2026-08-16T14:46:31Z
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
- **State history:** Open (2026-08-16T14:46:31Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:54:18Z, deltic:auto role=fix run=fix-20260913T154452Z-d6eb07e1 branch=task/bug-MM-BUG-KILN-00223-run-fix-20260913T154452Z-d6eb07e1 code=6c12c7220ddf55536781cc8d8eeb9a5ef59b7f5c gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: per-bank C2/G2 decode restored fails the pointer-identity assertion)

## Observation

Static review confirms that bank! calls parse_wav for every Zone (crates/ferrosintesis/src/sampler.rs:325-335). piano_pp and piano_pp_rr2 both name piano_C2_pp.wav and piano_G2_pp.wav (sampler.rs:405-419,456-471), and prewarm initializes both banks (sampler.rs:3104-3114). Each source has 79,732 PCM frames, so the two second parses retain 637,856 duplicate decoded bytes in independent Vec<f32> allocations. The existing equality oracle at sampler.rs:7576-7582 proves content equality but not shared storage; Kawai and Steinway already enforce pointer sharing for logical aliases at sampler.rs:7600-7631. Expected: declared single-take aliases share decoded storage. Actual: prewarm retains two copies of each aliased payload. Fix by sharing canonical decoded storage for the two zones or by introducing a canonical decode cache, then add a pointer/storage-identity regression while retaining the content and round-robin assertions. Estimated effort: Small-Medium. Static review only; no app, build, test, generator, render, or exploratory harness ran.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `6c12c722`) by an agent other than the fixer.

**Original observation re-derived.** `piano_C2_pp.flac` and `piano_G2_pp.flac` are decoded only in `piano_c2_pp_data`/`piano_g2_pp_data` (`sampler.rs:506`, `:511`), and `piano_pp` and `piano_pp_rr2` both clone that shared `Arc`.

**Fails-before (method B).** Making `piano_pp_rr2` decode its own copies fails `sampler::tests::upright_round_robin_bank_only_aliases_declared_single_takes` with "quiet C2/G2 aliases must share their decoded PCM buffer". Restored; `git diff` empty; passes on HEAD. Real second takes keep distinct storage.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes
