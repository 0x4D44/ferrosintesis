# MM-REQ-KILN-00032 — Render entry points must share one machine-checked default profile

- **State:** Implemented
- **Priority:** Should
- **Area:** ferrosintesis CLI/catalog render policy
- **Raised:** 2026-07-25
- **Implemented-by:** `crates/ferrosintesis-cli/src/main.rs` (defaults read from `Options::default()`); `crates/ferrosintesis-cli/examples/raw_dump.rs` (same); `crates/render-catalog/src/main.rs` (`ENCODER_SETTINGS` derived from `TARGET_LUFS`; pin rationale documented)
- **Satisfied-by:** `crates/ferrosintesis/src/render_profile.rs` — `catalog_pins_match_the_library_default`, `the_realtime_defaults_agree_with_the_offline_ones`, `the_readme_options_table_states_the_real_defaults`, `the_cli_help_text_states_the_real_defaults`, `the_tempo_echo_formula_is_stated_identically_everywhere`, `the_loudness_target_is_stated_consistently`, `the_shipping_entry_points_derive_the_profile_rather_than_restating_it`, `the_set_of_render_entry_points_is_known`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-25, captured by Codex GPT-5.6-Sol from the coverage review of `crates/ferrosintesis-cli/`) → Implemented (2026-07-25, Gate-1 choice was the derived source-scan oracle; scope widened past the three named entry points)

## Resolution (2026-07-25)

Gate 1 chose the **derived cross-entry-point oracle** over a shared typed profile. The
deciding constraint: `ferrosintesis-cli` has no lib target (its `Cargo.toml` declares only
`[[bin]]`) and its defaults were `let mut` locals inside `fn main`, so **no Rust code
anywhere could read them** — a dependency would have exposed nothing. Reading source as
text is the technique `engine.rs` already uses to reach `amp-lab` without depending on it,
and it needs no public API addition to a published crate.

The requirement named three entry points; there were more, so the set was re-derived rather
than trusted. Also restating the profile: `impl Default for RealtimeOptions`
(`crates/ferrosintesis/src/live.rs`), the README options table, `examples/quickstart.rs`,
the CLI's own `--help` text, and — the only one a listener could read — the
`ENCODER_SETTINGS` tag written into every shipped `.opus`, which was a bare `-18 LUFS`
literal frozen by a golden byte-equality.

Two mechanisms, chosen per site:

- **By construction** where one definition is unambiguously right. `ferrosintesis-cli` and
  `raw_dump` now read `Options::default()`. Proven value-preserving: rendering a reference
  MIDI with no flags and with `--rate 44100 --wet 0.32 --tail 6` gives byte-identical WAVs.
- **By oracle** where a second statement is legitimate. `render-catalog` *pins* its profile
  deliberately — the albums' committed sound must not move because a library default moved
  — so it keeps its constants and the oracle asserts they still match. A default change now
  turns the catalog red and forces a human decision, which is what a pin is for.

`ENCODER_SETTINGS` is now built with `format!` from `TARGET_LUFS`; the goldens still match
byte-for-byte because Rust prints `-18.0f32` as `-18`.

`synth_options_match_ferrosintesis_cli_defaults` was **renamed, not deleted**, to
`catalog_synth_options_hold_their_pinned_values`. It never observed the CLI and could not,
but it does detect a catalog-side edit and it runs `synth_options` for real — deleting it
would have lost coverage the requirement never complained about.

**Verified by refutation.** Changing `wet` in `Options::default()` from 0.32 to 0.30 turns
four oracles red at once (catalog pin, realtime default, README table, CLI help) — the
exact drift the old test slept through. Re-introducing a literal `.with_reverb(0.32)` into
`raw_dump` turns the anti-restatement guard red. Both were applied and observed, then
reverted.

**Not addressed, deliberately:** the true-peak ceiling still differs (-4.5 dBTP catalog vs
-1.0 CLI). That is a documented, physically-motivated departure — the lossy encode adds
inter-sample peak — not drift, so the oracle holds the loudness target shared and leaves the
ceiling alone.

## Statement

The shipping CLI, catalog renderer, and raw measurement renderer must derive
their shared render defaults and tempo-derived echo policy from one
authoritative definition, or from a parity oracle that actually observes each
entry point's effective configuration.

## Notes

- Current values match; this is structural drift risk, not a present sound
  mismatch.
- `crates/ferrosintesis-cli/src/main.rs:28-37,112-140` defines rate, wetness,
  tail, normalization, and tempo-derived echo policy locally.
- `crates/ferrosintesis-cli/examples/raw_dump.rs:65-80` copies the same profile
  because calibration requires it to match the shipping renderer.
- `crates/render-catalog/src/main.rs:26-39,264-280` carries a third copy.
- `crates/render-catalog/src/main.rs:911-931` is named
  `synth_options_match_ferrosintesis_cli_defaults`, but it checks catalog
  constants and options against literals from that same file. A CLI-only
  default change leaves it green.
- `deltic reqs --json` and the open requirement files showed no requirement
  covering this render-profile parity gap.
- Gate 1 should choose a shared typed profile/formula consumed by all entry
  points, or a genuinely derived cross-entry-point oracle. Another copied
  literal table would inherit the same defect.
