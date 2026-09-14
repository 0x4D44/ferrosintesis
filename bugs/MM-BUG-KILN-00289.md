# MM-BUG-KILN-00289 — Orchestral package publishes stale inventory, routing, and FLAC contracts

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** orchestral sample crate / public package contract
- **Raised:** 2026-08-17T13:41:05Z
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
- **State history:** Open (2026-08-17T13:41:05Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:27:08Z, deltic:auto role=fix run=fix-20260913T191728Z-96ba64bb branch=task/bug-MM-BUG-KILN-00289-run-fix-20260913T191728Z-96ba64bb code=900d8cd2f2e9d3cdf15e5fee038d2666a7c7fcc6 gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 1d87b00f: orchestral README, PROVENANCE, manifest and module docs re-derived against the payload, the sampler routes and the pinned VCSL revision)

## Observation

The published orchestral package contract disagrees with both its current
payloads and its runtime routes:

- `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\README.md:5`
  calls all 158 payloads WAVs; lines 24-25 demonstrate
  `get("trumpet_C3_f.wav").unwrap()` and assert `RIFF`. The exact-name table at
  `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\src\lib.rs:12`
  contains only `.flac` keys, so the documented call returns
  `None`; real payloads start with `fLaC`.
- The same README at line 76 says there are six chanter files, contradicting the 15 declared
  at line 13 and present in the table. Lines 15-18 and module docs at
  `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\src\lib.rs:1`
  describe every file as an onset crossfaded into a model, but the
  17 bagpipe files are whole-sound loops played by `LoopVoice` at
  `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis\src\sampler.rs:3044`.
- The README provenance section names no source for the ten `harpsi_*` files;
  `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\PROVENANCE.md:17`
  identifies their VCSL revision.
- `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\Cargo.toml:6`
  omits harpsichord and bagpipe from the package description.
- `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis-samples-orchestral\PROVENANCE.md:3`
  calls every packaged asset a WAV, and line 13 maps
  `celens_*` to GM 42. The consumer uses it as the low half of GM 48-49 string
  sections at
  `D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis\src\sampler.rs:847`;
  GM 42 now uses a separate solo-cello bank.

Expected: crates.io/docs.rs users, exact-name API callers, auditors, and
maintainers receive one accurate inventory, container, source, playback, and GM
route contract. Concrete fix: audit every package-local claim against the
generated inventory and consumer routes; update the FLAC keys/magic, counts,
VCSL source, bagpipe exception, description, and cello-section route together.
Make the README example executable or add a source-derived documentation guard
so the next bank/container change cannot leave these surfaces behind. Static
review only; the example, decoder, app, and package command were not run.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `900d8cd2`) by an agent other than the fixer.

**Each recorded claim, re-derived against code and files.**
- Payload: 158 files, all `.flac`; the README's `get("trumpet_C3_f.flac")` example names a real key (`src/lib.rs:480`) and asserts `fLaC`.
- Bagpipe: README counts two `drone_*` and fifteen `chanter_*`, matching the table. It now says `LoopVoice` plays those files as whole loops, which matches `sampler.rs:3089` (`bagpipe_chanter_loop -> LoopVoice`) and the looped drone banks at `sampler.rs:2950-2967`.
- Routes: PROVENANCE maps `celens_*` to the GM 48-49 string sections' low split, matching `sampler.rs:962-970`; GM 42 uses the separate solo-cello attack at `sampler.rs:1196`.
- Harpsichord: the README names VCSL revision `c1ea7bcc...`, equal to `prepare.py` `VCSL_REV`.
- Manifest names harpsichord and bagpipe; module docs say onset and looped-sustain samples; PROVENANCE says the payloads are FLAC.

**Fails-before (method A).** Against `900d8cd2^`, six of the eight checks in `OrchestralPackagedContractTest` fail (LoopVoice wording, harpsichord source, FLAC note, GM 42 celens row, manifest, module docs); all eight hold on the fix. The FLAC `get` example and the chanter count were already right before this commit. These are text needles, so the re-derivation above is what supports closure. The test passes in the gate's Python suite (its 4 errors are the MM-BUG-CRU-00068 classes).

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes

The FLAC-specific regression arrived with commit `9046cd1`; the older inventory
and routing drift was recorded in the 2026-08-15 review but could not be filed
because that session lacked access to the sanctioned Deltic allocator.
