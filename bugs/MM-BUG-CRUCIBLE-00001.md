# MM-BUG-CRUCIBLE-00001 — Published YDP notices omit named performer Dr. Mikhail Krishtal

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** packaging / licensing
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new`) -> Fixed (2026-07-31, deltic:auto role=fix run=fix-20260731T061755Z-p76200-n609412900-c1 branch=task/bug-MM-BUG-CRUCIBLE-00001-run-fix-20260731T061755Z-p76200-n609412900-c1 code=d305249e287da01fc300c8a3ff2f44ab6ca3ff57 gate=manual)

## Observation

**Symptom.** The authoritative FreePats YDP page identifies Dr. Mikhail
Krishtal, Director of Music Research and Production, and his Zenph Studios team
as the performers and recordists of the original Yamaha Disklavier Pro samples:
<https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html>.

The independently publishable package instead credits only the SoundFont
producer, `roberto@zenvoid.org`, plus Zenph Studios and OLPC generically:

- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis-samples-ydp-grand\NOTICE:4`
- `D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis-samples-ydp-grand\PROVENANCE.md:20`

The consolidated parent credits repeat the omission at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis\NOTICE:60`.

**Expected.** A distributed copy preserves the supplied name of the original
performer/recordist. CC BY 3.0 section 4(b) requires the Original Author's name
when supplied:
<https://creativecommons.org/licenses/by/3.0/legalcode.en>.

**Actual.** A distributor can ship both the standalone sample crate and the
default parent crate without Dr. Krishtal's supplied credit.

**Concrete fix.** Add Dr. Mikhail Krishtal and his Zenph Studios team's
performance/recording role to the packaged `NOTICE` and `PROVENANCE.md`, then
carry that credit into the parent `NOTICE` and licensing guide. Strengthen the
licensing oracle so required identities come from retained upstream evidence,
not from the already-incomplete local `NOTICE`. Add a negative control that
removes Krishtal while retaining Roberto, the work title, and the source URL.

**Effort:** Small.

## Fix

<unfixed — raised only>

## Notes

This is not covered by Draft `MM-REQ-KILN-00144`, which concerns exact source
SHA-256 pins. Closed `MM-BUG-KILN-00069` added the omitted SoundFont producer,
Roberto; it did not census the authoritative YDP page or cover Dr. Krishtal.

Static code review only. No application or test harness was run.
