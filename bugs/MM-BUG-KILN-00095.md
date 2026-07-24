# MM-BUG-KILN-00095 — The fret-noise bake's byte-identical promise has no stable environment

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`)

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

## Notes

The current twelve payloads were not shown to be wrong. Static inspection confirmed
valid PCM mono 44.1 kHz/16-bit files. This bug concerns the false unconditional
regeneration guarantee and its missing oracle.
