#![cfg(ferrosintesis_repository_tests)]

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path, PathBuf};

#[derive(Debug, Clone, PartialEq, Eq)]
enum TokenKind {
    Ident(String),
    String(String),
    Char,
    Punct(char),
}

#[derive(Debug, Clone)]
struct Token {
    kind: TokenKind,
    line: usize,
}

impl Token {
    fn ident(&self, wanted: &str) -> bool {
        matches!(&self.kind, TokenKind::Ident(value) if value == wanted)
    }

    fn punct(&self, wanted: char) -> bool {
        matches!(self.kind, TokenKind::Punct(value) if value == wanted)
    }

    fn string(&self) -> Option<&str> {
        match &self.kind {
            TokenKind::String(value) => Some(value),
            _ => None,
        }
    }
}

#[derive(Debug, Clone)]
struct Function {
    name: String,
    line: usize,
    body_start: usize,
    body_end: usize,
    is_test: bool,
    repository_gated: bool,
}

struct SourceUnit {
    path: PathBuf,
    tokens: Vec<Token>,
    functions: Vec<Function>,
}

#[derive(Debug)]
struct Finding {
    path: PathBuf,
    line: usize,
    function: String,
    reason: String,
}

#[derive(Debug)]
struct ScanReport {
    test_count: usize,
    findings: Vec<Finding>,
}

fn push_decoded_escape(value: &mut String, escaped: u8) {
    value.push(match escaped {
        b'n' => '\n',
        b'r' => '\r',
        b't' => '\t',
        b'0' => '\0',
        b'\\' => '\\',
        b'"' => '"',
        other => other as char,
    });
}

fn quoted_string(bytes: &[u8], quote: usize) -> (String, usize, usize) {
    let mut value = String::new();
    let mut index = quote + 1;
    let mut lines = 0;
    let mut escaped = false;
    while index < bytes.len() {
        let byte = bytes[index];
        if escaped {
            push_decoded_escape(&mut value, byte);
            escaped = false;
            index += 1;
            continue;
        }
        match byte {
            b'\\' => escaped = true,
            b'"' => return (value, index + 1, lines),
            b'\n' => {
                lines += 1;
                value.push('\n');
            }
            other => value.push(other as char),
        }
        index += 1;
    }
    (value, index, lines)
}

fn raw_string(bytes: &[u8], start: usize) -> Option<(String, usize, usize)> {
    let mut index = start;
    if bytes.get(index) == Some(&b'b') {
        if bytes.get(index + 1) != Some(&b'r') {
            return None;
        }
        index += 1;
    } else if bytes.get(index) != Some(&b'r') {
        return None;
    }
    index += 1;

    let mut hashes = 0usize;
    while bytes.get(index) == Some(&b'#') {
        hashes += 1;
        index += 1;
    }
    if bytes.get(index) != Some(&b'"') {
        return None;
    }
    let content_start = index + 1;
    index = content_start;
    let mut lines = 0;
    while index < bytes.len() {
        if bytes[index] == b'"'
            && bytes.get(index + 1..index + 1 + hashes) == Some(&vec![b'#'; hashes][..])
        {
            let value = String::from_utf8_lossy(&bytes[content_start..index]).into_owned();
            return Some((value, index + 1 + hashes, lines));
        }
        if bytes[index] == b'\n' {
            lines += 1;
        }
        index += 1;
    }
    Some((
        String::from_utf8_lossy(&bytes[content_start..]).into_owned(),
        index,
        lines,
    ))
}

fn char_literal(bytes: &[u8], start: usize) -> Option<(usize, usize)> {
    let quote = if bytes.get(start) == Some(&b'\'') {
        start
    } else if bytes.get(start) == Some(&b'b') && bytes.get(start + 1) == Some(&b'\'') {
        start + 1
    } else {
        return None;
    };

    let mut index = quote + 1;
    let mut lines = 0;
    if bytes.get(index) == Some(&b'\\') {
        index += 1;
        match bytes.get(index) {
            Some(b'x') => {
                index += 1;
                index = index.saturating_add(2);
            }
            Some(b'u') if bytes.get(index + 1) == Some(&b'{') => {
                index += 2;
                while index < bytes.len() && bytes[index] != b'}' {
                    if bytes[index] == b'\n' {
                        lines += 1;
                    }
                    index += 1;
                }
                if bytes.get(index) == Some(&b'}') {
                    index += 1;
                }
            }
            Some(_) => index += 1,
            None => return None,
        }
        return (bytes.get(index) == Some(&b'\'')).then_some((index + 1, lines));
    }

    let rest = std::str::from_utf8(bytes.get(index..)?).ok()?;
    let character = rest.chars().next()?;
    if character == '\n' || character == '\r' {
        return None;
    }
    index += character.len_utf8();
    (bytes.get(index) == Some(&b'\'')).then_some((index + 1, lines))
}

fn is_ident_start(byte: u8) -> bool {
    byte == b'_' || byte.is_ascii_alphabetic()
}

fn is_ident_continue(byte: u8) -> bool {
    byte == b'_' || byte.is_ascii_alphanumeric()
}

fn tokenize(source: &str) -> Vec<Token> {
    let bytes = source.as_bytes();
    let mut tokens = Vec::new();
    let mut index = 0usize;
    let mut line = 1usize;

    while index < bytes.len() {
        let byte = bytes[index];
        if byte.is_ascii_whitespace() {
            if byte == b'\n' {
                line += 1;
            }
            index += 1;
            continue;
        }

        if byte == b'/' && bytes.get(index + 1) == Some(&b'/') {
            index += 2;
            while index < bytes.len() && bytes[index] != b'\n' {
                index += 1;
            }
            continue;
        }
        if byte == b'/' && bytes.get(index + 1) == Some(&b'*') {
            index += 2;
            let mut depth = 1usize;
            while index < bytes.len() && depth > 0 {
                if bytes.get(index..index + 2) == Some(b"/*") {
                    depth += 1;
                    index += 2;
                } else if bytes.get(index..index + 2) == Some(b"*/") {
                    depth -= 1;
                    index += 2;
                } else {
                    if bytes[index] == b'\n' {
                        line += 1;
                    }
                    index += 1;
                }
            }
            continue;
        }

        if let Some((value, next, newlines)) = raw_string(bytes, index) {
            tokens.push(Token {
                kind: TokenKind::String(value),
                line,
            });
            line += newlines;
            index = next;
            continue;
        }

        if let Some((next, newlines)) = char_literal(bytes, index) {
            tokens.push(Token {
                kind: TokenKind::Char,
                line,
            });
            line += newlines;
            index = next;
            continue;
        }

        if byte == b'"' || (byte == b'b' && bytes.get(index + 1) == Some(&b'"')) {
            let quote = if byte == b'"' { index } else { index + 1 };
            let (value, next, newlines) = quoted_string(bytes, quote);
            tokens.push(Token {
                kind: TokenKind::String(value),
                line,
            });
            line += newlines;
            index = next;
            continue;
        }

        if is_ident_start(byte) {
            let start = index;
            index += 1;
            while index < bytes.len() && is_ident_continue(bytes[index]) {
                index += 1;
            }
            tokens.push(Token {
                kind: TokenKind::Ident(String::from_utf8_lossy(&bytes[start..index]).into_owned()),
                line,
            });
            continue;
        }

        tokens.push(Token {
            kind: TokenKind::Punct(byte as char),
            line,
        });
        index += 1;
    }
    tokens
}

fn matching(tokens: &[Token], open: usize, left: char, right: char) -> Option<usize> {
    let mut depth = 0usize;
    for (index, token) in tokens.iter().enumerate().skip(open) {
        if token.punct(left) {
            depth += 1;
        } else if token.punct(right) {
            depth = depth.checked_sub(1)?;
            if depth == 0 {
                return Some(index);
            }
        }
    }
    None
}

fn attribute_at(tokens: &[Token], hash: usize) -> Option<(usize, bool, bool)> {
    if !tokens.get(hash)?.punct('#') || !tokens.get(hash + 1)?.punct('[') {
        return None;
    }
    let close = matching(tokens, hash + 1, '[', ']')?;
    let attribute = &tokens[hash + 2..close];
    let is_test = attribute.len() == 1 && attribute[0].ident("test");
    let is_repository = attribute
        .iter()
        .any(|token| token.ident("ferrosintesis_repository_tests"));
    Some((close + 1, is_test, is_repository))
}

fn attribute_flags_before(tokens: &[Token], function: usize) -> (bool, bool) {
    let mut is_test = false;
    let mut is_repository = false;
    let mut index = function;
    while index > 0 {
        if tokens[index - 1].punct(']') {
            let mut depth = 1usize;
            let mut open = index - 1;
            while open > 0 {
                open -= 1;
                if tokens[open].punct(']') {
                    depth += 1;
                } else if tokens[open].punct('[') {
                    depth -= 1;
                    if depth == 0 {
                        break;
                    }
                }
            }
            if depth == 0 && open > 0 && tokens[open - 1].punct('#') {
                if let Some((end, test, repository)) = attribute_at(tokens, open - 1) {
                    if end == index {
                        is_test |= test;
                        is_repository |= repository;
                        index = open - 1;
                        continue;
                    }
                }
            }
        }
        if matches!(
            &tokens[index - 1].kind,
            TokenKind::Ident(value)
                if matches!(
                    value.as_str(),
                    "pub" | "crate" | "self" | "super" | "async" | "unsafe" | "const"
                        | "extern" | "default"
                )
        ) || tokens[index - 1].punct('(')
            || tokens[index - 1].punct(')')
        {
            index -= 1;
            continue;
        }
        break;
    }
    (is_test, is_repository)
}

fn repository_gate_at(tokens: &[Token]) -> Vec<bool> {
    let mut gates = vec![false; tokens.len()];
    let mut stack = vec![false];
    let mut pending_repository = false;
    let mut index = 0usize;
    while index < tokens.len() {
        gates[index] = *stack.last().unwrap_or(&false);
        if let Some((end, _, repository)) = attribute_at(tokens, index) {
            pending_repository |= repository;
            for gate in gates.iter_mut().take(end).skip(index) {
                *gate = *stack.last().unwrap_or(&false);
            }
            index = end;
            continue;
        }
        if tokens[index].punct('{') {
            let inherited = *stack.last().unwrap_or(&false);
            stack.push(inherited || pending_repository);
            pending_repository = false;
        } else if tokens[index].punct('}') {
            if stack.len() > 1 {
                stack.pop();
            }
            pending_repository = false;
        } else if tokens[index].punct(';') {
            pending_repository = false;
        }
        index += 1;
    }
    gates
}

fn function_body(tokens: &[Token], start: usize) -> Option<(usize, usize)> {
    let mut parentheses = 0usize;
    let mut brackets = 0usize;
    for index in start..tokens.len() {
        if tokens[index].punct('(') {
            parentheses += 1;
        } else if tokens[index].punct(')') {
            parentheses = parentheses.saturating_sub(1);
        } else if tokens[index].punct('[') {
            brackets += 1;
        } else if tokens[index].punct(']') {
            brackets = brackets.saturating_sub(1);
        } else if tokens[index].punct('{') && parentheses == 0 && brackets == 0 {
            return Some((index + 1, matching(tokens, index, '{', '}')?));
        } else if tokens[index].punct(';') && parentheses == 0 && brackets == 0 {
            return None;
        }
    }
    None
}

fn parse_functions(tokens: &[Token]) -> Vec<Function> {
    let gates = repository_gate_at(tokens);
    let mut functions = Vec::new();
    for (index, token) in tokens.iter().enumerate() {
        if !token.ident("fn") {
            continue;
        }
        let Some(name) = tokens.get(index + 1).and_then(|token| match &token.kind {
            TokenKind::Ident(name) => Some(name.clone()),
            _ => None,
        }) else {
            continue;
        };
        let Some((body_start, body_end)) = function_body(tokens, index + 2) else {
            continue;
        };
        let (is_test, direct_repository_gate) = attribute_flags_before(tokens, index);
        functions.push(Function {
            name,
            line: token.line,
            body_start,
            body_end,
            is_test,
            repository_gated: direct_repository_gate || gates[index],
        });
    }
    functions
}

fn rust_sources(directory: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    let Ok(entries) = fs::read_dir(directory) else {
        return files;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let Ok(kind) = entry.file_type() else {
            continue;
        };
        if kind.is_dir() {
            files.extend(rust_sources(&path));
        } else if kind.is_file() && path.extension().and_then(|ext| ext.to_str()) == Some("rs") {
            files.push(path);
        }
    }
    files.sort();
    files
}

fn repository_gated_external_modules(lib_source: &str) -> BTreeSet<String> {
    let mut modules = BTreeSet::new();
    let mut pending_repository = false;
    for raw in lib_source.lines() {
        let line = raw.trim();
        if line.starts_with("#[") {
            pending_repository |= line.contains("ferrosintesis_repository_tests");
            continue;
        }
        if pending_repository {
            let Some(rest) = line.split_once("mod ").map(|(_, rest)| rest) else {
                pending_repository = false;
                continue;
            };
            if let Some(name) = rest.strip_suffix(';') {
                modules.insert(name.trim().to_owned());
            }
            pending_repository = false;
        }
    }
    modules
}

fn lexical_path(base: &Path, raw: &str) -> PathBuf {
    let mut path = base.to_path_buf();
    for component in Path::new(raw).components() {
        match component {
            Component::Prefix(prefix) => path.push(prefix.as_os_str()),
            Component::RootDir => path.push(Path::new(std::path::MAIN_SEPARATOR_STR)),
            Component::CurDir => {}
            Component::ParentDir => {
                path.pop();
            }
            Component::Normal(part) => path.push(part),
        }
    }
    path
}

fn path_escapes(crate_root: &Path, base: &Path, raw: &str) -> bool {
    let path = lexical_path(base, raw);
    !path.starts_with(crate_root)
}

fn body_tokens<'a>(unit: &'a SourceUnit, function: &Function) -> &'a [Token] {
    &unit.tokens[function.body_start..function.body_end]
}

fn has_method(tokens: &[Token], method: &str) -> bool {
    tokens
        .windows(2)
        .any(|window| window[0].punct('.') && window[1].ident(method))
}

fn has_filesystem_operation(tokens: &[Token]) -> bool {
    [
        "read",
        "read_dir",
        "read_to_string",
        "read_to_end",
        "write",
        "open",
        "create_dir",
        "metadata",
        "canonicalize",
        "File",
    ]
    .iter()
    .any(|name| tokens.iter().any(|token| token.ident(name)))
}

fn has_manifest_dir_marker(tokens: &[Token]) -> bool {
    tokens.iter().any(|token| token.ident("CARGO_MANIFEST_DIR"))
        || tokens.windows(5).any(|window| {
            window[0].ident("env")
                && window[1].punct('!')
                && window[2].punct('(')
                && window[3].string() == Some("CARGO_MANIFEST_DIR")
                && window[4].punct(')')
        })
}

fn has_parent_path_component(value: &str) -> bool {
    value
        .split(|character| character == '/' || character == '\\')
        .any(|component| component == "..")
}

fn statement_slices(tokens: &[Token]) -> Vec<&[Token]> {
    let mut result = Vec::new();
    let mut start = 0usize;
    let mut parentheses = 0usize;
    let mut brackets = 0usize;
    for (index, token) in tokens.iter().enumerate() {
        if token.punct('(') {
            parentheses += 1;
        } else if token.punct(')') {
            parentheses = parentheses.saturating_sub(1);
        } else if token.punct('[') {
            brackets += 1;
        } else if token.punct(']') {
            brackets = brackets.saturating_sub(1);
        } else if token.punct(';') && parentheses == 0 && brackets == 0 {
            result.push(&tokens[start..index]);
            start = index + 1;
        }
    }
    if start < tokens.len() {
        result.push(&tokens[start..]);
    }
    result
}

fn direct_outside_read(
    unit: &SourceUnit,
    function: &Function,
    crate_root: &Path,
) -> Option<String> {
    let tokens = body_tokens(unit, function);
    let source_directory = unit.path.parent().unwrap_or_else(|| Path::new("."));

    for (index, token) in tokens.iter().enumerate() {
        if !token.ident("include_str") && !token.ident("include_bytes") {
            continue;
        }
        let mut cursor = index + 1;
        if tokens.get(cursor).is_some_and(|token| token.punct('!')) {
            cursor += 1;
        }
        if tokens.get(cursor).is_some_and(|token| token.punct('(')) {
            cursor += 1;
        }
        let Some(path) = tokens.get(cursor).and_then(Token::string) else {
            return Some(format!(
                "{}! has no statically visible path",
                if token.ident("include_str") {
                    "include_str"
                } else {
                    "include_bytes"
                }
            ));
        };
        if path_escapes(crate_root, source_directory, path) {
            return Some(format!("compile-time include escapes the crate: {path}"));
        }
    }

    for statement in statement_slices(tokens) {
        if !has_manifest_dir_marker(statement) {
            continue;
        }
        if has_method(statement, "parent") || has_method(statement, "ancestors") {
            return Some("CARGO_MANIFEST_DIR is traversed above the crate root".to_owned());
        }
        if statement
            .iter()
            .any(|token| token.string().is_some_and(has_parent_path_component))
        {
            return Some("CARGO_MANIFEST_DIR is combined with a parent path".to_owned());
        }
    }

    if tokens.iter().any(|token| token.ident("crates_dir")) && has_filesystem_operation(tokens) {
        return Some("filesystem access uses the repository-only crates_dir helper".to_owned());
    }

    if tokens.iter().any(|token| token.ident("current_dir")) && has_filesystem_operation(tokens) {
        return Some("filesystem access depends on the process working directory".to_owned());
    }

    for (index, token) in tokens.iter().enumerate() {
        let Some(value) = token.string() else {
            continue;
        };
        let path_like = tokens[..index].iter().rev().take(8).any(|previous| {
            previous.ident("join")
                || previous.ident("Path")
                || previous.ident("PathBuf")
                || [
                    "read",
                    "read_dir",
                    "read_to_string",
                    "read_to_end",
                    "open",
                    "File",
                ]
                .iter()
                .any(|name| previous.ident(name))
        });
        if path_like
            && (value == ".."
                || value.starts_with("../")
                || value.starts_with("..\\")
                || value.starts_with("ferrosintesis-samples-")
                || value.starts_with("tools/")
                || value.starts_with("tools\\"))
        {
            return Some(format!("filesystem path may escape the crate: {value}"));
        }
    }
    None
}

fn body_mentions(tokens: &[Token], name: &str) -> bool {
    tokens.iter().any(|token| token.ident(name))
}

fn analyze_units(units: &[SourceUnit], crate_root: &Path) -> ScanReport {
    let mut escaping = BTreeMap::<String, String>::new();
    for unit in units {
        for function in &unit.functions {
            if function.repository_gated {
                continue;
            }
            if let Some(reason) = direct_outside_read(unit, function, crate_root) {
                escaping.entry(function.name.clone()).or_insert(reason);
            }
        }
    }

    loop {
        let mut changed = false;
        let names: Vec<String> = escaping.keys().cloned().collect();
        for unit in units {
            for function in &unit.functions {
                if function.repository_gated || escaping.contains_key(&function.name) {
                    continue;
                }
                if names
                    .iter()
                    .any(|name| body_mentions(body_tokens(unit, function), name))
                {
                    escaping.insert(
                        function.name.clone(),
                        "calls a helper whose path leaves the crate".to_owned(),
                    );
                    changed = true;
                }
            }
        }
        if !changed {
            break;
        }
    }

    let mut test_count = 0usize;
    let mut findings = Vec::new();
    for unit in units {
        for function in &unit.functions {
            if !function.is_test {
                continue;
            }
            test_count += 1;
            if function.repository_gated {
                continue;
            }
            if let Some(reason) = escaping.get(&function.name) {
                findings.push(Finding {
                    path: unit.path.clone(),
                    line: function.line,
                    function: function.name.clone(),
                    reason: reason.clone(),
                });
            }
        }
    }
    ScanReport {
        test_count,
        findings,
    }
}

fn parse_unit(path: PathBuf, source: &str) -> SourceUnit {
    let tokens = tokenize(source);
    let functions = parse_functions(&tokens);
    SourceUnit {
        path,
        tokens,
        functions,
    }
}

fn scan_repository(crate_root: &Path) -> ScanReport {
    let source_root = crate_root.join("src");
    let lib_source = fs::read_to_string(source_root.join("lib.rs")).expect("lib.rs is readable");
    let gated_modules = repository_gated_external_modules(&lib_source);
    let mut units = Vec::new();
    for path in rust_sources(&source_root) {
        let is_root_module = path.parent() == Some(source_root.as_path());
        if is_root_module
            && path
                .file_stem()
                .and_then(|stem| stem.to_str())
                .is_some_and(|stem| gated_modules.contains(stem))
        {
            continue;
        }
        let source = fs::read_to_string(&path)
            .unwrap_or_else(|error| panic!("cannot read {}: {error}", path.display()));
        units.push(parse_unit(path, &source));
    }
    analyze_units(&units, crate_root)
}

fn outside_reads(source: &str) -> Vec<String> {
    let crate_root = Path::new("C:\\fixture");
    let unit = parse_unit(crate_root.join("src/fixture.rs"), source);
    analyze_units(&[unit], crate_root)
        .findings
        .into_iter()
        .map(|finding| finding.function)
        .collect()
}

#[test]
fn guard_rejects_an_ungated_sibling_read_but_allows_a_packaged_read() {
    let source = r#"
        #[test]
        fn reads_sibling() {
            let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap();
            std::fs::read_to_string(root.join("ferrosintesis-samples-sax/PROVENANCE.md"))
                .unwrap();
        }

        #[test]
        fn reads_packaged_file() {
            let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("README.md");
            std::fs::read_to_string(path).unwrap();
        }
    "#;

    let findings = outside_reads(source);
    assert_eq!(findings.len(), 1, "findings: {findings:?}");
    assert!(findings[0].contains("reads_sibling"));
}

#[test]
fn guard_ignores_test_data_and_repository_gated_reads() {
    let source = r#"
        #[cfg(ferrosintesis_repository_tests)]
        #[test]
        fn reads_repository_file() {
            let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap();
            std::fs::read_to_string(root.join("tools/ferrosintesis-samples/prepare.py"))
                .unwrap();
        }

        #[cfg(ferrosintesis_repository_tests)]
        mod repository_tests {
            #[test]
            fn reads_a_sibling_from_a_gated_module() {
                let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                    .parent()
                    .unwrap();
                std::fs::read_to_string(root.join("tools/README.md")).unwrap();
            }
        }

        #[test]
        fn checks_a_relative_name() {
            let name = "../not-a-path";
            assert!(name.starts_with("../"));
        }
    "#;

    assert!(outside_reads(source).is_empty());
}

#[test]
fn guard_detects_compile_time_includes_and_escaping_helpers() {
    let source = r#"
        fn repository_root() -> std::path::PathBuf {
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap()
                .to_path_buf()
        }

        #[test]
        fn calls_an_escaping_helper() {
            std::fs::read_to_string(repository_root().join("tools/README.md")).unwrap();
        }

        #[test]
        fn includes_a_sibling() {
            let _ = include_str!("../../ferrosintesis-samples-sax/PROVENANCE.md");
        }

        #[test]
        fn reads_a_relative_sibling_directly() {
            std::fs::read("../outside.txt").unwrap();
        }
    "#;

    let findings = outside_reads(source);
    assert_eq!(findings.len(), 3, "findings: {findings:?}");
    assert!(findings
        .iter()
        .any(|name| name == "calls_an_escaping_helper"));
    assert!(findings.iter().any(|name| name == "includes_a_sibling"));
    assert!(findings
        .iter()
        .any(|name| name == "reads_a_relative_sibling_directly"));
}

#[test]
fn guard_rejects_adversarial_manifest_path_escapes() {
    let source = r#"
        #[test]
        fn char_literal_before_escape() {
            let quote = '"';
            let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap();
            std::fs::read_to_string(root.join("CLAUDE.md")).unwrap();
        }

        #[test]
        fn concat_manifest_escape() {
            let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../CLAUDE.md");
            std::fs::read_to_string(path).unwrap();
        }

        #[test]
        fn format_manifest_escape() {
            let path = format!("{}/../../CLAUDE.md", env!("CARGO_MANIFEST_DIR"));
            std::fs::read_to_string(path).unwrap();
        }

        #[test]
        fn chained_parent_escape() {
            let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap()
                .parent()
                .unwrap();
            std::fs::read_to_string(path.join("CLAUDE.md")).unwrap();
        }

        #[test]
        fn ancestors_escape() {
            let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .ancestors()
                .nth(2)
                .unwrap();
            std::fs::read_to_string(path.join("CLAUDE.md")).unwrap();
        }

        #[test]
        fn qualified_crates_dir_escape() {
            std::fs::read_to_string(
                crate::licensing::crates_dir()
                    .join("ferrosintesis")
                    .join("README.md"),
            )
            .unwrap();
        }
    "#;

    let findings = outside_reads(source);
    let expected = [
        "char_literal_before_escape",
        "concat_manifest_escape",
        "format_manifest_escape",
        "chained_parent_escape",
        "ancestors_escape",
        "qualified_crates_dir_escape",
    ];
    assert_eq!(findings.len(), expected.len(), "findings: {findings:?}");
    for name in expected {
        assert!(
            findings.iter().any(|finding| finding == name),
            "missing {name}: {findings:?}"
        );
    }
}

#[test]
fn repository_source_has_no_ungated_outside_reads() {
    let crate_root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let report = scan_repository(crate_root);
    assert!(
        report.test_count > 300,
        "the archive-boundary scan found only {} tests; it stopped parsing the source tree",
        report.test_count
    );
    assert!(
        report.findings.is_empty(),
        "ungated tests read outside the published crate:\n{}",
        report
            .findings
            .iter()
            .map(|finding| {
                format!(
                    "{}:{} {} — {}",
                    finding.path.display(),
                    finding.line,
                    finding.function,
                    finding.reason
                )
            })
            .collect::<Vec<_>>()
            .join("\n")
    );
}
