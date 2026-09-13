# MM-BUG-CRUCIBLE-00045 — Clavinet bank's format assertion accepts RIFF or FLAC, so a WAV regression into a FLAC bank stays green

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-samples-clavinet
- **Raised:** 2026-08-18T19:41:06Z
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
- **State history:** Open (2026-08-18T19:41:06Z, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-09-13T14:35:13Z, deltic:auto role=fix run=fix-20260913T141946Z-971f4b5e branch=task/bug-MM-BUG-CRUCIBLE-00045-run-fix-20260913T141946Z-971f4b5e code=3385fe47a80d983e636bc90520432087f9dfb772 gate=manual) -> Closed (2026-09-13T19:35:03Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: a WAV planted in the clavinet bank and RIFF bytes named .flac each fail the derived container policy)

## Observation

The clavinet crate's format assertion no longer proves what it was written to prove.

`crates/ferrosintesis-samples-clavinet/src/lib.rs:113-127`:

```rust
const EXPECTED_BYTES: usize = 529574;
...
let riff = &bytes[..4] == b"RIFF" && &bytes[8..12] == b"WAVE";
let flac = &bytes[..4] == b"fLaC";
assert!(riff || flac, "{name} is neither RIFF/WAVE nor FLAC");
```

The bank has been 100% FLAC since 2026-08-16 (`crates/ferrosintesis/CHANGELOG.md:18`), and
the whole point of that change was payload size — it took 43.5 MiB off the binary. Yet
nothing in this crate, or in `crates/ferrosintesis/src/payload.rs`, pins the container:

- the per-file check accepts RIFF **or** FLAC, so an uncompressed WAV dropped back into
  this bank asserts clean;
- the only size tripwire is `EXPECTED_BYTES`, a hand-maintained sum. Whoever re-cuts a file
  updates it mechanically, so it flags *change*, never *regression* — a WAV re-import
  presents as "the constant needs bumping", which is exactly what an editor would do;
- `crates/ferrosintesis/src/payload.rs:56-66` counts `wav` **or** `flac` alike when
  deriving the embedded payload total, so the workspace-level oracle does not catch it
  either.

The permissive `riff || flac` was correct during the migration, when both containers were
in flight. It is now a no-op for every crate except the one deliberate exception
(`ferrosintesis-samples-b1-upright`, whose custom `b1t` chunk a FLAC container cannot hold
— see `.gitignore:52-58`). Twelve other sample crates carry the same permissive assertion.

Classification: test-infrastructure defect — an assertion that no longer proves anything
(CLAUDE.md, "Keep test infrastructure efficient and low on tech debt"). No user-visible
misbehaviour today; the failure it fails to catch is a silent multi-MiB binary regression.

Related: `MM-BUG-CRUCIBLE-00044` (the same FLAC migration left the crates' public rustdoc
naming a `.wav` suffix). Both are best fixed by the one derived oracle described there.

## Fix

Derive each bank's container from its `samples/` directory instead of accepting either,
in the style of `crates/ferrosintesis/src/licensing.rs` and `src/manifest.rs`:

- assert every file in a crate's `samples/` shares one container and that its magic bytes
  match its extension (so a `.flac` that is really a RIFF, or the reverse, fails);
- assert the container is FLAC for every default-embedded sample crate **except** an
  explicit, commented allowlist holding `ferrosintesis-samples-b1-upright` — and derive the
  crate set from `licensing::default_sample_crates()` rather than a second hand-written
  list, so a new crate is covered by default rather than by remembering;
- keep the vacuous-pass guard the sibling oracles use (assert the crate and file counts are
  non-trivial), and write the adversarial fixture that *should* fail it — a WAV planted in
  a FLAC bank — and check that it does.

Site: fold into `crates/ferrosintesis/src/payload.rs`, which already walks exactly this
directory set (`payload.rs:42-67`). Once that oracle exists, the twelve crates' local
`riff || flac` per-file checks can be simplified to a single container assertion.

Effort: ~1 h, and it shares its enumeration with MM-BUG-CRUCIBLE-00044 — fix both together.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `3385fe47`) by an agent other than the fixer.

**Original observation re-run.** A real B1 WAV planted as `ferrosintesis-samples-clavinet/samples/clavinet_zz_planted.wav` fails `default_sample_bank_containers_match_the_derived_policy` ("uses wav, mixed with the bank's flac files"; "uses wav, but this bank must use flac"), and RIFF bytes named `clavinet_zz_riff.flac` fail with "does not contain a flac header". Both plants removed; it and `sample_container_oracle_rejects_a_wav_planted_in_a_flac_bank` pass on HEAD.

**Fails-before (method A, by reading).** At `3385fe47^` the per-crate check was `riff || flac` and `payload.rs` counted wav or flac with no policy, so both plants would pass. A census shows 23 crates assert `fLaC` directly, b1-upright is the one allowlisted exception, and no `riff || flac` remains.

## Notes
