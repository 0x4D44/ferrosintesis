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

    #[derive(Clone, Copy)]
    enum StringKind {
        Basic,
        Literal,
    }

    /// Count structural braces before a comment, ignoring string contents.
    ///
    /// TOML basic strings (`"..."`) use backslash escapes; literal strings
    /// (`'...'`) do not. A `#`, `{`, `}` or `"` inside a literal string is data,
    /// just as those characters inside a basic string are data.
    ///
    /// This deliberately handles the single-line forms only. Multi-line basic and
    /// literal strings need lexer state across lines; no workspace manifest uses
    /// either form. If that changes, replace this narrow inline-table oracle with a
    /// stateful TOML lexer rather than extending it with another line-local special
    /// case.
    fn structural_braces(line: &str) -> (usize, usize) {
        let mut string = None;
        let mut escaped = false;
        let mut opens = 0;
        let mut closes = 0;

        for c in line.chars() {
            match string {
                Some(StringKind::Basic) => {
                    if escaped {
                        escaped = false;
                    } else {
                        match c {
                            '\\' => escaped = true,
                            '"' => string = None,
                            _ => {}
                        }
                    }
                }
                Some(StringKind::Literal) => {
                    if c == '\'' {
                        string = None;
                    }
                }
                None => match c {
                    '"' => string = Some(StringKind::Basic),
                    '\'' => string = Some(StringKind::Literal),
                    '#' => break,
                    '{' => opens += 1,
                    '}' => closes += 1,
                    _ => {}
                },
            }
        }

        (opens, closes)
    }

    /// Lines that open an inline table without closing it — invalid under TOML 1.0.
    fn unclosed_inline_tables(text: &str) -> Vec<(usize, String)> {
        let mut out = Vec::new();
        for (idx, raw) in text.lines().enumerate() {
            let (opens, closes) = structural_braces(raw);
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

        // Literal strings use single quotes: `#`, `"` and braces inside them are data.
        let literal_hash = "foo = { path = 'vendor/a#b' }\n";
        assert!(unclosed_inline_tables(literal_hash).is_empty());
        let literal_braces = "foo = { pattern = '{not structure}' }\n";
        assert!(unclosed_inline_tables(literal_braces).is_empty());

        // A double quote inside a literal string must not hide the real comment.
        // The closing brace is commented out, so this inline table is genuinely open.
        let hidden_by_literal_quote = "foo = { path = 'vendor/\"quoted' # }\n";
        assert_eq!(unclosed_inline_tables(hidden_by_literal_quote).len(), 1);

        // A genuinely commented-out brace must not count as an opener.
        let commented = "# foo = {\nbar = 1\n";
        assert!(unclosed_inline_tables(commented).is_empty());

        // Multi-line ARRAYS are valid TOML and must not be flagged.
        let array = "include = [\n  \"src/**\",\n  \"README.md\",\n]\n";
        assert!(unclosed_inline_tables(array).is_empty());
    }
}
