//! Malformed-input oracles for [`crate::offline::parse`] — the crate's only
//! untrusted-input surface.
//!
//! ## Why this exists
//!
//! `midi.rs` tested well-formed files thoroughly and malformed ones barely: of the
//! fourteen `parse` calls in its test module, thirteen were `.unwrap()` on a file the
//! test had just assembled correctly, and exactly one
//! (`system_status_never_becomes_the_running_status`) asserted that a `MidiError`
//! variant is produced at all. `error.rs` only exercised `Display` and `source`. So
//! seven of the eight variants had no test proving they are still reachable, and a
//! parser that regressed to returning one variant for everything would have passed the
//! whole suite. The crate publishes to crates.io, which makes this the surface a
//! stranger's bytes reach first.
//!
//! Three oracles, in increasing order of how much input they see:
//!
//! 1. [`tests::every_error_variant_is_reachable_with_its_payload`] — a table of minimal
//!    hand-built files, each a *valid* SMF with exactly one thing corrupted, asserting
//!    the **specific** variant **and its payload**. `is_err()` is deliberately never
//!    used: it passes for a parser that has collapsed to a single variant.
//! 2. [`tests::corpus_files_parse_or_fail_with_a_specific_error`] — walks the gitignored
//!    third-party `test-corpus/`, when a machine has one, and proves no real-world file
//!    panics.
//! 3. `fuzz/` at the repository root — the libFuzzer target for the same entry point,
//!    for the inputs nobody thought to write down. See `fuzz/README.md`.
//!
//! ## What it found
//!
//! Three `usize` additions of an attacker-controlled `u32` — `8 + hlen` (midi.rs:217),
//! `c.pos + len` (midi.rs:231) and `self.pos + n` in `Cursor::bytes` (midi.rs:166).
//! Unreachable on a 64-bit `usize`, a contract break on a 32-bit one, where `parse`
//! panics in debug and silently misparses in release. Three fixtures below carry the
//! reproducing bytes; see the note above the header-length case. **Reported, not fixed
//! here.**
//!
//! The coverage claim in (1) is **derived from the enum, not from a second list**:
//! [`tests::variant_name`] matches `MidiError` exhaustively, so a new variant stops this
//! module compiling until someone adds a fixture for it. A hand-counted "we test 7 of 8"
//! assertion would rot exactly the way the three lists in CLAUDE.md's "Hand-maintained
//! lists are the recurring defect here" did.

#[cfg(test)]
mod tests {
    use crate::offline::{self, MidiError, MAX_SONG_SECONDS};
    use std::path::{Path, PathBuf};

    // ---------------------------------------------------------------------------
    // Fixture builder: a valid file, then one deliberate corruption.
    // ---------------------------------------------------------------------------

    /// The event bytes of a well-formed track: middle C for one beat, then end-of-track.
    /// Same construction idiom as the crate-level doctest in `lib.rs`.
    fn good_events() -> Vec<u8> {
        vec![
            0x00, 0x90, 60, 100, // note on: middle C, velocity 100
            0x83, 0x60, 0x80, 60, 0, // 480 ticks later: note off
            0x00, 0xFF, 0x2F, 0x00, // end of track
        ]
    }

    /// One track chunk. The type tag and the declared length are separate fields so a
    /// fixture can corrupt one of them without disturbing the events.
    struct Track {
        /// The 4-byte chunk type. `MTrk` in a valid file.
        tag: [u8; 4],
        /// `None` means "the true byte length of `events`" — what a valid file carries.
        declared_len: Option<u32>,
        events: Vec<u8>,
    }

    impl Track {
        fn valid() -> Self {
            Track {
                tag: *b"MTrk",
                declared_len: None,
                events: good_events(),
            }
        }
    }

    /// A valid format-0 SMF, field by field.
    ///
    /// Every fixture below starts from [`Smf::valid`] and changes exactly one thing, so
    /// each case reads as "a valid file EXCEPT ..." rather than as opaque byte soup —
    /// and so a case that stops provoking its variant can only be the parser's doing.
    struct Smf {
        /// The 4-byte file magic. `MThd` in a valid file.
        magic: [u8; 4],
        /// The declared header length. 6 in a valid file; the parser seeks to `8 + this`
        /// for the first chunk.
        header_len: u32,
        format: u16,
        /// The track COUNT in the header. The actual chunks are `tracks`; a disagreement
        /// between the two is itself a corruption worth a fixture.
        ntracks: u16,
        /// Ticks per quarter note, or SMPTE timecode when bit 15 is set.
        division: u16,
        tracks: Vec<Track>,
        /// Cut the assembled file to this many bytes. How the truncation fixtures work.
        truncate_to: Option<usize>,
    }

    impl Smf {
        fn valid() -> Self {
            Smf {
                magic: *b"MThd",
                header_len: 6,
                format: 0,
                ntracks: 1,
                division: 480,
                tracks: vec![Track::valid()],
                truncate_to: None,
            }
        }

        fn bytes(&self) -> Vec<u8> {
            let mut d: Vec<u8> = Vec::new();
            d.extend(self.magic);
            d.extend(self.header_len.to_be_bytes());
            d.extend(self.format.to_be_bytes());
            d.extend(self.ntracks.to_be_bytes());
            d.extend(self.division.to_be_bytes());
            for track in &self.tracks {
                d.extend(track.tag);
                let len = track.declared_len.unwrap_or(track.events.len() as u32);
                d.extend(len.to_be_bytes());
                d.extend(&track.events);
            }
            if let Some(n) = self.truncate_to {
                d.truncate(n);
            }
            d
        }
    }

    /// A file that is valid except for whatever `corrupt` changes.
    fn corrupted(corrupt: impl FnOnce(&mut Smf)) -> Vec<u8> {
        let mut smf = Smf::valid();
        corrupt(&mut smf);
        smf.bytes()
    }

    /// The template every fixture corrupts must itself parse. Without this, a fixture
    /// could be "passing" because the *template* is broken, and the corruption under
    /// test would be doing nothing.
    #[test]
    fn the_uncorrupted_template_parses() {
        let song = offline::parse(&Smf::valid().bytes()).expect("the template must be valid");
        assert_eq!(song.events_len(), 2);
        // 480 ticks at the SMF default 120 bpm = one quarter = 0.5 s.
        assert!((song.seconds() - 0.5).abs() < 1e-9, "{}", song.seconds());
    }

    // ---------------------------------------------------------------------------
    // (1) Every error variant is reachable, with the right payload.
    // ---------------------------------------------------------------------------

    /// The variant of an error, as a string, via an **exhaustive** match.
    ///
    /// `MidiError` is `#[non_exhaustive]`, which binds downstream crates but not this
    /// one — so adding a variant breaks this match, and whoever adds it must also add a
    /// fixture below. That is the whole design: the "every variant is covered" claim is
    /// derived from the enum by the compiler, never from a second hand-written list.
    fn variant_name(e: &MidiError) -> &'static str {
        match e {
            MidiError::Io { .. } => "Io",
            MidiError::NotMidi => "NotMidi",
            MidiError::UnsupportedFormat { .. } => "UnsupportedFormat",
            MidiError::UnsupportedTimeDivision => "UnsupportedTimeDivision",
            MidiError::MissingTrack { .. } => "MissingTrack",
            MidiError::BadStatusByte { .. } => "BadStatusByte",
            MidiError::UnexpectedEof => "UnexpectedEof",
            MidiError::TooLong { .. } => "TooLong",
        }
    }

    struct Case {
        /// Which byte is wrong and why that byte forces this variant, in prose. This is
        /// the failure message, so it has to stand on its own.
        what: &'static str,
        bytes: Vec<u8>,
        /// The exact variant and payload expected, spelled out for the failure message.
        expected: &'static str,
        /// Matches the one acceptable variant. Never `|_| true`, never `is_err()`.
        is_expected: fn(&MidiError) -> bool,
    }

    /// One minimal file per reachable `parse` error. Byte offsets below are into the
    /// assembled file: 0..3 magic, 4..7 header length, 8..9 format, 10..11 track count,
    /// 12..13 division, 14..17 first chunk type, 18..21 first chunk length, 22.. events.
    fn cases() -> Vec<Case> {
        vec![
            Case {
                what: "NotMidi: byte 3 of the magic is 'x', so the file opens `MThx`. \
                       Everything else is the valid template — in particular there are \
                       still four readable bytes to compare, which is what separates \
                       this from the empty-input case below.",
                bytes: corrupted(|f| f.magic = *b"MThx"),
                expected: "NotMidi",
                is_expected: |e| matches!(e, MidiError::NotMidi),
            },
            Case {
                what: "UnsupportedFormat: header bytes 8-9 (the format field) are 00 02. \
                       SMF type 2 is a bag of independent patterns with no common \
                       timeline, which this reader does not model. The division stays \
                       480 on purpose: the SMPTE check runs FIRST and would otherwise \
                       mask this.",
                bytes: corrupted(|f| f.format = 2),
                expected: "UnsupportedFormat { format: 2 }",
                is_expected: |e| matches!(e, MidiError::UnsupportedFormat { format: 2, .. }),
            },
            Case {
                what: "UnsupportedFormat payload fidelity: the same field set to FF FF. \
                       The reported format must be the value actually read (65535), not \
                       a constant 2 — a parser that hard-codes the payload passes the \
                       case above and fails here.",
                bytes: corrupted(|f| f.format = 0xFFFF),
                expected: "UnsupportedFormat { format: 65535 }",
                is_expected: |e| matches!(e, MidiError::UnsupportedFormat { format: 0xFFFF, .. }),
            },
            Case {
                what: "UnsupportedTimeDivision: header bytes 12-13 (the division) are \
                       E7 28. Bit 15 set means SMPTE timecode (-25 fps, 40 ticks per \
                       frame) rather than ticks-per-quarter-note, and the whole tempo \
                       map below assumes the latter.",
                bytes: corrupted(|f| f.division = 0xE728),
                expected: "UnsupportedTimeDivision",
                is_expected: |e| matches!(e, MidiError::UnsupportedTimeDivision),
            },
            Case {
                what: "Check ORDER: a file that is BOTH SMPTE-divided and format 2 must \
                       report the division, because the division test precedes the \
                       format test. Pinned because it is invisible in the error type and \
                       a reordering refactor would flip it silently.",
                bytes: corrupted(|f| {
                    f.division = 0xE728;
                    f.format = 2;
                }),
                expected: "UnsupportedTimeDivision (not UnsupportedFormat)",
                is_expected: |e| matches!(e, MidiError::UnsupportedTimeDivision),
            },
            Case {
                what: "MissingTrack: byte 17, the last byte of the first chunk type, is \
                       'x', so the chunk reads `MTrx`. There are four readable bytes and \
                       they are not `MTrk`.",
                bytes: corrupted(|f| f.tracks[0].tag = *b"MTrx"),
                expected: "MissingTrack { index: 0 }",
                is_expected: |e| matches!(e, MidiError::MissingTrack { index: 0, .. }),
            },
            Case {
                what: "MissingTrack payload fidelity: two chunks, the FIRST intact and \
                       the second tagged `MTrx`. The reported index must be 1 — a parser \
                       that hard-codes 0, or that reports a count instead of an index, \
                       fails only here.",
                bytes: corrupted(|f| {
                    f.ntracks = 2;
                    f.tracks.push(Track::valid());
                    f.tracks[1].tag = *b"MTrx";
                }),
                expected: "MissingTrack { index: 1 }",
                is_expected: |e| matches!(e, MidiError::MissingTrack { index: 1, .. }),
            },
            Case {
                what: "BadStatusByte: the first event's status byte, at file offset 23, \
                       is F8 (MIDI real-time Timing Clock). It is >= 0x80 so it is taken \
                       as an explicit status, but it is neither meta (FF) nor SysEx \
                       (F0/F7), and its high nibble F0 matches no channel-voice message. \
                       Real-time bytes belong in a MIDI stream, never in an SMF track.",
                bytes: corrupted(|f| {
                    assert_eq!(
                        f.tracks[0].events[1], 0x90,
                        "fixture drift: events[1] is no longer the status byte"
                    );
                    f.tracks[0].events[1] = 0xF8;
                }),
                expected: "BadStatusByte { status: 0xF8 }",
                is_expected: |e| matches!(e, MidiError::BadStatusByte { status: 0xF8, .. }),
            },
            // The other route to BadStatusByte — a data byte arriving before any channel
            // status has been latched, giving `status: 0` — is already pinned by
            // `midi::tests::system_status_never_becomes_the_running_status`. Not
            // duplicated here.
            Case {
                what: "UnexpectedEof: zero bytes. The magic comparison needs four bytes \
                       and cannot get them, so an empty input is EOF and the magic is \
                       never examined. Worth pinning because `NotMidi` is the intuitive \
                       answer and it is the wrong one.",
                bytes: Vec::new(),
                expected: "UnexpectedEof (not NotMidi)",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            Case {
                what: "UnexpectedEof: the file stops after byte 11. `MThd`, the header \
                       length, the format and the track count are all present; the \
                       2-byte division field at offset 12 is not.",
                bytes: corrupted(|f| f.truncate_to = Some(12)),
                expected: "UnexpectedEof",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            // THIS FIXTURE FOUND A LIVE DEFECT. On a 32-bit target it does not return
            // UnexpectedEof — `8 + hlen` at midi.rs:217 is a `usize` addition of an
            // attacker-controlled `u32`, and on a 32-bit `usize` it overflows:
            //
            //   cargo test --target i686-pc-windows-msvc -p ferrosintesis --lib
            //     -> panicked at midi.rs:217: attempt to add with overflow
            //   release (checks off) -> wraps to 7, misdiagnosed as MissingTrack
            //
            // Two sibling sites overflow the same way: `c.pos + len` (midi.rs:231) and
            // `self.pos + n` in `Cursor::bytes` (midi.rs:166); a track length of
            // FF FF FF FF parses as an EMPTY SONG in 32-bit release instead of
            // UnexpectedEof. `parse` promises a `Result` on any bytes, so a panic here
            // is a contract break, and the crate is published — i686, armv7 and wasm32
            // are all 32-bit. Reported, deliberately NOT fixed in this change; the fix
            // is `checked_add`/`saturating_add` at all three sites, and this case is
            // already its regression test.
            Case {
                what: "UnexpectedEof: header bytes 4-7 (the declared header length) are \
                       FF FF FF FF. The parser seeks to `8 + header_len` for the first \
                       chunk, which lands ~4 GiB past the end of a 35-byte file. Sound \
                       on 64-bit; see the note above for what it does on 32-bit.",
                bytes: corrupted(|f| f.header_len = 0xFFFF_FFFF),
                expected: "UnexpectedEof",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            Case {
                what: "UnexpectedEof: the track chunk length at bytes 18-21 is FF FF FF \
                       FF, so the event loop's end marker is `c.pos + len` (midi.rs:231) \
                       — the second of the three 32-bit overflow sites in the note \
                       above, and the nastiest: in 32-bit release the sum wraps to a \
                       value BELOW the cursor, the loop never runs, and the file parses \
                       as an empty song with no error at all.",
                bytes: corrupted(|f| f.tracks[0].declared_len = Some(0xFFFF_FFFF)),
                expected: "UnexpectedEof",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            Case {
                what: "UnexpectedEof: a text meta event (FF 01) whose VLQ payload length \
                       is 8F FF FF FF 7F = 4_294_967_295, so the payload read runs off \
                       the end. This is the third 32-bit overflow site, `self.pos + n` \
                       in `Cursor::bytes` (midi.rs:166), reached through the meta arm; \
                       an F0 SysEx event with the same length reaches it too.",
                bytes: corrupted(|f| {
                    let mut events = vec![0x00, 0xFF, 0x01, 0x8F, 0xFF, 0xFF, 0xFF, 0x7F];
                    events.extend(good_events());
                    f.tracks[0].events = events;
                }),
                expected: "UnexpectedEof",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            Case {
                what: "UnexpectedEof: the track chunk length at bytes 18-21 claims 64 \
                       bytes more than the file holds, so the event loop keeps reading \
                       past the last byte instead of stopping at end-of-track. This is \
                       the shape the two rejected corpus files have.",
                bytes: corrupted(|f| {
                    f.tracks[0].declared_len = Some(good_events().len() as u32 + 64);
                }),
                expected: "UnexpectedEof",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            Case {
                what: "UnexpectedEof: header bytes 10-11 (the track count) say 2 but only \
                       one chunk follows, so reading the second chunk's 4-byte type runs \
                       off the end. Note this is EOF and NOT MissingTrack: MissingTrack \
                       needs four READABLE bytes that are not `MTrk`.",
                bytes: corrupted(|f| f.ntracks = 2),
                expected: "UnexpectedEof (not MissingTrack)",
                is_expected: |e| matches!(e, MidiError::UnexpectedEof),
            },
            Case {
                what: "TooLong: the track is replaced by a Set-Tempo of FF FF FF \
                       (16.777215 s per quarter, the largest a 24-bit field holds), a \
                       VLQ delta of FF FF FF 7F (268_435_455 ticks) and then a note — \
                       the note matters, because the length is taken from the last \
                       EVENT, so a tempo map alone proves nothing. At 480 ticks per \
                       quarter that is ~9.4e6 s, about 108 days, from 18 bytes of track. \
                       `render` allocates `seconds * rate * 8` bytes, so accepting this \
                       aborts the process in the allocator (MAX_SONG_SECONDS).",
                bytes: corrupted(|f| {
                    f.tracks[0].events = vec![
                        0x00, 0xFF, 0x51, 0x03, 0xFF, 0xFF, 0xFF, // Set-Tempo, max value
                        0xFF, 0xFF, 0xFF, 0x7F, // VLQ delta = 268_435_455 ticks
                        0x90, 60, 100, // ... and a note AT that tick
                        0x00, 0xFF, 0x2F, 0x00, // end of track
                    ];
                }),
                expected: "TooLong { seconds > MAX_SONG_SECONDS }",
                is_expected: |e| matches!(e, MidiError::TooLong { seconds, .. } if *seconds > MAX_SONG_SECONDS),
            },
            Case {
                what: "TooLong via NaN: header bytes 12-13 (the division) are 00 00 — \
                       zero ticks per quarter. Seconds-per-tick becomes a division by \
                       zero, so every event time is NaN and it is the FINITENESS half of \
                       the length guard that refuses the file. There is no separate \
                       zero-division check; this pins the guard that stands in for one, \
                       and would fail loudly if that guard were ever narrowed to a plain \
                       `seconds > MAX` comparison.",
                bytes: corrupted(|f| f.division = 0),
                expected: "TooLong { seconds: NaN }",
                is_expected: |e| matches!(e, MidiError::TooLong { seconds, .. } if seconds.is_nan()),
            },
        ]
    }

    /// Every `parse` error variant is reachable from a minimal input, and carries the
    /// payload the input implies.
    ///
    /// Asserting the SPECIFIC variant is the point. `is_err()` would pass for a parser
    /// that had regressed to returning `NotMidi` for every input, which is precisely the
    /// regression a suite made of `.unwrap()`s cannot see.
    #[test]
    fn every_error_variant_is_reachable_with_its_payload() {
        let mut produced: Vec<&'static str> = Vec::new();

        for case in cases() {
            match offline::parse(&case.bytes) {
                Ok(_) => panic!(
                    "{}\n  expected {}, but the file parsed cleanly\n  bytes: {:02X?}",
                    case.what, case.expected, case.bytes
                ),
                Err(e) => {
                    assert!(
                        (case.is_expected)(&e),
                        "{}\n  expected {}\n  got      {e:?}\n  bytes: {:02X?}",
                        case.what,
                        case.expected,
                        case.bytes
                    );
                    produced.push(variant_name(&e));
                }
            }
        }

        // Derived coverage: collect the variants the table ACTUALLY produced and require
        // the full set `parse` can emit. Counting cases instead would let a duplicate
        // fixture hide a variant that had quietly stopped being reachable.
        produced.sort_unstable();
        produced.dedup();
        assert_eq!(
            produced,
            [
                "BadStatusByte",
                "MissingTrack",
                "NotMidi",
                "TooLong",
                "UnexpectedEof",
                "UnsupportedFormat",
                "UnsupportedTimeDivision",
            ],
            "the fixture table no longer reaches every MidiError variant that `parse` \
             can produce (`Io` is excluded — only `load` produces it)"
        );
    }

    /// `Io` is the one variant `parse` cannot produce: it works from bytes already in
    /// memory. `load` is its only source, so cover it there — including the path and the
    /// underlying `ErrorKind`, which are what a caller actually reports to a user.
    #[test]
    fn load_reports_io_with_the_path_and_the_underlying_kind() {
        let missing = Path::new("no-such-directory-4f21b9/no-such-file.mid");
        match offline::load(missing) {
            Err(MidiError::Io { path, source }) => {
                assert_eq!(path.as_path(), missing, "the failing path must be reported");
                assert_eq!(source.kind(), std::io::ErrorKind::NotFound);
            }
            Err(e) => panic!("expected MidiError::Io, got {e:?}"),
            Ok(_) => panic!("expected MidiError::Io — a nonexistent file 'parsed'"),
        }
    }

    // ---------------------------------------------------------------------------
    // (2) The third-party corpus walker.
    // ---------------------------------------------------------------------------

    fn repo_root() -> PathBuf {
        // CARGO_MANIFEST_DIR = <root>/crates/ferrosintesis
        Path::new(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(2)
            .expect("crates/ferrosintesis sits two levels below the repo root")
            .to_path_buf()
    }

    /// Every `.mid` under `dir`, recursively.
    fn collect_midi(dir: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = std::fs::read_dir(dir) else {
            return; // an unreadable subdirectory is not this oracle's business
        };
        for entry in entries.filter_map(Result::ok) {
            let path = entry.path();
            if path.is_dir() {
                collect_midi(&path, out);
            } else if path
                .extension()
                .is_some_and(|e| e.eq_ignore_ascii_case("mid"))
            {
                out.push(path);
            }
        }
    }

    /// The two Tubular.net copies `test-corpus/README.md` records as having valid
    /// headers but malformed track data, "rejected with unexpected end of file". They
    /// are the most valuable files in the corpus: the only real-world malformed input we
    /// have.
    ///
    /// This is a PERMIT list, not a requirement — a file here may reject, it need not.
    /// That matters, because the README is already half stale: on 2026.07.25
    /// `05-tubular-bells-ii-early-stages.mid` parsed cleanly (15 449 events, 251.24 s —
    /// the 4:11 the README's own index quotes), and only `09-amarok-roses.mid` still
    /// fails. The running-status fix in `midi.rs` (a latched meta/SysEx status swallowed
    /// the rest of a track, "usually surfacing as UnexpectedEof") is the likely cure.
    /// The README has not caught up; requiring a rejection here would freeze the stale
    /// claim into a test.
    const KNOWN_REJECTED: [&str; 2] = [
        "05-tubular-bells-ii-early-stages.mid",
        "09-amarok-roses.mid",
    ];

    /// Every third-party MIDI in the local corpus either parses or is refused with a
    /// specific `MidiError` — and none of them panics.
    ///
    /// `test-corpus/` holds fan transcriptions that must never be committed (the remote
    /// is public and they are not redistributable), so it is gitignored and most
    /// checkouts will not have it. Absence is a SKIP with a note, never a failure —
    /// `test-corpus/README.md` is the tracked index for rebuilding it.
    #[test]
    fn corpus_files_parse_or_fail_with_a_specific_error() {
        let dir = repo_root().join("test-corpus");
        if !dir.is_dir() {
            eprintln!(
                "SKIP corpus walk: {} is not present. The third-party corpus is \
                 gitignored (unredistributable fan transcriptions); see \
                 test-corpus/README.md for the index that rebuilds it.",
                dir.display()
            );
            return;
        }

        let mut files = Vec::new();
        collect_midi(&dir, &mut files);
        files.sort();
        if files.is_empty() {
            eprintln!(
                "SKIP corpus walk: {} exists but holds no .mid files.",
                dir.display()
            );
            return;
        }

        let mut panicked: Vec<String> = Vec::new();
        let mut rejected: Vec<(String, &'static str, String)> = Vec::new();
        let mut parsed = 0usize;

        for path in &files {
            let name = path
                .strip_prefix(&dir)
                .unwrap_or(path)
                .display()
                .to_string()
                .replace('\\', "/");
            let Ok(data) = std::fs::read(path) else {
                continue; // a file we cannot read tells us nothing about the parser
            };

            // Catch rather than propagate, so ONE bad file names itself instead of
            // aborting the walk and hiding every file after it. A panic on untrusted
            // input is a defect: the contract is a `Result`, and a caller that has
            // written `match parse(..)` gets a process abort instead.
            match std::panic::catch_unwind(|| offline::parse(&data)) {
                Err(_) => panicked.push(name),
                Ok(Ok(song)) => {
                    parsed += 1;
                    let seconds = song.seconds();
                    assert!(
                        seconds.is_finite() && (0.0..=MAX_SONG_SECONDS).contains(&seconds),
                        "{name}: parsed with a length `render` cannot allocate against: \
                         {seconds}"
                    );
                }
                Ok(Err(e)) => {
                    let variant = variant_name(&e);
                    assert_ne!(
                        variant, "Io",
                        "{name}: `parse` works from bytes and must never report Io"
                    );
                    rejected.push((name, variant, e.to_string()));
                }
            }
        }

        eprintln!(
            "corpus walk: {} file(s) under {}, {parsed} parsed, {} rejected",
            files.len(),
            dir.display(),
            rejected.len()
        );
        for (name, variant, message) in &rejected {
            eprintln!("  rejected: {name} -> {variant}: {message}");
        }

        assert!(
            panicked.is_empty(),
            "`parse` PANICKED on {} corpus file(s). A panic on untrusted input is a \
             parser defect, not a rejection — find the byte and fix it, do not add the \
             file to an ignore list:\n  {}",
            panicked.len(),
            panicked.join("\n  ")
        );

        // Only `reference-midi/` is the README-indexed set; anything else under
        // test-corpus is a developer's scratch space and is held to the panic-free and
        // classifiable bar above, but not to "must parse".
        let unexpected: Vec<String> = rejected
            .iter()
            .filter(|(name, _, _)| name.starts_with("reference-midi/"))
            .filter(|(name, _, _)| !KNOWN_REJECTED.iter().any(|known| name.ends_with(known)))
            .map(|(name, variant, message)| format!("{name} -> {variant}: {message}"))
            .collect();
        assert!(
            unexpected.is_empty(),
            "indexed corpus file(s) newly rejected. Either the parser regressed or the \
             local copy differs from the one the README indexes — both need a human \
             look:\n  {}",
            unexpected.join("\n  ")
        );

        // The two files the README names must fail the way it says they do. A different
        // variant here means the parser's diagnosis of real malformed input has changed.
        for (name, variant, message) in &rejected {
            assert_eq!(
                *variant, "UnexpectedEof",
                "{name}: test-corpus/README.md records this file as 'unexpected end of \
                 file'; got {message}"
            );
        }
    }
}
