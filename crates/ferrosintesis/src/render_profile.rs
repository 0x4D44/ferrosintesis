//! Render-profile parity — the shipping defaults have ONE definition, and every
//! restatement of them is checked against it.
//!
//! ## The defect
//!
//! `Options`' defaults were stated independently in the CLI, in `raw_dump`, and in
//! `render-catalog`, and the test that claimed to check the three
//! (`synth_options_match_ferrosintesis_cli_defaults`) compared render-catalog's constants
//! against literals written in render-catalog's own source. A CLI-only change left it green.
//! Values happened to agree, so this was drift *risk*, not a present mismatch —
//! MM-REQ-KILN-00032.
//!
//! The requirement named three entry points. There were more: `impl Default for
//! RealtimeOptions` in `live.rs`, the README's options table, `examples/quickstart.rs`, and
//! the `ENCODER_SETTINGS` tag written into every shipped `.opus`. Per the repo's standing
//! lesson, the reported list was evidence of an unmaintained list rather than a spec of the
//! work, so this module re-derives the set instead of trusting it.
//!
//! ## Two mechanisms, deliberately
//!
//! **By construction, where one definition is unambiguously right.** `ferrosintesis-cli` and
//! `raw_dump` now read `Options::default()` instead of restating it. The shipping renderer's
//! defaults *are* the library's defaults; a copy could only ever be wrong. Nothing here needs
//! to check what no longer exists in two places.
//!
//! **By oracle, where a second statement is legitimate.** `render-catalog` deliberately
//! *pins* its profile — `main.rs` says changing one constant "silently changes the whole
//! catalog's sound", and that is correct: the albums' committed sound should not move because
//! a library default moved. So the catalog keeps its own constants, and this module asserts
//! they still equal the library's. If a default changes, the catalog goes red and a human
//! decides whether the albums move with it. That is the point — a pin you cannot detect is
//! just drift, and a pin that silently follows is not a pin.
//!
//! Documentation is checked the same way: the README table and the CLI's own `--help` text
//! are statements about the defaults, and a stale one misleads exactly the reader who cannot
//! check.
//!
//! ## What is deliberately NOT asserted here
//!
//! That `render-catalog`'s true-peak ceiling matches the CLI's. It does not, on purpose:
//! -4.5 dBTP versus -1.0, because the lossy 96k encode plus the 44.1->48 kHz resample *adds*
//! inter-sample peak. The invariant is that the LOUDNESS target is shared and the ceiling
//! departure stays documented, not that every number matches.
//!
//! Nor that `examples/quickstart.rs` uses the default reverb — it sets `0.25` to demonstrate
//! a builder, which is its job. Only its normalization targets are held to the profile.

#[cfg(test)]
mod tests {
    use std::path::{Path, PathBuf};

    fn repo_root() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(Path::parent)
            .expect("crates/ferrosintesis is two levels below the repo root")
            .to_path_buf()
    }

    fn read(rel: &str) -> String {
        std::fs::read_to_string(repo_root().join(rel))
            .unwrap_or_else(|e| panic!("cannot read {rel}: {e}"))
    }

    /// A numeric literal as written in Rust source, normalised to a comparable value.
    ///
    /// The same number is spelled differently in different places on purpose: the field is
    /// `sr: 44_100.0` (f32 internally), the accessor returns `u32`, and the README says
    /// `44100`. Comparing text would report a difference that does not exist, so compare
    /// values. Hex is handled for the `0xFFFF` solo mask.
    fn num(raw: &str) -> Option<f64> {
        let s: String = raw
            .trim()
            .trim_end_matches(|c: char| c.is_ascii_alphabetic())
            .replace('_', "");
        let s = s.trim();
        if let Some(hex) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
            return u64::from_str_radix(hex, 16).ok().map(|v| v as f64);
        }
        s.parse::<f64>().ok()
    }

    /// The `field: literal` pairs of an `impl Default for …` block, read from source text.
    fn default_fields(src: &str, header: &str) -> Vec<(String, String)> {
        let start = src
            .find(header)
            .unwrap_or_else(|| panic!("`{header}` not found — has the impl been renamed?"));
        let body = &src[start..];
        let open = body
            .find("Self {")
            .expect("a Default impl builds Self { … }");
        let end = body[open..]
            .find("\n        }")
            .expect("the Self { … } literal is closed at a known indent");
        let inner = &body[open + "Self {".len()..open + end];

        let mut out = Vec::new();
        for line in inner.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with("//") {
                continue;
            }
            if let Some((k, v)) = line.split_once(':') {
                let v = v.trim().trim_end_matches(',').trim();
                if !k.trim().is_empty() && !v.is_empty() {
                    out.push((k.trim().to_string(), v.to_string()));
                }
            }
        }
        assert!(
            out.len() >= 5,
            "parsed only {} fields from `{header}` — the parser is not reading what it \
             thinks it is",
            out.len()
        );
        out
    }

    fn authority() -> Vec<(String, String)> {
        default_fields(
            &read("crates/ferrosintesis/src/engine.rs"),
            "impl Default for Options",
        )
    }

    fn field<'a>(fields: &'a [(String, String)], name: &str) -> &'a str {
        fields
            .iter()
            .find(|(k, _)| k == name)
            .map(|(_, v)| v.as_str())
            .unwrap_or_else(|| panic!("`{name}` is not a field of the profile any more"))
    }

    // ------------------------------------------------------------ entry points

    /// Every file outside the library that renders a whole song.
    ///
    /// Derived, not listed: a new binary or example that calls `offline::render` joins this
    /// set automatically and the count assertion below forces a decision about its profile.
    /// That is the guard the requirement's own three-item list did not have.
    fn render_entry_points() -> Vec<String> {
        fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
            let Ok(entries) = std::fs::read_dir(dir) else {
                return;
            };
            for e in entries.filter_map(|e| e.ok()) {
                let p = e.path();
                if p.is_dir() {
                    if p.file_name().map(|n| n == "target").unwrap_or(false) {
                        continue;
                    }
                    walk(&p, out);
                } else if p.extension().map(|x| x == "rs").unwrap_or(false) {
                    out.push(p);
                }
            }
        }
        let crates = repo_root().join("crates");
        let mut files = Vec::new();
        walk(&crates, &mut files);

        let lib_src = crates.join("ferrosintesis").join("src");
        let mut out: Vec<String> = files
            .into_iter()
            .filter(|p| !p.starts_with(&lib_src))
            .filter(|p| {
                std::fs::read_to_string(p)
                    .map(|s| s.contains("offline::render"))
                    .unwrap_or(false)
            })
            .map(|p| {
                p.strip_prefix(&crates)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();
        out.sort();
        out
    }

    #[test]
    fn the_set_of_render_entry_points_is_known() {
        let found = render_entry_points();
        let expected = [
            "ferrosintesis-cli/examples/raw_dump.rs",
            "ferrosintesis-cli/src/main.rs",
            "ferrosintesis/examples/quickstart.rs",
            "render-catalog/src/main.rs",
        ];
        assert_eq!(
            found, expected,
            "the set of files calling an `offline::render*` API has changed.\nA new render entry \
             point must either take its profile from `Options::default()` (like \
             ferrosintesis-cli and raw_dump) or pin it deliberately and be added to \
             `catalog_pins_match_the_library_default` (like render-catalog). Add it to the \
             list here once you have decided which."
        );
    }

    #[test]
    fn the_shipping_entry_points_derive_the_profile_rather_than_restating_it() {
        // `ferrosintesis-cli` and `raw_dump` must not re-introduce a literal for a knob the
        // library already defines. They may still set the knobs they genuinely vary — the
        // tempo-derived echo, and raw_dump's `--no-samples` switch.
        for rel in [
            "crates/ferrosintesis-cli/src/main.rs",
            "crates/ferrosintesis-cli/examples/raw_dump.rs",
        ] {
            let src = read(rel);
            for builder in ["with_sample_rate", "with_reverb", "with_tail", "with_solo"] {
                for line in src.lines() {
                    let Some(rest) = line.split_once(&format!("{builder}(")).map(|(_, r)| r) else {
                        continue;
                    };
                    let arg = rest.split(')').next().unwrap_or("").trim();
                    assert!(
                        num(arg).is_none(),
                        "{rel} passes the literal `{arg}` to `{builder}`. That is a second \
                         statement of a library default — read it from `Options::default()` \
                         instead (MM-REQ-KILN-00032). If this entry point genuinely needs to \
                         PIN the value against library drift, do it the way render-catalog \
                         does and add it to `catalog_pins_match_the_library_default`."
                    );
                }
            }
        }
    }

    // -------------------------------------------------------------- the pins

    #[test]
    fn catalog_pins_match_the_library_default() {
        let a = authority();
        let cat = read("crates/render-catalog/src/main.rs");

        let konst = |name: &str| -> String {
            let needle = format!("const {name}");
            let line = cat
                .lines()
                .find(|l| l.trim_start().starts_with(&needle))
                .unwrap_or_else(|| panic!("render-catalog no longer declares `const {name}`"));
            line.split('=')
                .nth(1)
                .expect("a const declaration has an initialiser")
                .trim()
                .trim_end_matches(';')
                .trim()
                .to_string()
        };

        for (konst_name, field_name) in [("SR", "sr"), ("WET", "wet"), ("TAIL", "tail")] {
            let pinned = konst(konst_name);
            let want = field(&a, field_name);
            assert_eq!(
                num(&pinned),
                num(want),
                "render-catalog pins `{konst_name} = {pinned}` but the library default is \
                 `{field_name}: {want}`.\nThe catalog pins its profile on purpose — the \
                 albums' committed sound must not move because a library default moved — so \
                 this is a decision, not a typo: either update the pin and accept that every \
                 album re-renders differently, or revert the library default. Run the \
                 render-diff inventory either way (CLAUDE.md)."
            );
        }

        // `synth_options` sets these two inline rather than through a const.
        for (needle, field_name) in [(".with_samples(", "samples"), (".with_solo(", "solo")] {
            let line = cat
                .lines()
                .find(|l| l.contains(needle))
                .unwrap_or_else(|| panic!("render-catalog no longer calls `{needle}…)`"));
            let arg = line
                .split(needle)
                .nth(1)
                .and_then(|r| r.split(')').next())
                .unwrap_or("")
                .trim();
            let want = field(&a, field_name);
            let same = match (num(arg), num(want)) {
                (Some(x), Some(y)) => x == y,
                _ => arg == want,
            };
            assert!(
                same,
                "render-catalog pins `{needle}{arg})` but the library default is \
                 `{field_name}: {want}` — see the message above; the same decision applies."
            );
        }
    }

    #[test]
    fn the_realtime_defaults_agree_with_the_offline_ones() {
        let a = authority();
        let rt = default_fields(
            &read("crates/ferrosintesis/src/live.rs"),
            "impl Default for RealtimeOptions",
        );

        // Only the knobs both structs have. `tail` and `solo` are offline-only (a realtime
        // stream has no end to render past, and no stem-soloing), and `master_gain` is
        // realtime-only, so those are legitimately not shared.
        for (rt_name, off_name) in [
            ("sample_rate", "sr"),
            ("wet", "wet"),
            ("delay_s", "delay_s"),
            ("samples", "samples"),
        ] {
            let got = field(&rt, rt_name);
            let want = field(&a, off_name);
            let same = match (num(got), num(want)) {
                (Some(x), Some(y)) => x == y,
                _ => got == want,
            };
            assert!(
                same,
                "`RealtimeOptions::default()` has `{rt_name}: {got}` but `Options::default()` \
                 has `{off_name}: {want}`.\nThese are two hand-written defaults for the same \
                 instrument — a player who switches between the realtime and offline paths \
                 should not hear a different voicing. Nothing structurally ties them, which \
                 is why this is checked."
            );
        }
    }

    // ------------------------------------------------------------ the documents

    #[test]
    fn the_readme_options_table_states_the_real_defaults() {
        let a = authority();
        let readme = read("crates/ferrosintesis/README.md");

        // builder name -> field name. The correspondence is inherent (`with_sample_rate`
        // sets `sr`), so it cannot be derived from text; what IS checked is that the table
        // covers every field, so a new knob cannot land undocumented.
        let map = [
            ("with_sample_rate", "sr"),
            ("with_reverb", "wet"),
            ("with_tail", "tail"),
            ("with_echo", "delay_s"),
            ("with_samples", "samples"),
            ("with_solo", "solo"),
        ];
        assert_eq!(
            map.len(),
            a.len(),
            "`Options` has {} fields but this test maps {} — a knob was added or removed \
             without updating the README table's coverage check.",
            a.len(),
            map.len()
        );

        for (builder, field_name) in map {
            let row = readme
                .lines()
                .find(|l| l.trim_start().starts_with(&format!("| `{builder}`")))
                .unwrap_or_else(|| panic!("the README options table has no row for `{builder}`"));
            let cell = row
                .split('|')
                .nth(3)
                .unwrap_or("")
                .trim()
                .trim_matches('`')
                .trim();
            let want = field(&a, field_name);
            let same = match (num(cell), num(want)) {
                (Some(x), Some(y)) => x == y,
                _ => cell == want,
            };
            assert!(
                same,
                "the README says `{builder}` defaults to `{cell}`, but `Options::default()` \
                 sets `{field_name}: {want}`. The README is this crate's crates.io landing \
                 page — a stale default there misleads exactly the reader who cannot check."
            );
        }
    }

    #[test]
    fn the_cli_help_text_states_the_real_defaults() {
        let a = authority();
        let cli = read("crates/ferrosintesis-cli/src/main.rs");
        let docs: String = cli
            .lines()
            .filter(|l| l.trim_start().starts_with("//!") || l.contains("usage:"))
            .collect::<Vec<_>>()
            .join("\n");

        for (flag, field_name) in [("--rate", "sr"), ("--wet", "wet"), ("--tail", "tail")] {
            let want = num(field(&a, field_name)).expect("a numeric default");
            // The prose writes 6.0 as "6" and 44_100.0 as "44100"; accept either spelling of
            // the same value rather than pinning the formatting.
            let found = docs.split_whitespace().any(|tok| {
                num(tok.trim_matches(|c: char| !c.is_ascii_alphanumeric() && c != '.' && c != '-'))
                    .map(|v| v == want)
                    .unwrap_or(false)
            });
            assert!(
                found,
                "the CLI's own documentation never states the default for `{flag}` \
                 ({field_name} = {want}). It is the first thing a user reads; a default that \
                 has moved on since the doc was written is worse than no doc."
            );
        }
    }

    // ------------------------------------------------------ the shared formula

    /// The tempo-derived echo policy, stated identically everywhere it appears.
    ///
    /// This one is NOT unified into a helper, and that is a judgement worth recording: it is
    /// four characters of arithmetic whose f32 operation order is load-bearing (render-catalog
    /// notes that an f64 computation diverges in the last bits), and one of the four sites is
    /// a test that restates it precisely to catch a change. Making them textually identical
    /// and checking that is cheaper than a public API addition to a published crate, and
    /// catches the same drift.
    #[test]
    fn the_tempo_echo_formula_is_stated_identically_everywhere() {
        let sites = [
            "crates/ferrosintesis-cli/src/main.rs",
            "crates/ferrosintesis-cli/examples/raw_dump.rs",
            "crates/render-catalog/src/main.rs",
        ];
        let mut seen: Vec<(String, String)> = Vec::new();
        for rel in sites {
            for line in read(rel).lines() {
                if let Some(i) = line.find("0.75 * 60.0") {
                    // Normalise away the bpm expression, which differs by call site
                    // (`song.initial_bpm() as f32`, `bpm as f32`, a literal in the test).
                    let tail = &line[i..];
                    let clamp = tail
                        .find(".clamp(")
                        .map(|c| tail[c..].split(')').next().unwrap_or("").to_string())
                        .unwrap_or_default();
                    seen.push((rel.to_string(), clamp));
                }
            }
        }
        assert!(
            seen.len() >= 3,
            "found only {} statements of the echo formula — expected one per render entry \
             point. Has it been renamed or unified? If unified, delete this test.",
            seen.len()
        );
        let first = &seen[0].1;
        for (rel, clamp) in &seen {
            assert_eq!(
                clamp, first,
                "the echo clamp differs between entry points: `{}` in {} vs `{}` in {}.\nThe \
                 dotted-quaver echo is part of the shipping sound; a renderer that clamps it \
                 differently produces a different mix from the same MIDI.",
                clamp, rel, first, seen[0].0
            );
        }
    }

    #[test]
    fn the_loudness_target_is_stated_consistently() {
        // Every statement of the delivery loudness target, across the entry points and the
        // documents that promise it. The true-peak CEILING is deliberately not included:
        // render-catalog uses -4.5 dBTP against the CLI's -1.0, documented at its
        // declaration, because the lossy encode adds inter-sample peak.
        let target = "-18";
        for (rel, needle) in [
            (
                "crates/ferrosintesis-cli/src/main.rs",
                "target_lufs = -18.0",
            ),
            (
                "crates/render-catalog/src/main.rs",
                "TARGET_LUFS: f32 = -18.0",
            ),
            (
                "crates/ferrosintesis/examples/quickstart.rs",
                "Normalization::loudness(-18.0, -1.0)",
            ),
            ("crates/ferrosintesis/README.md", "-18 LUFS"),
        ] {
            assert!(
                read(rel).contains(needle),
                "{rel} no longer states the {target} LUFS delivery target as `{needle}`.\nIf \
                 the target moved, it must move in ALL of these at once — and every committed \
                 album re-renders. If only the spelling changed, update this test."
            );
        }

        // The tag written into every shipped .opus must be DERIVED from the constant, not
        // restated. A listener can read this one.
        let cat = read("crates/render-catalog/src/main.rs");
        assert!(
            !cat.contains("\"ENCODER_SETTINGS=ferrosintesis(-18 LUFS)"),
            "the ENCODER_SETTINGS tag is a hard-coded literal again. It is written into every \
             shipped .opus, so a stale figure there is drift a listener can actually read — \
             build it from TARGET_LUFS with `format!` instead."
        );
        assert!(
            cat.contains("ENCODER_SETTINGS=ferrosintesis({} LUFS)"),
            "the ENCODER_SETTINGS tag no longer derives its loudness figure from TARGET_LUFS."
        );
    }
}
