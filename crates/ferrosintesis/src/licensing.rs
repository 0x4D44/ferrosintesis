//! Licensing-coverage oracles — the shipped attribution guide must name every
//! sample bank that legally requires attribution.
//!
//! ## Why this exists
//!
//! `ferrosintesis` embeds its PCM in first-party asset crates, and the default
//! `embedded-samples` feature pulls in twenty-five of them. Most are **CC0-1.0** and need
//! no credit. The rest are **MIT**, **CC-BY-3.0** or **CC-BY-4.0**, and a downstream
//! binary distributor must reproduce their notices to ship legally.
//!
//! The parent `README.md` is the licensing guide such a distributor is most likely to
//! read, and it was hand-maintained. That does not scale: by the time this module was
//! written the guide named five of the ten attribution-bearing banks and silently
//! omitted the other five (MM-BUG-KILN-00060), because each new sample crate landed in
//! its own change and nobody re-read the inventory.
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

    /// CC0 waives attribution. Everything else here (MIT, CC-BY-3.0, CC-BY-4.0) requires
    /// the credit to travel with a binary distribution.
    fn requires_attribution(license: &str) -> bool {
        license != "CC0-1.0"
    }

    /// Attribution-bearing licences accepted in sample-bank provenance records.
    ///
    /// This is deliberately a licence vocabulary, not a list of crates. An unfamiliar
    /// non-CC0 licence therefore fails closed until the oracle learns how the provenance
    /// document spells it.
    const ATTRIBUTION_LICENSES: &[&str] = &["MIT", "CC-BY-3.0", "CC-BY-4.0"];

    /// Derive the obligation from the independent provenance record.
    fn provenance_requires_attribution(provenance: &str) -> bool {
        ATTRIBUTION_LICENSES
            .iter()
            .any(|license| names_license(provenance, license))
    }

    /// Whether the manifest's attribution claim agrees with the crate's provenance.
    fn attribution_claim_agrees(declared_license: &str, provenance: &str) -> bool {
        requires_attribution(declared_license) == provenance_requires_attribution(provenance)
    }

    /// Cross-check both records, then return the provenance-derived obligation.
    fn crate_requires_attribution(krate: &str, declared_license: &str) -> bool {
        let provenance = read(&crates_dir().join(krate).join("PROVENANCE.md"));
        let provenance_requires = provenance_requires_attribution(&provenance);
        assert!(
            attribution_claim_agrees(declared_license, &provenance),
            "{krate}/Cargo.toml declares {declared_license}, which says attribution is {}, \
             but {krate}/PROVENANCE.md says it is {}. The manifest cannot exempt its own \
             audio from the attribution oracles; reconcile the declaration with the \
             retained provenance evidence.",
            if requires_attribution(declared_license) {
                "required"
            } else {
                "not required"
            },
            if provenance_requires {
                "required"
            } else {
                "not required"
            }
        );
        provenance_requires
    }

    /// Spellings of a licence id that count as naming it.
    ///
    /// The repo uses both the SPDX form (`CC-BY-4.0`, in manifests) and the prose form
    /// (`CC BY 4.0`, in the notices a human reads); either satisfies "this document says
    /// which licence applies".
    fn license_spellings(license: &str) -> Vec<String> {
        let mut out = vec![license.to_string()];
        if license.starts_with("CC-BY-") {
            out.push(license.replace('-', " "));
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

    /// Does `text` name this licence in any accepted spelling?
    fn names_license(text: &str, license: &str) -> bool {
        license_spellings(license)
            .iter()
            .any(|s| contains_word(text, s))
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
        let license_spellings: Vec<String> = license_spellings(license)
            .into_iter()
            .map(|s| s.to_ascii_lowercase())
            .collect();
        out.retain(|candidate| {
            let candidate = candidate.to_ascii_lowercase();
            !krate.contains(&candidate)
                && !"ferrosintesis".contains(&candidate)
                && !license_spellings.iter().any(|s| s.contains(&candidate))
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

    /// Does the crate's `include` list actually package its `NOTICE`?
    fn notice_packaged(krate: &str) -> bool {
        let manifest = read(&crates_dir().join(krate).join("Cargo.toml"));
        // `include` is a single-line array in these hand-written manifests.
        manifest
            .lines()
            .find(|l| l.trim_start().starts_with("include"))
            .is_some_and(|l| l.contains("NOTICE"))
    }
}
