//! Licensing-coverage oracles — the shipped attribution guide must name every
//! sample bank that legally requires attribution.
//!
//! ## Why this exists
//!
//! `ferrosintesis` embeds its PCM in first-party asset crates, and the default
//! `embedded-samples` feature pulls in twenty-one of them. Most are **CC0-1.0** and need
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

#[cfg(test)]
mod tests {
    use std::path::{Path, PathBuf};

    /// `crates/`, the directory holding this crate and every sample-asset crate.
    fn crates_dir() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("crates/ferrosintesis always has a parent")
            .to_path_buf()
    }

    fn read(path: &Path) -> String {
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
    fn default_sample_crates() -> Vec<String> {
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
    fn quoted(line: &str) -> Option<&str> {
        let rest = line.split_once('"')?.1;
        rest.split_once('"').map(|(inner, _)| inner)
    }

    /// The `license` field a sample crate declares in its `[package]` table.
    fn declared_license(krate: &str) -> String {
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

    /// CC0 waives attribution. Everything else here (MIT, CC-BY-3.0, CC-BY-4.0) requires
    /// the credit to travel with a binary distribution.
    fn requires_attribution(license: &str) -> bool {
        license != "CC0-1.0"
    }

    /// Every attribution-bearing bank in the default build is named in the licensing
    /// guide a distributor reads.
    #[test]
    fn readme_names_every_attribution_bearing_sample_bank() {
        let readme = read(&crates_dir().join("ferrosintesis").join("README.md"));

        let mut missing = Vec::new();
        let mut covered = 0usize;
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if !requires_attribution(&license) {
                continue;
            }
            if readme.contains(&krate) {
                covered += 1;
            } else {
                missing.push(format!("{krate} ({license})"));
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
        for krate in default_sample_crates() {
            let license = declared_license(&krate);
            if requires_attribution(&license) && !notice.contains(&krate) {
                missing.push(format!("{krate} ({license})"));
            }
        }
        assert!(
            missing.is_empty(),
            "crates/ferrosintesis/NOTICE omits {} attribution-bearing bank(s):\n  {}",
            missing.len(),
            missing.join("\n  ")
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
