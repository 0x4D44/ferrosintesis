use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

fn be_u32(bytes: &[u8], pos: &mut usize) -> Result<u32, String> {
    let end = pos
        .checked_add(4)
        .ok_or_else(|| "u32 position overflow".to_string())?;
    let raw = bytes
        .get(*pos..end)
        .ok_or_else(|| "unexpected EOF reading u32".to_string())?;
    *pos = end;
    Ok(u32::from_be_bytes(raw.try_into().expect("four bytes")))
}

fn vlq(bytes: &[u8], pos: &mut usize) -> Result<u32, String> {
    let mut value = 0u32;
    for _ in 0..4 {
        let byte = *bytes
            .get(*pos)
            .ok_or_else(|| "unexpected EOF reading VLQ".to_string())?;
        *pos += 1;
        value = (value << 7) | u32::from(byte & 0x7f);
        if byte < 0x80 {
            return Ok(value);
        }
    }
    Err("VLQ exceeds four bytes".to_string())
}

fn skip(bytes: &[u8], pos: &mut usize, len: usize) -> Result<(), String> {
    let end = pos
        .checked_add(len)
        .ok_or_else(|| "event length overflow".to_string())?;
    bytes
        .get(*pos..end)
        .ok_or_else(|| "event extends past track".to_string())?;
    *pos = end;
    Ok(())
}

fn track_overlaps(track: &[u8]) -> Result<usize, String> {
    let mut pos = 0usize;
    let mut tick = 0u32;
    let mut running_status = None;
    let mut ons: BTreeMap<(u8, u8), Vec<u32>> = BTreeMap::new();
    let mut offs: BTreeMap<(u8, u8), Vec<u32>> = BTreeMap::new();

    while pos < track.len() {
        tick = tick
            .checked_add(vlq(track, &mut pos)?)
            .ok_or_else(|| "absolute tick overflow".to_string())?;
        let next = *track
            .get(pos)
            .ok_or_else(|| "missing event status".to_string())?;
        let status = if next >= 0x80 {
            pos += 1;
            if (0x80..=0xef).contains(&next) {
                running_status = Some(next);
            }
            next
        } else {
            running_status.ok_or_else(|| "data byte without running status".to_string())?
        };

        match status {
            0xff => {
                skip(track, &mut pos, 1)?;
                let len = vlq(track, &mut pos)? as usize;
                skip(track, &mut pos, len)?;
            }
            0xf0 | 0xf7 => {
                let len = vlq(track, &mut pos)? as usize;
                skip(track, &mut pos, len)?;
            }
            0x80..=0xef => {
                let kind = status & 0xf0;
                let channel = status & 0x0f;
                let data_len = if matches!(kind, 0xc0 | 0xd0) { 1 } else { 2 };
                let end = pos
                    .checked_add(data_len)
                    .ok_or_else(|| "channel event length overflow".to_string())?;
                let data = track
                    .get(pos..end)
                    .ok_or_else(|| "channel event extends past track".to_string())?;
                pos = end;

                if !matches!(kind, 0x80 | 0x90) {
                    continue;
                }
                let key = data[0] & 0x7f;
                if kind == 0x90 && data[1] > 0 {
                    ons.entry((channel, key)).or_default().push(tick);
                } else {
                    offs.entry((channel, key)).or_default().push(tick);
                }
            }
            _ => return Err(format!("unsupported status 0x{status:02x}")),
        }
    }

    let mut overlaps = 0usize;
    for (key, starts) in ons {
        let Some(ends) = offs.get(&key) else {
            continue;
        };
        if starts.len() != ends.len() {
            continue;
        }
        overlaps += starts
            .windows(2)
            .zip(ends)
            .filter(|(pair, end)| **end > pair[1])
            .count();
    }
    Ok(overlaps)
}

fn midi_overlaps(path: &Path) -> Result<usize, String> {
    let bytes = fs::read(path).map_err(|error| error.to_string())?;
    if bytes.get(0..4) != Some(b"MThd") {
        return Err("missing MThd".to_string());
    }
    let mut pos = 4usize;
    let header_len = be_u32(&bytes, &mut pos)? as usize;
    let header_end = 8usize
        .checked_add(header_len)
        .ok_or_else(|| "header length overflow".to_string())?;
    let header = bytes
        .get(8..header_end)
        .ok_or_else(|| "header extends past file".to_string())?;
    let track_count = u16::from_be_bytes(
        header
            .get(2..4)
            .ok_or_else(|| "short MThd".to_string())?
            .try_into()
            .expect("two bytes"),
    );
    pos = header_end;

    let mut overlaps = 0usize;
    for _ in 0..track_count {
        if bytes.get(pos..pos + 4) != Some(b"MTrk") {
            return Err("missing MTrk".to_string());
        }
        pos += 4;
        let len = be_u32(&bytes, &mut pos)? as usize;
        let end = pos
            .checked_add(len)
            .ok_or_else(|| "track length overflow".to_string())?;
        let track = bytes
            .get(pos..end)
            .ok_or_else(|| "track extends past file".to_string())?;
        overlaps += track_overlaps(track)?;
        pos = end;
    }
    Ok(overlaps)
}

fn find_midis(dir: &Path, out: &mut Vec<PathBuf>) {
    for entry in fs::read_dir(dir).expect("read albums directory") {
        let path = entry.expect("read album entry").path();
        if path.is_dir() {
            find_midis(&path, out);
        } else if path.extension().is_some_and(|extension| extension == "mid") {
            out.push(path);
        }
    }
}

#[test]
fn committed_album_midis_have_no_same_pitch_overlaps() {
    let repo = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("render-catalog is under <repo>/crates");
    let mut midis = Vec::new();
    find_midis(&repo.join("albums"), &mut midis);
    midis.sort();

    let failures: Vec<String> = midis
        .iter()
        .filter_map(|path| match midi_overlaps(path) {
            Ok(0) => None,
            Ok(count) => Some(format!(
                "{}: {count} same-pitch overlap(s)",
                path.strip_prefix(repo).unwrap_or(path).display()
            )),
            Err(error) => Some(format!(
                "{}: {error}",
                path.strip_prefix(repo).unwrap_or(path).display()
            )),
        })
        .collect();

    assert!(
        failures.is_empty(),
        "committed album MIDIs must be unambiguous on oldest- and newest-note-off synths:\n{}",
        failures.join("\n")
    );
}
