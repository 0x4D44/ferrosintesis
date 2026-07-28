# MM-BUG-KILN-00158 — Published sax crate omits the CC BY 3.0 licence URI

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** packaging / licensing
- **Raised:** 2026-07-28
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** The independently publishable `ferrosintesis-samples-sax` crate declares `CC-BY-4.0 AND CC-BY-3.0`, but its packaged `NOTICE` links only the CC BY 4.0 licence. `crates/ferrosintesis-samples-sax/NOTICE:4-5` merely names CC BY 3.0, and neither `PROVENANCE.md` nor another packaged file supplies its licence text or canonical URI.

**Expected.** Every distributed copy of the CC BY 3.0-derived recordings includes a copy of, or URI for, that licence. CC BY 3.0 legal code section 4(a) states this requirement: `https://creativecommons.org/licenses/by/3.0/legalcode.en`.

**Actual.** The package allowlist at `crates/ferrosintesis-samples-sax/Cargo.toml:10` ships `NOTICE` and `PROVENANCE.md`, but no CC BY 3.0 licence copy/URI. The SPDX token is machine-readable metadata, not the required licence URI. The parent `ferrosintesis` NOTICE has the 3.0 URI, but this sample crate is separately publishable and distributable. Closed MM-BUG-KILN-00068 corrected the compound SPDX declaration and named both layers; it did not fix this residual.

**Concrete fix.** Add `https://creativecommons.org/licenses/by/3.0/` to the sax crate NOTICE, and preserve the specific upstream Freesound pack links where practical. Strengthen the licensing oracle so every declared `CC-BY-*` operand requires its canonical URI or packaged legal text, with a negative control that removes the sax 3.0 URI.

**Effort:** Extra small to small.

## Fix

<unfixed — raised only>

## Notes
