//! Inventory-coverage oracles — every packaged sample must be documented by the crate
//! that ships it.
//!
//! ## A different question from `licensing.rs`
//!
//! `licensing.rs` asks *"is the attribution guide complete?"*. It keys off each bank's
//! declared `license` field and deliberately skips CC0 crates, because CC0 waives
//! attribution and needs no credit.
//!
//! This module asks *"has a crate's sample inventory outgrown its own documentation?"* —
//! and that applies to CC0 crates just as much. A consumer who receives eight
//! `pizzbass_*.wav` files that no document in the package mentions cannot trace their
//! origin, whatever their licence. Widening the licensing oracle to cover this would
//! blur two questions into one predicate that answers neither well; MM-BUG-KILN-00069
//! says so explicitly, and it is right.
//!
//! ## Why it is derived from the filesystem
//!
//! The defect it replaces is drift: eight WAVs arrived in one commit and the README was
//! last touched in an earlier one, so the package documented 32 of the 40 files it
//! shipped. Nobody notices, because nobody re-reads a table that looks complete. So the
//! oracle enumerates what is actually PACKAGED — `crates/ferrosintesis-samples-*/samples/
//! *.wav` — and requires the crate's own documents to account for it. A new bank cannot
//! be added without either documenting it or turning this red.

#[cfg(test)]
mod tests {
    use std::path::{Path, PathBuf};

    fn crates_dir() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("crates/ferrosintesis always has a parent")
            .to_path_buf()
    }

    /// Every first-party sample-asset crate, read from the filesystem rather than a list.
    fn sample_crates() -> Vec<String> {
        let mut out: Vec<String> = std::fs::read_dir(crates_dir())
            .expect("crates/ is readable")
            .filter_map(|e| e.ok())
            .map(|e| e.file_name().to_string_lossy().to_string())
            .filter(|n| n.starts_with("ferrosintesis-samples-"))
            .filter(|n| crates_dir().join(n).join("samples").is_dir())
            .collect();
        out.sort();
        assert!(
            out.len() > 15,
            "found only {} sample crates — the scan is not reading what it thinks it is",
            out.len()
        );
        out
    }

    /// The value assigned to `key` in `[package]`, including a multi-line array.
    fn package_assignment(manifest: &str, key: &str) -> Option<String> {
        let mut in_package = false;
        let mut lines = manifest.lines();
        while let Some(line) = lines.next() {
            let trimmed = line.trim();
            if trimmed.starts_with('[') {
                in_package = trimmed == "[package]";
                continue;
            }
            if !in_package {
                continue;
            }
            let Some((name, value)) = trimmed.split_once('=') else {
                continue;
            };
            if name.trim() != key {
                continue;
            }

            let mut value = value.trim().to_owned();
            if value.starts_with('[') {
                while !toml_array_is_closed(&value) {
                    let next = lines.next()?;
                    value.push('\n');
                    value.push_str(next);
                }
            }
            return Some(value);
        }
        None
    }

    fn toml_array_is_closed(value: &str) -> bool {
        let mut quote = None;
        let mut escaped = false;
        let mut depth = 0usize;
        for character in value.chars() {
            if let Some(delimiter) = quote {
                if delimiter == '"' && character == '\\' && !escaped {
                    escaped = true;
                    continue;
                }
                if character == delimiter && !escaped {
                    quote = None;
                }
                escaped = false;
                continue;
            }
            match character {
                '"' | '\'' => quote = Some(character),
                '[' => depth += 1,
                ']' => {
                    depth = depth.saturating_sub(1);
                    if depth == 0 {
                        return true;
                    }
                }
                _ => {}
            }
        }
        false
    }

    /// String values from the small TOML subset used by package path fields.
    fn toml_strings(value: &str) -> Vec<String> {
        let mut strings = Vec::new();
        let mut current = String::new();
        let mut quote = None;
        let mut escaped = false;
        for character in value.chars() {
            if let Some(delimiter) = quote {
                if delimiter == '"' && character == '\\' && !escaped {
                    escaped = true;
                    continue;
                }
                if character == delimiter && !escaped {
                    strings.push(std::mem::take(&mut current));
                    quote = None;
                    continue;
                }
                current.push(character);
                escaped = false;
            } else if character == '"' || character == '\'' {
                quote = Some(character);
            }
        }
        strings
    }

    fn declared_literal_package_files(manifest: &str) -> Result<Vec<String>, String> {
        let readme = package_assignment(manifest, "readme")
            .ok_or_else(|| "[package] has no explicit `readme`".to_owned())?;
        let readme = toml_strings(&readme);
        if readme.len() != 1 {
            return Err("`readme` must name exactly one string path".to_owned());
        }

        let include = package_assignment(manifest, "include")
            .ok_or_else(|| "[package] has no explicit `include`".to_owned())?;
        let include = toml_strings(&include);
        if include.is_empty() {
            return Err("`include` names no paths".to_owned());
        }

        let mut literal = readme;
        literal.extend(include.into_iter().filter(|path| {
            !path.starts_with('!')
                && !path.contains('*')
                && !path.contains('?')
                && !path.contains('[')
        }));
        literal.sort();
        literal.dedup();
        Ok(literal)
    }

    fn missing_declared_package_files(
        manifest: &str,
        mut exists: impl FnMut(&str) -> bool,
    ) -> Result<Vec<String>, String> {
        Ok(declared_literal_package_files(manifest)?
            .into_iter()
            .filter(|path| !exists(path))
            .collect())
    }

    /// The FAMILY prefixes a crate actually ships (`pizzbass_C2.wav` -> `pizzbass`).
    fn packaged_families(krate: &str) -> Vec<String> {
        let mut fams: Vec<String> = std::fs::read_dir(crates_dir().join(krate).join("samples"))
            .expect("a sample crate has a samples/ directory")
            .filter_map(|e| e.ok())
            .map(|e| e.file_name().to_string_lossy().to_string())
            .filter(|n| n.ends_with(".wav"))
            .filter_map(|n| n.split('_').next().map(str::to_string))
            .collect();
        fams.sort();
        fams.dedup();
        fams
    }

    /// Everything the crate's own package says about itself, lowercased.
    ///
    /// Deliberately the PACKAGED documents only. A pin that lives in `prepare.py` is
    /// invisible to a crates.io consumer, which is the whole complaint.
    fn crate_documentation(krate: &str) -> String {
        let root = crates_dir().join(krate);
        let mut text = String::new();
        for name in ["README.md", "PROVENANCE.md", "NOTICE"] {
            if let Ok(s) = std::fs::read_to_string(root.join(name)) {
                text.push_str(&s.to_lowercase());
                text.push('\n');
            }
        }
        text
    }

    /// Every packaged sample family is named in the documents its own crate ships.
    #[test]
    fn every_packaged_sample_family_is_documented_by_its_own_crate() {
        let mut undocumented = Vec::new();
        let mut checked = 0usize;
        for krate in sample_crates() {
            let docs = crate_documentation(&krate);
            for family in packaged_families(&krate) {
                checked += 1;
                if !docs.contains(&family.to_lowercase()) {
                    undocumented.push(format!("{krate}: {family}_*.wav"));
                }
            }
        }
        assert!(
            checked > 40,
            "only {checked} families scanned — the scan is broken"
        );
        assert!(
            undocumented.is_empty(),
            "{} sample family/families are packaged but named nowhere in their own \
             crate's README, PROVENANCE or NOTICE, so a consumer receives audio it \
             cannot trace:\n  {}",
            undocumented.len(),
            undocumented.join("\n  ")
        );
    }

    /// Every sample crate ships a `PROVENANCE.md`, and actually packages it.
    ///
    /// A pin recorded only in `tools/ferrosintesis-samples/prepare.py` does not travel:
    /// the tool is not part of any published crate. The file existing is not enough —
    /// `include` has to carry it, the same trap `licensing.rs` found for `NOTICE`.
    #[test]
    fn every_sample_crate_ships_a_packaged_provenance() {
        let mut missing = Vec::new();
        let mut unpackaged = Vec::new();
        for krate in sample_crates() {
            let root = crates_dir().join(krate.as_str());
            if !root.join("PROVENANCE.md").is_file() {
                missing.push(krate.clone());
                continue;
            }
            let manifest = std::fs::read_to_string(root.join("Cargo.toml"))
                .expect("a sample crate has a Cargo.toml");
            let packaged = manifest
                .lines()
                .find(|l| l.trim_start().starts_with("include"))
                .is_some_and(|l| l.contains("PROVENANCE"));
            if !packaged {
                unpackaged.push(krate.clone());
            }
        }
        assert!(
            missing.is_empty(),
            "{} sample crate(s) ship audio with no PROVENANCE.md, so their source pins \
             exist only in tools/ferrosintesis-samples/prepare.py — which is not part of \
             any published crate:\n  {}",
            missing.len(),
            missing.join("\n  ")
        );
        assert!(
            unpackaged.is_empty(),
            "{} sample crate(s) have a PROVENANCE.md that their `include` list does not \
             package, so the published crate ships without it:\n  {}",
            unpackaged.len(),
            unpackaged.join("\n  ")
        );
    }

    /// Every literal file named by a sample crate's package metadata exists.
    ///
    /// Path builds do not exercise Cargo's package assembly, so a missing `readme`
    /// can stay invisible until release day. Glob entries (`src/**`, `samples/**`)
    /// are intentionally left to Cargo; this oracle checks the literal documents
    /// whose absence is otherwise masked by ordinary builds.
    #[test]
    fn every_sample_crate_package_path_exists() {
        let mut malformed = Vec::new();
        let mut missing = Vec::new();
        let mut checked = 0usize;
        for krate in sample_crates() {
            let root = crates_dir().join(&krate);
            let manifest = std::fs::read_to_string(root.join("Cargo.toml"))
                .expect("a sample crate has a Cargo.toml");
            match missing_declared_package_files(&manifest, |path| root.join(path).exists()) {
                Ok(paths) => {
                    checked += 1;
                    missing.extend(paths.into_iter().map(|path| format!("{krate}/{path}")));
                }
                Err(error) => malformed.push(format!("{krate}: {error}")),
            }
        }

        assert!(
            checked > 20,
            "only {checked} sample manifests were checked — the scan is broken"
        );
        assert!(
            malformed.is_empty(),
            "sample crate package metadata could not be checked:\n  {}",
            malformed.join("\n  ")
        );
        assert!(
            missing.is_empty(),
            "sample crate manifests name files that do not exist, so `cargo package` \
             cannot assemble their declared archive:\n  {}",
            missing.join("\n  ")
        );
    }

    #[test]
    fn package_path_oracle_rejects_a_missing_literal_but_not_globs() {
        let manifest = "\
[package]\n\
readme = 'README.md'\n\
include = [\n\
  \"src/**\",\n\
  'samples/**',\n\
  \"README.md\",\n\
  \"PROVENANCE.md\",\n\
]\n";

        let missing =
            missing_declared_package_files(manifest, |path| path == "PROVENANCE.md").unwrap();
        assert_eq!(missing, ["README.md"]);
        assert!(missing_declared_package_files(manifest, |_| true)
            .unwrap()
            .is_empty());
    }
}
