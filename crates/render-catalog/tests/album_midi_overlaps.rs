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

#[derive(Clone, Copy)]
enum NoteKind {
    On,
    Off,
}

#[derive(Clone, Copy)]
struct NoteEvent {
    tick: u32,
    ordinal: usize,
    channel: u8,
    key: u8,
    kind: NoteKind,
}

#[derive(Debug, Default, PartialEq, Eq)]
struct NoteAudit {
    overlaps: usize,
    unmatched_note_ons: usize,
    unmatched_note_offs: usize,
}

impl NoteAudit {
    fn is_clean(&self) -> bool {
        self.overlaps == 0 && self.unmatched_note_ons == 0 && self.unmatched_note_offs == 0
    }
}

fn track_note_events(
    track: &[u8],
    events: &mut Vec<NoteEvent>,
    ordinal: &mut usize,
) -> Result<(), String> {
    let mut pos = 0usize;
    let mut tick = 0u32;
    let mut running_status = None;

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
                let kind = if kind == 0x90 && data[1] > 0 {
                    NoteKind::On
                } else {
                    NoteKind::Off
                };
                events.push(NoteEvent {
                    tick,
                    ordinal: *ordinal,
                    channel,
                    key,
                    kind,
                });
                *ordinal = ordinal
                    .checked_add(1)
                    .ok_or_else(|| "note event ordinal overflow".to_string())?;
            }
            _ => return Err(format!("unsupported status 0x{status:02x}")),
        }
    }
    Ok(())
}

fn audit_midi_bytes(bytes: &[u8]) -> Result<NoteAudit, String> {
    if bytes.get(0..4) != Some(b"MThd") {
        return Err("missing MThd".to_string());
    }
    let mut pos = 4usize;
    let header_len = be_u32(bytes, &mut pos)? as usize;
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

    let mut events = Vec::new();
    let mut ordinal = 0usize;
    for _ in 0..track_count {
        if bytes.get(pos..pos + 4) != Some(b"MTrk") {
            return Err("missing MTrk".to_string());
        }
        pos += 4;
        let len = be_u32(bytes, &mut pos)? as usize;
        let end = pos
            .checked_add(len)
            .ok_or_else(|| "track length overflow".to_string())?;
        let track = bytes
            .get(pos..end)
            .ok_or_else(|| "track extends past file".to_string())?;
        track_note_events(track, &mut events, &mut ordinal)?;
        pos = end;
    }

    events.sort_by_key(|event| (event.tick, event.ordinal));
    let mut active: BTreeMap<(u8, u8), usize> = BTreeMap::new();
    let mut audit = NoteAudit::default();
    for event in events {
        let note = (event.channel, event.key);
        match event.kind {
            NoteKind::On => {
                let depth = active.entry(note).or_default();
                if *depth > 0 {
                    audit.overlaps += 1;
                }
                *depth += 1;
            }
            NoteKind::Off => match active.get_mut(&note) {
                Some(depth) => {
                    *depth -= 1;
                    if *depth == 0 {
                        active.remove(&note);
                    }
                }
                None => audit.unmatched_note_offs += 1,
            },
        }
    }
    audit.unmatched_note_ons = active.values().sum();
    Ok(audit)
}

fn midi_note_audit(path: &Path) -> Result<NoteAudit, String> {
    let bytes = fs::read(path).map_err(|error| error.to_string())?;
    audit_midi_bytes(&bytes)
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
        .filter_map(|path| match midi_note_audit(path) {
            Ok(audit) if audit.is_clean() => None,
            Ok(audit) => Some(format!(
                "{}: {} same-pitch overlap(s), {} unmatched note-on(s), {} unmatched note-off(s)",
                path.strip_prefix(repo).unwrap_or(path).display(),
                audit.overlaps,
                audit.unmatched_note_ons,
                audit.unmatched_note_offs
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

#[cfg(test)]
mod controls {
    use super::{audit_midi_bytes, NoteAudit};

    fn midi_file(tracks: &[&[u8]]) -> Vec<u8> {
        let mut midi = Vec::new();
        midi.extend_from_slice(b"MThd");
        midi.extend_from_slice(&6u32.to_be_bytes());
        midi.extend_from_slice(&1u16.to_be_bytes());
        midi.extend_from_slice(&(tracks.len() as u16).to_be_bytes());
        midi.extend_from_slice(&480u16.to_be_bytes());
        for events in tracks {
            let mut track = events.to_vec();
            track.extend_from_slice(&[0x00, 0xff, 0x2f, 0x00]);
            midi.extend_from_slice(b"MTrk");
            midi.extend_from_slice(&(track.len() as u32).to_be_bytes());
            midi.extend_from_slice(&track);
        }
        midi
    }

    fn audit(tracks: &[&[u8]]) -> NoteAudit {
        audit_midi_bytes(&midi_file(tracks)).expect("audit MIDI control")
    }

    #[test]
    fn detects_overlap_split_across_tracks() {
        let first = [0x00, 0x90, 60, 100, 0x14, 0x80, 60, 0];
        let second = [0x0a, 0x90, 60, 100, 0x14, 0x80, 60, 0];
        assert_eq!(
            audit(&[&first, &second]),
            NoteAudit {
                overlaps: 1,
                ..NoteAudit::default()
            }
        );
    }

    #[test]
    fn same_tick_serialization_order_distinguishes_handoff_from_overlap() {
        let off_before_on = [
            0x00, 0x90, 60, 100, 0x0a, 0x80, 60, 0, 0x00, 0x90, 60, 100, 0x0a, 0x80, 60, 0,
        ];
        let on_before_off = [
            0x00, 0x90, 60, 100, 0x0a, 0x90, 60, 100, 0x00, 0x80, 60, 0, 0x0a, 0x80, 60, 0,
        ];
        assert_eq!(audit(&[&off_before_on]), NoteAudit::default());
        assert_eq!(
            audit(&[&on_before_off]),
            NoteAudit {
                overlaps: 1,
                ..NoteAudit::default()
            }
        );
    }

    #[test]
    fn detects_overlap_when_note_lifecycle_is_unbalanced() {
        let events = [0x00, 0x90, 60, 100, 0x0a, 0x90, 60, 100, 0x0a, 0x80, 60, 0];
        assert_eq!(
            audit(&[&events]),
            NoteAudit {
                overlaps: 1,
                unmatched_note_ons: 1,
                unmatched_note_offs: 0,
            }
        );
    }

    #[test]
    fn accepts_balanced_repeated_note() {
        let events = [
            0x00, 0x90, 60, 100, 0x0a, 0x80, 60, 0, 0x0a, 0x90, 60, 100, 0x0a, 0x80, 60, 0,
        ];
        assert_eq!(audit(&[&events]), NoteAudit::default());
    }
}
