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

    fn markdown_family_patterns(markdown: &str) -> Vec<String> {
        let mut rows = Vec::new();
        for line in markdown.lines() {
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
            if !pattern.is_empty() {
                rows.push(pattern.to_owned());
            }
        }
        rows.sort();
        rows.dedup();
        rows
    }

    fn package_description(manifest: &str) -> Result<String, String> {
        let description = package_assignment(manifest, "description")
            .ok_or_else(|| "[package] has no explicit `description`".to_owned())?;
        let description = toml_strings(&description);
        if description.len() != 1 {
            return Err("`description` must name exactly one string expression".to_owned());
        }
        Ok(description[0].clone())
    }

    fn family_prefix_mentions(text: &str, packaged: &BTreeMap<String, usize>) -> Vec<String> {
        let tokens: Vec<String> = text
            .split(|c: char| !c.is_ascii_alphanumeric())
            .filter(|token| !token.is_empty())
            .map(|token| token.to_ascii_lowercase())
            .collect();
        packaged
            .keys()
            .filter(|family| {
                tokens
                    .iter()
                    .any(|token| token == &family.to_ascii_lowercase())
            })
            .cloned()
            .collect()
    }

    fn markdown_family_row_text(markdown: &str) -> BTreeMap<String, String> {
        let mut rows = BTreeMap::new();
        for line in markdown.lines() {
            let line = line.trim();
            if !line.starts_with('|') || !line.ends_with('|') {
                continue;
            }
            let cells: Vec<&str> = line.trim_matches('|').split('|').map(str::trim).collect();
            let Some(family) = cells
                .first()
                .and_then(|cell| cell.strip_prefix('`'))
                .and_then(|cell| cell.strip_suffix("_*`"))
            else {
                continue;
            };
            if !family.is_empty() {
                rows.entry(family.to_owned())
                    .or_insert_with(String::new)
                    .push_str(&cells.join(" "));
            }
        }
        rows
    }

    fn gm_programs(text: &str) -> BTreeSet<u8> {
        let mut programs = BTreeSet::new();
        let bytes = text.as_bytes();
        let mut index = 0usize;
        while let Some(offset) = text[index..].find("GM") {
            index += offset + 2;
            while index < bytes.len() && bytes[index].is_ascii_whitespace() {
                index += 1;
            }
            loop {
                let start = index;
                while index < bytes.len() && bytes[index].is_ascii_digit() {
                    index += 1;
                }
                if start == index {
                    break;
                }
                if let Ok(program) = text[start..index].parse::<u8>() {
                    programs.insert(program);
                }
                if index < bytes.len() && bytes[index] == b'/' {
                    index += 1;
                    continue;
                }
                break;
            }
        }
        programs
    }

    fn documented_family_programs(
        readme: &str,
        provenance: &str,
        packaged: &BTreeMap<String, usize>,
    ) -> BTreeMap<String, BTreeSet<u8>> {
        let mut out: BTreeMap<String, BTreeSet<u8>> = BTreeMap::new();
        for rows in [
            markdown_family_row_text(readme),
            markdown_family_row_text(provenance),
        ] {
            for (family, text) in rows {
                if packaged.contains_key(&family) {
                    out.entry(family).or_default().extend(gm_programs(&text));
                }
            }
        }
        out
    }

    fn family_gm_mentions(
        text: &str,
        family_programs: &BTreeMap<String, BTreeSet<u8>>,
    ) -> Vec<String> {
        let mentioned = gm_programs(text);
        family_programs
            .iter()
            .filter(|(_, programs)| programs.iter().any(|program| mentioned.contains(program)))
            .map(|(family, _)| family.clone())
            .collect()
    }

    fn markdown_intro(markdown: &str) -> String {
        markdown
            .lines()
            .take_while(|line| {
                let trimmed = line.trim();
                !trimmed.starts_with('|') && !trimmed.contains("PROVENANCE.md")
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn module_docs(lib: &str) -> String {
        lib.lines()
            .take_while(|line| {
                let trimmed = line.trim_start();
                trimmed.starts_with("//!") || trimmed.is_empty()
            })
            .map(|line| line.trim_start().trim_start_matches("//!"))
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn concrete_prepare_only_selectors(markdown: &str) -> Vec<String> {
        let mut selectors = Vec::new();
        for line in markdown.lines() {
            let mut rest = line;
            while let Some(offset) = rest.find("--only=") {
                let after = &rest[offset + "--only=".len()..];
                let selector: String = after
                    .chars()
                    .take_while(|ch| {
                        ch.is_ascii_alphanumeric()
                            || *ch == '_'
                            || *ch == '-'
                            || *ch == ','
                            || *ch == '<'
                            || *ch == '>'
                    })
                    .collect();
                let selector_len = selector.len();
                if !selector.is_empty() && !selector.contains('<') && !selector.contains('>') {
                    selectors.push(selector);
                }
                rest = &after[selector_len..];
            }
        }
        selectors
    }

    fn selector_families(selector: &str) -> Vec<String> {
        let mut families: Vec<String> = selector
            .split(',')
            .filter(|family| !family.is_empty())
            .map(str::to_owned)
            .collect();
        families.sort();
        families.dedup();
        families
    }

    fn family_list(families: &[String]) -> String {
        if families.is_empty() {
            "-".to_owned()
        } else {
            families
                .iter()
                .map(|family| format!("`{family}_*`"))
                .collect::<Vec<_>>()
                .join(", ")
        }
    }

    fn sorted_set_list(families: BTreeSet<String>) -> Vec<String> {
        families.into_iter().collect()
    }

    fn partial_summary_error(
        surface: &str,
        text: &str,
        packaged: &BTreeMap<String, usize>,
        family_programs: &BTreeMap<String, BTreeSet<u8>>,
        include_family_prefixes: bool,
    ) -> Option<String> {
        if packaged.len() > 8 {
            return None;
        }
        let mut mentions: BTreeSet<String> = family_gm_mentions(text, family_programs)
            .into_iter()
            .collect();
        if include_family_prefixes {
            mentions.extend(family_prefix_mentions(text, packaged));
        }
        if mentions.is_empty() || mentions.len() == packaged.len() {
            return None;
        }
        let missing: BTreeSet<String> = packaged
            .keys()
            .filter(|family| !mentions.contains(*family))
            .cloned()
            .collect();
        Some(format!(
            "{surface} summary names a partial family list (mentions {}; omits {})",
            family_list(&sorted_set_list(std::mem::take(&mut mentions))),
            family_list(&sorted_set_list(missing))
        ))
    }

    fn regeneration_selector_errors(
        surface: &str,
        markdown: &str,
        packaged: &BTreeMap<String, usize>,
    ) -> Vec<String> {
        concrete_prepare_only_selectors(markdown)
            .into_iter()
            .filter_map(|selector| {
                let selected = selector_families(&selector);
                if !selected.iter().any(|family| packaged.contains_key(family)) {
                    return None;
                }
                let missing: Vec<String> = packaged
                    .keys()
                    .filter(|family| !selected.contains(*family))
                    .cloned()
                    .collect();
                let extra: Vec<String> = selected
                    .iter()
                    .filter(|family| !packaged.contains_key(*family))
                    .cloned()
                    .collect();
                (!missing.is_empty() || !extra.is_empty()).then(|| {
                    format!(
                        "{surface} regeneration selector `--only={selector}` does not match \
                         packaged families (missing {}; extra {})",
                        family_list(&missing),
                        family_list(&extra)
                    )
                })
            })
            .collect()
    }

    fn public_inventory_surface_errors(
        packaged: &BTreeMap<String, usize>,
        readme: &str,
        provenance: &str,
        manifest: &str,
        lib: &str,
    ) -> Vec<String> {
        let mut errors = Vec::new();
        let packaged_families: Vec<String> = packaged.keys().cloned().collect();
        let family_programs = documented_family_programs(readme, provenance, packaged);

        let readme_rows = markdown_family_patterns(readme);
        let mut readme_table_is_complete = false;
        if !readme_rows.is_empty() {
            let missing: Vec<String> = packaged_families
                .iter()
                .filter(|family| !readme_rows.contains(*family))
                .cloned()
                .collect();
            let extra: Vec<String> = readme_rows
                .iter()
                .filter(|family| !packaged.contains_key(*family))
                .cloned()
                .collect();
            if !missing.is_empty() || !extra.is_empty() {
                errors.push(format!(
                    "README family table is partial (missing {}; extra {})",
                    family_list(&missing),
                    family_list(&extra)
                ));
            } else {
                readme_table_is_complete = true;
            }
        } else if readme.to_ascii_lowercase().contains("contents")
            && !readme.contains("PROVENANCE.md")
        {
            errors.push(
                "README contents section has no family table and does not delegate to packaged \
                 PROVENANCE.md"
                    .to_owned(),
            );
        }

        match package_description(manifest) {
            Ok(description) => {
                if let Some(error) = partial_summary_error(
                    "manifest description",
                    &description,
                    packaged,
                    &family_programs,
                    true,
                ) {
                    errors.push(error);
                }
            }
            Err(error) => errors.push(format!("manifest description is malformed: {error}")),
        }

        if let Some(error) = partial_summary_error(
            "README introduction",
            &markdown_intro(readme),
            packaged,
            &family_programs,
            false,
        ) {
            errors.push(error);
        }
        if let Some(error) = partial_summary_error(
            "module docs",
            &module_docs(lib),
            packaged,
            &family_programs,
            false,
        ) {
            errors.push(error);
        }
        errors.extend(regeneration_selector_errors("README", readme, packaged));
        errors.extend(regeneration_selector_errors(
            "PROVENANCE",
            provenance,
            packaged,
        ));

        let lib_lower = lib.to_ascii_lowercase();
        if lib_lower.contains("provenance")
            && (lib.contains("README.md") || lib.contains("tools/ferrosintesis-samples"))
            && !lib.contains("PROVENANCE.md")
            && !readme_table_is_complete
        {
            errors.push(
                "module docs direct provenance readers to README/tooling without naming packaged \
                 PROVENANCE.md"
                    .to_owned(),
            );
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
    fn every_public_sample_inventory_surface_is_complete_or_delegated() {
        let mut errors = Vec::new();
        let mut checked = 0usize;
        for krate in sample_crates() {
            let root = crates_dir().join(&krate);
            let packaged = packaged_family_counts(&krate);
            let read = |rel: &str| {
                std::fs::read_to_string(root.join(rel))
                    .unwrap_or_else(|e| panic!("cannot read {krate}/{rel}: {e}"))
            };
            let readme = read("README.md");
            let provenance = read("PROVENANCE.md");
            let manifest = read("Cargo.toml");
            let lib = read("src/lib.rs");
            checked += 1;
            errors.extend(
                public_inventory_surface_errors(&packaged, &readme, &provenance, &manifest, &lib)
                    .into_iter()
                    .map(|error| format!("{krate}: {error}")),
            );
        }
        assert!(
            checked > 20,
            "only {checked} sample crates were checked - the scan is broken"
        );
        assert!(
            errors.is_empty(),
            "{} public sample inventory surface error(s):\n  {}",
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

    #[test]
    fn public_inventory_oracle_rejects_partial_front_door_inventories() {
        let packaged = BTreeMap::from([
            ("banjo".to_owned(), 24),
            ("eastpick".to_owned(), 8),
            ("glock".to_owned(), 4),
            ("harp".to_owned(), 11),
        ]);
        let readme = "\
## Contents & provenance\n\
\n\
| Prefix | GM | Source |\n\
|--------|----|--------|\n\
| `banjo_*` | 105 | local |\n\
| `harp_*` | 46 | VCSL |\n";
        let manifest = "\
[package]\n\
description = \"Embedded samples for ferrosintesis (banjo, glock, harp)\"\n";
        let lib = "\
//! Embedded samples.\n\
//!\n\
//! Source provenance is in README.md and tools/ferrosintesis-samples.\n";
        let provenance = "\
| Family | Files | Instrument |\n\
| --- | ---: | --- |\n\
| `banjo_*` | 24 | Banjo (GM 105) |\n\
| `eastpick_*` | 8 | Steel guitar (GM 25) |\n\
| `glock_*` | 4 | Glockenspiel (GM 9) |\n\
| `harp_*` | 11 | Harp (GM 46) |\n";

        let errors = public_inventory_surface_errors(&packaged, readme, provenance, manifest, lib);
        assert!(errors.iter().any(|error| error.contains("README")));
        assert!(errors
            .iter()
            .any(|error| error.contains("manifest description")));
        assert!(errors.iter().any(|error| error.contains("module docs")));
    }

    #[test]
    fn public_inventory_oracle_rejects_partial_regeneration_selector_with_complete_table() {
        let packaged = BTreeMap::from([
            ("cellosolo".to_owned(), 16),
            ("dbass".to_owned(), 16),
            ("pizzbass".to_owned(), 8),
        ]);
        let readme = "\
| Prefix | GM | Instrument |\n\
| --- | --- | --- |\n\
| `cellosolo_*` | 42 | Solo cello |\n\
| `dbass_*` | 43 | Solo double bass |\n\
| `pizzbass_*` | 32 | Pizzicato double bass |\n\
\n\
Regenerate with `python3 tools/ferrosintesis-samples/prepare.py --only=cellosolo,dbass`.\n";
        let provenance = "\
| Family | Files | Instrument |\n\
| --- | ---: | --- |\n\
| `cellosolo_*` | 16 | Solo cello (GM 42) |\n\
| `dbass_*` | 16 | Solo double bass (GM 43) |\n\
| `pizzbass_*` | 8 | Pizzicato double bass (GM 32) |\n";
        let manifest = "\
[package]\n\
description = \"Embedded CC0 string samples for ferrosintesis; packaged PROVENANCE.md lists the full inventory\"\n";
        let lib = "//! Source provenance is in packaged `PROVENANCE.md`.\n";

        let errors = public_inventory_surface_errors(&packaged, readme, provenance, manifest, lib);
        assert_eq!(
            errors,
            ["README regeneration selector `--only=cellosolo,dbass` does not match packaged families (missing `pizzbass_*`; extra -)"]
        );
    }

    #[test]
    fn public_inventory_oracle_rejects_two_of_three_gm_summary() {
        let packaged = BTreeMap::from([
            ("cellosolo".to_owned(), 16),
            ("dbass".to_owned(), 16),
            ("pizzbass".to_owned(), 8),
        ]);
        let readme = "\
Embedded string samples for GM 42 cello and GM 43 double bass.\n\
\n\
| Prefix | GM | Instrument |\n\
| --- | --- | --- |\n\
| `cellosolo_*` | 42 | Solo cello |\n\
| `dbass_*` | 43 | Solo double bass |\n\
| `pizzbass_*` | 32 | Pizzicato double bass |\n";
        let provenance = "\
| Family | Files | Instrument |\n\
| --- | ---: | --- |\n\
| `cellosolo_*` | 16 | Solo cello (GM 42) |\n\
| `dbass_*` | 16 | Solo double bass (GM 43) |\n\
| `pizzbass_*` | 8 | Pizzicato double bass (GM 32) |\n";
        let manifest = "\
[package]\n\
description = \"Embedded samples for GM 42 cello and GM 43 double bass\"\n";
        let lib = "\
//! Embedded samples for GM 42 cello and GM 43 double bass.\n\
//! Source provenance is in packaged `PROVENANCE.md`.\n";

        let errors = public_inventory_surface_errors(&packaged, readme, provenance, manifest, lib);
        assert!(errors
            .iter()
            .any(|error| error.contains("manifest description summary")));
        assert!(errors
            .iter()
            .any(|error| error.contains("README introduction summary")));
        assert!(errors
            .iter()
            .any(|error| error.contains("module docs summary")));
    }

    #[test]
    fn public_inventory_oracle_accepts_complete_table_or_packaged_provenance_delegation() {
        let packaged = BTreeMap::from([("banjo".to_owned(), 24), ("harp".to_owned(), 11)]);
        let complete_readme = "\
| Prefix | GM | Source |\n\
|--------|----|--------|\n\
| `banjo_*` | 105 | local |\n\
| `harp_*` | 46 | VCSL |\n";
        let delegated_readme = "\
## Contents & provenance\n\
\n\
The canonical packaged inventory is `PROVENANCE.md`.\n";
        let manifest = "\
[package]\n\
description = \"Embedded CC0 onset samples for ferrosintesis; packaged PROVENANCE.md lists the full inventory\"\n";
        let lib = "//! Source provenance is in packaged `PROVENANCE.md`.\n";
        let provenance = "\
| Family | Files | Instrument |\n\
| --- | ---: | --- |\n\
| `banjo_*` | 24 | Banjo (GM 105) |\n\
| `harp_*` | 11 | Harp (GM 46) |\n";

        assert!(public_inventory_surface_errors(
            &packaged,
            complete_readme,
            provenance,
            manifest,
            lib
        )
        .is_empty());
        assert!(public_inventory_surface_errors(
            &packaged,
            delegated_readme,
            provenance,
            manifest,
            lib
        )
        .is_empty());
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
