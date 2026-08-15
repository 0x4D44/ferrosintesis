//! Embedded first-party Yamaha B1 upright piano samples (GM 0 Acoustic Grand default, CC0=0).
//!
//! The generated sample inventory is refreshed from the committed `samples/*.wav`
//! by `tools/ferrosintesis-samples/regen_samples_table.py`; the B1-specific tail
//! validator below remains handwritten. Consumers normally reach this crate through
//! `ferrosintesis`. Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

// BEGIN GENERATED SAMPLE INVENTORY
/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 52;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "b1_hard_A0.wav",
        include_bytes!("../samples/b1_hard_A0.wav"),
    ),
    (
        "b1_hard_A2.wav",
        include_bytes!("../samples/b1_hard_A2.wav"),
    ),
    (
        "b1_hard_A4.wav",
        include_bytes!("../samples/b1_hard_A4.wav"),
    ),
    (
        "b1_hard_A6.wav",
        include_bytes!("../samples/b1_hard_A6.wav"),
    ),
    (
        "b1_hard_B1.wav",
        include_bytes!("../samples/b1_hard_B1.wav"),
    ),
    (
        "b1_hard_B3.wav",
        include_bytes!("../samples/b1_hard_B3.wav"),
    ),
    (
        "b1_hard_B5.wav",
        include_bytes!("../samples/b1_hard_B5.wav"),
    ),
    (
        "b1_hard_B7.wav",
        include_bytes!("../samples/b1_hard_B7.wav"),
    ),
    (
        "b1_hard_C1.wav",
        include_bytes!("../samples/b1_hard_C1.wav"),
    ),
    (
        "b1_hard_C3.wav",
        include_bytes!("../samples/b1_hard_C3.wav"),
    ),
    (
        "b1_hard_C5.wav",
        include_bytes!("../samples/b1_hard_C5.wav"),
    ),
    (
        "b1_hard_C7.wav",
        include_bytes!("../samples/b1_hard_C7.wav"),
    ),
    (
        "b1_hard_C8.wav",
        include_bytes!("../samples/b1_hard_C8.wav"),
    ),
    (
        "b1_hard_D2.wav",
        include_bytes!("../samples/b1_hard_D2.wav"),
    ),
    (
        "b1_hard_D4.wav",
        include_bytes!("../samples/b1_hard_D4.wav"),
    ),
    (
        "b1_hard_D6.wav",
        include_bytes!("../samples/b1_hard_D6.wav"),
    ),
    (
        "b1_hard_E1.wav",
        include_bytes!("../samples/b1_hard_E1.wav"),
    ),
    (
        "b1_hard_E3.wav",
        include_bytes!("../samples/b1_hard_E3.wav"),
    ),
    (
        "b1_hard_E5.wav",
        include_bytes!("../samples/b1_hard_E5.wav"),
    ),
    (
        "b1_hard_E7.wav",
        include_bytes!("../samples/b1_hard_E7.wav"),
    ),
    (
        "b1_hard_F2.wav",
        include_bytes!("../samples/b1_hard_F2.wav"),
    ),
    (
        "b1_hard_F4.wav",
        include_bytes!("../samples/b1_hard_F4.wav"),
    ),
    (
        "b1_hard_F6.wav",
        include_bytes!("../samples/b1_hard_F6.wav"),
    ),
    (
        "b1_hard_G1.wav",
        include_bytes!("../samples/b1_hard_G1.wav"),
    ),
    (
        "b1_hard_G3.wav",
        include_bytes!("../samples/b1_hard_G3.wav"),
    ),
    (
        "b1_hard_G5.wav",
        include_bytes!("../samples/b1_hard_G5.wav"),
    ),
    (
        "b1_hard_G7.wav",
        include_bytes!("../samples/b1_hard_G7.wav"),
    ),
    (
        "b1_normal_A2.wav",
        include_bytes!("../samples/b1_normal_A2.wav"),
    ),
    (
        "b1_normal_A4.wav",
        include_bytes!("../samples/b1_normal_A4.wav"),
    ),
    (
        "b1_normal_A6.wav",
        include_bytes!("../samples/b1_normal_A6.wav"),
    ),
    (
        "b1_normal_B1.wav",
        include_bytes!("../samples/b1_normal_B1.wav"),
    ),
    (
        "b1_normal_B3.wav",
        include_bytes!("../samples/b1_normal_B3.wav"),
    ),
    (
        "b1_normal_B5.wav",
        include_bytes!("../samples/b1_normal_B5.wav"),
    ),
    (
        "b1_normal_B7.wav",
        include_bytes!("../samples/b1_normal_B7.wav"),
    ),
    (
        "b1_normal_C1.wav",
        include_bytes!("../samples/b1_normal_C1.wav"),
    ),
    (
        "b1_normal_C3.wav",
        include_bytes!("../samples/b1_normal_C3.wav"),
    ),
    (
        "b1_normal_C5.wav",
        include_bytes!("../samples/b1_normal_C5.wav"),
    ),
    (
        "b1_normal_C7.wav",
        include_bytes!("../samples/b1_normal_C7.wav"),
    ),
    (
        "b1_normal_D2.wav",
        include_bytes!("../samples/b1_normal_D2.wav"),
    ),
    (
        "b1_normal_D4.wav",
        include_bytes!("../samples/b1_normal_D4.wav"),
    ),
    (
        "b1_normal_D6.wav",
        include_bytes!("../samples/b1_normal_D6.wav"),
    ),
    (
        "b1_normal_E1.wav",
        include_bytes!("../samples/b1_normal_E1.wav"),
    ),
    (
        "b1_normal_E3.wav",
        include_bytes!("../samples/b1_normal_E3.wav"),
    ),
    (
        "b1_normal_E5.wav",
        include_bytes!("../samples/b1_normal_E5.wav"),
    ),
    (
        "b1_normal_E7.wav",
        include_bytes!("../samples/b1_normal_E7.wav"),
    ),
    (
        "b1_normal_F2.wav",
        include_bytes!("../samples/b1_normal_F2.wav"),
    ),
    (
        "b1_normal_F4.wav",
        include_bytes!("../samples/b1_normal_F4.wav"),
    ),
    (
        "b1_normal_F6.wav",
        include_bytes!("../samples/b1_normal_F6.wav"),
    ),
    (
        "b1_normal_G1.wav",
        include_bytes!("../samples/b1_normal_G1.wav"),
    ),
    (
        "b1_normal_G3.wav",
        include_bytes!("../samples/b1_normal_G3.wav"),
    ),
    (
        "b1_normal_G5.wav",
        include_bytes!("../samples/b1_normal_G5.wav"),
    ),
    (
        "b1_normal_G7.wav",
        include_bytes!("../samples/b1_normal_G7.wav"),
    ),
];
// END GENERATED SAMPLE INVENTORY

/// Returns the embedded WAV bytes for an exact (case-sensitive) file name.
pub fn get(name: &str) -> Option<&'static [u8]> {
    SAMPLES
        .iter()
        .find(|(candidate, _)| *candidate == name)
        .map(|(_, bytes)| *bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::OsStr;
    use std::fs;
    use std::path::Path;

    // Aggregate byte sizes of the extended WAVs and their compact natural tails;
    // re-pin both only after a deterministic full-bank bake.
    const EXPECTED_BYTES: usize = 10271480;
    const EXPECTED_TAIL_BYTES: usize = 3351922;

    /// The strict publish-time predicate for one extended B1 asset — a
    /// deliberate mirror of the runtime's `parse_b1_tail` in
    /// `ferrosintesis::sampler`, which every consumer runs at bank build and
    /// whose rejection is a *panic* reached on the first samples-on prewarm.
    ///
    /// MM-BUG-KILN-00195: this used to validate the `b1t ` chunk and nothing
    /// else. An asset whose `fmt ` said stereo or 8-bit, whose `data` chunk was
    /// missing, duplicated, empty or half a frame, that carried a nonzero pad
    /// byte, or whose tail entry sat past the end of its own PCM body, passed
    /// `cargo test -p ferrosintesis-samples-b1-upright` and published green —
    /// then panicked in every consumer. This crate cannot depend on
    /// `ferrosintesis` (that is the dependency edge, and inverting it would
    /// invert the publish order), so the mirror is hand-written; what keeps it
    /// honest is `strict_validator_rejects_each_defeat`, which mutates a real
    /// packaged asset once per check and requires each mutation to be rejected.
    ///
    /// Returns the tail payload, or the first rejection reason.
    fn parse_b1_strict(bytes: &[u8]) -> Result<&[u8], String> {
        if bytes.len() < 12 || &bytes[..4] != b"RIFF" || &bytes[8..12] != b"WAVE" {
            return Err("B1 asset is not RIFF/WAVE".into());
        }
        let declared_end = 8usize
            .checked_add(u32::from_le_bytes(bytes[4..8].try_into().unwrap()) as usize)
            .ok_or("B1 RIFF size overflow")?;
        if declared_end != bytes.len() {
            return Err(format!(
                "B1 RIFF declares {declared_end} bytes, asset has {}",
                bytes.len()
            ));
        }

        let mut pos = 12usize;
        let mut fmt_count = 0usize;
        let mut data_frames: Option<usize> = None;
        let mut tail: Option<&[u8]> = None;
        while pos < declared_end {
            let header_end = pos.checked_add(8).ok_or("B1 chunk header overflow")?;
            if header_end > declared_end {
                return Err("B1 RIFF has a truncated chunk header".into());
            }
            let len = u32::from_le_bytes(bytes[pos + 4..header_end].try_into().unwrap()) as usize;
            let body_start = header_end;
            let body_end = body_start
                .checked_add(len)
                .ok_or("B1 chunk body overflow")?;
            let padded_end = body_end
                .checked_add(len & 1)
                .ok_or("B1 chunk padding overflow")?;
            if padded_end > declared_end {
                return Err("B1 RIFF has a truncated or oversized chunk".into());
            }
            if len & 1 != 0 && bytes[body_end] != 0 {
                return Err("B1 RIFF has a nonzero pad byte".into());
            }

            match &bytes[pos..pos + 4] {
                b"fmt " => {
                    fmt_count += 1;
                    let body = &bytes[body_start..body_end];
                    if body.len() < 16
                        || u16::from_le_bytes(body[0..2].try_into().unwrap()) != 1
                        || u16::from_le_bytes(body[2..4].try_into().unwrap()) != 1
                        || u32::from_le_bytes(body[4..8].try_into().unwrap()) != 44_100
                        || u16::from_le_bytes(body[12..14].try_into().unwrap()) != 2
                        || u16::from_le_bytes(body[14..16].try_into().unwrap()) != 16
                    {
                        return Err("B1 body is not PCM16 mono 44.1 kHz".into());
                    }
                }
                b"data" => {
                    if len == 0 || len & 1 != 0 {
                        return Err("B1 PCM body is empty or has a partial frame".into());
                    }
                    if data_frames.replace(len / 2).is_some() {
                        return Err("B1 RIFF has duplicate PCM data chunks".into());
                    }
                }
                b"b1t " => {
                    if tail.is_some() {
                        return Err("B1 RIFF has duplicate natural tails".into());
                    }
                    if padded_end != declared_end {
                        return Err("B1 natural tail is not terminal".into());
                    }
                    let body = &bytes[body_start..body_end];
                    if body.len() < 13 {
                        return Err("B1 natural tail is truncated or empty".into());
                    }
                    if body[0] != 1 {
                        return Err("unsupported B1 natural-tail version".into());
                    }
                    if body[1] != 4 {
                        return Err("unsupported B1 natural-tail rate divisor".into());
                    }
                    if u16::from_le_bytes(body[2..4].try_into().unwrap()) != 0 {
                        return Err("nonzero B1 natural-tail reserved field".into());
                    }
                    let entry_frame = u32::from_le_bytes(body[4..8].try_into().unwrap()) as usize;
                    if entry_frame != 59_535 {
                        return Err(format!("unexpected B1 tail entry {entry_frame}"));
                    }
                    let source_frames =
                        u32::from_le_bytes(body[8..12].try_into().unwrap()) as usize;
                    if body.len() - 12 != source_frames.div_ceil(4) {
                        return Err("B1 natural-tail payload length mismatch".into());
                    }
                    tail = Some(&body[12..]);
                }
                _ => {}
            }
            pos = padded_end;
        }

        if fmt_count != 1 {
            return Err(format!(
                "B1 RIFF requires exactly one fmt chunk, found {fmt_count}"
            ));
        }
        let Some(frames) = data_frames else {
            return Err("B1 RIFF is missing its PCM data chunk".into());
        };
        // The runtime relates the tail entry to an INDEPENDENTLY decoded body;
        // crate-side the `data` chunk is that body, so this is the same check.
        if 59_535 >= frames {
            return Err(format!(
                "B1 natural-tail entry 59535 is outside a {frames}-frame PCM body"
            ));
        }
        tail.ok_or_else(|| "B1 RIFF is missing its natural tail".to_string())
    }

    fn b1_tail(bytes: &[u8]) -> &[u8] {
        match parse_b1_strict(bytes) {
            Ok(payload) => payload,
            Err(reason) => panic!("{reason}"),
        }
    }

    /// Split a packaged asset into `(fourcc, body)` pairs so a test can rebuild
    /// a deliberately-defeated variant of it.
    fn split_chunks(bytes: &[u8]) -> Vec<([u8; 4], Vec<u8>)> {
        let declared_end = 8 + u32::from_le_bytes(bytes[4..8].try_into().unwrap()) as usize;
        let mut out = Vec::new();
        let mut pos = 12usize;
        while pos < declared_end {
            let len = u32::from_le_bytes(bytes[pos + 4..pos + 8].try_into().unwrap()) as usize;
            let mut name = [0u8; 4];
            name.copy_from_slice(&bytes[pos..pos + 4]);
            out.push((name, bytes[pos + 8..pos + 8 + len].to_vec()));
            pos += 8 + len + (len & 1);
        }
        out
    }

    /// Reassemble a well-formed RIFF from chunks, using `pad` for odd bodies.
    fn rebuild(chunks: &[([u8; 4], Vec<u8>)], pad: u8) -> Vec<u8> {
        let mut body = b"WAVE".to_vec();
        for (name, chunk) in chunks {
            body.extend_from_slice(name);
            body.extend_from_slice(&(chunk.len() as u32).to_le_bytes());
            body.extend_from_slice(chunk);
            if chunk.len() & 1 != 0 {
                body.push(pad);
            }
        }
        let mut out = b"RIFF".to_vec();
        out.extend_from_slice(&(body.len() as u32).to_le_bytes());
        out.extend_from_slice(&body);
        out
    }

    fn find(chunks: &[([u8; 4], Vec<u8>)], fourcc: &[u8; 4]) -> usize {
        chunks
            .iter()
            .position(|(name, _)| name == fourcc)
            .unwrap_or_else(|| panic!("packaged asset has no {} chunk", fourcc.escape_ascii()))
    }

    /// MM-BUG-KILN-00195: prove every check in `parse_b1_strict` bites.
    ///
    /// Each case mutates a real packaged asset in exactly one direction the
    /// runtime rejects, and requires the crate-side predicate to reject it too.
    /// Without this the validator could silently narrow again — which is how it
    /// came to check only the `b1t ` chunk in the first place. The unmutated
    /// asset is checked first, so a predicate that rejected *everything* would
    /// not pass either.
    #[test]
    fn strict_validator_rejects_each_defeat() {
        let (name, bytes) = SAMPLES[find_sample("b1_normal_C3.wav")];
        assert!(
            parse_b1_strict(bytes).is_ok(),
            "{name} must pass unmutated: {:?}",
            parse_b1_strict(bytes).err()
        );
        let base = split_chunks(bytes);
        let fmt = find(&base, b"fmt ");
        let data = find(&base, b"data");
        let tail = find(&base, b"b1t ");
        assert_eq!(tail, base.len() - 1, "the natural tail must be terminal");

        // (label, mutated asset, the reason the rejection must give). Pinning
        // the reason as well as the rejection is what stops a validator that
        // fails everything for one blunt reason from passing this test.
        let mut cases: Vec<(&str, Vec<u8>, &str)> = Vec::new();

        let mut stereo = base.clone();
        stereo[fmt].1[2..4].copy_from_slice(&2u16.to_le_bytes());
        cases.push(("fmt says stereo", rebuild(&stereo, 0), "PCM16 mono"));

        let mut eight_bit = base.clone();
        eight_bit[fmt].1[14..16].copy_from_slice(&8u16.to_le_bytes());
        cases.push(("fmt says 8-bit", rebuild(&eight_bit, 0), "PCM16 mono"));

        let mut half_rate = base.clone();
        half_rate[fmt].1[4..8].copy_from_slice(&22_050u32.to_le_bytes());
        cases.push(("fmt says 22.05 kHz", rebuild(&half_rate, 0), "PCM16 mono"));

        let mut wide_align = base.clone();
        wide_align[fmt].1[12..14].copy_from_slice(&4u16.to_le_bytes());
        cases.push((
            "fmt says block-align 4",
            rebuild(&wide_align, 0),
            "PCM16 mono",
        ));

        let mut adpcm = base.clone();
        adpcm[fmt].1[0..2].copy_from_slice(&2u16.to_le_bytes());
        cases.push(("fmt says a non-PCM codec", rebuild(&adpcm, 0), "PCM16 mono"));

        let mut short_fmt = base.clone();
        short_fmt[fmt].1.truncate(14);
        cases.push(("fmt is truncated", rebuild(&short_fmt, 0), "PCM16 mono"));

        let mut no_fmt = base.clone();
        no_fmt.remove(fmt);
        cases.push((
            "fmt is absent",
            rebuild(&no_fmt, 0),
            "exactly one fmt chunk",
        ));

        let mut two_fmt = base.clone();
        two_fmt.insert(fmt, base[fmt].clone());
        cases.push((
            "fmt is duplicated",
            rebuild(&two_fmt, 0),
            "exactly one fmt chunk",
        ));

        let mut junk_data = base.clone();
        junk_data[data].0 = *b"junk";
        cases.push((
            "data became a same-sized junk chunk",
            rebuild(&junk_data, 0),
            "missing its PCM data chunk",
        ));

        let mut two_data = base.clone();
        two_data.insert(data, base[data].clone());
        cases.push((
            "data is duplicated",
            rebuild(&two_data, 0),
            "duplicate PCM data chunks",
        ));

        let mut empty_data = base.clone();
        empty_data[data].1.clear();
        cases.push((
            "data is empty",
            rebuild(&empty_data, 0),
            "empty or has a partial frame",
        ));

        let mut partial_frame = base.clone();
        partial_frame[data].1.truncate(base[data].1.len() - 1);
        cases.push((
            "data holds half a frame",
            rebuild(&partial_frame, 0),
            "empty or has a partial frame",
        ));

        let mut short_body = base.clone();
        short_body[data].1.truncate(59_535 * 2);
        cases.push((
            "data stops exactly at the tail entry frame",
            rebuild(&short_body, 0),
            "outside a 59535-frame PCM body",
        ));

        let mut padded = base.clone();
        padded.insert(tail, (*b"junk", vec![0u8]));
        cases.push((
            "an odd chunk carries a nonzero pad byte",
            rebuild(&padded, 0xFF),
            "nonzero pad byte",
        ));

        for (label, mutated, expected) in cases {
            match parse_b1_strict(&mutated) {
                Ok(_) => panic!("strict validator accepted a defeated asset: {label}"),
                Err(reason) => assert!(
                    reason.contains(expected),
                    "{label}: rejected for the wrong reason \
                     (got {reason:?}, expected it to mention {expected:?})"
                ),
            }
        }
    }

    fn find_sample(name: &str) -> usize {
        SAMPLES
            .iter()
            .position(|(candidate, _)| *candidate == name)
            .unwrap_or_else(|| panic!("{name} is not packaged"))
    }

    #[test]
    fn inventory_matches_packaged_wavs() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let mut packaged: Vec<String> = fs::read_dir(samples_dir)
            .expect("sample directory must exist")
            .map(|e| e.expect("readable entry").path())
            .filter(|p| p.extension() == Some(OsStr::new("wav")))
            .map(|p| p.file_name().unwrap().to_string_lossy().into_owned())
            .collect();
        packaged.sort();
        let mut embedded: Vec<String> = SAMPLES.iter().map(|(n, _)| (*n).to_owned()).collect();
        embedded.sort();
        assert_eq!(packaged.len(), FILE_COUNT);
        assert_eq!(embedded, packaged);
    }

    #[test]
    fn every_sample_is_an_extended_wav_with_the_expected_aggregate_sizes() {
        assert_eq!(
            SAMPLES.iter().map(|(_, b)| b.len()).sum::<usize>(),
            EXPECTED_BYTES
        );
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a WAV");
            assert_eq!(&bytes[..4], b"RIFF", "{name} has no RIFF header");
            assert_eq!(&bytes[8..12], b"WAVE", "{name} has no WAVE signature");
            assert!(
                !b1_tail(bytes).is_empty(),
                "{name} has an empty natural tail"
            );
            assert_eq!(get(name), Some(bytes));
        }
        assert_eq!(
            SAMPLES
                .iter()
                .map(|(_, bytes)| b1_tail(bytes).len())
                .sum::<usize>(),
            EXPECTED_TAIL_BYTES
        );
        assert_eq!(get("missing.wav"), None);
    }
}
