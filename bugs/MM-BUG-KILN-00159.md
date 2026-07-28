# MM-BUG-KILN-00159 — Published sax provenance describes the retired onset-only voice

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / sax documentation
- **Raised:** 2026-07-28
- **Owner:** deltic:claude
- **Owner role:** verify
- **Owner run:** verify-20260728T173704Z-p57192-n572381000-c263
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00159-run-verify-20260728T173704Z-p57192-n572381000-c263
- **Owner base:** 62f5e9024aedfd99935a0cc88e47055af1056eca
- **Owner fingerprint:** sha256:17193d7db3e2dce872531c16bc9b5ed07822ce1ee8ded8cab8b6bfb1944fa324
- **Owner since:** 2026-07-28T17:37:04Z
- **Owner until:** 2026-07-28T18:22:04Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T040109Z-p57192-n646860400-c93 branch=task/bug-MM-BUG-KILN-00159-run-fix-20260728T040109Z-p57192-n646860400-c93 code=0df7aa7c3dae8e9851afd7dba024d9321d02c2ba gate=deltic model=codex@xhigh)

## Observation

**Symptom.** The published sax crate documents the retired onset-only architecture. `crates/ferrosintesis-samples-sax/PROVENANCE.md:9-14` calls the bank attack/body material, and `:56-62` says the model carries sustain. Crate rustdoc at `src/lib.rs:3-6` says the samples layer over the modeled reed.

**Expected.** Published docs describe the current default voice: the recorded attack plays through into a pitch-synchronous loop of the recorded sustain; the modeled reed is used only with `--no-samples` or when the loop/repitch is unusable.

**Actual.** Current routing says the whole default voice is the recording and explicitly records that this replaced the onset-only layer (`crates/ferrosintesis/src/voices.rs:14926-14945`). `SaxLoopVoice` renders the recorded loop (`crates/ferrosintesis/src/sampler.rs:4061-4064,4133-4178`). The package docs therefore give consumers and maintainers an obsolete architecture and processing claim. No existing bug or requirement covers this documentation drift.

**Concrete fix.** Update crate rustdoc, README/provenance language, and the corresponding generator comments to describe recorded attack plus looped recorded sustain, with the modeled reed only as the documented fallback. Keep the 0.62-second source processing facts, but remove the claim that the model carries the default hold.

**Effort:** Extra small.

## Fix

The sax crate README, provenance, notice, rustdoc, and generator comments now
describe the active default voice: recorded attack followed by a
pitch-synchronous loop of recorded sustain. They identify the modeled reed only
as the `--no-samples` or unusable-loop fallback.

Restoring the obsolete “LA sample layer” wording in the real README made the
source-scanning regression fail; the corrected tree passed both the focused test
and Deltic’s final combined sax gate.

Focused validation:

- `cargo test -p ferrosintesis sax_published_docs_describe_the_looped_recording_voice` — passed.
- `deltic integrate --push` — affected-area gate passed and landed code commit `0df7aa7c3dae8e9851afd7dba024d9321d02c2ba`.

## Notes
