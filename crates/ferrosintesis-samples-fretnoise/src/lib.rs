//! Embedded CC0 owner-recorded fret-noise one-shots for GM 120 (Guitar Fret Noise).
//!
//! Finger-slide takes on Arthur's Eastman E1D (all strings damped at the nut), played
//! as a round-robin one-shot bank by `ferrosintesis` — [`ROUND_ROBINS`] is the bank
//! size, derived from the table below. Consumers normally access this crate through
//! `ferrosintesis`. CC0-1.0 (public-domain dedication) — no attribution obligation;
//! see `PROVENANCE.md` for the recording provenance.
//! Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs, in the bank's canonical round-robin order —
/// the ascending `fretnoise_rrNN` ordinal order `fretnoise_bake.py` writes them in.
/// [`take_name`] indexes this table POSITIONALLY, so the row order is part of the
/// contract, not an implementation detail; `samples_are_in_canonical_round_robin_order`
/// pins it. Kept as a slice (not a fixed-size array) so the count need not be
/// threaded through the declaration — see [`FILE_COUNT`].
static SAMPLES: &[(&str, &[u8])] = &[
    (
        "fretnoise_rr01.flac",
        include_bytes!("../samples/fretnoise_rr01.flac"),
    ),
    (
        "fretnoise_rr02.flac",
        include_bytes!("../samples/fretnoise_rr02.flac"),
    ),
    (
        "fretnoise_rr03.flac",
        include_bytes!("../samples/fretnoise_rr03.flac"),
    ),
    (
        "fretnoise_rr04.flac",
        include_bytes!("../samples/fretnoise_rr04.flac"),
    ),
    (
        "fretnoise_rr05.flac",
        include_bytes!("../samples/fretnoise_rr05.flac"),
    ),
    (
        "fretnoise_rr06.flac",
        include_bytes!("../samples/fretnoise_rr06.flac"),
    ),
    (
        "fretnoise_rr07.flac",
        include_bytes!("../samples/fretnoise_rr07.flac"),
    ),
    (
        "fretnoise_rr08.flac",
        include_bytes!("../samples/fretnoise_rr08.flac"),
    ),
    (
        "fretnoise_rr09.flac",
        include_bytes!("../samples/fretnoise_rr09.flac"),
    ),
    (
        "fretnoise_rr10.flac",
        include_bytes!("../samples/fretnoise_rr10.flac"),
    ),
    (
        "fretnoise_rr11.flac",
        include_bytes!("../samples/fretnoise_rr11.flac"),
    ),
    (
        "fretnoise_rr12.flac",
        include_bytes!("../samples/fretnoise_rr12.flac"),
    ),
];

/// Number of sample files embedded in this package. Derived from [`SAMPLES`] so the
/// whole chain (count → round-robin size → the synth's take cache) bottoms out on
/// the table of `include_bytes!` rows, never on a hand-written number.
pub const FILE_COUNT: usize = SAMPLES.len();

/// The number of round-robin takes in the bank. The synth cycles these so
/// consecutive fret-noise events do not repeat the same sample.
pub const ROUND_ROBINS: usize = FILE_COUNT;

/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
pub fn get(name: &str) -> Option<&'static [u8]> {
    SAMPLES
        .iter()
        .find(|(candidate, _)| *candidate == name)
        .map(|(_, bytes)| *bytes)
}

/// The file name of round-robin take `rr` (0-based, wraps at [`ROUND_ROBINS`]).
pub fn take_name(rr: usize) -> &'static str {
    SAMPLES[rr % ROUND_ROBINS].0
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::OsStr;
    use std::fs;
    use std::path::Path;

    /// Aggregate byte size of the embedded WAVs. DELIBERATELY a pinned literal, not
    /// a sum derived from `SAMPLES` (that would assert `sum == sum` — vacuous) nor
    /// from the files on disk (that would only mirror whatever was last baked). Its
    /// value here is as a CANARY on the committed bank's identity: a re-bake that
    /// changes any take's length turns this red and forces a human to look, which is
    /// exactly the event this repo wants flagged. The *derived* half of the same
    /// property — that the embedded bytes are the committed files, byte-length for
    /// byte-length — is `embedded_bytes_match_the_committed_files`, which needs no
    /// re-pinning.
    const EXPECTED_BYTES: usize = 739062;

    fn samples_dir() -> std::path::PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("samples")
    }

    /// The `.wav` files actually committed under `samples/`, sorted ascending. The
    /// bake writes `fretnoise_rrNN.wav` with a zero-padded two-digit ordinal, so
    /// lexicographic order here IS the bake's emission order.
    fn packaged_names() -> Vec<String> {
        let mut names: Vec<String> = fs::read_dir(samples_dir())
            .expect("sample directory must exist")
            .map(|entry| entry.expect("sample dir entry must be readable").path())
            .filter(|path| {
                matches!(
                    path.extension().and_then(OsStr::to_str),
                    Some("wav" | "flac")
                )
            })
            .map(|path| {
                path.file_name()
                    .expect("sample must have a file name")
                    .to_string_lossy()
                    .into_owned()
            })
            .collect();
        names.sort();
        names
    }

    /// Every packaged WAV is embedded and vice versa.
    ///
    /// This is the generated-crate shape emitted by `gen_crate_lib.py:79-86`, where
    /// `get(name)` is the only accessor and row order genuinely does not matter — so
    /// it SORTS both sides. fretnoise is the one crate with a positional accessor
    /// (`take_name`), for which a sorted comparison is strictly too weak: it waves
    /// through any permutation of the rows. `samples_are_in_canonical_round_robin_order`
    /// is the oracle that covers that gap; keep both.
    #[test]
    fn inventory_matches_packaged_samples() {
        let packaged = packaged_names();

        let mut embedded: Vec<String> =
            SAMPLES.iter().map(|(name, _)| (*name).to_owned()).collect();
        embedded.sort();

        assert_eq!(packaged.len(), FILE_COUNT);
        assert_eq!(embedded, packaged);
    }

    /// The ROW ORDER of `SAMPLES` is a contract, not an implementation detail:
    /// `take_name` indexes the table positionally and `sampler.rs:fret_noise_takes`
    /// caches the decoded takes "in the crate's canonical round-robin order". A
    /// permutation of rows 2..N silently reorders the bank, and every other test in
    /// this file stays green through it.
    ///
    /// Pinned two ways, neither of them a second hand-written list: against the
    /// packaged files in ascending order (what `fretnoise_bake.py` wrote), and
    /// against the `fretnoise_rrNN` naming contract, which also proves the ordinals
    /// run contiguously from 01 with no holes.
    #[test]
    fn samples_are_in_canonical_round_robin_order() {
        let packaged = packaged_names();
        let embedded: Vec<String> = SAMPLES.iter().map(|(name, _)| (*name).to_owned()).collect();

        assert_eq!(
            embedded, packaged,
            "SAMPLES rows must be in ascending packaged-file order — take_name() \
             indexes them positionally, so a permutation reorders the bank"
        );

        for (rr, name) in embedded.iter().enumerate() {
            assert_eq!(
                name.as_str(),
                format!("fretnoise_rr{:02}.flac", rr + 1),
                "round-robin slot {rr} must hold ordinal {} — the ordinals must run \
                 contiguously from 01",
                rr + 1
            );
            assert_eq!(take_name(rr), name.as_str(), "take_name({rr}) must agree");
        }
    }

    /// The embedded bytes ARE the committed files. Derived from the directory, so
    /// unlike `EXPECTED_BYTES` it never needs a human to re-pin it; it catches an
    /// `include_bytes!` path that resolves elsewhere and a stale build whose
    /// compiled-in copy has drifted from what is on disk.
    #[test]
    fn embedded_bytes_match_the_committed_files() {
        let dir = samples_dir();
        for (name, bytes) in SAMPLES {
            let on_disk = fs::metadata(dir.join(name))
                .unwrap_or_else(|e| panic!("{name} must exist under samples/: {e}"))
                .len();
            assert_eq!(
                bytes.len() as u64,
                on_disk,
                "{name}: embedded {} bytes but the committed file is {on_disk}",
                bytes.len()
            );
        }
    }

    #[test]
    fn every_sample_is_a_nonempty_bank_file_with_the_expected_size() {
        assert_eq!(
            SAMPLES.iter().map(|(_, bytes)| bytes.len()).sum::<usize>(),
            EXPECTED_BYTES
        );
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a sample");
            let riff = &bytes[..4] == b"RIFF" && &bytes[8..12] == b"WAVE";
            let flac = &bytes[..4] == b"fLaC";
            assert!(riff || flac, "{name} is neither RIFF/WAVE nor FLAC");
            assert_eq!(get(name), Some(*bytes));
        }
        assert_eq!(get("missing.wav"), None);
    }

    #[test]
    fn take_name_wraps_round_robin() {
        assert_eq!(take_name(0), "fretnoise_rr01.flac");
        assert_eq!(take_name(ROUND_ROBINS), take_name(0));
        assert_eq!(take_name(ROUND_ROBINS + 3), take_name(3));
    }
}
