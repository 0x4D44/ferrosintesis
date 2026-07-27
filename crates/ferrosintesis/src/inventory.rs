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
    use std::collections::{BTreeMap, BTreeSet};
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

    fn top_level_python_def(line: &str) -> Option<String> {
        let rest = line.strip_prefix("def ")?;
        let name = rest.split_once('(')?.0;
        Some(name.to_owned())
    }

    fn python_code_without_strings_or_comments(source: &str) -> String {
        let chars: Vec<char> = source.chars().collect();
        let mut out = String::with_capacity(source.len());
        let mut i = 0usize;
        let mut string: Option<(char, bool)> = None;

        while i < chars.len() {
            let ch = chars[i];
            if let Some((quote, triple)) = string {
                if triple {
                    if ch == quote
                        && i + 2 < chars.len()
                        && chars[i + 1] == quote
                        && chars[i + 2] == quote
                    {
                        string = None;
                        i += 3;
                        continue;
                    }
                    if ch == '\n' {
                        out.push('\n');
                    }
                    i += 1;
                    continue;
                }

                if ch == '\\' {
                    i = (i + 2).min(chars.len());
                    continue;
                }
                if ch == quote {
                    string = None;
                    i += 1;
                    continue;
                }
                if ch == '\n' {
                    string = None;
                    out.push('\n');
                }
                i += 1;
                continue;
            }

            match ch {
                '#' => {
                    while i < chars.len() && chars[i] != '\n' {
                        i += 1;
                    }
                }
                '\'' | '"' => {
                    let triple = i + 2 < chars.len() && chars[i + 1] == ch && chars[i + 2] == ch;
                    string = Some((ch, triple));
                    i += if triple { 3 } else { 1 };
                }
                _ => {
                    out.push(ch);
                    i += 1;
                }
            }
        }
        out
    }

    fn top_level_python_functions(source: &str) -> BTreeMap<String, String> {
        let mut functions = BTreeMap::new();
        let mut current_name = None;
        let mut current_body = String::new();

        for line in source.lines() {
            if let Some(name) = top_level_python_def(line) {
                if let Some(previous) = current_name.replace(name) {
                    functions.insert(
                        previous,
                        python_code_without_strings_or_comments(&current_body),
                    );
                    current_body.clear();
                }
            } else if current_name.is_some() {
                current_body.push_str(line);
                current_body.push('\n');
            }
        }

        if let Some(previous) = current_name {
            functions.insert(
                previous,
                python_code_without_strings_or_comments(&current_body),
            );
        }
        functions
    }

    fn is_python_ident(ch: char) -> bool {
        ch == '_' || ch.is_ascii_alphanumeric()
    }

    fn python_call_positions(code: &str, name: &str) -> Vec<usize> {
        code.match_indices(name)
            .filter_map(|(index, _)| {
                let before = code[..index].chars().next_back();
                if before.is_some_and(is_python_ident) {
                    return None;
                }
                let after = &code[index + name.len()..];
                after.trim_start().starts_with('(').then_some(index)
            })
            .collect()
    }

    #[derive(Clone, Copy, Default)]
    struct PythonBakeEffects {
        writes: bool,
        validates: bool,
        validates_before_first_write: bool,
    }

    fn python_bake_effects(
        name: &str,
        functions: &BTreeMap<String, String>,
        memo: &mut BTreeMap<String, PythonBakeEffects>,
        visiting: &mut BTreeSet<String>,
    ) -> PythonBakeEffects {
        const VALIDATOR: &str = "_validate_generated_output_inventory";
        if let Some(&effects) = memo.get(name) {
            return effects;
        }
        if !visiting.insert(name.to_owned()) {
            return PythonBakeEffects::default();
        }

        let body = &functions[name];
        let mut calls: Vec<(usize, Option<&str>)> = python_call_positions(body, "write_wav_mono")
            .into_iter()
            .map(|position| (position, None))
            .collect();
        for target in functions.keys().filter(|target| target.as_str() != name) {
            calls.extend(
                python_call_positions(body, target)
                    .into_iter()
                    .map(|position| (position, Some(target.as_str()))),
            );
        }
        calls.sort_by_key(|call| call.0);

        let mut effects = PythonBakeEffects::default();
        for (_, target) in calls {
            let Some(target) = target else {
                effects.writes = true;
                effects.validates_before_first_write = effects.validates;
                break;
            };
            if target == VALIDATOR {
                effects.validates = true;
                continue;
            }
            let called = python_bake_effects(target, functions, memo, visiting);
            if called.writes {
                effects.writes = true;
                effects.validates_before_first_write =
                    effects.validates || called.validates_before_first_write;
                effects.validates |= called.validates;
                break;
            }
            effects.validates |= called.validates;
        }

        visiting.remove(name);
        memo.insert(name.to_owned(), effects);
        effects
    }

    fn unvalidated_bake_output_helpers(source: &str) -> Vec<String> {
        let functions = top_level_python_functions(source);
        let mut memo = BTreeMap::new();

        functions
            .keys()
            .filter_map(|name| {
                if !(name.starts_with("_bake_") || name.starts_with("bake_")) {
                    return None;
                }
                let effects =
                    python_bake_effects(name, &functions, &mut memo, &mut BTreeSet::new());
                (effects.writes && !effects.validates_before_first_write).then(|| name.clone())
            })
            .collect()
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

    fn packaged_cc0_legal_text(manifest: &str, legal_text_exists: bool) -> Result<(), String> {
        let license = package_assignment(manifest, "license")
            .ok_or_else(|| "[package] has no explicit `license`".to_owned())?;
        let license = toml_strings(&license);
        if license.len() != 1 {
            return Err("`license` must name exactly one string expression".to_owned());
        }
        if license[0] != "CC0-1.0" {
            return Ok(());
        }
        if !legal_text_exists {
            return Err("declares CC0-1.0 but has no LICENSE-CC0".to_owned());
        }
        let include = package_assignment(manifest, "include")
            .ok_or_else(|| "[package] has no explicit `include`".to_owned())?;
        if !toml_strings(&include)
            .iter()
            .any(|path| path == "LICENSE-CC0")
        {
            return Err("has LICENSE-CC0 but does not package it".to_owned());
        }
        Ok(())
    }

    /// The FAMILY prefixes and counts a crate actually ships (`pizzbass_C2.wav` ->
    /// `pizzbass`).
    fn packaged_family_counts(krate: &str) -> BTreeMap<String, usize> {
        let mut families = BTreeMap::new();
        for name in std::fs::read_dir(crates_dir().join(krate).join("samples"))
            .expect("a sample crate has a samples/ directory")
            .filter_map(|entry| entry.ok())
            .map(|entry| entry.file_name().to_string_lossy().to_string())
            .filter(|name| name.ends_with(".wav"))
        {
            if let Some(family) = name.split('_').next() {
                *families.entry(family.to_owned()).or_insert(0) += 1;
            }
        }
        families
    }

    /// Canonical Markdown rows: ``| `family_*` | 12 | ... |``.
    ///
    /// Returning a list rather than a map preserves duplicates so the oracle can reject
    /// them instead of silently letting the last row win.
    fn provenance_family_rows(provenance: &str) -> Result<Vec<(String, usize)>, String> {
        let mut rows = Vec::new();
        for (index, line) in provenance.lines().enumerate() {
            let line = line.trim();
            if !line.starts_with('|') || !line.ends_with('|') {
                continue;
            }
            let cells: Vec<&str> = line.trim_matches('|').split('|').map(str::trim).collect();
            let Some(pattern) = cells
                .first()
                .and_then(|cell| cell.strip_prefix('`'))
                .and_then(|cell| cell.strip_suffix("_*`"))
            else {
                continue;
            };
            if pattern.is_empty() {
                return Err(format!("line {} has an empty family pattern", index + 1));
            }
            let count = cells
                .get(1)
                .ok_or_else(|| format!("line {} has no file count", index + 1))?
                .parse::<usize>()
                .map_err(|_| {
                    format!(
                        "line {} has a non-numeric file count for `{pattern}_*`",
                        index + 1
                    )
                })?;
            rows.push((pattern.to_owned(), count));
        }
        Ok(rows)
    }

    fn provenance_inventory_errors(
        packaged: &BTreeMap<String, usize>,
        provenance: &str,
    ) -> Vec<String> {
        let rows = match provenance_family_rows(provenance) {
            Ok(rows) => rows,
            Err(error) => return vec![error],
        };
        let mut errors = Vec::new();

        for (family, packaged_count) in packaged {
            let matches: Vec<usize> = rows
                .iter()
                .filter_map(|(row_family, count)| (row_family == family).then_some(*count))
                .collect();
            match matches.as_slice() {
                [] => errors.push(format!("missing canonical row for `{family}_*`")),
                [documented_count] if documented_count != packaged_count => errors.push(format!(
                    "`{family}_*` documents {documented_count} files but packages {packaged_count}"
                )),
                [_] => {}
                _ => errors.push(format!(
                    "`{family}_*` has {} canonical rows; expected exactly one",
                    matches.len()
                )),
            }
        }

        for (family, _) in &rows {
            if !packaged.contains_key(family) {
                errors.push(format!(
                    "canonical row `{family}_*` has no packaged sample family"
                ));
            }
        }
        errors
    }

    /// Every packaged sample family has one counted row in its crate's provenance.
    #[test]
    fn every_packaged_sample_family_has_one_counted_provenance_row() {
        let mut errors = Vec::new();
        let mut checked = 0usize;
        for krate in sample_crates() {
            let packaged = packaged_family_counts(&krate);
            checked += packaged.len();
            let provenance =
                std::fs::read_to_string(crates_dir().join(&krate).join("PROVENANCE.md"))
                    .expect("a sample crate has a PROVENANCE.md");
            errors.extend(
                provenance_inventory_errors(&packaged, &provenance)
                    .into_iter()
                    .map(|error| format!("{krate}: {error}")),
            );
        }
        assert!(
            checked > 40,
            "only {checked} families scanned — the scan is broken"
        );
        assert!(
            errors.is_empty(),
            "{} provenance inventory error(s); each packaged family needs exactly one \
             canonical `| `family_*` | FILES |` row in its own PROVENANCE.md:\n  {}",
            errors.len(),
            errors.join("\n  ")
        );
    }

    #[test]
    fn provenance_inventory_ignores_a_family_mention_outside_provenance() {
        let packaged = BTreeMap::from([("piano".to_owned(), 52)]);
        let readme = "The package contains the piano_* family.";
        let provenance = "# Provenance\n\nNo canonical inventory row.\n";

        assert!(readme.contains("piano_*"));
        assert_eq!(
            provenance_inventory_errors(&packaged, provenance),
            ["missing canonical row for `piano_*`"]
        );
    }

    #[test]
    fn provenance_inventory_rejects_wrong_duplicate_and_extra_rows() {
        let packaged = BTreeMap::from([("piano".to_owned(), 52), ("violin".to_owned(), 12)]);
        let provenance = "\
| Family | Files |\n\
| --- | ---: |\n\
| `piano_*` | 51 |\n\
| `violin_*` | 12 |\n\
| `violin_*` | 12 |\n\
| `obsolete_*` | 1 |\n";

        assert_eq!(
            provenance_inventory_errors(&packaged, provenance),
            [
                "`piano_*` documents 51 files but packages 52",
                "`violin_*` has 2 canonical rows; expected exactly one",
                "canonical row `obsolete_*` has no packaged sample family",
            ]
        );
    }

    /// A helper that writes a generated sample family must validate that family's
    /// packaged output inventory before its first write.
    #[test]
    fn every_generated_bake_output_family_is_inventory_validated() {
        let root = crates_dir()
            .parent()
            .expect("crates/ lives under the repository root")
            .to_path_buf();
        let prepare = std::fs::read_to_string(root.join("tools/ferrosintesis-samples/prepare.py"))
            .expect("prepare.py is readable");
        let missing = unvalidated_bake_output_helpers(&prepare);
        assert!(
            missing.is_empty(),
            "{} bake helper(s) write generated WAV outputs before reaching \
             `_validate_generated_output_inventory`:\n  {}",
            missing.len(),
            missing.join("\n  ")
        );
    }

    #[test]
    fn bake_output_inventory_oracle_rejects_an_unvalidated_writer() {
        let source = r#"
def _validate_generated_output_inventory(family, expected):
    pass

def _bake_newbank(src):
    # _validate_generated_output_inventory("newbank", NAMES) is only a comment.
    out_dir = os.path.join(REPO_ROOT, "crates", "ferrosintesis-samples-new", "samples")
    for name in NAMES:
        write_wav_mono(os.path.join(out_dir, f"newbank_{name}.wav"), [], OUT_SR)
"#;

        assert_eq!(unvalidated_bake_output_helpers(source), ["_bake_newbank"]);
    }

    #[test]
    fn bake_output_inventory_oracle_rejects_an_unvalidated_delegated_writer() {
        let source = r#"
def _validate_generated_output_inventory(family, expected):
    pass

def _write_newbank(out_dir):
    for name in NAMES:
        write_wav_mono(os.path.join(out_dir, f"newbank_{name}.wav"), [], OUT_SR)

def _bake_newbank(src):
    out_dir = os.path.join(REPO_ROOT, "crates", "ferrosintesis-samples-new", "samples")
    _write_newbank(out_dir)
"#;

        assert_eq!(unvalidated_bake_output_helpers(source), ["_bake_newbank"]);
    }

    #[test]
    fn bake_output_inventory_oracle_rejects_delegated_validation_after_write() {
        let source = r#"
def _validate_generated_output_inventory(family, expected):
    pass

def _write_newbank(out_dir):
    write_wav_mono(os.path.join(out_dir, "newbank_C4.wav"), [], OUT_SR)
    _validate_generated_output_inventory("newbank", {"newbank_C4.wav"})

def _bake_newbank(src):
    _write_newbank(src)
"#;

        assert_eq!(unvalidated_bake_output_helpers(source), ["_bake_newbank"]);
    }

    #[test]
    fn bake_output_inventory_oracle_accepts_transitive_validation() {
        let source = r#"
def _validate_generated_output_inventory(family, expected):
    pass

def _validate_generated_output_families(expected):
    _validate_generated_output_inventory("goodbank", expected)

def _bake_goodbank(src):
    _validate_generated_output_families({f"goodbank_{name}.wav" for name in NAMES})
    out_dir = os.path.join(REPO_ROOT, "crates", "ferrosintesis-samples-good", "samples")
    for name in NAMES:
        write_wav_mono(os.path.join(out_dir, f"goodbank_{name}.wav"), [], OUT_SR)
"#;

        assert!(unvalidated_bake_output_helpers(source).is_empty());
    }

    #[test]
    fn bake_output_inventory_oracle_accepts_validated_delegated_writer() {
        let source = r#"
def _validate_generated_output_inventory(family, expected):
    pass

def _write_goodbank(out_dir):
    _validate_generated_output_inventory("goodbank", {"goodbank_C4.wav"})
    write_wav_mono(os.path.join(out_dir, "goodbank_C4.wav"), [], OUT_SR)

def _bake_goodbank(src):
    _write_goodbank(src)
"#;

        assert!(unvalidated_bake_output_helpers(source).is_empty());
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

    /// Every CC0 sample archive carries the legal text promised by its manifest.
    ///
    /// A repository-level copy does not reach a separately published asset crate.
    /// Both the file and its literal `include` entry are required.
    #[test]
    fn every_cc0_sample_crate_ships_its_legal_text() {
        let mut errors = Vec::new();
        let mut checked = 0usize;
        for krate in sample_crates() {
            let root = crates_dir().join(&krate);
            let manifest = std::fs::read_to_string(root.join("Cargo.toml"))
                .expect("a sample crate has a Cargo.toml");
            if package_assignment(&manifest, "license")
                .is_some_and(|value| toml_strings(&value) == ["CC0-1.0"])
            {
                checked += 1;
            }
            if let Err(error) =
                packaged_cc0_legal_text(&manifest, root.join("LICENSE-CC0").is_file())
            {
                errors.push(format!("{krate}: {error}"));
            }
        }
        assert!(
            checked > 10,
            "only {checked} CC0 sample crates were checked — the scan is broken"
        );
        assert!(
            errors.is_empty(),
            "CC0 sample package legal-text errors:\n  {}",
            errors.join("\n  ")
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

    #[test]
    fn cc0_legal_text_oracle_rejects_missing_and_unpackaged_text() {
        let missing = "\
[package]\n\
license = \"CC0-1.0\"\n\
include = [\"src/**\", \"PROVENANCE.md\"]\n";
        assert_eq!(
            packaged_cc0_legal_text(missing, false).unwrap_err(),
            "declares CC0-1.0 but has no LICENSE-CC0"
        );
        assert_eq!(
            packaged_cc0_legal_text(missing, true).unwrap_err(),
            "has LICENSE-CC0 but does not package it"
        );

        let packaged = "\
[package]\n\
license = \"CC0-1.0\"\n\
include = [\"src/**\", \"LICENSE-CC0\", \"PROVENANCE.md\"]\n";
        assert!(packaged_cc0_legal_text(packaged, true).is_ok());
    }
}
