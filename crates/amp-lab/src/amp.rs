//! The amp-parameter model, and the bytes that carry it.
//!
//! Every control is emitted as the exact MIDI an album would author, so a setting
//! found here reproduces itself when pasted into a `.mid`. That is the whole
//! reason the lab talks to the synth in bytes instead of poking at internals.

/// NRPN MSB (CC99) selecting the ferrosintesis amp block. Must match
/// `engine.rs:AMP_NRPN_MSB`.
pub const AMP_NRPN_MSB: u8 = 0x30;
pub const NEUTRAL: u8 = 64;

#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Knob {
    pub idx: u8,
    pub name: &'static str,
    pub blurb: &'static str,
}

pub const KNOBS: [Knob; 6] = [
    Knob {
        idx: 0,
        name: "Drive",
        blurb: "pedal gain — near-clean to heavy. Changes level, like a real gain knob.",
    },
    Knob {
        idx: 1,
        name: "Tone",
        blurb: "pre-clip EQ. Subtle by nature: a saturator swallows pre-clip EQ.",
    },
    Knob {
        idx: 2,
        name: "Tightness",
        blurb: "low cut BEFORE the shaper — focus vs woolly.",
    },
    Knob {
        idx: 3,
        name: "Body",
        blurb: "cabinet low-mid. One of the three big movers.",
    },
    Knob {
        idx: 4,
        name: "Presence",
        blurb: "cabinet presence — cut vs smooth.",
    },
    Knob {
        idx: 5,
        name: "Cab Tone",
        blurb: "cabinet HF corner, DARKENS ONLY (above 64 is inert). The widest knob.",
    },
];

/// One complete rig: which voice, and where the six knobs sit.
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Rig {
    pub program: u8, // 29 or 30
    pub lead_bank: bool,
    pub vals: [u8; 6],
}

impl Default for Rig {
    fn default() -> Self {
        Rig {
            program: 29,
            lead_bank: true,
            vals: [NEUTRAL; 6],
        }
    }
}

impl Rig {
    /// The bytes that put a channel into this rig, in the order an album would
    /// author them: bank, program, then the six NRPN triples.
    pub fn bytes(&self, ch: u8) -> Vec<u8> {
        let mut v = Vec::with_capacity(8 + 6 * 9);
        v.extend_from_slice(&[0xB0 | ch, 0, u8::from(self.lead_bank)]);
        v.extend_from_slice(&[0xC0 | ch, self.program]);
        for (i, &val) in self.vals.iter().enumerate() {
            v.extend_from_slice(&Self::knob_bytes(ch, i as u8, val));
        }
        v
    }

    /// One knob, as its NRPN triple.
    pub fn knob_bytes(ch: u8, idx: u8, val: u8) -> [u8; 9] {
        [
            0xB0 | ch,
            99,
            AMP_NRPN_MSB,
            0xB0 | ch,
            98,
            idx,
            0xB0 | ch,
            6,
            val,
        ]
    }

    /// What this rig is, in a form that can be pasted somewhere useful.
    ///
    /// The tool's real output is numbers, not audio — without this we would end a
    /// session with an opinion instead of a setting.
    ///
    /// The emitted Python calls the album engines' **actual** `Score` surface —
    /// `sc.cc(ch, num, val, beat)` and `sc.program(ch, prog, beat)` — with `SC`, `CH` and
    /// `BEAT` left as explicit placeholders. It used to emit `amp(idx, val)`, a helper
    /// that exists in no album engine, so the advertised snippet raised `NameError` and
    /// carried neither the score object, the channel, nor the event time
    /// (MM-BUG-KILN-00077).
    ///
    /// **Every knob is emitted, including neutral ones.** The snippet's job is to
    /// reproduce this rig completely wherever it is pasted, and an album's channel may
    /// already carry a non-neutral amp block from an earlier beat — eliding neutrals
    /// would silently inherit those instead of resetting them. It is also what lets
    /// `export_snippet_reproduces_the_rig_bytes` compare against [`Rig::bytes`] directly.
    ///
    /// Ordering matches `Rig::bytes`: bank, program, then the six NRPN triples.
    /// `Score.cc`'s own sort key ranks CC0 before a program change before other CCs, so
    /// the album writes them in this order too.
    pub fn export(&self) -> String {
        let named: Vec<String> = KNOBS
            .iter()
            .map(|k| format!("{}={}", k.name.replace(' ', ""), self.vals[k.idx as usize]))
            .collect();
        // (code, trailing comment) so the comment column lines up whatever width the
        // numbers take — this snippet is the tool's deliverable, not debug output.
        let mut rows: Vec<(String, String)> = vec![
            (
                format!("sc.cc(CH, 0, {}, BEAT)", u8::from(self.lead_bank)),
                format!(
                    "bank select MSB — {} bank",
                    if self.lead_bank { "lead" } else { "main" }
                ),
            ),
            (
                format!("sc.program(CH, {}, BEAT)", self.program),
                format!(
                    "GM{} {}",
                    self.program,
                    if self.program == 29 {
                        "overdriven guitar"
                    } else {
                        "distortion guitar"
                    }
                ),
            ),
        ];
        for k in KNOBS {
            let val = self.vals[k.idx as usize];
            let neutral = if val == NEUTRAL { "  (neutral)" } else { "" };
            rows.push((
                format!("sc.cc(CH, 99, {AMP_NRPN_MSB:#04x}, BEAT)"),
                "NRPN MSB — amp block".to_string(),
            ));
            rows.push((
                format!("sc.cc(CH, 98, {}, BEAT)", k.idx),
                format!("NRPN LSB — knob {} {}{}", k.idx, k.name, neutral),
            ));
            rows.push((format!("sc.cc(CH, 6, {val}, BEAT)"), "value".to_string()));
        }
        let w = rows.iter().map(|(c, _)| c.len()).max().unwrap_or(0);
        let py: Vec<String> = rows
            .iter()
            .map(|(c, note)| format!("{c:<w$}  # {note}"))
            .collect();
        format!(
            "GM{} {} bank   {}\n\n\
             # engine.py — paste into an album to author this rig.\n\
             # SC/CH/BEAT are yours: the Score, the guitar channel, the beat it takes\n\
             # effect. Every knob is written, so this sets the rig rather than nudging\n\
             # whatever the channel already had.\n\
             {}\n\n\
             # raw NRPN (MSB {:#04x}): {}\n",
            self.program,
            if self.lead_bank {
                "lead (CC0=1)"
            } else {
                "main (CC0=0)"
            },
            named.join("  "),
            py.join("\n"),
            AMP_NRPN_MSB,
            KNOBS
                .iter()
                .map(|k| format!("{}:{}", k.idx, self.vals[k.idx as usize]))
                .collect::<Vec<_>>()
                .join(" "),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn knob_triple_is_the_authoring_sequence() {
        // CC99 = block, CC98 = index, CC6 = value — the order engine.rs requires
        // (the select must precede the data entry, or the latch is not live).
        assert_eq!(
            Rig::knob_bytes(3, 5, 100),
            [0xB3, 99, 0x30, 0xB3, 98, 5, 0xB3, 6, 100]
        );
    }

    #[test]
    fn rig_bytes_set_bank_before_program() {
        let r = Rig {
            program: 30,
            lead_bank: true,
            vals: [NEUTRAL; 6],
        };
        let b = r.bytes(0);
        assert_eq!(&b[0..3], &[0xB0, 0, 1], "bank select first");
        assert_eq!(&b[3..5], &[0xC0, 30], "then program change");
        assert_eq!(b.len(), 5 + 6 * 9);
    }

    #[test]
    fn export_names_every_knob() {
        let r = Rig::default();
        let s = r.export();
        assert!(s.contains("GM29"), "{s}");
        for k in KNOBS {
            assert!(
                s.contains(&k.name.replace(' ', "")),
                "missing {} in {s}",
                k.name
            );
        }
    }

    /// Read the exported snippet back as MIDI, exactly as pasting it into an album would.
    ///
    /// Only lines that actually call the `Score` API are executed; `CH` stands in for a
    /// real channel and `BEAT` is ignored, since it sets an event's TIME and not its
    /// bytes. Every such line must parse — an unrecognised call is a hard failure, not a
    /// skip, because a line the parser quietly ignored is a line this oracle does not
    /// check.
    fn snippet_to_midi(export: &str, ch: u8) -> Vec<u8> {
        let num = |s: &str| -> u8 {
            let s = s.trim();
            let v = match s.strip_prefix("0x") {
                Some(h) => u32::from_str_radix(h, 16).ok(),
                None => s.parse::<u32>().ok(),
            }
            .unwrap_or_else(|| panic!("snippet argument {s:?} is not a number"));
            u8::try_from(v).unwrap_or_else(|_| panic!("snippet argument {s} exceeds a byte"))
        };
        let mut out = Vec::new();
        let mut seen = 0usize;
        for raw in export.lines() {
            let line = raw.trim();
            if !line.starts_with("sc.") {
                continue;
            }
            seen += 1;
            let code = line.split('#').next().unwrap().trim();
            let (call, rest) = code.split_once('(').expect("a Score call opens a paren");
            let args = rest
                .trim_end()
                .strip_suffix(')')
                .expect("a Score call closes its paren");
            let a: Vec<&str> = args.split(',').map(str::trim).collect();
            assert_eq!(a[0], "CH", "channel placeholder missing in {code:?}");
            assert_eq!(
                *a.last().unwrap(),
                "BEAT",
                "beat placeholder missing in {code:?}"
            );
            match call {
                "sc.cc" => {
                    assert_eq!(a.len(), 4, "Score.cc takes (ch, num, val, beat): {code:?}");
                    out.extend_from_slice(&[0xB0 | ch, num(a[1]), num(a[2])]);
                }
                "sc.program" => {
                    assert_eq!(a.len(), 3, "Score.program takes (ch, prog, beat): {code:?}");
                    out.extend_from_slice(&[0xC0 | ch, num(a[1])]);
                }
                other => panic!("snippet calls {other}, which the album Score API does not have"),
            }
        }
        assert_eq!(
            seen,
            export.matches("sc.").count(),
            "some `sc.` call is not on a line of its own, so the parser skipped it"
        );
        out
    }

    /// MM-BUG-KILN-00077: the Copy Settings snippet must actually author this rig.
    ///
    /// It used to emit `amp(idx, val)` — a helper that exists in no album engine — so the
    /// advertised "engine.py" code raised `NameError`, and it carried neither the score,
    /// the channel, nor the beat. The old test checked knob NAMES and prose only, which is
    /// why an unusable export passed it.
    ///
    /// This reads the snippet back as MIDI and requires it to equal [`Rig::bytes`] byte for
    /// byte — the same bytes the live audition sends — so the pasted album and the tool
    /// cannot disagree about what the rig is. Swept over all four program/bank
    /// combinations and several knob states including both extremes, because the bank flag
    /// and the program are exactly what a single hand-checked case would have fixed.
    #[test]
    fn export_snippet_reproduces_the_rig_bytes() {
        let knob_states: [[u8; 6]; 5] = [
            [NEUTRAL; 6],
            [0; 6],
            [127; 6],
            [0, 127, NEUTRAL, 1, 126, 64],
            [72, 40, 100, 64, 12, 90],
        ];
        for program in [29u8, 30] {
            for lead_bank in [false, true] {
                for vals in knob_states {
                    let r = Rig {
                        program,
                        lead_bank,
                        vals,
                    };
                    for ch in [0u8, 1, 9, 15] {
                        let parsed = snippet_to_midi(&r.export(), ch);
                        assert_eq!(
                            parsed,
                            r.bytes(ch),
                            "GM{program} lead_bank={lead_bank} vals={vals:?} ch={ch}: the \
                             pasted snippet does not author the rig the tool auditioned.\n\
                             export:\n{}",
                            r.export()
                        );
                    }
                }
            }
        }
    }
}
