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
//! These oracles remove the hand-maintenance. They derive the truth from the manifests —
//! the default feature list, then each bank's own `license` field — and fail the build if
//! the guide has drifted. Adding a new CC-BY bank to the default set and forgetting the
//! README is now a red test, not a compliance risk discovered later.
//!
//! ## What is deliberately NOT asserted here
//!
//! Whether each bank's declared licence is *correct* for the PCM it actually ships. That
//! is a provenance question, answered by the per-crate `PROVENANCE.md` and its pinned
//! source hashes, not something a text oracle can settle. This module takes each crate's
//! declared `license` at face value and only checks that the guide is consistent with it.

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

    /// CC0 waives attribution. Everything else here (MIT, CC-BY-3.0, CC-BY-4.0) requires
    /// the credit to travel with a binary distribution.
    fn requires_attribution(license: &str) -> bool {
        license != "CC0-1.0"
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

    /// Does `text` name this licence in any accepted spelling?
    fn names_license(text: &str, license: &str) -> bool {
        license_spellings(license).iter().any(|s| text.contains(s))
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
    fn credit_tokens(notice: &str) -> Vec<String> {
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
        out
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
            if !requires_attribution(&license) {
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
            let tokens = credit_tokens(&read(&crates_dir().join(&krate).join("NOTICE")));
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
            if !requires_attribution(&license) {
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
            let tokens = credit_tokens(&read(&crates_dir().join(&krate).join("NOTICE")));
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
            if !requires_attribution(&license) {
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
                !credit_tokens(&text).is_empty(),
                "{krate}/NOTICE names no work and cites no source (no quoted title, no \
                 URL) — it is text, not an attribution"
            );
            assert!(
                names_license(&text, &license),
                "{krate}/NOTICE never states the {license} licence it is reproducing, so \
                 a distributor cannot tell what the obligation is"
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
