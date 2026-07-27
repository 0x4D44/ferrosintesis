# MM-BUG-KILN-00152 — Orchestral2 publishes a no-op banjo regeneration recipe

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** orchestral2 / regeneration provenance
- **Raised:** 2026-07-27
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00152-run-fix-20260727T090201Z-p9812-n987723200-c60-code-1785143390172
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** The packaged provenance document says every family regenerates with
`python tools/ferrosintesis-samples/prepare.py --only=<family>`, including the
24-file `banjo_*` row at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\PROVENANCE.md:7`.
That command cannot regenerate banjo.

`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\prepare.py:3138`
describes `--only=banjo` as a supported selector. Lines 3216–3220 then explicitly
exclude banjo from the bake, and no later selected-family path dispatches it.
Static control flow reaches `_print_sample_rows([])` and returns success without
touching the 24 outputs. The real producer is the standalone command documented
at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\tools\ferrosintesis-samples\banjo_extract.py:26`.

The public README compounds the mismatch at
`D:\worktrees\midi-music\20260727-REV-CLA@KILN-code-review-093105\crates\ferrosintesis-samples-orchestral2\README.md:8`
by saying every WAV was trimmed by `prepare.py`.

**Expected.** Every published regeneration command either produces the named
family or fails clearly before reporting success.

**Actual.** The documented banjo command is a successful no-op, so a maintainer
can mistake stale or missing assets for a completed rebuild.

**Concrete fix.** Give banjo its real family-specific command in packaged
provenance, narrow the generic command to the families it reaches, and make
`prepare.py` reject an unsupported or non-producing `--only` selection. Add a
contract regression for `--only=banjo` and for an unknown family.

## Fix

<unfixed — raised only>

## Notes

The retained Opus source is an intentional size/fidelity tradeoff; this bug does
not require bit-exact reproduction from the unavailable original lossless take.
It tracks the false command and false producer attribution.
