//! Licensing-coverage oracles — the shipped attribution guide must name every
//! sample bank that legally requires attribution.
//!
//! ## Why this exists
//!
//! `ferrosintesis` embeds its PCM in first-party asset crates, and the default
//! `embedded-samples` feature pulls in first-party sample-asset crates. Most are
//! **CC0-1.0** and need no credit. The rest are **MIT**, **CC-BY-3.0** or
//! **CC-BY-4.0**, and a downstream binary distributor must reproduce their notices to
//! ship legally.
//!
//! The parent `README.md` is the licensing guide such a distributor is most likely to
//! read, and it was hand-maintained. That does not scale: by the time this module was
//! written the guide named only some of the attribution-bearing banks and silently
//! omitted the rest (MM-BUG-KILN-00060), because each new sample crate landed in its own
//! change and nobody re-read the inventory.
//!
//! These oracles remove the hand-maintenance. They derive the default bank set from the
//! manifest, derive each bank's attribution obligation independently from `PROVENANCE.md`,
//! and fail the build if the guide has drifted. Adding a new CC-BY bank to the default set
//! and forgetting the README is now a red test, not a compliance risk discovered later.
//!
//! ## What is deliberately NOT asserted here
//!
//! Whether each bank's provenance record is *correct* for the PCM it actually ships. The
//! per-crate `PROVENANCE.md` and its pinned source hashes preserve the evidence, but a text
//! oracle cannot settle that human judgement. This module does ensure that the provenance
//! record and the crate's declared `license` agree about whether attribution is required.

use std::path::{Path, PathBuf};

/// `crates/`, the directory holding this crate and every sample-asset crate.
pub(crate) fn crates_dir() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("crates/ferrosintesis always has a parent")
        .to_path_buf()
}

pub(crate) fn read(path: &Path) -> String {
    std::fs::read_to_string(path).unwrap_or_else(|e| {
        panic!(
            "licensing oracle cannot read {}: {e}.\n\
             These oracles derive the attribution guide from the sibling asset \
             manifests, so they only run inside the ferrosintesis workspace.",
            path.display()
        )
    })
}

/// The sample crates a **default** build embeds.
///
/// Read from the `embedded-samples` feature list rather than from `cfg!(feature)`, so
/// the oracle asserts the same thing under `--no-default-features`. An oracle that
/// quietly evaporates with a feature flag is how MM-BUG-KILN-00020 happened.
pub(crate) fn default_sample_crates() -> Vec<String> {
    let manifest = read(&crates_dir().join("ferrosintesis").join("Cargo.toml"));
    let mut out = Vec::new();
    let mut inside = false;
    for line in manifest.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("embedded-samples") && trimmed.contains('[') {
            inside = true;
            continue;
        }
        if inside {
            if trimmed.starts_with(']') {
                break;
            }
            if let Some(dep) = quoted(trimmed) {
                out.push(dep.trim_start_matches("dep:").to_string());
            }
        }
    }
    assert!(
        !out.is_empty(),
        "could not parse the `embedded-samples` feature list out of \
         crates/ferrosintesis/Cargo.toml — the oracle would otherwise pass vacuously"
    );
    out
}

/// The first double-quoted run in `line`, if any.
pub(crate) fn quoted(line: &str) -> Option<&str> {
    let rest = line.split_once('"')?.1;
    rest.split_once('"').map(|(inner, _)| inner)
}

/// The `license` field a sample crate declares in its `[package]` table.
pub(crate) fn declared_license(krate: &str) -> String {
    let manifest = read(&crates_dir().join(krate).join("Cargo.toml"));
    for line in manifest.lines() {
        let trimmed = line.trim();
        if let Some(rest) = trimmed.strip_prefix("license") {
            if rest.trim_start().starts_with('=') {
                if let Some(value) = quoted(trimmed) {
                    return value.to_string();
                }
            }
        }
    }
    panic!("{krate}/Cargo.toml declares no `license` field");
}

mod tests {
    use super::*;

    const MS_BASIC_SOURCE_REV: &str = "d307a2bd899f15bf650efc3c2891211af5cb78b5";
    const MS_BASIC_LICENSE: &str = include_str!(
        "upstream_licenses/ms_basic_license_d307a2bd899f15bf650efc3c2891211af5cb78b5.md"
    );
    const YDP_GRAND_UPSTREAM_CREDITS: &str =
        include_str!("upstream_licenses/ydp_grand_freepats_credits_20260731.md");

    /// The individual SPDX license ids joined by the subset of expressions these
    /// sample-crate manifests use.
    fn license_terms(expression: &str) -> Vec<&str> {
        expression
            .split(" AND ")
            .map(|term| {
                term.trim()
                    .trim_start_matches('(')
                    .trim_end_matches(')')
                    .trim()
            })
            .filter(|term| !term.is_empty())
            .collect()
    }

    fn declared_attribution_licenses(declared_license: &str) -> Vec<&str> {
        let mut licenses: Vec<&str> = license_terms(declared_license)
            .into_iter()
            .filter(|license| *license != "CC0-1.0")
            .collect();
        licenses.sort_unstable();
        licenses.dedup();
        licenses
    }

    /// Attribution-bearing licences accepted in sample-bank provenance records.
    ///
    /// This is deliberately a licence vocabulary, not a list of crates. An unfamiliar
    /// non-CC0 licence therefore fails closed until the oracle learns how the provenance
    /// document spells it.
    const ATTRIBUTION_LICENSES: &[&str] = &["MIT", "CC-BY-3.0", "CC-BY-4.0"];

    /// Derive the exact attribution-bearing licence ids from the independent provenance
    /// record.
    fn provenance_attribution_licenses(provenance: &str) -> Vec<&'static str> {
        let mut licenses: Vec<&'static str> = ATTRIBUTION_LICENSES
            .iter()
            .copied()
            .filter(|license| names_license_id(provenance, license))
            .collect();
        licenses.sort_unstable();
        licenses.dedup();
        licenses
    }

    /// Whether the manifest's attribution claim agrees with the crate's provenance.
    fn attribution_claim_agrees(declared_license: &str, provenance: &str) -> bool {
        declared_attribution_licenses(declared_license)
            == provenance_attribution_licenses(provenance)
    }

    fn format_licenses(licenses: &[&str]) -> String {
        if licenses.is_empty() {
            "none".to_string()
        } else {
            licenses.join(", ")
        }
    }

    /// Cross-check both records, then return the provenance-derived obligation.
    fn crate_requires_attribution(krate: &str, declared_license: &str) -> bool {
        let provenance = read(&crates_dir().join(krate).join("PROVENANCE.md"));
        let declared_licenses = declared_attribution_licenses(declared_license);
        let provenance_licenses = provenance_attribution_licenses(&provenance);
        assert!(
            declared_licenses == provenance_licenses,
            "{krate}/Cargo.toml declares {declared_license}, whose attribution licence \
             ids are {}, but {krate}/PROVENANCE.md names {}. The manifest cannot \
             exempt, understate, or overstate its own audio obligations; reconcile \
             the declaration with the retained provenance evidence.",
            format_licenses(&declared_licenses),
            format_licenses(&provenance_licenses)
        );
        !provenance_licenses.is_empty()
    }

    fn attribution_bearing_sample_crates() -> Vec<String> {
        default_sample_crates()
            .into_iter()
            .filter(|krate| {
                let license = declared_license(krate);
                crate_requires_attribution(krate, &license)
            })
            .collect()
    }

    /// Spellings of one licence id that count as naming it.
    ///
    /// The repo uses both the SPDX form (`CC-BY-4.0`, in manifests) and the prose form
    /// (`CC BY 4.0`, in the notices a human reads); either satisfies "this document says
    /// which licence applies".
    fn license_spellings(license_id: &str) -> Vec<String> {
        let mut out = vec![license_id.to_string()];
        if license_id.starts_with("CC-BY-") {
            out.push(license_id.replace('-', " "));
        }
        out
    }

    /// Does `text` contain `needle` as a whole token rather than inside a longer word?
    ///
    /// `MIT` is three letters that occur inside ordinary English: `LIMITED`, `LIMITATION`,
    /// `PERMIT`, `TRANSMIT`. A bare `contains` therefore reads the MIT licence into any
    /// document containing "WITHOUT LIMITATION" — which is most licence texts. No crate
    /// trips it today, but the failure it would produce is a CC0 bank being told to
    /// reconcile its manifest with a licence nobody claimed, which is a baffling place to
    /// start debugging.
    fn contains_word(text: &str, needle: &str) -> bool {
        let boundary = |c: Option<char>| !matches!(c, Some(c) if c.is_ascii_alphanumeric());
        let mut from = 0;
        while let Some(i) = text[from..].find(needle) {
            let at = from + i;
            let before = text[..at].chars().next_back();
            let after = text[at + needle.len()..].chars().next();
            if boundary(before) && boundary(after) {
                return true;
            }
            from = at + needle.len();
        }
        false
    }

    /// Does `text` name this licence id in any accepted spelling?
    fn names_license_id(text: &str, license_id: &str) -> bool {
        license_spellings(license_id)
            .iter()
            .any(|s| contains_word(text, s))
    }

    /// Does `text` name every licence id in the declared expression?
    fn names_license(text: &str, license: &str) -> bool {
        let terms = license_terms(license);
        !terms.is_empty()
            && terms
                .into_iter()
                .all(|license_id| names_license_id(text, license_id))
    }

    /// Does this NOTICE carry something only the LICENSOR could have supplied?
    ///
    /// `credit_tokens` answers "did a distinctive token travel into the guide", and for
    /// that it is right to be permissive. It is the wrong instrument for "is this document
    /// an attribution at all", because it extracts *any* quoted phrase — and licence
    /// boilerplate is full of them. Reduce `ferrosintesis-samples-clavinet`'s NOTICE to the
    /// bare MIT text and it still yields `"Software"` and `"AS IS"`, while Frank Wen,
    /// Michael Cowgill and S. Christian Collins — the people the MIT licence actually
    /// obliges us to credit — are gone (MM-BUG-KILN-00115).
    ///
    /// A source URL and a `Copyright (c) …` line are the two signals that cannot come from
    /// the licence text or from our own identifiers. Every attribution-bearing crate in the
    /// tree carries at least one: the Freesound/GitHub/archive.org banks have URLs, and the
    /// two MuseScore-lineage banks carry the FluidR3 copyright block instead.
    ///
    /// The licence's own `creativecommons.org` URL is excluded for the reason
    /// `credit_tokens` excludes it: it appears in every CC notice, so it identifies nobody.
    fn carries_licensor_owned_signal(notice: &str) -> bool {
        let has_source_url = notice.split_whitespace().any(|word| {
            word.find("http")
                .map(|i| word[i..].len() > 12 && !word.contains("creativecommons.org"))
                .unwrap_or(false)
        });
        // `©` alone is a copyright notice; the spelled-out word is only one when it is
        // making a claim (`Copyright (c) <holder>`), because every licence body contains
        // the sentence "The above copyright notice … shall be included".
        let has_copyright_line = notice.lines().any(|line| {
            let lower = line.to_ascii_lowercase();
            line.contains('©') || (lower.contains("copyright") && lower.contains("(c)"))
        });
        has_source_url || has_copyright_line
    }

    fn normalized_credit(text: &str) -> String {
        let separated: String = text
            .to_ascii_lowercase()
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() { c } else { ' ' })
            .collect();
        separated.split_whitespace().collect::<Vec<_>>().join(" ")
    }

    fn required_distributed_credits(evidence: &str) -> Vec<&str> {
        let required: Vec<&str> = evidence
            .lines()
            .filter_map(|line| line.strip_prefix("- Required distributed credit: `"))
            .filter_map(|credit| credit.strip_suffix('`'))
            .collect();
        assert!(
            !required.is_empty(),
            "retained upstream credit evidence contains no required distributed credits"
        );
        required
    }

    fn missing_required_credits<'a>(evidence: &'a str, document: &str) -> Vec<&'a str> {
        let normalized_document = normalized_credit(document);
        required_distributed_credits(evidence)
            .into_iter()
            .filter(|credit| !normalized_document.contains(&normalized_credit(credit)))
            .collect()
    }

    #[test]
    fn ydp_credit_oracle_rejects_notice_missing_krishtal() {
        let gutted = r#"
            "YDP Grand Piano" SoundFont by roberto@zenvoid.org for FreePats.
            Underlying computer-performed samples by the Zenph Studios team,
            recorded for OLPC.
            Source: https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html
        "#;
        let missing = missing_required_credits(YDP_GRAND_UPSTREAM_CREDITS, gutted);
        assert!(
            missing.contains(&"Dr. Mikhail Krishtal"),
            "the retained upstream evidence must reject a notice that keeps Roberto, \
             the work title, the source URL, and the recording context but removes \
             Dr. Mikhail Krishtal; missing={missing:?}"
        );
    }

    #[test]
    fn ydp_documents_reproduce_retained_upstream_credits() {
        let ydp = crates_dir().join("ferrosintesis-samples-ydp-grand");
        let parent = crates_dir().join("ferrosintesis");
        let documents = [
            (
                "ferrosintesis-samples-ydp-grand/NOTICE",
                read(&ydp.join("NOTICE")),
            ),
            (
                "ferrosintesis-samples-ydp-grand/PROVENANCE.md",
                read(&ydp.join("PROVENANCE.md")),
            ),
            ("ferrosintesis/NOTICE", read(&parent.join("NOTICE"))),
            ("ferrosintesis/README.md", read(&parent.join("README.md"))),
        ];

        let incomplete: Vec<String> = documents
            .into_iter()
            .filter_map(|(name, text)| {
                let missing = missing_required_credits(YDP_GRAND_UPSTREAM_CREDITS, &text);
                (!missing.is_empty()).then(|| format!("{name}: {}", missing.join(", ")))
            })
            .collect();
        assert!(
            incomplete.is_empty(),
            "published YDP credit documents omit identity or role fragments retained \
             from the independent FreePats source record:\n  {}",
            incomplete.join("\n  ")
        );
    }

    fn ms_basic_required_acknowledgements() -> Vec<(&'static str, String)> {
        let obligation = "The acknowledgements and copyright notices above must be included";
        let before_obligation = MS_BASIC_LICENSE.split_once(obligation).unwrap_or_else(|| {
            panic!(
                "the committed MS Basic licence fixture no longer carries the redistribution \
                 obligation marker"
            )
        });
        let required: Vec<(&str, String)> = before_obligation
            .0
            .lines()
            .map(str::trim)
            .filter(|line| line.contains("Copyright (c)"))
            .map(|line| (line, normalized_credit(line)))
            .collect();
        assert!(
            required.len() >= 5,
            "the committed MS Basic licence fixture yielded only {} acknowledgement \
             line(s); the parser is probably too narrow",
            required.len()
        );
        required
    }

    fn ms_basic_sample_crates() -> Vec<String> {
        let crates: Vec<String> = default_sample_crates()
            .into_iter()
            .filter(|krate| {
                let provenance = read(&crates_dir().join(krate).join("PROVENANCE.md"));
                provenance.contains(MS_BASIC_SOURCE_REV)
                    && provenance.contains("MS Basic.sf3")
                    && provenance.contains("SHA-256")
            })
            .collect();
        assert!(
            !crates.is_empty(),
            "no default sample crate provenance names the pinned MS Basic SF3 source"
        );
        crates
    }

    fn missing_ms_basic_acknowledgements(document: &str, text: &str) -> Vec<String> {
        let haystack = normalized_credit(text);
        ms_basic_required_acknowledgements()
            .into_iter()
            .filter_map(|(raw, normalized)| {
                (!haystack.contains(&normalized)).then(|| format!("{document}: {raw}"))
            })
            .collect()
    }

    #[test]
    fn licence_boilerplate_alone_is_not_an_attribution() {
        // The exact reduction that defeats the credit-token check: clavinet's NOTICE with
        // every real credit removed, leaving only the MIT grant.
        let gutted = "MIT License\n\nPermission is hereby granted, free of charge, to any \
                      person obtaining a copy of this software and associated documentation \
                      files (the \"Software\"), to deal in the Software without \
                      restriction.\n\nTHE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY \
                      OF ANY KIND.";
        assert!(
            !carries_licensor_owned_signal(gutted),
            "bare licence boilerplate must not read as an attribution"
        );
        // …and the parts that make it a real one, each sufficient on its own.
        assert!(carries_licensor_owned_signal(
            "Copyright (c) 2000-2002, 2008 Frank Wen <getfrank@gmail.com>"
        ));
        assert!(carries_licensor_owned_signal("© 2014-16 Michael Cowgill"));
        assert!(carries_licensor_owned_signal(
            "Source: https://freesound.org/people/tim.kahn/packs/3957/"
        ));
        // The licence's own URL identifies nobody, so it must not qualify.
        assert!(!carries_licensor_owned_signal(
            "Licensed CC BY 4.0, see https://creativecommons.org/licenses/by/4.0/"
        ));
    }

    #[test]
    fn ms_basic_notices_reproduce_every_required_upstream_acknowledgement() {
        let mut missing = Vec::new();
        for krate in ms_basic_sample_crates() {
            missing.extend(missing_ms_basic_acknowledgements(
                &format!("{krate}/NOTICE"),
                &read(&crates_dir().join(&krate).join("NOTICE")),
            ));
        }
        missing.extend(missing_ms_basic_acknowledgements(
            "ferrosintesis/NOTICE",
            &read(&crates_dir().join("ferrosintesis").join("NOTICE")),
        ));
        assert!(
            missing.is_empty(),
            "MS-Basic-derived sample notices omit required upstream acknowledgement \
             line(s):\n  {}",
            missing.join("\n  ")
        );
    }

    #[test]
    fn a_licence_id_inside_a_longer_word_does_not_name_that_licence() {
        assert!(names_license("distributed under the MIT License", "MIT"));
        assert!(names_license("**CC BY 4.0**, irrevocable", "CC-BY-4.0"));
        assert!(names_license("licensed CC-BY-3.0.", "CC-BY-3.0"));
        // The whole point: MIT boilerplate prose must not read as an MIT declaration.
        assert!(!names_license(
            "including without LIMITATION the rights to use",
            "MIT"
        ));
        assert!(!names_license("PERMITTED USES ARE LIMITED", "MIT"));
    }

    /// The DISTINCTIVE credit tokens a crate's own NOTICE carries: quoted work titles
    /// and source URLs.
    ///
    /// This is what turns "the guide mentions the crate" into "the credit travelled".
    /// A crate name is our own identifier and proves nothing about attribution — the
    /// verifier's repro for MM-BUG-KILN-00071 replaced the README and NOTICE with ten
    /// crate names, one per line, and every oracle still passed. A work title or source
    /// URL is the licensor's, so it cannot be reproduced by accident.
    ///
    /// The licence's own URL is excluded deliberately: it appears in every notice, so it
    /// would make the check pass for a bank whose credit was never carried over.
    /// Likewise, tokens contained in our crate, project or licence names are identifiers
    /// we own, not evidence that a third party was credited.
    fn credit_tokens(notice: &str, krate: &str, license: &str) -> Vec<String> {
        let mut out = Vec::new();
        let mut rest = notice;
        while let Some((_, after)) = rest.split_once('"') {
            match after.split_once('"') {
                Some((inner, tail)) => {
                    let title = inner.trim();
                    if title.len() >= 4 && !title.contains('\n') {
                        out.push(title.to_string());
                    }
                    rest = tail;
                }
                None => break,
            }
        }
        for word in notice.split_whitespace() {
            if let Some(i) = word.find("http") {
                let url = word[i..].trim_end_matches([')', ',', '.', ';', '—']);
                if url.len() > 12 && !url.contains("creativecommons.org") {
                    out.push(url.to_string());
                }
            }
        }
        let krate = krate.to_ascii_lowercase();
        let license_words: Vec<String> = license_terms(license)
            .into_iter()
            .flat_map(license_spellings)
            .map(|s| s.to_ascii_lowercase())
            .collect();
        out.retain(|candidate| {
            let candidate = candidate.to_ascii_lowercase();
            !krate.contains(&candidate)
                && !"ferrosintesis".contains(&candidate)
                && !license_words.iter().any(|s| s.contains(&candidate))
        });
        out
    }

    #[test]
    fn a_crates_own_name_is_not_a_credit_token() {
        let gutted =
            "ferrosintesis-samples-ccby audio is licensed CC BY 4.0. See the \"ccby\" bank.";
        assert!(
            credit_tokens(gutted, "ferrosintesis-samples-ccby", "CC-BY-4.0").is_empty(),
            "our own crate name cannot stand in for a licensor, work title, or source URL"
        );
    }

    #[test]
    fn provenance_prevents_a_manifest_from_self_exempting() {
        let provenance = "Two real recordings from Freesound, each licensed under **CC BY 4.0**.";
        assert!(
            !attribution_claim_agrees("CC0-1.0", provenance),
            "a CC0 manifest declaration must disagree with provenance that records CC BY audio"
        );
    }

    #[test]
    fn sax_manifest_declares_both_attribution_layers() {
        assert_eq!(
            declared_license("ferrosintesis-samples-sax"),
            "CC-BY-4.0 AND CC-BY-3.0",
            "the sax package embeds the CC BY 4.0 MTG.SoloSax derivative and the \
             underlying CC BY 3.0 good-sounds recordings"
        );
    }

    #[test]
    fn compound_licence_expression_requires_every_and_operand() {
        let declared = "CC-BY-4.0 AND CC-BY-3.0";
        assert!(names_license(
            "MTG.SoloSax is CC BY 4.0; the underlying good-sounds packs are CC BY 3.0.",
            declared
        ));
        assert!(
            !names_license("MTG.SoloSax is CC BY 4.0.", declared),
            "omitting the underlying CC BY 3.0 layer must not satisfy the declaration"
        );
        assert!(
            !names_license("The good-sounds packs are CC BY 3.0.", declared),
            "omitting the derivative CC BY 4.0 layer must not satisfy the declaration"
        );
        assert!(
            !attribution_claim_agrees(
                declared,
                "MTG.SoloSax derivative files are licensed CC BY 4.0."
            ),
            "provenance that omits CC BY 3.0 must disagree with a compound declaration"
        );
        assert!(
            !attribution_claim_agrees(declared, "The underlying recordings are CC BY 3.0."),
            "provenance that omits CC BY 4.0 must disagree with a compound declaration"
        );
    }

    /// The licence-section heading in force where `krate` is named in the parent NOTICE.
    ///
    /// The file groups banks under `---- / MIT / ----` style rules, and several banks
    /// share one credit body under a heading (the three MuseScore-lineage crates do), so
    /// a naive "span to the next crate name" would read an empty block for all but the
    /// last of a group. Keying off the heading matches how the document is actually
    /// written, and still catches a bank filed under the wrong licence.
    fn notice_section_for(notice: &str, krate: &str) -> Option<String> {
        let lines: Vec<&str> = notice.lines().collect();
        let is_rule = |l: &str| l.len() >= 20 && l.chars().all(|c| c == '-');
        let mut section: Option<String> = None;
        for (i, line) in lines.iter().enumerate() {
            if is_rule(line) && i + 2 < lines.len() && is_rule(lines[i + 2]) {
                section = Some(lines[i + 1].trim().to_string());
            }
            if mentions(line, krate) {
                return section;
            }
        }
        None
    }

    /// Does `text` name `krate` as an identifier rather than as a prefix of a longer one?
    fn mentions(text: &str, krate: &str) -> bool {
        let mut from = 0;
        while let Some(i) = text[from..].find(krate) {
            let at = from + i;
            let after = text[at + krate.len()..].chars().next();
            if !matches!(after, Some(c) if c.is_alphanumeric() || c == '-') {
                return true;
            }
            from = at + krate.len();
        }
        false
    }

    /// Parse a decimal or simple English number token used in the NOTICE's obligation
    /// paragraph. The parser stays deliberately small: it is not a general number parser,
    /// only an oracle for a document phrase whose count must track the derived set.
    fn number_value(token: &str) -> Option<usize> {
        let normalized = token
            .trim_matches(|c: char| !c.is_ascii_alphanumeric() && c != '-')
            .to_ascii_lowercase();
        if normalized.chars().all(|c| c.is_ascii_digit()) {
            if let Ok(value) = normalized.parse() {
                return Some(value);
            }
        }
        match normalized.as_str() {
            "zero" => Some(0),
            "one" => Some(1),
            "two" => Some(2),
            "three" => Some(3),
            "four" => Some(4),
            "five" => Some(5),
            "six" => Some(6),
            "seven" => Some(7),
            "eight" => Some(8),
            "nine" => Some(9),
            "ten" => Some(10),
            "eleven" => Some(11),
            "twelve" => Some(12),
            "thirteen" => Some(13),
            "fourteen" => Some(14),
            "fifteen" => Some(15),
            "sixteen" => Some(16),
            "seventeen" => Some(17),
            "eighteen" => Some(18),
            "nineteen" => Some(19),
            "twenty" => Some(20),
            "twenty-one" => Some(21),
            "twenty-two" => Some(22),
            "twenty-three" => Some(23),
            "twenty-four" => Some(24),
            "twenty-five" => Some(25),
            "twenty-six" => Some(26),
            "twenty-seven" => Some(27),
            "twenty-eight" => Some(28),
            "twenty-nine" => Some(29),
            _ => None,
        }
    }

    fn first_number(text: &str) -> Option<usize> {
        text.split_whitespace().next().and_then(number_value)
    }

    fn last_number(text: &str) -> Option<usize> {
        text.split_whitespace().rev().find_map(number_value)
    }

    /// Return count phrases in shipped attribution prose that disagree with the attribution
    /// set derived from the feature list and each bank's licence evidence. A count may be
    /// omitted entirely; if prose states one, it must be correct.
    fn attribution_count_mismatches(text: &str, expected: usize) -> Vec<String> {
        let normalized = text.split_whitespace().collect::<Vec<_>>().join(" ");
        let lower = normalized.to_ascii_lowercase();
        let mut mismatches = Vec::new();
        if let Some((before, _)) = lower.split_once("below are not") {
            if let Some(value) = last_number(before) {
                if value != expected {
                    mismatches.push(format!(
                        "{value} before `below are not` (expected {expected})"
                    ));
                }
            }
        }
        if let Some((before, _)) = lower.split_once("notices listed here") {
            if let Some(value) = last_number(before) {
                if value != expected {
                    mismatches.push(format!(
                        "{value} before `notices listed here` (expected {expected})"
                    ));
                }
            }
        }
        if lower.contains("satisfies every obligation") {
            if let Some((_, after)) = lower.split_once("those") {
                if let Some(value) = first_number(after) {
                    if value != expected {
                        mismatches.push(format!("{value} after `those` (expected {expected})"));
                    }
                }
            }
        }

        let words: Vec<&str> = lower.split_whitespace().collect();
        for (index, word) in words.iter().enumerate() {
            if word.trim_matches(|character: char| {
                !character.is_ascii_alphanumeric() && character != '-'
            }) != "attribution-bearing"
            {
                continue;
            }
            let start = index.saturating_sub(5);
            let end = (index + 6).min(words.len());
            let value = (start..index)
                .rev()
                .chain((index + 1)..end)
                .find_map(|position| number_value(words[position]));
            if let Some(value) = value {
                if value != expected {
                    mismatches.push(format!(
                        "{value} near `attribution-bearing` (expected {expected})"
                    ));
                }
            }
        }
        mismatches
    }

    #[test]
    fn notice_attribution_count_oracle_rejects_stale_count() {
        let expected = attribution_bearing_sample_crates().len();
        let stale = expected + 1;
        let notice = format!(
            "The {stale} below are not.\n\
             YOU MUST REPRODUCE THE {stale} NOTICES LISTED HERE.\n\
             concatenating those {stale} satisfies every obligation below."
        );
        let mismatches = attribution_count_mismatches(&notice, expected);
        assert_eq!(
            mismatches.len(),
            3,
            "the oracle must reject each stale obligation count: {mismatches:?}"
        );

        let hidden = format!("This index covers {stale} attribution-bearing crates.");
        let hidden_mismatches = attribution_count_mismatches(&hidden, expected);
        assert_eq!(
            hidden_mismatches.len(),
            1,
            "the oracle must reject a stale count outside its three legacy phrases: \
             {hidden_mismatches:?}"
        );

        let historical = format!("five of these {stale} attribution-bearing banks");
        let historical_mismatches = attribution_count_mismatches(&historical, expected);
        assert_eq!(
            historical_mismatches.len(),
            1,
            "the oracle must bind a compound phrase to its total count: \
             {historical_mismatches:?}"
        );
    }

    /// Every attribution-bearing bank in the default build is CREDITED in the licensing
    /// guide a distributor reads — named, with its licence, and carrying the licensor's
    /// own words.
    ///
    /// "Mentioned" is not "credited": the row must also state the licence and repeat a
    /// distinctive token (a work title or source URL) from the bank's own NOTICE, so a
    /// gutted table cannot pass (MM-BUG-KILN-00071).
    #[test]
    fn readme_names_every_attribution_bearing_sample_bank() {
        let readme = read(&crates_dir().join("ferrosintesis").join("README.md"));
        let expected_count = attribution_bearing_sample_crates().len();
        let count_mismatches = attribution_count_mismatches(&readme, expected_count);
        assert!(
            count_mismatches.is_empty(),
            "crates/ferrosintesis/README.md states stale attribution count(s):\n  {}",
            count_mismatches.join("\n  ")
        );

        let mut missing = Vec::new();
        let mut unlicensed = Vec::new();
        let mut uncredited = Vec::new();
        let mut covered = 0usize;
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if !crate_requires_attribution(&krate, &license) {
                continue;
            }
            let Some(row) = readme.lines().find(|l| mentions(l, &krate)) else {
                missing.push(format!("{krate} ({license})"));
                continue;
            };
            covered += 1;
            if !names_license(row, &license) {
                unlicensed.push(format!("{krate}: declares {license}, row says none"));
            }
            let tokens = credit_tokens(
                &read(&crates_dir().join(&krate).join("NOTICE")),
                &krate,
                &license,
            );
            assert!(
                !tokens.is_empty(),
                "{krate}/NOTICE carries no quoted work title and no source URL, so \
                 there is nothing distinctive to check travelled — that notice cannot \
                 be a real attribution"
            );
            if !tokens.iter().any(|t| row.contains(t.as_str())) {
                uncredited.push(format!("{krate}: none of {tokens:?} appear in its row"));
            }
        }

        assert!(
            missing.is_empty(),
            "crates/ferrosintesis/README.md omits {} attribution-bearing sample \
             bank(s) that the default build embeds:\n  {}\n\n\
             A downstream distributor following that guide would ship without the \
             required credit. Add each bank, its authors and its licence to the \
             \"Sample provenance and licensing\" section.",
            missing.len(),
            missing.join("\n  ")
        );
        assert!(
            unlicensed.is_empty(),
            "{} README row(s) name a bank without stating which licence applies, so a \
             distributor cannot tell what obligation they are under:\n  {}",
            unlicensed.len(),
            unlicensed.join("\n  ")
        );
        assert!(
            uncredited.is_empty(),
            "{} README row(s) name a bank but carry none of the credit its own NOTICE \
             requires — a row of bare crate names is not an attribution:\n  {}",
            uncredited.len(),
            uncredited.join("\n  ")
        );
        assert!(
            covered > 0,
            "no attribution-bearing bank was found at all — the oracle is not \
             actually checking anything"
        );
    }

    /// The parent crate ships a consolidated notice naming every attribution-bearing
    /// bank, and actually packages it.
    ///
    /// Without this, the published `ferrosintesis` crate carries no credit at all: the
    /// asset crates' own `NOTICE` files are not part of *its* package, and three sibling
    /// `PROVENANCE.md` files pointed at a `../ferrosintesis` notice that did not exist.
    #[test]
    fn parent_notice_is_packaged_and_names_every_attribution_bearing_bank() {
        let root = crates_dir().join("ferrosintesis");
        let notice_path = root.join("NOTICE");
        assert!(
            notice_path.is_file(),
            "crates/ferrosintesis/NOTICE is missing. A default build embeds \
             attribution-bearing audio, so the crate must carry a consolidated notice \
             telling a binary distributor what to reproduce."
        );

        let manifest = read(&root.join("Cargo.toml"));
        let include = manifest
            .lines()
            .find(|l| l.trim_start().starts_with("include"))
            .unwrap_or_else(|| {
                panic!("crates/ferrosintesis/Cargo.toml declares no `include` list")
            });
        assert!(
            include.contains("NOTICE"),
            "crates/ferrosintesis/NOTICE exists but the `include` list does not package \
             it, so the published crate would ship without it:\n  {include}"
        );

        let notice = read(&notice_path);
        let expected_notice_count = attribution_bearing_sample_crates().len();
        let count_mismatches = attribution_count_mismatches(&notice, expected_notice_count);
        assert!(
            count_mismatches.is_empty(),
            "crates/ferrosintesis/NOTICE states stale attribution count(s):\n  {}",
            count_mismatches.join("\n  ")
        );
        let mut missing = Vec::new();
        let mut misfiled = Vec::new();
        let mut uncredited = Vec::new();
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if !crate_requires_attribution(&krate, &license) {
                continue;
            }
            if !mentions(&notice, &krate) {
                missing.push(format!("{krate} ({license})"));
                continue;
            }
            // Filed under a heading that states ITS licence, not some other bank's.
            match notice_section_for(&notice, &krate) {
                Some(section) if names_license(&section, &license) => {}
                Some(section) => misfiled.push(format!(
                    "{krate} declares {license} but is listed under \"{section}\""
                )),
                None => misfiled.push(format!(
                    "{krate} is named outside any licence section, so the notice never \
                     says what applies to it"
                )),
            }
            // The licensor's own words reached this file.
            let tokens = credit_tokens(
                &read(&crates_dir().join(&krate).join("NOTICE")),
                &krate,
                &license,
            );
            if !tokens.iter().any(|t| notice.contains(t.as_str())) {
                uncredited.push(format!("{krate}: none of {tokens:?} appear"));
            }
        }
        assert!(
            missing.is_empty(),
            "crates/ferrosintesis/NOTICE omits {} attribution-bearing bank(s):\n  {}",
            missing.len(),
            missing.join("\n  ")
        );
        assert!(
            misfiled.is_empty(),
            "{} bank(s) are named in crates/ferrosintesis/NOTICE under a licence heading \
             that is not their own:\n  {}",
            misfiled.len(),
            misfiled.join("\n  ")
        );
        assert!(
            uncredited.is_empty(),
            "{} bank(s) are named in crates/ferrosintesis/NOTICE but none of the credit \
             from their own NOTICE travelled with them — a list of crate names satisfies \
             no licence:\n  {}",
            uncredited.len(),
            uncredited.join("\n  ")
        );
    }

    /// Every attribution-bearing bank carries the notice text it needs, in its own crate.
    #[test]
    fn every_attribution_bearing_sample_bank_ships_a_notice() {
        let mut missing = Vec::new();
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if !crate_requires_attribution(&krate, &license) {
                continue;
            }
            let notice = crates_dir().join(&krate).join("NOTICE");
            if !notice.is_file() {
                missing.push(format!("{krate} ({license})"));
                continue;
            }
            let text = read(&notice);
            assert!(
                text.trim().len() > 40,
                "{krate}/NOTICE exists but is too short to carry a real attribution"
            );
            // A length floor is satisfied by any 41 characters. These are the parts a
            // licence actually requires: who is credited, and under what terms.
            assert!(
                !credit_tokens(&text, &krate, &license).is_empty(),
                "{krate}/NOTICE names no work and cites no source (no quoted title, no \
                 URL) — it is text, not an attribution"
            );
            assert!(
                names_license(&text, &license),
                "{krate}/NOTICE never states the {license} licence it is reproducing, so \
                 a distributor cannot tell what the obligation is"
            );
            assert!(
                carries_licensor_owned_signal(&text),
                "{krate}/NOTICE carries no source URL and no `Copyright (c) …` line, so \
                 nothing in it identifies a licensor.\nA quoted phrase is not enough on \
                 its own: strip this crate's NOTICE down to bare MIT boilerplate and the \
                 quoted tokens \"Software\" and \"AS IS\" survive, so the credit check \
                 passes while every real credit has been deleted (MM-BUG-KILN-00115). A \
                 URL and a copyright line are the licensor's, not the licence text's."
            );
            assert!(
                notice_packaged(&krate),
                "{krate} has a NOTICE but its Cargo.toml `include` does not package it, \
                 so the published crate would ship without the required credit"
            );
        }
        assert!(
            missing.is_empty(),
            "sample bank(s) require attribution but ship no NOTICE:\n  {}",
            missing.join("\n  ")
        );
    }

    /// Every published package that can redistribute the sampled binary carries the
    /// consolidated notice in the package Cargo actually publishes.
    #[test]
    fn every_published_audio_consumer_packages_the_consolidated_notice() {
        let consumers = published_audio_consumers();
        assert!(
            consumers.iter().any(|krate| krate == "ferrosintesis-cli"),
            "the manifest-derived package census must discover ferrosintesis-cli"
        );

        let expected = read(&crates_dir().join("ferrosintesis").join("NOTICE"));
        let mut missing = Vec::new();
        let mut unbundled = Vec::new();
        let mut divergent = Vec::new();
        for krate in consumers {
            let notice = crates_dir().join(&krate).join("NOTICE");
            if !notice.is_file() {
                missing.push(krate);
                continue;
            }
            if !notice_packaged(&krate) {
                unbundled.push(krate);
                continue;
            }
            if normalize_line_endings(&read(&notice)) != normalize_line_endings(&expected) {
                divergent.push(krate);
            }
        }

        assert!(
            missing.is_empty(),
            "published audio consumer(s) carry no NOTICE:\n  {}",
            missing.join("\n  ")
        );
        assert!(
            unbundled.is_empty(),
            "published audio consumer(s) have a NOTICE, but Cargo does not package it:\n  {}",
            unbundled.join("\n  ")
        );
        assert!(
            divergent.is_empty(),
            "published audio consumer(s) do not carry the consolidated ferrosintesis notice:\n  {}",
            divergent.join("\n  ")
        );
    }

    /// Find package directories from the workspace tree instead of maintaining a list of
    /// binary or audio consumers beside the manifests that define them.
    fn published_audio_consumers() -> Vec<String> {
        let attribution_bearing = attribution_bearing_sample_crates();
        let mut consumers = Vec::new();
        let entries = std::fs::read_dir(crates_dir()).unwrap_or_else(|e| {
            panic!(
                "licensing oracle cannot enumerate workspace packages under {}: {e}",
                crates_dir().display()
            )
        });

        for entry in entries {
            let entry = entry.expect("licensing oracle could not read a workspace package entry");
            let path = entry.path();
            let manifest_path = path.join("Cargo.toml");
            if !manifest_path.is_file() {
                continue;
            }
            let manifest = read(&manifest_path);
            if !package_is_published(&manifest) {
                continue;
            }
            let name = package_name(&manifest);
            let has_binary = manifest.lines().any(|line| line.trim() == "[[bin]]");
            let depends_on_attribution_bearing = attribution_bearing
                .iter()
                .any(|krate| dependency_declared(&manifest, krate));
            if has_binary || depends_on_attribution_bearing {
                consumers.push(name);
            }
        }

        consumers.sort_unstable();
        consumers.dedup();
        assert!(
            !consumers.is_empty(),
            "manifest-derived published audio consumer census is empty"
        );
        consumers
    }

    fn normalize_line_endings(text: &str) -> String {
        text.replace("\r\n", "\n")
    }

    fn package_name(manifest: &str) -> String {
        let mut in_package = false;
        for line in manifest.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with('[') {
                in_package = trimmed == "[package]";
                continue;
            }
            if in_package && trimmed.starts_with("name") {
                if let Some(name) = quoted(trimmed) {
                    return name.to_string();
                }
            }
        }
        panic!("workspace package manifest declares no [package] name");
    }

    fn package_is_published(manifest: &str) -> bool {
        !manifest
            .lines()
            .any(|line| line.trim() == "publish = false")
    }

    fn dependency_declared(manifest: &str, dependency: &str) -> bool {
        let mut in_dependencies = false;
        for line in manifest.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with('[') {
                in_dependencies = trimmed == "[dependencies]";
                continue;
            }
            if !in_dependencies || !trimmed.starts_with(dependency) {
                continue;
            }
            return trimmed[dependency.len()..].trim_start().starts_with('=');
        }
        false
    }

    /// Does the crate's `include` list actually package its `NOTICE`?
    fn notice_packaged(krate: &str) -> bool {
        let manifest = read(&crates_dir().join(krate).join("Cargo.toml"));
        // `include` is a single-line array in these hand-written manifests.
        manifest
            .lines()
            .find(|l| l.trim_start().starts_with("include"))
            .is_some_and(|l| l.contains("NOTICE"))
    }

    /// Packaged documentation files for a bank crate: the text a crate consumer receives.
    fn packaged_bank_documents(krate: &str) -> Vec<(String, String)> {
        let root = crates_dir().join(krate);
        manifest_include_items(krate)
            .into_iter()
            .filter(|item| !item.contains('*'))
            .filter(|item| {
                let lower = item.to_ascii_lowercase();
                lower == "notice"
                    || lower.ends_with(".md")
                    || lower.contains("copying")
                    || lower.contains("license")
            })
            .filter_map(|item| {
                let path = root.join(&item);
                path.is_file().then(|| (item, read(&path)))
            })
            .collect()
    }

    fn packaged_documents_text(docs: &[(String, String)]) -> String {
        docs.iter()
            .map(|(name, text)| format!("--- {name} ---\n{text}"))
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn manifest_include_items(krate: &str) -> Vec<String> {
        let manifest = read(&crates_dir().join(krate).join("Cargo.toml"));
        let mut include = String::new();
        let mut inside_include = false;
        for line in manifest.lines() {
            let trimmed = line.trim_start();
            if !inside_include && trimmed.starts_with("include") {
                inside_include = true;
            }
            if inside_include {
                include.push_str(line);
                include.push('\n');
                if line.contains(']') {
                    break;
                }
            }
        }
        assert!(
            !include.is_empty(),
            "{krate}/Cargo.toml declares no `include` list, so the licensing oracle \
             cannot tell which upstream documents the published crate packages"
        );

        let mut out = Vec::new();
        let mut rest = include.as_str();
        while let Some((_, after_open)) = rest.split_once('"') {
            match after_open.split_once('"') {
                Some((item, after_close)) => {
                    out.push(item.to_string());
                    rest = after_close;
                }
                None => break,
            }
        }
        assert!(
            !out.is_empty(),
            "{krate}/Cargo.toml has an `include` list but the oracle parsed no entries:\n\
             {include}"
        );
        out
    }

    fn cc_by_canonical_uri(license_id: &str) -> Option<&'static str> {
        match license_id {
            "CC-BY-3.0" => Some("https://creativecommons.org/licenses/by/3.0/"),
            "CC-BY-4.0" => Some("https://creativecommons.org/licenses/by/4.0/"),
            _ => None,
        }
    }

    fn cc_by_legal_text_marker(license_id: &str) -> Option<&'static str> {
        match license_id {
            "CC-BY-3.0" => Some("Creative Commons Attribution 3.0 Unported"),
            "CC-BY-4.0" => Some("Creative Commons Attribution 4.0 International Public License"),
            _ => None,
        }
    }

    fn missing_cc_by_license_documents<'a>(docs: &str, declared_license: &'a str) -> Vec<&'a str> {
        license_terms(declared_license)
            .into_iter()
            .filter(|license_id| license_id.starts_with("CC-BY-"))
            .filter(|license_id| {
                let uri_present =
                    cc_by_canonical_uri(license_id).is_some_and(|uri| docs.contains(uri));
                let legal_text_present =
                    cc_by_legal_text_marker(license_id).is_some_and(|marker| docs.contains(marker));
                !(uri_present || legal_text_present)
            })
            .collect()
    }

    #[test]
    fn cc_by_sample_banks_package_license_uri_or_text() {
        let mut incomplete = Vec::new();
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if !license_terms(&license)
                .into_iter()
                .any(|license_id| license_id.starts_with("CC-BY-"))
            {
                continue;
            }

            let docs = packaged_bank_documents(&krate);
            assert!(
                !docs.is_empty(),
                "{krate} declares {license} audio but packages no README/NOTICE/COPYING/LICENSE \
                 document carrying the upstream terms"
            );
            let missing =
                missing_cc_by_license_documents(&packaged_documents_text(&docs), &license);
            if !missing.is_empty() {
                incomplete.push(format!("{krate}: {}", missing.join(", ")));
            }
        }

        assert!(
            incomplete.is_empty(),
            "CC BY sample bank package(s) omit the licence URI or legal text required by \
             their declared licence:\n  {}",
            incomplete.join("\n  ")
        );
    }

    #[test]
    fn sax_cc_by_3_uri_is_required_independently_of_cc_by_4_uri() {
        let krate = "ferrosintesis-samples-sax";
        let license = declared_license(krate);
        let docs = packaged_documents_text(&packaged_bank_documents(krate));
        assert!(
            missing_cc_by_license_documents(&docs, &license).is_empty(),
            "the checked-in sax package must carry every declared CC BY licence URI or text"
        );

        let without_cc_by_3_uri = docs.replace("https://creativecommons.org/licenses/by/3.0/", "");
        assert_eq!(
            missing_cc_by_license_documents(&without_cc_by_3_uri, &license),
            vec!["CC-BY-3.0"],
            "a CC BY 4.0 URI must not satisfy the sax package's independent CC BY 3.0 layer"
        );
    }

    fn missing_mit_notice_requirements(docs: &str, provenance: &str) -> Vec<&'static str> {
        let mut missing = Vec::new();
        let required_mit_fragments = [
            (
                "MIT permission grant",
                "Permission is hereby granted, free of charge",
            ),
            (
                "MIT permission-notice inclusion condition",
                "The above copyright notice and this permission notice shall be included",
            ),
            (
                "MIT warranty disclaimer",
                "THE SOFTWARE IS PROVIDED \"AS IS\"",
            ),
        ];
        for (name, fragment) in required_mit_fragments {
            if !docs.contains(fragment) {
                missing.push(name);
            }
        }

        if provenance.contains("MuseScore") || provenance.contains("FluidR3") {
            let required_musescore_fragments = [
                (
                    "FluidR3 original copyright",
                    "FluidR3 (original version) by Frank Wen Copyright (c) 2000-02",
                ),
                (
                    "FluidR3Mono conversion copyright",
                    "Mono conversion (FluidR3Mono) by Michael Cowgill Copyright (c) 2014-17",
                ),
                (
                    "MuseScore_General adaptation copyright",
                    "Adaptation for MuseScore_General.sf2 by S. Christian Collins Copyright (c) 2018-19",
                ),
                (
                    "Temple Blocks copyright",
                    "Temple Blocks instrument provided by Ethan Winer Copyright (c) 2002",
                ),
                (
                    "Drumline Cymbals copyright",
                    "Drumline Cymbals provided by Michael Schorsch Copyright (c) 2016",
                ),
                (
                    "FluidR3Mono copyright notice",
                    "Copyright (c) 2014-16 Michael Cowgill",
                ),
                (
                    "FluidR3 copyright notice",
                    "Copyright (c) 2000-2002, 2008 Frank Wen <getfrank@gmail.com>",
                ),
            ];
            for (name, fragment) in required_musescore_fragments {
                if !docs.contains(fragment) {
                    missing.push(name);
                }
            }
        }

        missing
    }

    #[test]
    fn mit_sample_banks_package_permission_grant_and_required_copyrights() {
        let mut incomplete = Vec::new();
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if license != "MIT" {
                continue;
            }

            let docs = packaged_bank_documents(&krate);
            assert!(
                !docs.is_empty(),
                "{krate} declares MIT audio but packages no README/NOTICE/COPYING/LICENSE \
                 document carrying the upstream terms"
            );
            let packaged_text = packaged_documents_text(&docs);
            let provenance = read(&crates_dir().join(&krate).join("PROVENANCE.md"));
            let missing = missing_mit_notice_requirements(&packaged_text, &provenance);
            if !missing.is_empty() {
                incomplete.push(format!("{krate}: {}", missing.join(", ")));
            }
        }

        assert!(
            incomplete.is_empty(),
            "MIT sample bank package(s) omit required upstream notice text:\n  {}",
            incomplete.join("\n  ")
        );
    }
}
