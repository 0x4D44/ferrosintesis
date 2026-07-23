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
    pub fn export(&self) -> String {
        let named: Vec<String> = KNOBS
            .iter()
            .map(|k| format!("{}={}", k.name.replace(' ', ""), self.vals[k.idx as usize]))
            .collect();
        let py: Vec<String> = KNOBS
            .iter()
            .filter(|k| self.vals[k.idx as usize] != NEUTRAL)
            .map(|k| {
                format!(
                    "    amp({}, {})  # {}",
                    k.idx, self.vals[k.idx as usize], k.name
                )
            })
            .collect();
        format!(
            "GM{} {} bank   {}\n\n\
             # engine.py — author this rig on the guitar channel:\n\
             {}\n\n\
             # raw NRPN (MSB {:#04x}): {}\n",
            self.program,
            if self.lead_bank {
                "lead (CC0=1)"
            } else {
                "main (CC0=0)"
            },
            named.join("  "),
            if py.is_empty() {
                "    # (all knobs neutral — this is the shipped voicing)".to_string()
            } else {
                py.join("\n")
            },
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
    fn export_names_every_knob_and_flags_neutral() {
        let r = Rig::default();
        let s = r.export();
        assert!(s.contains("GM29"), "{s}");
        assert!(s.contains("shipped voicing"), "{s}");
        for k in KNOBS {
            assert!(
                s.contains(&k.name.replace(' ', "")),
                "missing {} in {s}",
                k.name
            );
        }
    }
}
