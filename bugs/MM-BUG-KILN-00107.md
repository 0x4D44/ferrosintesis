# MM-BUG-KILN-00107 — PROGRAM_TRIM_DB is calibrated against 2026-07-17 voices and was never re-verified; several trimmed programs have been re-voiced since

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth / instrument balance
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high)

## Observation

PROGRAM_TRIM_DB's values are a snapshot of a comparison between ferrosintesis and
a Roland SC-55mkII taken on 2026-07-17 (48 entries) and 2026-07-22 (5 panel
entries, commit fc1ef10). The trim is only correct while the voice it corrects is
the voice that was measured.

Since the 07-17 freeze roughly 165 commits of voice work have landed, several of
them rewriting programs that carry a non-zero trim:

  ec8bfd7  rewrote GM 84/85/93   - which carry -2.0 / +5.5 / -5.0 dB
  d1245e9  GM6 harpsichord       - the flagship +6.0 dB entry
  2a8f39a  GM8                   - +2.0 dB (an M-CAL v3 panel entry)
  f6ed468  GM0/GM1 piano damper decoupling
  70b7067  GM0/GM1 modelled felt damper

A trim derived against a voice that has since been re-voiced is measuring
something that no longer exists. The drift is UNKNOWN, not known-bad: nobody has
re-measured, which is the point of this entry.

The decisive check was specified at the time and never executed. From
`wrk_journals/2026.07.22 - JRN - M-CAL certified full derivation.md`: "a
closed-loop re-run. Apply, re-render, re-derive; expect proposals '(none)',
anchor 8.13 +-0.1, MAD <= 1.0, glue all-inert. Any proposal on a just-trimmed
program is a sign/linearity bug."

The tooling is committed and works: tools/instrument-balance/{mkprobe,derive_trims}.py
and crates/ferrosintesis-cli/examples/{calmeter,raw_dump}.rs. It needs mdmidiemu
plus the SC-55 ROMs (both present on KILN). The run is diagnostic - it ships
nothing - and is largely unattended.

NOT a defect in the balance itself. A control measurement taken 2026-07-25 shows
ferrosintesis's program-to-program spread is statistically indistinguishable from
the reference modules' own: within +/-1 dB of own median, ferro 11-16% vs SC-55
14% and S-YXG50 14%. The bank is not mis-balanced; its calibration is simply
stale and unverified.

Do NOT ship whatever the re-derive proposes without Arthur's ear. The last
derivation shipped ahead of his listening pass (candidate-1) was reversed in SIGN
on ~8 voices by that pass.

## Fix

<unfixed — raised only>

## Notes
