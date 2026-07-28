# MM-BUG-KILN-00158 — Published sax crate omits the CC BY 3.0 licence URI

- **State:** Closed
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T031803Z-p57192-n403887300-c85 branch=task/bug-MM-BUG-KILN-00158-run-fix-20260728T031803Z-p57192-n403887300-c85 code=cf82c32e52243975552bbc78e9cb6d801398e50b gate=deltic model=codex@xhigh) → Closed (2026-07-28, deltic:auto role=verify run=verify-20260728T165502Z-p57192-n970469200-c256 verified_fix_run=fix-20260728T031803Z-p57192-n403887300-c85 verdict=close model=claude)

## Observation

**Symptom.** The independently publishable `ferrosintesis-samples-sax` crate declares `CC-BY-4.0 AND CC-BY-3.0`, but its packaged `NOTICE` links only the CC BY 4.0 licence. `crates/ferrosintesis-samples-sax/NOTICE:4-5` merely names CC BY 3.0, and neither `PROVENANCE.md` nor another packaged file supplies its licence text or canonical URI.

**Expected.** Every distributed copy of the CC BY 3.0-derived recordings includes a copy of, or URI for, that licence. CC BY 3.0 legal code section 4(a) states this requirement: `https://creativecommons.org/licenses/by/3.0/legalcode.en`.

**Actual.** The package allowlist at `crates/ferrosintesis-samples-sax/Cargo.toml:10` ships `NOTICE` and `PROVENANCE.md`, but no CC BY 3.0 licence copy/URI. The SPDX token is machine-readable metadata, not the required licence URI. The parent `ferrosintesis` NOTICE has the 3.0 URI, but this sample crate is separately publishable and distributable. Closed MM-BUG-KILN-00068 corrected the compound SPDX declaration and named both layers; it did not fix this residual.

**Concrete fix.** Add `https://creativecommons.org/licenses/by/3.0/` to the sax crate NOTICE, and preserve the specific upstream Freesound pack links where practical. Strengthen the licensing oracle so every declared `CC-BY-*` operand requires its canonical URI or packaged legal text, with a negative control that removes the sax 3.0 URI.

**Effort:** Extra small to small.

## Fix

The separately publishable sax sample crate now links its CC BY 3.0 licence in
the packaged `NOTICE`. The licensing oracle derives every declared CC-BY
operand for each default sample crate and requires its shipped documents to
carry the matching canonical URI or legal text.

Regression coverage removes only the sax package's CC BY 3.0 URI and proves
that its CC BY 4.0 URI cannot satisfy the separate licence layer. That negative
case failed with `ferrosintesis-samples-sax: CC-BY-3.0`; the fixed tree passed
all 13 licensing tests.

Focused validation:

- `cargo test -p ferrosintesis licensing::tests` — 13 passed.
- `deltic integrate --push` — affected-area gate passed and landed code commit `cf82c32e52243975552bbc78e9cb6d801398e50b`.

### Verification summary (2026-07-28, deltic:auto run=verify-20260728T165502Z-p57192-n970469200-c256 verified_fix_run=fix-20260728T031803Z-p57192-n403887300-c85 verdict=close)

Verifier note: Sax crate's packaged NOTICE now carries the CC BY 3.0 URI; a derived oracle plus a negative control enforce it for every declared CC-BY operand, and all repo gates are green. — Symptom gone: crates/ferrosintesis-samples-sax/NOTICE:5 now reads 'good-sounds recordings are CC BY 3.0 (http[PATH])'; grep over the whole sax crate shows that URI present and no other CC URI/legal text anywhere in README.md or PROVENANCE.md, so the original 'no packaged file supplies the CC BY 3.0 URI' observation no longer holds. Cargo.toml:10 include list ships NOTICE, so it is genuinely packaged. Regression tests ex...

## Notes
