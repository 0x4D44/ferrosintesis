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
}
