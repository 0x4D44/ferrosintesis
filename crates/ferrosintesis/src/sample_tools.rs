#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;
    use std::path::{Path, PathBuf};

    fn repo_root() -> PathBuf {
        // CARGO_MANIFEST_DIR = <root>/crates/ferrosintesis
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(2)
            .expect("crates/ferrosintesis sits two levels below the repo root")
            .to_path_buf()
    }

    fn read_repo(relative: &str) -> String {
        let path = repo_root().join(relative);
        std::fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", path.display()))
    }

    fn quoted_segments(line: &str) -> impl Iterator<Item = &str> {
        line.split('"').skip(1).step_by(2)
    }

    fn embedded_banjo_files() -> BTreeSet<String> {
        read_repo("crates/ferrosintesis-samples-orchestral2/src/lib.rs")
            .lines()
            .filter(|line| line.contains("include_bytes!"))
            .flat_map(quoted_segments)
            .filter(|name| name.starts_with("banjo_") && name.ends_with(".wav"))
            .map(str::to_owned)
            .collect()
    }

    fn sampler_banjo_files() -> BTreeSet<String> {
        read_repo("crates/ferrosintesis/src/sampler.rs")
            .lines()
            .map(str::trim)
            .filter(|line| line.starts_with("\"banjo_") && line.contains("\" =>"))
            .flat_map(quoted_segments)
            .map(str::to_owned)
            .collect()
    }

    fn first_line_containing(text: &str, needle: &str) -> Option<usize> {
        text.lines()
            .enumerate()
            .find(|(_, line)| line.contains(needle))
            .map(|(idx, _)| idx + 1)
    }

    fn last_line_containing(text: &str, needle: &str) -> Option<usize> {
        let mut last = None;
        for (idx, line) in text.lines().enumerate() {
            if line.contains(needle) {
                last = Some(idx + 1);
            }
        }
        last
    }

    fn deletes_current_bank_before_direct_final_write(source: &str) -> bool {
        let Some(unlink) = first_line_containing(source, "f.unlink()") else {
            return false;
        };
        let Some(write) = first_line_containing(source, "write_wav16(OUT /") else {
            return false;
        };
        unlink < write
    }

    #[test]
    fn banjo_extract_uses_derived_exact_bank_inventory() {
        let embedded = embedded_banjo_files();
        let sampler = sampler_banjo_files();
        assert_eq!(
            embedded.len(),
            24,
            "ferrosintesis-samples-orchestral2 must expose the documented 24 banjo WAVs"
        );
        assert_eq!(
            sampler, embedded,
            "the synth's banjo root table and embedded sample crate must name the same files"
        );

        let script = read_repo("tools/ferrosintesis-samples/banjo_extract.py");
        assert!(
            script.contains("EXPECTED_BANJO_FILE_COUNT = 24"),
            "banjo_extract.py must reject a regeneration that does not stage exactly 24 files"
        );
        assert!(
            script.contains("ferrosintesis-samples-orchestral2")
                && script.contains("sampler.rs")
                && script.contains("include_bytes!"),
            "banjo_extract.py must derive its exact expected bank from the checked-in bank sources"
        );
        assert!(
            script.contains("def validate_banjo_output_plan("),
            "banjo_extract.py must validate the staged filename set and WAV contracts before publish"
        );
        assert!(
            script.contains("validate_wav16_contract(staging / name)")
                && script.contains("data[:4] != b\"RIFF\"")
                && script.contains("SR * 2")
                && script.contains("data_size == 0"),
            "banjo_extract.py must validate the staged files as non-empty mono 16-bit 44.1 kHz WAVs"
        );
    }

    #[test]
    fn banjo_extract_validates_staged_bank_before_publishing() {
        let script = read_repo("tools/ferrosintesis-samples/banjo_extract.py");
        assert!(
            !deletes_current_bank_before_direct_final_write(&script),
            "banjo_extract.py must not delete the old banjo bank before replacement files exist"
        );
        assert!(
            script.contains("tempfile.TemporaryDirectory("),
            "banjo_extract.py must generate into a sibling staging directory"
        );
        assert!(
            script.contains("write_wav16(staging /"),
            "banjo_extract.py must write generated WAVs into staging, not final paths"
        );
        assert!(
            !script.contains("write_wav16(OUT /"),
            "banjo_extract.py must not write directly to final tracked WAV paths"
        );

        let write = first_line_containing(&script, "write_wav16(staging /")
            .expect("banjo_extract.py should write generated WAVs to staging");
        let validate = last_line_containing(&script, "validate_banjo_output_plan(staging")
            .expect("banjo_extract.py should validate the staged bank from main");
        let publish = last_line_containing(&script, "publish_banjo_bank(staging")
            .expect("banjo_extract.py should publish the staged bank from main");
        assert!(
            write < validate,
            "banjo_extract.py must finish staged writes before validating the output plan"
        );
        assert!(
            validate < publish,
            "banjo_extract.py must validate the complete staging plan before publishing"
        );
        assert!(
            script.contains(".replace(out / name)"),
            "banjo_extract.py should publish with atomic per-file replacement"
        );
    }

    #[test]
    fn banjo_extract_bad_publish_shape_detector_matches_this_bug() {
        let bad = r#"
OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob("banjo_*.wav"):
    f.unlink()
for m in zones:
    write_wav16(OUT / f"banjo_{note_name(m)}.wav", clip)
"#;
        assert!(deletes_current_bank_before_direct_final_write(bad));

        let good = r#"
with tempfile.TemporaryDirectory(prefix=".banjo-staging-", dir=OUT.parent) as stage_dir:
    staging = Path(stage_dir)
    write_wav16(staging / name, clip)
    validate_banjo_output_plan(staging)
    publish_banjo_bank(staging)
"#;
        assert!(!deletes_current_bank_before_direct_final_write(good));
    }
}
