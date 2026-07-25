//! Provenance-evidence oracles — every committed upstream source must be pinned by a hash
//! in a packaged document.
//!
//! ## A third question, distinct from `licensing.rs` and `inventory.rs`
//!
//! - `licensing.rs` asks *"is the attribution guide complete?"* — keyed off each bank's
//!   declared `license`, and deliberately blind to CC0.
//! - `inventory.rs` asks *"has a crate's PACKAGED sample set outgrown its documentation?"*
//!   — keyed off `crates/ferrosintesis-samples-*/samples/*.wav`.
//! - This module asks *"is every committed INPUT still the one we say it is?"* — keyed off
//!   `tools/ferrosintesis-samples/*-src/`.
//!
//! Nothing else covers that third set. The `*-src/` directories hold the material we cannot
//! re-fetch: Freesound gates its downloads behind a login, and the owner-recorded mandolin
//! cuts have no raw take committed at all. They are inputs, not packaged outputs, so
//! `inventory.rs` never looks at them — which is how 53 of 74 committed source files came to
//! sit with no recorded hash while every oracle stayed green (MM-REQ-KILN-00029).
//!
//! ## Why it is derived from the filesystem
//!
//! The requirement that raised this named one crate. The repo's standing lesson is that a
//! reported item is evidence a list is unmaintained, not a specification of the work — so the
//! predicate here is a glob, `tools/ferrosintesis-samples/*-src`, not a list of directory
//! names. A future `flute-src/` is covered on the day it is created, by nobody's decision.
//!
//! An earlier draft of this oracle *did* carry a hand-written list of the three directories
//! that exist today. That guard would have inherited the exact defect it exists to catch.
//!
//! ## What is deliberately NOT asserted here
//!
//! That the hash pins the *right* upstream sound, or that the licence named beside it is
//! correct. A hash proves only that the bytes have not changed since someone recorded them.
//! Whether those bytes came from Freesound 65754 under CC BY 4.0 is a provenance judgement,
//! answered by the retained `_readme_and_license_*.txt` manifests and the per-sound tables in
//! each `PROVENANCE.md` — not by anything a test can settle.
//!
//! What this DOES guarantee is that such a judgement, once made and recorded, cannot silently
//! stop applying to the file it was made about.

#[cfg(test)]
mod tests {
    use std::path::{Path, PathBuf};

    fn repo_root() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .and_then(Path::parent)
            .expect("crates/ferrosintesis is always two levels below the repo root")
            .to_path_buf()
    }

    // ---------------------------------------------------------------- SHA-256

    /// SHA-256 (FIPS 180-4). Hand-rolled because this crate takes no third-party
    /// dependencies, and a provenance oracle that cannot hash is no oracle at all.
    ///
    /// Correctness is pinned two ways: the NIST vectors in `sha256_matches_known_vectors`,
    /// and — the one that actually matters — the 77 committed source files whose recorded
    /// hashes were produced independently by Python's `hashlib`. If this implementation were
    /// subtly wrong, `every_committed_source_is_pinned_by_a_packaged_document` would fail on
    /// all 77 at once.
    fn sha256_hex(data: &[u8]) -> String {
        #[rustfmt::skip]
        const K: [u32; 64] = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
            0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
            0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
            0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
            0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
            0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
        ];

        let mut h: [u32; 8] = [
            0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
            0x5be0cd19,
        ];

        let mut msg = Vec::with_capacity(data.len() + 72);
        msg.extend_from_slice(data);
        msg.push(0x80);
        while msg.len() % 64 != 56 {
            msg.push(0);
        }
        msg.extend_from_slice(&((data.len() as u64) * 8).to_be_bytes());

        for chunk in msg.chunks_exact(64) {
            let mut w = [0u32; 64];
            for (i, word) in w.iter_mut().take(16).enumerate() {
                *word = u32::from_be_bytes([
                    chunk[4 * i],
                    chunk[4 * i + 1],
                    chunk[4 * i + 2],
                    chunk[4 * i + 3],
                ]);
            }
            for i in 16..64 {
                let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
                let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
                w[i] = w[i - 16]
                    .wrapping_add(s0)
                    .wrapping_add(w[i - 7])
                    .wrapping_add(s1);
            }

            let (mut a, mut b, mut c, mut d, mut e, mut f, mut g, mut hh) =
                (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7]);

            for i in 0..64 {
                let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
                let ch = (e & f) ^ ((!e) & g);
                let t1 = hh
                    .wrapping_add(s1)
                    .wrapping_add(ch)
                    .wrapping_add(K[i])
                    .wrapping_add(w[i]);
                let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
                let maj = (a & b) ^ (a & c) ^ (b & c);
                let t2 = s0.wrapping_add(maj);

                hh = g;
                g = f;
                f = e;
                e = d.wrapping_add(t1);
                d = c;
                c = b;
                b = a;
                a = t1.wrapping_add(t2);
            }

            for (slot, v) in h.iter_mut().zip([a, b, c, d, e, f, g, hh]) {
                *slot = slot.wrapping_add(v);
            }
        }

        h.iter().map(|w| format!("{w:08x}")).collect()
    }

    #[test]
    fn sha256_matches_known_vectors() {
        assert_eq!(
            sha256_hex(b""),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        // 448-bit message: exercises the pad-to-a-second-block path.
        assert_eq!(
            sha256_hex(b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"),
            "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
        );
        // 1 000 000 x 'a': exercises many-block accumulation.
        assert_eq!(
            sha256_hex(&vec![b'a'; 1_000_000]),
            "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"
        );
    }

    // ------------------------------------------------------- committed sources

    /// Every committed-source directory, read from the filesystem rather than a list.
    ///
    /// The predicate is `tools/ferrosintesis-samples/*-src`. A new one is covered the day it
    /// appears; nobody has to remember to add it here.
    fn source_dirs() -> Vec<PathBuf> {
        let tools = repo_root().join("tools").join("ferrosintesis-samples");
        let mut out: Vec<PathBuf> = std::fs::read_dir(&tools)
            .expect("tools/ferrosintesis-samples is readable")
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| p.is_dir())
            .filter(|p| {
                p.file_name()
                    .map(|n| n.to_string_lossy().ends_with("-src"))
                    .unwrap_or(false)
            })
            .collect();
        out.sort();
        assert!(
            out.len() >= 3,
            "found only {} committed-source directories under {} — the scan is not reading \
             what it thinks it is",
            out.len(),
            tools.display()
        );
        out
    }

    /// Every committed source file, as `(display path, sha-256)`.
    fn committed_sources() -> Vec<(String, String)> {
        let mut out = Vec::new();
        for dir in source_dirs() {
            let dir_name = dir.file_name().unwrap().to_string_lossy().to_string();
            let mut files: Vec<PathBuf> = std::fs::read_dir(&dir)
                .expect("a committed-source directory is readable")
                .filter_map(|e| e.ok())
                .map(|e| e.path())
                .filter(|p| p.is_file())
                .collect();
            files.sort();
            for f in files {
                let bytes = std::fs::read(&f).expect("a committed source file is readable");
                let name = f.file_name().unwrap().to_string_lossy().to_string();
                out.push((format!("{dir_name}/{name}"), sha256_hex(&bytes)));
            }
        }
        assert!(
            out.len() > 50,
            "found only {} committed source files — the scan is not reading what it thinks \
             it is",
            out.len()
        );
        out
    }

    /// Everything every sample crate's packaged `PROVENANCE.md` says, concatenated.
    ///
    /// Packaged on purpose: evidence that ships with the crate is evidence a downstream
    /// consumer can actually audit. A hash recorded only in a repo-root document would leave
    /// the published artifact unverifiable.
    fn packaged_provenance_text() -> String {
        let crates = repo_root().join("crates");
        let mut all = String::new();
        let mut dirs: Vec<PathBuf> = std::fs::read_dir(&crates)
            .expect("crates/ is readable")
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| {
                p.file_name()
                    .map(|n| n.to_string_lossy().starts_with("ferrosintesis-samples-"))
                    .unwrap_or(false)
            })
            .collect();
        dirs.sort();
        for d in dirs {
            if let Ok(text) = std::fs::read_to_string(d.join("PROVENANCE.md")) {
                all.push_str(&text);
                all.push('\n');
            }
        }
        assert!(
            all.len() > 5_000,
            "collected only {} bytes of packaged provenance — the scan is not reading what \
             it thinks it is",
            all.len()
        );
        all
    }

    /// The coverage predicate, factored out so it can be refuted directly (see
    /// `the_coverage_check_rejects_an_unpinned_source`).
    fn unpinned<'a>(sources: &'a [(String, String)], docs: &str) -> Vec<&'a str> {
        sources
            .iter()
            .filter(|(_, hash)| !docs.contains(hash.as_str()))
            .map(|(name, _)| name.as_str())
            .collect()
    }

    #[test]
    fn every_committed_source_is_pinned_by_a_packaged_document() {
        let sources = committed_sources();
        let docs = packaged_provenance_text();
        let missing = unpinned(&sources, &docs);
        assert!(
            missing.is_empty(),
            "{} of {} committed source files have no SHA-256 in any packaged PROVENANCE.md.\n\
             These are inputs we cannot re-fetch — Freesound gates downloads behind a login, \
             and the mandolin raw take is not committed — so an unpinned one is a file nobody \
             can prove is still the one the licence record describes.\n\
             Add its hash to the owning crate's PROVENANCE.md:\n  {}",
            missing.len(),
            sources.len(),
            missing.join("\n  ")
        );
    }

    /// The adversarial half: prove the check can actually FAIL.
    ///
    /// The repo's standing lesson is that a derived oracle is only as good as its predicate,
    /// and that the way to find out is to write the document that *should* fail it. A
    /// `contains`-based check is exactly the shape that has passed on gutted documents here
    /// before (MM-BUG-KILN-00071), so it does not get to go untested.
    #[test]
    fn the_coverage_check_rejects_an_unpinned_source() {
        let sources = vec![
            ("freesound-src/a.wav".to_string(), "aaaa1111".to_string()),
            ("gong-src/b.wav".to_string(), "bbbb2222".to_string()),
        ];

        // A document pinning both: covered.
        assert!(unpinned(
            &sources,
            "| `a.wav` | `aaaa1111` |\n| `b.wav` | `bbbb2222` |"
        )
        .is_empty());

        // Drop one hash: that file, and only that file, is reported.
        assert_eq!(
            unpinned(&sources, "| `a.wav` | `aaaa1111` |"),
            vec!["gong-src/b.wav"]
        );

        // A document that names the files but pins nothing — the gutted-document case — must
        // NOT satisfy the check. Mentioning a file is not evidence about its bytes.
        assert_eq!(
            unpinned(
                &sources,
                "We ship a.wav and b.wav, both properly licensed. Trust us."
            ),
            vec!["freesound-src/a.wav", "gong-src/b.wav"]
        );
    }

    /// The retained upstream licence manifests are themselves committed sources, so the
    /// coverage oracle above already pins their bytes. This names them, so that deleting one
    /// fails with a sentence about licence evidence rather than a bare missing-hash list.
    #[test]
    fn the_retained_freesound_licence_manifests_are_present() {
        let dir = repo_root()
            .join("tools")
            .join("ferrosintesis-samples")
            .join("freesound-src");
        for pack in ["3957", "19445", "44539"] {
            let p = dir.join(format!("_readme_and_license_{pack}.txt"));
            let text = std::fs::read_to_string(&p).unwrap_or_else(|e| {
                panic!(
                    "{} is missing ({e}). This is the bundled Freesound manifest for pack \
                     {pack} — the only offline evidence of the per-sound licence, and \
                     un-refetchable without a login. It is not a regenerable artifact.",
                    p.display()
                )
            });
            assert!(
                text.contains(&format!("packs/{pack}/")),
                "{} does not name pack {pack} — it is not the manifest it claims to be",
                p.display()
            );
            assert!(
                text.contains("license:"),
                "{} carries no per-sound licence lines",
                p.display()
            );
        }
    }
}
