# MM-BUG-KILN-00278 — Crate rustdoc overstates the embedded payload and evades its size oracle

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / public payload documentation
- **Raised:** 2026-08-17T09:42:03Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T181332Z-673057bf
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00278-run-fix-20260913T181332Z-673057bf
- **Owner base:** e8ddf6024fd7110f743735af46ea6fec342cf92a
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T18:13:32Z
- **Owner until:** 2026-09-13T20:13:32Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T09:42:03Z, raised via `deltic bugs new`)

## Observation

Observation: public crate rustdoc at crates/ferrosintesis/src/lib.rs:51-53 still claims the default feature embeds roughly 111 MiB across 1156 WAVs. The current default sample-crate directories contain 1080 WAV/FLAC recordings totaling 56,450,470 bytes (53.835 MiB), matching README.md:84-96 after the FLAC migration. The source-derived size oracle does not catch the stale rustdoc because payload.rs:size_claims at :123-149 scans one line at a time: line 51 contains compiles but no MiB, while line 52 contains MiB but neither embed nor compil. The stale wrapped paragraph therefore contributes no claim and the test passes on the README claim alone.

Expected: docs.rs describes the current embedded payload and the guard rejects a stale claim even when Markdown/rustdoc wraps it. Actual: the public size/count contract is about two times too large and names the retired all-WAV container set; its guard silently skips it.

Concrete fix: update the crate rustdoc to approximately 54 MiB, 1080 recordings, WAV/FLAC wording; make size_claims inspect paragraphs or joined continuation lines; add an adversarial wrapped stale-claim fixture that must fail.

Static review only. File count and bytes were independently read from the current sample directories. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
