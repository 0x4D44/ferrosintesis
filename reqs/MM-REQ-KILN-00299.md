# MM-REQ-KILN-00299 — Derive the CLI's documented flag set from its argument loop, the way the README options table is already derived

- **State:** Draft
- **Priority:** Could
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:50:57Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-08-17T22:50:57Z, raised via `deltic reqs new` model=claude-opus-5@high)

## Statement

**What must be true.** Every flag the CLI's argument loop accepts appears in both
user-visible surfaces — the `usage()` text and the `crates/ferrosintesis-cli/README.md`
options table — and neither surface documents a flag the loop does not accept. A new flag
cannot land undocumented.

**The oracle.** A source-scanning test that extracts the accepted flag set from the match
arms of `crates/ferrosintesis-cli/src/main.rs:48-107` (the string literals in each arm's
pattern) and asserts set equality against the flags named in `usage()`
(`main.rs:21-23`) and in the README table rows. Set equality both ways, so a *removed* flag
left in the docs also fails.

**Evidence the list has already drifted.** The loop accepts `-o | --out`, `-q | --quiet`,
and `-h | --help`. The README table (`README.md:28-40`) documents `-o` and `-q` but not
their long forms, and does not mention `-h` / `--help` at all. That is exactly one entry per
feature change going unread — the repo's recurring defect class.

**The pattern to copy already exists in-tree.** `the_readme_options_table_states_the_real_
defaults` (`crates/ferrosintesis/src/render_profile.rs:328-377`) derives the library's knob
set from `impl Default for Options` and requires a README row per knob, including a
coverage assertion (line 344-351) that fails when a knob is added without updating the
check. This requirement asks for the same treatment one level up, for the CLI's flags rather
than the library's knobs.

**Adversarial acceptance criterion.** Per CLAUDE.md, the oracle is only accepted once the
document that *should* fail it does: add a flag to the match arm without documenting it, and
watch the test go red; delete a README row, and watch it go red; then restore.

## Notes

- Deliberately scoped to *coverage* (which flags exist), not to *values*. Whether each
  documented default matches the library is a separate, already-existing concern —
  `the_cli_help_text_states_the_real_defaults` (`render_profile.rs:379-405`), whose own
  weakness is tracked as a bug from the same review pass.
- Light flow: one source-scanning test plus the small doc additions it forces. No public API
  change, no dependency (the workspace's offline build forbids registry deps).
- Raised by an autonomous read-only code-review pass over `crates/ferrosintesis-cli/`.
  The drift above was confirmed by reading `main.rs:48-107` and `README.md:28-40`.
