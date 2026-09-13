//! Embedded-payload oracles — the prose must not lie about how much PCM a default
//! build compiles in.
//!
//! ## Why this exists
//!
//! Three separate documents quote the size of the embedded sample bank: the crate-level
//! docs in `lib.rs` (the docs.rs front page), the `README.md` (the crates.io front page),
//! and the `NOTICE` (the file a binary distributor reads to discharge its attribution
//! obligations). All three were hand-maintained, and all three had drifted:
//!
//! | Claim | Said | Actual at the time |
//! |---|---|---|
//! | `lib.rs` | "16.68 MiB … two first-party asset crates" | ~107 MiB, 23 crates |
//! | `README.md` | "~22 MiB", "twenty-one" crates | ~107 MiB, 23 crates |
//! | `NOTICE` | "twenty-one … Eleven are CC0" | 23 crates, 13 CC0 |
//!
//! A reader sizing their binary was misled by roughly five times. Nobody wrote a wrong
//! number: each figure was right when written, and each new sample crate landed in its
//! own change without anyone re-reading the totals. That is the repo's recurring defect
//! (see `CLAUDE.md`, "Hand-maintained lists are the recurring defect here"), and the
//! remedy is the same one `licensing.rs` applies to the attribution guide — derive the
//! number from the source of truth and fail the build when the prose disagrees.
//!
//! ## What is derived
//!
//! The default-feature crate list comes from the `embedded-samples` feature (read as
//! TEXT, via [`crate::licensing::default_sample_crates`], so these oracles assert the
//! same thing under `--no-default-features` — an oracle that evaporates with a feature
//! flag is how MM-BUG-KILN-00020 happened). The sample-file count and byte total come
//! from walking each of those crates' `samples/` directories on disk.
//!
//! ## What is deliberately NOT asserted
//!
//! An exact byte figure in the prose. Requiring one would make every re-cut sample a
//! docs change, and would tempt a future editor to paste a number rather than think.
//! The oracles assert the CRATE COUNT exactly (it is small, discrete and load-bearing)
//! and the size only to the nearest sensible rounding, with a tolerance stated below.

use crate::licensing::{crates_dir, default_sample_crates, read};
use std::path::Path;

/// The only default sample bank that deliberately remains WAV.
///
/// Every other default-embedded bank is a FLAC bank. Keep this exception explicit and
/// derive the covered crate set from the embedded-samples feature below.
const NON_FLAC_SAMPLE_CRATES: &[&str] = &["ferrosintesis-samples-b1-upright"];

fn expected_sample_container(krate: &str) -> &'static str {
    if NON_FLAC_SAMPLE_CRATES.contains(&krate) {
        "wav"
    } else {
        "flac"
    }
}

fn sample_container_errors<'a, I>(entries: I, expected: &'static str) -> Vec<String>
where
    I: IntoIterator<Item = (&'a str, &'a [u8])>,
{
    let mut files = 0usize;
    let mut found = None;
    let mut errors = Vec::new();

    for (name, bytes) in entries {
        files += 1;
        let extension = Path::new(name)
            .extension()
            .and_then(|extension| extension.to_str())
            .unwrap_or("");
        let Some(container) = (match extension {
            "wav" => Some("wav"),
            "flac" => Some("flac"),
            _ => None,
        }) else {
            errors.push(format!(
                "{name} has unsupported sample extension {extension:?}"
            ));
            continue;
        };

        if let Some(previous) = found {
            if previous != container {
                errors.push(format!(
                    "{name} uses {container}, mixed with the bank's {previous} files"
                ));
            }
        } else {
            found = Some(container);
        }

        if container != expected {
            errors.push(format!(
                "{name} uses {container}, but this bank must use {expected}"
            ));
        }

        let magic_matches = match container {
            "wav" => bytes.len() >= 12 && &bytes[..4] == b"RIFF" && &bytes[8..12] == b"WAVE",
            "flac" => bytes.len() >= 4 && &bytes[..4] == b"fLaC",
            _ => false,
        };
        if !magic_matches {
            errors.push(format!("{name} does not contain a {container} header"));
        }
    }

    if files == 0 {
        errors.push("sample directory contains no files".to_owned());
    }
    errors
}

fn sample_inventory(krate: &str) -> (usize, u64, &'static str) {
    fn visit(root: &Path, dir: &Path, entries: &mut Vec<(String, Vec<u8>)>) {
        for entry in
            std::fs::read_dir(dir).unwrap_or_else(|e| panic!("cannot read {}: {e}", dir.display()))
        {
            let path = entry.expect("sample entry must be readable").path();
            if path.is_dir() {
                visit(root, &path, entries);
                continue;
            }
            let name = path
                .strip_prefix(root)
                .unwrap_or(&path)
                .to_string_lossy()
                .into_owned();
            entries.push((
                name,
                std::fs::read(&path)
                    .unwrap_or_else(|e| panic!("cannot read {}: {e}", path.display())),
            ));
        }
    }

    let dir = crates_dir().join(krate).join("samples");
    let mut entries = Vec::new();
    visit(&dir, &dir, &mut entries);
    let expected = expected_sample_container(krate);
    let errors = sample_container_errors(
        entries
            .iter()
            .map(|(name, bytes)| (name.as_str(), bytes.as_slice())),
        expected,
    );
    assert!(
        errors.is_empty(),
        "{krate}/samples container oracle failed:\n  {}",
        errors.join("\n  ")
    );
    let actual = entries
        .iter()
        .find_map(|(name, _)| {
            match Path::new(name)
                .extension()
                .and_then(|extension| extension.to_str())
            {
                Some("wav") => Some("wav"),
                Some("flac") => Some("flac"),
                _ => None,
            }
        })
        .expect("validated sample inventory must have a known container");
    assert_eq!(
        actual, expected,
        "{krate}/samples uses {actual}, but its default-bank policy requires {expected}"
    );
    let bytes = entries
        .iter()
        .map(|(_, contents)| contents.len() as u64)
        .sum();
    (entries.len(), bytes, actual)
}

/// Number of embedded sample files and their total size, across the default sample crates.
pub(crate) fn embedded_payload() -> (usize, usize, u64) {
    let crates = default_sample_crates();
    let mut files = 0usize;
    let mut bytes = 0u64;
    for krate in &crates {
        let (crate_files, crate_bytes, _) = sample_inventory(krate);
        files += crate_files;
        bytes += crate_bytes;
    }
    assert!(
        crates.len() > 15 && files > 500,
        "payload scan collapsed to {} crates / {files} files — the oracle would pass \
         vacuously. Check the `embedded-samples` feature list parse.",
        crates.len()
    );
    (crates.len(), files, bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    /// Spelt-out numbers the prose uses, e.g. "twenty-four".
    fn spelled(n: usize) -> String {
        const ONES: [&str; 20] = [
            "zero",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        ];
        const TENS: [&str; 10] = [
            "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
        ];
        if n < 20 {
            return ONES[n].to_string();
        }
        let (t, o) = (n / 10, n % 10);
        if o == 0 {
            TENS[t].to_string()
        } else {
            format!("{}-{}", TENS[t], ONES[o])
        }
    }

    fn parent(file: &str) -> String {
        read(&crates_dir().join("ferrosintesis").join(file))
    }

    /// The container formats the package actually embeds, derived from its sample files.
    ///
    /// The docs below describe the published crate, not the upstream recordings or the
    /// temporary PCM/WAV produced while baking. Keep those source and processing references
    /// valid while refusing a package claim that names a format no longer under `samples/`.
    fn packaged_containers(krate: &str) -> BTreeSet<&'static str> {
        let (_, _, container) = sample_inventory(krate);
        BTreeSet::from([container])
    }

    fn mentions_container(text: &str, container: &str) -> bool {
        let lower = text.to_lowercase();
        let mut tokens = lower.split(|c: char| !(c.is_ascii_alphanumeric() || c == '_'));
        match container {
            "wav" => {
                lower.contains(".wav")
                    || tokens.clone().any(|token| matches!(token, "wav" | "wavs"))
                    || tokens.clone().any(|token| matches!(token, "riff" | "wave"))
            }
            "flac" => {
                lower.contains(".flac") || tokens.any(|token| matches!(token, "flac" | "flacs"))
            }
            _ => false,
        }
    }

    fn source_or_processing_context(text: &str) -> bool {
        let lower = text.to_lowercase();
        [
            "source",
            "upstream",
            "archive",
            "decode",
            "input",
            "trimmed from",
            "extracted from",
            "fetched",
            "retired",
            "read_wav",
            "temporary",
            "bake",
            "source cuts",
            "source recordings",
            "original",
            "auto-fetch",
        ]
        .iter()
        .any(|marker| lower.contains(marker))
    }

    fn package_claim_context(text: &str) -> bool {
        let lower = text.to_lowercase();
        [
            "embedded",
            "packaged",
            "crate ships",
            "package ships",
            "include_bytes",
            "in `samples/",
            "samples/ are",
            "under `samples/",
            "under samples/",
            "baked to `samples/",
            "raw ",
            "suffix",
            "exact",
            "file name",
            "file-name",
            "sample names",
            "sample file",
            "sample bytes",
            "stored as",
            "get(\"",
            "wav data",
            "flac data",
            "wav bytes",
            "flac bytes",
            "wav recordings",
            "flac recordings",
            "wav attack",
            "flac attack",
            "wav bodies",
            "flac bodies",
            "flac is lossless",
            "package file",
            "final package",
        ]
        .iter()
        .any(|marker| lower.contains(marker))
    }

    /// Find format words that describe the package surface, not its source or bake steps.
    ///
    /// The split at sentence/semicolon/dash boundaries matters: a correct sentence can say
    /// "source WAV ...; FLACs under samples ...". Treating that whole line as one claim would
    /// make a source format look like a packaged format and would blind the oracle to future
    /// mixed-input docs.
    fn documented_container_mismatches(
        file: &str,
        text: &str,
        packaged: &BTreeSet<&'static str>,
    ) -> Vec<String> {
        let source_file = file.ends_with("src/lib.rs");
        let mut packaged_section = !source_file;
        let mut errors = Vec::new();

        for (line_number, line) in text.lines().enumerate() {
            let trimmed = line.trim();
            let lower = trimmed.to_lowercase();
            if !source_file && trimmed.starts_with('#') {
                let ends_package_section = if file.ends_with("README.md") {
                    lower.contains("provenance and license")
                        || lower.starts_with("## source")
                        || lower.starts_with("## processing")
                        || lower.starts_with("## regenerat")
                } else {
                    lower.starts_with("## source")
                        || lower.starts_with("## sources")
                        || lower.starts_with("## processing")
                        || lower.starts_with("## regenerat")
                        || lower.starts_with("## selection")
                        || lower.contains("upstream")
                        || lower.contains("identity")
                        || lower.contains("committed-source")
                        || lower.contains("checksums")
                        || lower.starts_with("## removed")
                };
                if ends_package_section {
                    packaged_section = false;
                }
            }

            if source_file && !trimmed.starts_with("///") && !trimmed.starts_with("//!") {
                continue;
            }
            if !source_file
                && trimmed.starts_with('|')
                && !lower.contains("embedded")
                && !lower.contains("packaged")
            {
                continue;
            }

            let clauses = line
                .split(';')
                .flat_map(|part| part.split(" — "))
                .flat_map(|part| part.split(". "));
            for clause in clauses {
                if clause.to_lowercase().contains("alias") {
                    continue;
                }
                let sourceish = source_or_processing_context(clause);
                let packageish = package_claim_context(clause);
                if !packaged_section && !packageish {
                    continue;
                }
                if sourceish && !packageish {
                    continue;
                }
                for container in ["wav", "flac"] {
                    if packaged.contains(container) || !mentions_container(clause, container) {
                        continue;
                    }
                    errors.push(format!(
                        "{file}:{} names {container} for a package containing {}: {}",
                        line_number + 1,
                        packaged.iter().copied().collect::<Vec<_>>().join("/"),
                        trimmed
                    ));
                }
            }
        }
        errors
    }

    /// Size-of-the-embedded-bank claims: `(file, paragraph, value in MiB)`.
    ///
    /// Scoped to paragraphs that both name a unit and say they are describing what a build
    /// *embeds* or *compiles in* — the per-crate provenance tables also quote MiB, and
    /// those figures are correct for their own crate. Prose wraps at arbitrary line
    /// boundaries, so join each paragraph before looking for the two halves of a claim.
    fn size_claims_in(file: &'static str, text: &str) -> Vec<(&'static str, String, f64)> {
        let mut out = Vec::new();
        let mut paragraph = String::new();
        let mut scan = |paragraph: &str| {
            let lower = paragraph.to_ascii_lowercase();
            let has_unit = lower.contains("mib") || lower.contains(" mb");
            let about_embedding = lower.contains("embed") || lower.contains("compil");
            if !has_unit || !about_embedding || lower.trim_start().starts_with('|') {
                return;
            }
            for unit in ["mib", " mb"] {
                for (unit_start, _) in lower.match_indices(unit) {
                    let Some(tok) = paragraph[..unit_start]
                        .split(|c: char| !(c.is_ascii_digit() || c == '.'))
                        .rfind(|tok| !tok.is_empty())
                    else {
                        continue;
                    };
                    let Ok(v) = tok.parse::<f64>() else {
                        continue;
                    };
                    // Below 1 is a version fragment or a decimal tail, not a size.
                    if v >= 1.0 {
                        out.push((file, paragraph.to_string(), v));
                    }
                }
            }
        };

        for line in text.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                if !paragraph.is_empty() {
                    scan(&paragraph);
                    paragraph.clear();
                }
                continue;
            }
            if !paragraph.is_empty() {
                paragraph.push(' ');
            }
            paragraph.push_str(trimmed);
        }
        if !paragraph.is_empty() {
            scan(&paragraph);
        }
        out
    }

    fn size_claims() -> Vec<(&'static str, String, f64)> {
        ["README.md", "NOTICE", "src/lib.rs"]
            .into_iter()
            .flat_map(|file| size_claims_in(file, &parent(file)))
            .collect()
    }

    /// Words in `line` that state a number, as lowercase tokens.
    ///
    /// Deliberately token-exact rather than `contains`: `contains("4")` matches "24",
    /// and `contains("one")` matches "twenty-one". Both would make the staleness check
    /// below fire at random.
    fn number_tokens(line: &str) -> Vec<String> {
        line.split(|c: char| !(c.is_alphanumeric() || c == '-'))
            .map(|t| t.trim_matches('-').to_lowercase())
            .filter(|t| !t.is_empty())
            .collect()
    }

    /// Numeric value of a token, whether written as digits or as a word.
    fn as_number(tok: &str) -> Option<usize> {
        if let Ok(v) = tok.parse::<usize>() {
            return Some(v);
        }
        (0..=40).find(|&n| spelled(n) == tok)
    }

    /// Counts a document claims *of asset crates specifically*: `(file, line, count)`.
    ///
    /// The number must directly qualify the noun — "twenty-four first-party asset
    /// crates", "all twenty-four banks". A bare number elsewhere on the line is left
    /// alone, because the same sentences legitimately carry other counts: the NOTICE
    /// says "Fourteen are CC0 1.0 ... The ten below are not", and both are correct and
    /// about something else. An earlier draft of this oracle flagged that "ten", which
    /// is exactly the enumeration-predicate trap `CLAUDE.md` warns about.
    fn claimed_counts_in(line: &str) -> Vec<usize> {
        // Words that may sit between the number and the noun.
        const FILLER: &[&str] = &["first-party", "sample-asset", "asset", "embedded"];
        // A number introduced by one of these counts a SUBSET, not the whole bank:
        // "the remaining fourteen banks are CC0" is a true statement about part of a
        // 24-crate total, and reading it as a total claim is a false positive. This is
        // the same trap as the NOTICE's "ten below are not", one level subtler.
        const SUBSET: &[&str] = &["remaining", "other", "another", "further", "only"];
        let lower = line.to_lowercase();
        let mut out = Vec::new();
        let toks = number_tokens(&lower);
        for (i, tok) in toks.iter().enumerate() {
            if tok != "crates" && tok != "banks" {
                continue;
            }
            // Walk back over filler to the number that qualifies this noun, if any.
            // Stop at the first non-filler word: "ten of the twenty-four crates" must
            // bind to "twenty-four", never to "ten".
            let mut j = i;
            let mut hops = 0;
            while j > 0 && hops < 4 {
                j -= 1;
                hops += 1;
                let prev = toks[j].as_str();
                if let Some(n) = as_number(prev) {
                    // "crates" alone is ambiguous (workspace crates, dependency
                    // crates); require the asset-crate context. "banks" is ours.
                    let asset_context =
                        tok == "banks" || toks[j..=i].iter().any(|t| FILLER.contains(&t.as_str()));
                    let subset = j > 0 && SUBSET.contains(&toks[j - 1].as_str());
                    if asset_context && !subset {
                        out.push(n);
                    }
                    break;
                }
                if !FILLER.contains(&prev) {
                    break;
                }
            }
        }
        out
    }

    fn crate_count_claims() -> Vec<(&'static str, String, usize)> {
        let mut out = Vec::new();
        for file in ["README.md", "NOTICE", "src/lib.rs"] {
            for line in parent(file).lines() {
                // A table row is data, not prose.
                if line.trim_start().starts_with('|') {
                    continue;
                }
                for n in claimed_counts_in(line) {
                    out.push((file, line.to_string(), n));
                }
            }
        }
        out
    }

    /// Counts package-wide recording claims, including a format list between the number and
    /// noun: `(file, paragraph, count)`. Bank-specific prose such as "a recording" is not a
    /// total and is deliberately ignored.
    fn recording_count_claims_in(
        file: &'static str,
        text: &str,
    ) -> Vec<(&'static str, String, usize)> {
        const FORMAT_WORDS: &[&str] = &["wav", "flac", "audio", "sample", "samples"];
        let mut out = Vec::new();
        let mut paragraph = String::new();
        let mut scan = |paragraph: &str| {
            let lower = paragraph.to_lowercase();
            if paragraph.trim_start().starts_with('|')
                || !lower.contains("recording")
                || !lower.contains("binary")
                || !lower.contains("embed")
            {
                return;
            }
            let toks = number_tokens(&lower);
            for (i, tok) in toks.iter().enumerate() {
                if tok != "recordings" {
                    continue;
                }
                let mut j = i;
                let mut hops = 0;
                while j > 0 && hops < 4 {
                    j -= 1;
                    hops += 1;
                    if let Some(n) = as_number(&toks[j]) {
                        out.push((file, paragraph.to_string(), n));
                        break;
                    }
                    if !FORMAT_WORDS.contains(&toks[j].as_str()) {
                        break;
                    }
                }
            }
        };

        for line in text.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                if !paragraph.is_empty() {
                    scan(&paragraph);
                    paragraph.clear();
                }
                continue;
            }
            if !paragraph.is_empty() {
                paragraph.push(' ');
            }
            paragraph.push_str(trimmed);
        }
        if !paragraph.is_empty() {
            scan(&paragraph);
        }
        out
    }

    fn recording_count_claims() -> Vec<(&'static str, String, usize)> {
        ["README.md", "NOTICE", "src/lib.rs"]
            .into_iter()
            .flat_map(|file| recording_count_claims_in(file, &parent(file)))
            .collect()
    }

    const NUMBER_WORDS: &[&str] = &[
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
        "twenty-one",
        "twenty-two",
        "twenty-three",
        "twenty-four",
        "twenty-five",
        "twenty-six",
        "twenty-seven",
        "twenty-eight",
        "twenty-nine",
        "thirty",
    ];

    /// No document may state a STALE asset-crate count, and at least one must state
    /// the right one.
    ///
    /// Two halves on purpose. "No stale count" alone passes a document that dropped the
    /// figure entirely; "someone states it" alone passes a document that states both the
    /// right number and a leftover wrong one. Checked as digits ("24 crates") and words
    /// ("twenty-four") because the documents differ in register — `NOTICE` spells it out.
    ///
    /// A sentence that mentions asset crates WITHOUT quoting a count is fine and is not
    /// examined: prose is allowed to talk about the bank without sizing it.
    #[test]
    fn no_document_states_a_stale_asset_crate_count() {
        let (crates, _, _) = embedded_payload();
        let claims = crate_count_claims();
        assert!(
            !claims.is_empty(),
            "no document quotes an asset-crate count at all — either the wording changed \
             and this oracle now scans nothing, or the figure was dropped."
        );

        let mut stated_correctly = false;
        for (file, line, claimed) in &claims {
            assert_eq!(
                *claimed,
                crates,
                "{file} states {claimed} asset crates, but a default build embeds \
                 {crates} ({}), in:\n  {line}\n\
                 If you just added or split a crate, this is the oracle doing its job.",
                spelled(crates),
            );
            stated_correctly = true;
        }
        assert!(
            stated_correctly,
            "no document states the asset-crate count ({crates} / {})",
            spelled(crates),
        );
    }

    #[test]
    fn no_document_states_a_stale_recording_count() {
        let (_, recordings, _) = embedded_payload();
        let claims = recording_count_claims();
        assert!(
            !claims.is_empty(),
            "no document quotes the embedded recording count — either the wording changed \
             and this oracle now scans nothing, or the figure was dropped."
        );
        for (file, paragraph, claimed) in &claims {
            assert_eq!(
                *claimed, recordings,
                "{file} states {claimed} recordings, but a default build embeds {recordings} \
                 recordings, in:\n  {paragraph}"
            );
        }
    }

    #[test]
    fn recording_count_oracle_rejects_a_wrapped_stale_claim() {
        let wrapped = "The default `embedded-samples` feature compiles roughly 51.5 MiB of\n\
recorded audio across 1080 WAV/FLAC recordings from first-party asset crates into the binary.";
        let claims = recording_count_claims_in("src/lib.rs", wrapped);
        assert_eq!(
            claims
                .iter()
                .map(|(_, _, count)| *count)
                .collect::<Vec<_>>(),
            vec![1080]
        );
        assert_ne!(claims[0].2, embedded_payload().1);
    }

    /// The stated payload size must be within 10% of the real one.
    ///
    /// A loose bound on purpose: the point is to catch a figure that has drifted by
    /// multiples (16.68 MiB vs 107 MiB), not to force a docs commit whenever a sample is
    /// re-cut a few kilobytes shorter. 10% is far tighter than any drift seen here and
    /// far looser than routine re-baking.
    #[test]
    fn documented_payload_size_is_within_ten_percent() {
        let (_, _, bytes) = embedded_payload();
        let real_mib = bytes as f64 / (1024.0 * 1024.0);

        let claims = size_claims();
        assert!(
            !claims.is_empty(),
            "no embedded-size claim found in any of the three documents — either the \
             wording changed and this oracle now scans nothing, or the size claim was \
             dropped. Both need a human."
        );
        for (file, line, v) in &claims {
            let err = (v - real_mib).abs() / real_mib;
            assert!(
                err <= 0.10,
                "{file} claims {v} MiB of embedded audio but the default feature embeds \
                 {real_mib:.1} MiB ({:.0}% off), in:\n  {line}",
                err * 100.0,
            );
        }
    }

    #[test]
    fn size_oracle_rejects_a_wrapped_stale_claim() {
        let real_mib = embedded_payload().2 as f64 / (1024.0 * 1024.0);
        let wrapped = "The default `embedded-samples` feature compiles\n\
roughly 111 MiB of recorded audio across 1156 recordings in first-party asset crates.";
        let claims = size_claims_in("src/lib.rs", wrapped);
        assert_eq!(
            claims
                .iter()
                .map(|(_, _, value)| *value)
                .collect::<Vec<_>>(),
            vec![111.0],
            "the size oracle extracted numbers unrelated to the MiB unit: {claims:?}"
        );
        assert!(
            (claims[0].2 - real_mib).abs() / real_mib > 0.10,
            "the size oracle accepted a wrapped stale claim: {claims:?}"
        );
    }

    /// The oracles must actually FAIL on the documents they were written to catch.
    ///
    /// `CLAUDE.md`: "a derived oracle is only as good as its enumeration predicate, and
    /// the predicate is itself an assumption." Three of this repo's derived oracles were
    /// holed the day they were written by a reviewer who tried to defeat them rather
    /// than confirm them. So rather than trust that the predicates above discriminate,
    /// this runs them over the exact prose they replaced and asserts each one trips.
    ///
    /// The scanners are re-applied to fixture text here instead of to the real files, so
    /// this proves the PREDICATE, not the current documents.
    #[test]
    fn the_oracles_reject_the_prose_they_were_written_to_catch() {
        let real = 24usize;

        // The historical claims, verbatim from before 2026-07-25.
        let stale_counts = [
            "sample-asset crates into the binary. Eleven are CC0 1.0 and require nothing.",
            "A build with default features embeds all twenty-one banks.",
            "16.68 MiB of CC0 attack transients (two first-party asset crates) into",
        ];
        for text in stale_counts {
            let lower = text.to_lowercase();
            let toks = number_tokens(&lower);
            let has_stale = toks
                .iter()
                .any(|t| NUMBER_WORDS.contains(&t.as_str()) && *t != spelled(real));
            assert!(
                has_stale,
                "the count predicate does NOT flag a known-stale line: {text:?}\n\
                 It would have passed the drift it exists to catch."
            );
        }

        // ...and must NOT read a count out of prose that carries no asset-crate
        // figure, or out of a neighbouring count that is about something else. The
        // NOTICE line below is the one that holed an earlier draft.
        for benign in [
            "`embedded-samples` (default) compiles the asset crates into the binary.",
            "sample-asset crates into the binary. Fourteen are CC0 1.0 and require              nothing. The ten below are not,",
            "ten of the twenty-four crates carry an attribution obligation",
            "The remaining fourteen banks are CC0 and require nothing.",
        ] {
            for got in claimed_counts_in(benign) {
                assert_eq!(
                    got, real,
                    "the extractor invented a count {got} from benign prose {benign:?}"
                );
            }
        }

        // The size bound must reject the old ~22 MiB and 16.68 MiB claims against the
        // real ~104 MiB, and accept a figure within 10%.
        let real_mib = embedded_payload().2 as f64 / (1024.0 * 1024.0);
        for stale in [22.0_f64, 16.68] {
            assert!(
                (stale - real_mib).abs() / real_mib > 0.10,
                "the size bound would ACCEPT the stale claim {stale} MiB against the real \
                 {real_mib:.1} MiB — the tolerance is too loose to catch real drift."
            );
        }
        assert!(
            (real_mib * 1.05 - real_mib).abs() / real_mib <= 0.10,
            "the size bound rejects a figure only 5% out; it is too tight for routine \
             re-cutting and will produce docs churn."
        );
    }

    /// The scan must see the whole bank, not a subset.
    ///
    /// Without this, a broken feature-list parse would shrink what the two oracles above
    /// cover while they both kept passing — the failure mode `licensing.rs` and
    /// `sampler.rs` each guard against, for the same reason.
    #[test]
    fn payload_scan_covers_every_default_sample_crate() {
        let (crates, files, bytes) = embedded_payload();
        let members = read(&crates_dir().parent().unwrap().join("Cargo.toml"));
        let declared = members
            .lines()
            .filter(|l| l.contains("crates/ferrosintesis-samples-"))
            .count();
        assert_eq!(
            crates, declared,
            "the `embedded-samples` feature lists {crates} sample crates but the \
             workspace declares {declared} members. A crate in the workspace but not in \
             the default feature is embedded by nobody; add it to the feature list, or \
             mark it optional-by-design here."
        );
        // Anti-vacuity floor, NOT a size budget: it exists so a scan that has
        // stopped matching anything fails loudly rather than passing on an
        // empty set. Re-pinned when the banks moved from RIFF to FLAC, which
        // took the payload from ~111 MiB to ~54 MiB without losing a single
        // recording. Kept just under the real figure, for the same reason it
        // sat just under the old one.
        assert!(
            files > 1000 && bytes > 48 * 1024 * 1024,
            "payload scan found only {files} files / {bytes} bytes"
        );
    }

    /// Every public sample-crate document must name only the format its samples/ payload
    /// actually ships. The scan covers the API rustdoc and both packaged prose documents,
    /// while deliberately leaving upstream and temporary decode formats alone.
    #[test]
    fn sample_crate_documents_match_their_packaged_containers() {
        let crates = default_sample_crates();
        assert!(
            crates.len() > 15,
            "found only {} default sample crates — the documentation scan would be too narrow",
            crates.len()
        );

        let mut checked_documents = 0usize;
        let mut errors = Vec::new();
        for krate in crates {
            let packaged = packaged_containers(&krate);
            let root = crates_dir().join(&krate);
            for file in ["src/lib.rs", "README.md", "PROVENANCE.md"] {
                let path = root.join(file);
                let text = read(&path);
                checked_documents += 1;
                errors.extend(
                    documented_container_mismatches(file, &text, &packaged)
                        .into_iter()
                        .map(|error| format!("{krate}: {error}")),
                );
            }
        }
        assert!(
            checked_documents > 45,
            "checked only {checked_documents} sample-crate documents — the scan is not seeing the full set"
        );
        assert!(
            errors.is_empty(),
            "sample-crate prose names a container its package does not ship:\n  {}",
            errors.join("\n  ")
        );
    }

    #[test]
    fn sample_container_oracle_rejects_a_mutated_public_document() {
        let packaged = BTreeSet::from(["flac"]);
        let stale = "/// Returns the embedded WAV bytes for an exact file name.\n\
/// Names include the .wav suffix and are case-sensitive.";
        let errors = documented_container_mismatches("src/lib.rs", stale, &packaged);
        assert!(
            !errors.is_empty(),
            "the oracle accepted a stale WAV public contract"
        );

        let valid_mixed_input = "The source WAV is decoded; the FLAC under samples/ is packaged.";
        assert!(
            documented_container_mismatches("PROVENANCE.md", valid_mixed_input, &packaged)
                .is_empty(),
            "the oracle mistook a source WAV for the packaged FLAC"
        );

        let valid_legacy_alias = r#"The legacy .wav spelling is an alias: get("piano_C2_pp_rr2.wav") resolves to a packaged FLAC single take."#;
        assert!(
            documented_container_mismatches("README.md", valid_legacy_alias, &packaged).is_empty(),
            "the oracle mistook a compatibility alias for a packaged WAV"
        );

        let source_context = "The 11 WAVs in `samples/` are extracted from the source archive.";
        assert!(
            !documented_container_mismatches("PROVENANCE.md", source_context, &packaged).is_empty(),
            "the oracle exempted a packaged WAV claim because the same sentence names its source"
        );

        let source_heading = "## Extraction and bake\n\nThis crate ships 11 WAV files.";
        assert!(
            !documented_container_mismatches("PROVENANCE.md", source_heading, &packaged).is_empty(),
            "the oracle exempted a packaged WAV claim under an extraction heading"
        );
    }

    #[test]
    fn sample_container_oracle_rejects_a_wav_planted_in_a_flac_bank() {
        let wav = *b"RIFF....WAVE";
        let errors = sample_container_errors([("clavinet_C2.wav", wav.as_slice())], "flac");
        assert!(
            !errors.is_empty(),
            "the container oracle accepted a WAV planted in a FLAC bank"
        );
        assert!(
            sample_container_errors([("b1_hard_A0.wav", wav.as_slice())], "wav").is_empty(),
            "the explicit B1 WAV exception was rejected"
        );
    }

    #[test]
    fn default_sample_bank_containers_match_the_derived_policy() {
        let crates = default_sample_crates();
        let mut non_flac = Vec::new();
        for krate in &crates {
            let (_, _, actual) = sample_inventory(krate);
            let expected = expected_sample_container(krate);
            assert_eq!(actual, expected, "unexpected container for {krate}");
            if actual != "flac" {
                non_flac.push(krate.as_str());
            }
        }
        assert_eq!(
            non_flac, NON_FLAC_SAMPLE_CRATES,
            "the non-FLAC allowlist must stay explicit and minimal"
        );
    }

    /// No two asset crates may ship the same WAV basename.
    ///
    /// `sampler::embedded_wav` resolves a bare filename down a `.or_else` chain across
    /// every asset crate, first match wins, with no collision check. Today that is safe
    /// only because the banks happen to use distinct prefixes — nothing enforces it. A
    /// future crate adding a generically-named `flute_A4.wav` would silently shadow the
    /// existing one, and the symptom would be a wrong TIMBRE on a voice nobody edited:
    /// the hardest kind of bug to trace back to its cause.
    ///
    /// Scanning every `ferrosintesis-samples-*` directory on disk rather than the default
    /// feature list is deliberate — it is a superset of the lookup chain, so a collision
    /// is caught before any feature combination can reach it.
    #[test]
    fn no_two_asset_crates_ship_the_same_wav_basename() {
        let mut owner: std::collections::HashMap<String, String> = std::collections::HashMap::new();
        let mut clashes: Vec<String> = Vec::new();
        let mut scanned = 0usize;

        let mut crate_dirs: Vec<_> = std::fs::read_dir(crates_dir())
            .expect("readable crates/ directory")
            .map(|e| e.expect("readable entry").path())
            .filter(|p| {
                p.file_name()
                    .and_then(|n| n.to_str())
                    .is_some_and(|n| n.starts_with("ferrosintesis-samples-"))
            })
            .collect();
        crate_dirs.sort();

        for dir in &crate_dirs {
            let krate = dir
                .file_name()
                .and_then(|n| n.to_str())
                .expect("crate dir name")
                .to_owned();
            let samples = dir.join("samples");
            let Ok(entries) = std::fs::read_dir(&samples) else {
                continue;
            };
            for entry in entries {
                let path = entry.expect("readable directory entry").path();
                if path.extension().is_some_and(|e| e == "wav" || e == "flac") {
                    let name = path
                        .file_name()
                        .and_then(|n| n.to_str())
                        .expect("wav file name")
                        .to_owned();
                    scanned += 1;
                    if let Some(first) = owner.insert(name.clone(), krate.clone()) {
                        clashes.push(format!("{name} is in both {first} and {krate}"));
                    }
                }
            }

            // ALIASES logical names are part of the namespace too
            // (MM-BUG-KILN-00200). Each crate's `get()` rewrites its own alias names
            // to canonical files BEFORE looking anything up, so `embedded_wav`'s
            // first-match-wins chain resolves them exactly like physical names — but
            // this scan saw only what was on disk, leaving the alias names invisible.
            //
            // Both directions were unguarded: an earlier crate adding a physical WAV
            // that shadows a later crate's alias, and a later crate adding one that a
            // an earlier alias already claims. Either way a voice plays the wrong
            // recording with every suite green.
            if let Ok(aliases) = std::fs::read_to_string(dir.join("ALIASES")) {
                for line in aliases.lines() {
                    let line = line.trim();
                    if line.is_empty() || line.starts_with('#') {
                        continue;
                    }
                    let Some(alias) = line.split_whitespace().next() else {
                        continue;
                    };
                    scanned += 1;
                    if let Some(first) = owner.insert(alias.to_owned(), krate.clone()) {
                        clashes.push(format!(
                            "{alias} is an alias in {krate} and a name in {first}"
                        ));
                    }
                }
            }
        }

        assert!(
            crate_dirs.len() > 15 && scanned > 500,
            "basename scan collapsed to {} crates / {scanned} WAVs — it would pass \
             vacuously. Check that crates/ still holds the asset crates.",
            crate_dirs.len()
        );
        assert!(
            clashes.is_empty(),
            "{} duplicate WAV basename(s) across asset crates; `embedded_wav` resolves by \
             bare filename, first match wins, so the later crate's copy is unreachable and \
             a voice would silently play the wrong recording:\n  {}",
            clashes.len(),
            clashes.join("\n  ")
        );
    }
}
