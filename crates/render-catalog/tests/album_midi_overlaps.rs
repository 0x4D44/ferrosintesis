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
    /// GM System On. Not a note, but it ends every sounding one, so the audit has to
    /// see it or it mis-reads valid reset-bearing MIDI (MM-BUG-CRUCIBLE-00034).
    Reset,
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

/// The universal GM System On message body, as `midi::decode_sysex_payload` matches it:
/// `F0 7E <device> 09 01 F7`, with the framing `F0` already consumed and the payload
/// still carrying its terminating `F7`. The device byte is any value.
fn is_gm_system_on(payload: &[u8]) -> bool {
    matches!(payload.strip_suffix(&[0xf7]), Some([0x7e, _, 0x09, 0x01]))
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
                let end = pos
                    .checked_add(len)
                    .ok_or_else(|| "sysex length overflow".to_string())?;
                let payload = track
                    .get(pos..end)
                    .ok_or_else(|| "sysex extends past track".to_string())?;
                pos = end;
                // Mirrors `midi::parse` exactly: in an SMF only F0 begins a message,
                // the payload must be terminated by F7, and the body is then matched
                // against the universal GM System On shape. Getting any of those three
                // wrong would make the audit disagree with the renderer, which is the
                // whole defect this arm exists to fix.
                if status == 0xf0 && is_gm_system_on(payload) {
                    events.push(NoteEvent {
                        tick,
                        ordinal: *ordinal,
                        channel: 0,
                        key: 0,
                        kind: NoteKind::Reset,
                    });
                    *ordinal = ordinal
                        .checked_add(1)
                        .ok_or_else(|| "note event ordinal overflow".to_string())?;
                }
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

    // A GM System On sorts BEFORE other events at the same tick, exactly as
    // `midi::parse` orders it — otherwise a reset and its replacement note-on at one
    // tick would be read in the wrong order and the replacement would look like an
    // overlap. `false < true`, so the reset key sorts first.
    events.sort_by_key(|event| {
        (
            event.tick,
            !matches!(event.kind, NoteKind::Reset),
            event.ordinal,
        )
    });
    let mut active: BTreeMap<(u8, u8), usize> = BTreeMap::new();
    // Notes a reset silenced, which may still be followed by their original note-off.
    // The renderer ignores such an off — the voice is already gone — so the audit must
    // too. Counted per note rather than forgiven wholesale, so an off for a key that
    // was never held still counts as unmatched in the new epoch.
    let mut cleared_by_reset: BTreeMap<(u8, u8), usize> = BTreeMap::new();
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
                None => match cleared_by_reset.get_mut(&note) {
                    // A stale off from before the reset: harmless in the renderer.
                    Some(pending) => {
                        *pending -= 1;
                        if *pending == 0 {
                            cleared_by_reset.remove(&note);
                        }
                    }
                    None => audit.unmatched_note_offs += 1,
                },
            },
            NoteKind::Reset => {
                // The engine clears every active voice, so nothing sounding survives
                // and none of it is "unmatched" — it was ended, just not by a note-off.
                for (note, depth) in std::mem::take(&mut active) {
                    *cleared_by_reset.entry(note).or_default() += depth;
                }
            }
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

    /// `F0 05 7E 7F 09 01 F7` — the universal GM System On, as it appears in a track.
    const GM_SYSTEM_ON: [u8; 7] = [0xf0, 0x05, 0x7e, 0x7f, 0x09, 0x01, 0xf7];

    /// MM-BUG-CRUCIBLE-00034: GM System On ends every sounding note, so the audit must
    /// see it. It skipped all SysEx, which made valid reset-bearing MIDI fail the
    /// repository gate as overlapping or unbalanced.
    ///
    /// A note held across a reset is not "unmatched": the renderer ended it, just not
    /// with a note-off.
    #[test]
    fn gm_system_on_clears_a_held_note() {
        let mut events = vec![0x00, 0x90, 60, 100, 0x0a];
        events.extend_from_slice(&GM_SYSTEM_ON);
        assert_eq!(audit(&[&events]), NoteAudit::default());
    }

    /// The reset is ordered before other events at the same tick, exactly as
    /// `midi::parse` orders it — so a replacement note-on at the reset's own tick is a
    /// handoff, not an overlap. Getting the order wrong is the difference between a
    /// clean file and a reported overlap, which is why this control uses delta 0.
    #[test]
    fn gm_system_on_and_a_replacement_note_at_one_tick_is_not_an_overlap() {
        let mut events = vec![0x00, 0x90, 60, 100, 0x0a];
        events.extend_from_slice(&GM_SYSTEM_ON);
        events.extend_from_slice(&[0x00, 0x90, 60, 100, 0x0a, 0x80, 60, 0]);
        assert_eq!(audit(&[&events]), NoteAudit::default());
    }

    /// A note-off left over from before the reset is harmless in the renderer — its
    /// voice is already gone — so the audit forgives it. Once, and only for a note the
    /// reset actually cleared.
    ///
    /// The replacement note is what makes this a real test of forgiveness. Without it
    /// the sequence is just an on and an off, which an audit that ignores the reset
    /// entirely also reads as clean — so the fixture would agree with the broken
    /// implementation and prove nothing. Here the second off has no active note to
    /// match, so it reaches the forgiveness path or it is counted.
    #[test]
    fn a_stale_note_off_after_a_reset_is_forgiven() {
        let mut events = vec![0x00, 0x90, 60, 100, 0x0a];
        events.extend_from_slice(&GM_SYSTEM_ON);
        events.extend_from_slice(&[
            0x00, 0x90, 60, 100, // replacement note in the new epoch
            0x0a, 0x80, 60, 0, // its own note-off, which matches it
            0x0a, 0x80, 60, 0, // the stale one from before the reset
        ]);
        assert_eq!(audit(&[&events]), NoteAudit::default());
    }

    /// The other half of that forgiveness, and the reason it is counted per note
    /// rather than granted wholesale: a reset does not license every later note-off.
    /// An off for a key the reset never cleared is still unmatched, and a SECOND off
    /// for a key it cleared once is too.
    #[test]
    fn a_reset_does_not_forgive_note_offs_it_never_cleared() {
        let mut never_held = vec![0x00, 0x90, 60, 100, 0x0a];
        never_held.extend_from_slice(&GM_SYSTEM_ON);
        never_held.extend_from_slice(&[0x0a, 0x80, 67, 0]); // key 67 was never on
        assert_eq!(
            audit(&[&never_held]),
            NoteAudit {
                unmatched_note_offs: 1,
                ..NoteAudit::default()
            }
        );

        let mut twice = vec![0x00, 0x90, 60, 100, 0x0a];
        twice.extend_from_slice(&GM_SYSTEM_ON);
        twice.extend_from_slice(&[0x0a, 0x80, 60, 0, 0x0a, 0x80, 60, 0]);
        assert_eq!(
            audit(&[&twice]),
            NoteAudit {
                unmatched_note_offs: 1,
                ..NoteAudit::default()
            }
        );
    }

    /// Only the exact GM System On shape resets anything. A SysEx that merely looks
    /// similar must stay invisible, or the audit would forgive notes the renderer
    /// keeps sounding — the same disagreement in the opposite direction.
    #[test]
    fn other_sysex_does_not_reset_the_audit() {
        // Right prefix, wrong sub-ID (09 02 is GM System Off, not On).
        let mut gm_off = vec![0x00, 0x90, 60, 100, 0x0a];
        gm_off.extend_from_slice(&[0xf0, 0x05, 0x7e, 0x7f, 0x09, 0x02, 0xf7]);
        // Right bytes but unterminated: no F7, so `midi::parse` does not recognize it.
        let mut unterminated = vec![0x00, 0x90, 62, 100, 0x0a];
        unterminated.extend_from_slice(&[0xf0, 0x04, 0x7e, 0x7f, 0x09, 0x01]);
        // A GS Reset — a real message the renderer models, but not a voice reset.
        let mut gs = vec![0x00, 0x90, 64, 100, 0x0a];
        gs.extend_from_slice(&[
            0xf0, 0x0a, 0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7f, 0x00, 0x41, 0xf7,
        ]);

        for (label, events) in [
            ("GM System Off", gm_off),
            ("unterminated", unterminated),
            ("GS Reset", gs),
        ] {
            assert_eq!(
                audit(&[&events]),
                NoteAudit {
                    unmatched_note_ons: 1,
                    ..NoteAudit::default()
                },
                "{label} was treated as a GM System On"
            );
        }
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
