# MM-BUG-KILN-00223 — Core single-take aliases are decoded twice during prewarm

- **State:** Open
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
- **State history:** Open (2026-08-16T14:46:31Z, raised via `deltic bugs new`)

## Observation

Static review confirms that bank! calls parse_wav for every Zone (crates/ferrosintesis/src/sampler.rs:325-335). piano_pp and piano_pp_rr2 both name piano_C2_pp.wav and piano_G2_pp.wav (sampler.rs:405-419,456-471), and prewarm initializes both banks (sampler.rs:3104-3114). Each source has 79,732 PCM frames, so the two second parses retain 637,856 duplicate decoded bytes in independent Vec<f32> allocations. The existing equality oracle at sampler.rs:7576-7582 proves content equality but not shared storage; Kawai and Steinway already enforce pointer sharing for logical aliases at sampler.rs:7600-7631. Expected: declared single-take aliases share decoded storage. Actual: prewarm retains two copies of each aliased payload. Fix by sharing canonical decoded storage for the two zones or by introducing a canonical decode cache, then add a pointer/storage-identity regression while retaining the content and round-robin assertions. Estimated effort: Small-Medium. Static review only; no app, build, test, generator, render, or exploratory harness ran.

## Fix

<unfixed — raised only>

## Notes
