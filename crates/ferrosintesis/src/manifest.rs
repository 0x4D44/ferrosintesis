//! Manifest oracles — every workspace `Cargo.toml` must stay parseable at the MSRV.
//!
//! ## Why this exists
//!
//! Every crate here declares `rust-version = "1.87"`, and that declaration is only true
//! if a 1.87 toolchain can actually build the tree. It could not: two dependencies in
//! `crates/ferrosintesis/Cargo.toml` were written as **multi-line inline tables**, which
//! TOML 1.0 forbids ("no newlines are allowed between the curly braces"). Cargo 1.87
//! rejects them outright — `cargo +1.87 metadata` exited 101 at parse time, before
//! compiling a single line — while newer cargo accepts the form leniently.
//!
//! That leniency is the whole problem. The fleet builds on a current toolchain, so
//! every ordinary `cargo` invocation passed and the declared MSRV quietly became false
//! for ten days (MM-BUG-KILN-00067). The manifest even carried a comment warning
//! against exactly this, three lines above the offending entries — a comment is not a
//! gate.
//!
//! This oracle is deliberately a **text check, not a build check**: it fails on any
//! machine, in the ordinary test run, without a second toolchain installed. Proving the
//! MSRV for real still requires `cargo +1.87 check --workspace`; this just stops the one
//! mistake that has actually happened from recurring silently.

#[cfg(test)]
mod tests {
    use std::path::{Path, PathBuf};

    fn repo_root() -> PathBuf {
        // CARGO_MANIFEST_DIR = <root>/crates/ferrosintesis
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(2)
            .expect("crates/ferrosintesis sits two levels below the repo root")
            .to_path_buf()
    }

    /// Every `Cargo.toml` in the workspace: the root plus one per crate.
    fn workspace_manifests() -> Vec<PathBuf> {
        let root = repo_root();
        let mut out = vec![root.join("Cargo.toml")];

        let crates = root.join("crates");
        let entries = std::fs::read_dir(&crates)
            .unwrap_or_else(|e| panic!("cannot list {}: {e}", crates.display()));
        let mut found: Vec<PathBuf> = entries
            .filter_map(Result::ok)
            .map(|e| e.path().join("Cargo.toml"))
            .filter(|p| p.is_file())
            .collect();
        found.sort();
        out.extend(found);

        assert!(
            out.len() > 5,
            "found only {} manifests under {} — the oracle is not scanning the \
             workspace it thinks it is",
            out.len(),
            root.display()
        );
        out
    }

    /// Strip a trailing `#` comment, ignoring `#` inside a double-quoted string.
    ///
    /// Naive splitting on `#` would corrupt any line holding a `#` in a value — a URL
    /// fragment, or a sample name like `F#6.wav` — and could invent or hide a brace.
    fn strip_comment(line: &str) -> &str {
        let mut in_string = false;
        let mut prev_backslash = false;
        for (i, c) in line.char_indices() {
            match c {
                '"' if !prev_backslash => in_string = !in_string,
                '#' if !in_string => return &line[..i],
                _ => {}
            }
            prev_backslash = c == '\\' && !prev_backslash;
        }
        line
    }

    /// Lines that open an inline table without closing it — invalid under TOML 1.0.
    fn unclosed_inline_tables(text: &str) -> Vec<(usize, String)> {
        let mut out = Vec::new();
        for (idx, raw) in text.lines().enumerate() {
            let code = strip_comment(raw);
            let opens = code.matches('{').count();
            let closes = code.matches('}').count();
            if opens > closes {
                out.push((idx + 1, raw.trim().to_string()));
            }
        }
        out
    }

    /// No workspace manifest may open an inline table it does not close on the same
    /// line — cargo at our declared MSRV refuses to parse the file at all.
    #[test]
    fn no_manifest_uses_a_multi_line_inline_table() {
        let mut failures = Vec::new();
        for manifest in workspace_manifests() {
            let text = std::fs::read_to_string(&manifest)
                .unwrap_or_else(|e| panic!("cannot read {}: {e}", manifest.display()));
            for (line_no, line) in unclosed_inline_tables(&text) {
                let shown = manifest
                    .strip_prefix(repo_root())
                    .unwrap_or(&manifest)
                    .display()
                    .to_string();
                failures.push(format!("{shown}:{line_no}: {line}"));
            }
        }

        assert!(
            failures.is_empty(),
            "TOML 1.0 requires an inline table to be on one line, and cargo at our \
             declared MSRV (rust-version = \"1.87\") refuses a manifest that breaks \
             this — it fails at parse time, before compiling anything. Newer cargo \
             accepts it, so an ordinary build will NOT catch this.\n\n\
             Put each of these on a single line:\n  {}",
            failures.join("\n  ")
        );
    }

    #[test]
    fn the_oracle_detects_the_shape_it_is_meant_to_catch() {
        // The exact form that broke the build (KILN-00067).
        let bad = "[dependencies]\nfoo = {\n    path = \"../foo\",\n}\n";
        assert_eq!(unclosed_inline_tables(bad).len(), 1);

        // The corrected single-line form.
        let good = "[dependencies]\nfoo = { path = \"../foo\", version = \"=0.1.0\" }\n";
        assert!(unclosed_inline_tables(good).is_empty());

        // A `#` inside a string must not be treated as a comment: naive splitting
        // would drop the closing brace and report a false positive.
        let hashed = "a = { file = \"F#6.wav\" } # trailing comment\n";
        assert!(unclosed_inline_tables(hashed).is_empty());

        // A genuinely commented-out brace must not count as an opener.
        let commented = "# foo = {\nbar = 1\n";
        assert!(unclosed_inline_tables(commented).is_empty());

        // Multi-line ARRAYS are valid TOML and must not be flagged.
        let array = "include = [\n  \"src/**\",\n  \"README.md\",\n]\n";
        assert!(unclosed_inline_tables(array).is_empty());
    }
}
