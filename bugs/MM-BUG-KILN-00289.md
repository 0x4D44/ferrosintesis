# MM-BUG-KILN-00289 — Orchestral package publishes stale inventory, routing, and FLAC contracts

- **State:** Open
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
- **State history:** Open (2026-08-17T13:41:05Z, raised via `deltic bugs new`)

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

## Notes

The FLAC-specific regression arrived with commit `9046cd1`; the older inventory
and routing drift was recorded in the 2026-08-15 review but could not be filed
because that session lacked access to the sanctioned Deltic allocator.
