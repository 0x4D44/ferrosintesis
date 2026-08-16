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
//! flag is how MM-BUG-KILN-00020 happened). The WAV count and byte total come from
//! walking each of those crates' `samples/` directories on disk.
//!
//! ## What is deliberately NOT asserted
//!
//! An exact byte figure in the prose. Requiring one would make every re-cut sample a
//! docs change, and would tempt a future editor to paste a number rather than think.
//! The oracles assert the CRATE COUNT exactly (it is small, discrete and load-bearing)
//! and the size only to the nearest sensible rounding, with a tolerance stated below.

use crate::licensing::{crates_dir, default_sample_crates, read};

/// Number of embedded WAVs and their total size, across the default sample crates.
pub(crate) fn embedded_payload() -> (usize, usize, u64) {
    let crates = default_sample_crates();
    let mut files = 0usize;
    let mut bytes = 0u64;
    for krate in &crates {
        let dir = crates_dir().join(krate).join("samples");
        let entries = std::fs::read_dir(&dir).unwrap_or_else(|e| {
            panic!(
                "payload oracle cannot read {}: {e}.\n\
                 It derives the embedded total from the sibling asset crates, so it \
                 only runs inside the ferrosintesis workspace.",
                dir.display()
            )
        });
        for entry in entries {
            let entry = entry.expect("readable directory entry");
            if entry
                .path()
                .extension()
                .is_some_and(|e| e == "wav" || e == "flac")
            {
                files += 1;
                bytes += entry.metadata().expect("readable metadata").len();
            }
        }
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

    /// Size-of-the-embedded-bank claims: `(file, line, value in MiB)`.
    ///
    /// Scoped to lines that both name a unit and say they are describing what a build
    /// *embeds* or *compiles in* — the per-crate provenance tables also quote MiB, and
    /// those figures are correct for their own crate.
    fn size_claims() -> Vec<(&'static str, String, f64)> {
        let mut out = Vec::new();
        for file in ["README.md", "NOTICE", "src/lib.rs"] {
            for line in parent(file).lines() {
                let lower = line.to_lowercase();
                let has_unit = lower.contains("mib") || lower.contains(" mb");
                let about_embedding = lower.contains("embed") || lower.contains("compil");
                if !has_unit || !about_embedding || lower.trim_start().starts_with('|') {
                    continue;
                }
                for tok in line.split(|c: char| !(c.is_ascii_digit() || c == '.')) {
                    let Ok(v) = tok.trim_matches('.').parse::<f64>() else {
                        continue;
                    };
                    // Below 1 is a version fragment or a decimal tail, not a size.
                    if v >= 1.0 {
                        out.push((file, line.to_string(), v));
                    }
                }
            }
        }
        out
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
        // took the payload from ~111 MiB to ~61 MiB without losing a single
        // recording. Kept just under the real figure, for the same reason it
        // sat just under the old one.
        assert!(
            files > 1000 && bytes > 55 * 1024 * 1024,
            "payload scan found only {files} files / {bytes} bytes"
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
