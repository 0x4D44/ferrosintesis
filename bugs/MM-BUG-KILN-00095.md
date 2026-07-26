# MM-BUG-KILN-00095 — The fret-noise bake's byte-identical promise has no stable environment

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** fret-noise sample generation / reproducibility
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — scoped byte identity to a locked canonical environment and added non-mutating per-file verification) → Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: GPT-5.6 Codex on KILN-Windows), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree at b0b93d9: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (628 passed) and `test --workspace --exclude amp-lab --locked` (731 passed) - 1461 tests, 0 failures. Original observation re-run by execution, not by reading. The unconditional byte-identity claim is gone: `fretnoise_bake.py`'s docstring now scopes it to the declared canonical environment, `requirements-fretnoise-bake.txt` pins `numpy==2.4.4`, and `BAKE-SHA256` pins all twelve outputs independently. I ran `fretnoise_bake.py --verify`: it re-baked the complete bank in memory, matched all twelve committed SHA-256 pins, and reported "verified 12 generated and committed files (998 KiB); wrote nothing". I proved the non-mutation claim myself rather than trusting it - snapshotted every WAV's bytes and mtime_ns before the run and re-compared afterwards: both unchanged, and `git status --porcelain` for the crate is empty.)

## Observation

`tools/ferrosintesis-samples/fretnoise_bake.py:15-17` promises that a re-bake is
byte-identical, and
`crates/ferrosintesis-samples-fretnoise/PROVENANCE.md:25-30` repeats that contract.
The bake imports an unpinned NumPy installation, uses NumPy FFT resampling at
`fretnoise_bake.py:75-86`, and seeds `np.random.default_rng()` for TPDF dither at
lines 100-103 and 120.

The repository has no requirements file, lock, or canonical generator environment
that pins NumPy. NumPy's own `Generator` documentation explicitly states that it
provides no version-compatibility guarantee and that its bit stream may change:
<https://numpy.org/doc/stable/reference/random/generator.html>.

**Expected.** The same committed source cuts and bake definition reproduce the
committed payload bytes, or the documentation precisely scopes which canonical
environment owns that guarantee and provides a check against the committed result.

**Actual.** A fixed integer seed does not guarantee the same dither stream across
supported NumPy versions. FFT rounding is also environment-sensitive near 16-bit
quantization boundaries. The crate test pins only aggregate bytes and RIFF/WAVE
magic (`crates/ferrosintesis-samples-fretnoise/src/lib.rs:90-128`), so a different
same-length payload can pass.

No re-bake ran in this read-only review, so a concrete cross-version byte diff is
unverified. The unconditional byte-identity claim is nevertheless unsupported by
the dependency contract and the absent environment definition.

## Fix

Choose and document one reproducibility contract:

- use locally specified stable RNG/resampling algorithms with test vectors; or
- define a canonical locked generator environment and scope byte identity to it.

In either case, pin per-file output SHA-256 values and add a non-mutating verification
mode that checks a re-bake before replacing tracked assets. If cross-platform FFT
identity is not guaranteed, state that limitation and use an explicit acoustic
tolerance oracle in addition to canonical-environment hashes.

Estimated effort: Small–Medium.

## Resolution — 2026-07-26

The bake now scopes byte identity to the environment that demonstrably produced
the committed bank: 64-bit CPython 3.14.3 on Windows x86-64 with NumPy 2.4.4.
The existing NumPy dependency is pinned in
`requirements-fretnoise-bake.txt`, and the script refuses another interpreter,
NumPy version, platform, or architecture before generating output.

`BAKE-SHA256` pins all twelve outputs independently and is included in the
published sample package. `fretnoise_bake.py --verify` regenerates the complete
bank in memory, rejects missing, extra, malformed, duplicate, or changed pins,
checks the committed files, and never creates or writes an output. A real bake
also prepares and validates every payload before its first tracked-file write.

The package documentation no longer claims cross-version or cross-platform FFT
and random-stream identity. It identifies the existing GM120 level, spectrum,
pitch-independence, and one-shot acoustic oracles as the behavior layer that a
deliberate future environment and hash update must also satisfy.

## Verification — 2026-07-26

- A canonical in-memory re-bake matched all 12 committed WAVs byte-for-byte and
  matched every independent SHA-256 pin.
- Four new Python regressions passed, including an actual canonical re-bake that
  proves `--verify` preserves every WAV's bytes and modification time. The full
  sample-tool suite passed all 37 tests.
- The fret-noise sample crate passed all 5 tests, and
  `cargo package --list --allow-dirty` includes `BAKE-SHA256`.
- All 6 GM120 modeled/sampled acoustic-tolerance tests passed.
- Strict workspace clippy passed with warnings denied; formatting and
  `git diff --check` passed.
- No render inventory was needed: no WAV or synth path changed. The twelve
  committed payload hashes are exactly unchanged from base `a73bec1`.

## Notes

The current twelve payloads were not shown to be wrong. Static inspection confirmed
valid PCM mono 44.1 kHz/16-bit files. This bug concerns the false unconditional
regeneration guarantee and its missing oracle.
