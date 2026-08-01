//! The UI's write side of the command ring, with convergence guarantees.
//!
//! The ring drops commands when it is full — correctly, because the UI must never block
//! on the audio thread. But every call site used to ignore that, so a transient audio
//! stall (the ring backing up, then draining) could leave the heard synth on a stale rig
//! while the UI showed the new one, with no path back to agreement (MM-BUG-KILN-00083).
//!
//! `Outbox` closes that gap without changing the realtime side. The UI already repaints
//! continuously, so the fix is convergence, not reliability of a single push:
//!
//! - Every failed enqueue sets a `dirty` flag.
//! - [`Outbox::pump`], called once per frame, resends the COMPLETE latest state as one
//!   atomic snapshot whenever `dirty` is set, and clears it only when the whole snapshot
//!   lands. So after any stall the audio thread converges to exactly what the UI shows.
//! - Panic has its own pending flag, retried ahead of the snapshot: a dropped
//!   all-notes-off is a stuck note, which is worse than a stale knob.
//!
//! Factored out of the egui `App` (which cannot be constructed in a test) exactly as
//! `Core` was factored out of the cpal closure, so the convergence logic is testable with
//! a real [`Ring`](crate::ring) pair.

use crate::amp::Rig;
use crate::ring::{Cmd, Producer};

pub struct Outbox {
    tx: Producer,
    ch: u8,
    /// The audio thread may not reflect the latest UI state — resend on the next pump.
    dirty: bool,
    /// A panic was requested but did not fit — keep trying until it lands.
    panic_pending: bool,
    /// Latched for the UI to surface; cleared once everything has been delivered.
    saturated: bool,
}

impl Outbox {
    pub fn new(tx: Producer, ch: u8) -> Self {
        Outbox {
            tx,
            ch,
            dirty: false,
            panic_pending: false,
            saturated: false,
        }
    }

    /// Record the outcome of an enqueue: any drop means the audio thread is now behind.
    fn observe(&mut self, ok: bool) {
        if !ok {
            self.dirty = true;
            self.saturated = true;
        }
    }

    /// Send one knob's triple (the cheap incremental path). A miss marks dirty, so the
    /// next [`pump`](Self::pump) resends the whole rig rather than losing this edit.
    pub fn send_knob(&mut self, rig: &Rig, idx: u8) {
        let ok = self
            .tx
            .push_midi(&Rig::knob_bytes(self.ch, idx, rig.vals[idx as usize]));
        self.observe(ok);
    }

    /// Send the whole rig (a voice change rebuilds the insert, so everything re-sends).
    pub fn send_rig(&mut self, rig: &Rig) {
        let ok = self.tx.push_midi(&rig.bytes(self.ch));
        self.observe(ok);
    }

    /// Transport / solo are STATE, so they ride the snapshot: a miss just marks dirty and
    /// `pump` re-establishes the correct play/solo along with the rig.
    pub fn send_cmd(&mut self, c: Cmd) {
        let ok = self.tx.push(c);
        self.observe(ok);
    }

    /// Request panic (all-notes-off). Retried every frame until it lands.
    pub fn request_panic(&mut self) {
        if !self.tx.push(Cmd::Panic) {
            self.panic_pending = true;
            self.saturated = true;
        }
    }

    /// True while the audio thread has not yet caught up — the UI shows this so a dropped
    /// command is never silent.
    pub fn saturated(&self) -> bool {
        self.saturated
    }

    /// Reconcile the audio thread to the current UI state. Call once per frame.
    ///
    /// Panic first (safety), then the state snapshot. The ring publishes the snapshot
    /// with one head update, so the audio thread never sees a half-applied rig (the A/B
    /// "partial recall" the bug describes). When everything is delivered, `dirty` and
    /// `saturated` clear together.
    pub fn pump(&mut self, rig: &Rig, playing: bool, solo: bool) {
        if self.panic_pending && self.tx.push(Cmd::Panic) {
            self.panic_pending = false;
        }

        if !self.dirty {
            self.saturated = self.panic_pending;
            return;
        }

        // Rig bytes + Play + Solo, written behind the unpublished head and made visible
        // by one Release store.
        let rig_bytes = rig.bytes(self.ch);
        let mut snapshot = Vec::with_capacity(rig_bytes.len() + 2);
        snapshot.extend(rig_bytes.into_iter().map(Cmd::Midi));
        snapshot.extend([Cmd::Play(playing), Cmd::Solo(solo)]);
        if self.tx.push_batch(&snapshot) {
            self.dirty = false;
        }
        self.saturated = self.dirty || self.panic_pending;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ring::{Consumer, Ring};

    const CH: u8 = 1;

    /// Drain everything the consumer can see into a flat command list.
    fn drain(rx: &Consumer) -> Vec<Cmd> {
        let mut out = Vec::new();
        while let Some(c) = rx.pop() {
            out.push(c);
        }
        out
    }

    /// The audio thread's rig, reconstructed from the MIDI byte stream the outbox sent.
    /// Returns (program-ish last CC map, play, solo) — enough to compare end states.
    fn apply(cmds: &[Cmd]) -> (Vec<u8>, Option<bool>, Option<bool>) {
        let (mut midi, mut play, mut solo) = (Vec::new(), None, None);
        for c in cmds {
            match c {
                Cmd::Midi(b) => midi.push(*b),
                Cmd::Play(p) => play = Some(*p),
                Cmd::Solo(s) => solo = Some(*s),
                Cmd::Panic => {}
            }
        }
        (midi, play, solo)
    }

    /// Fill the ring to near-full so the next pushes are dropped, leaving `room` slots.
    fn saturate(tx: &Producer, leave: usize) {
        while tx.free() > leave {
            assert!(tx.push(Cmd::Midi(0x00)));
        }
    }

    #[test]
    fn a_dropped_knob_edit_is_recovered_on_the_next_pump() {
        let (p, c) = Ring::channel();
        let mut ob = Outbox::new(p, CH);
        let mut rig = Rig::default();

        // Saturate, then edit a knob: the edit is dropped and the outbox knows.
        saturate(&ob.tx, 2);
        rig.vals[0] = 99;
        ob.send_knob(&rig, 0);
        assert!(ob.saturated(), "a dropped edit must be visible to the UI");

        // The audio thread drains (recovery).
        let _ = drain(&c);

        // One pump after recovery re-establishes the full latest state.
        ob.pump(&rig, true, false);
        let (midi, _, _) = apply(&drain(&c));
        assert!(
            midi.windows(3).any(|w| w[2] == 99),
            "the recovered rig does not carry the latest knob value: {midi:?}"
        );
        assert!(!ob.saturated(), "state converged, so saturation must clear");
    }

    #[test]
    fn an_ab_recall_is_never_half_applied() {
        let (p, c) = Ring::channel();
        let mut ob = Outbox::new(p, CH);

        // Room for only part of a rig snapshot.
        saturate(&ob.tx, 4);
        let recalled = Rig {
            program: 30,
            vals: [10, 20, 30, 40, 50, 60],
            ..Rig::default()
        };
        ob.send_rig(&recalled);

        // Before recovery: nothing partial reached the audio thread beyond the filler.
        let pre = drain(&c);
        let leaked = pre.iter().filter(|c| **c != Cmd::Midi(0x00)).count();
        assert_eq!(leaked, 0, "a partial rig leaked through the saturated ring");

        // Recovery + pump delivers the WHOLE rig at once.
        ob.pump(&recalled, true, false);
        let (midi, _, _) = apply(&drain(&c));
        assert_eq!(
            midi,
            recalled.bytes(CH),
            "the recalled rig was not delivered whole"
        );
    }

    #[test]
    fn panic_is_retried_until_it_lands() {
        let (p, c) = Ring::channel();
        let mut ob = Outbox::new(p, CH);

        saturate(&ob.tx, 0); // completely full
        ob.request_panic();
        assert!(ob.saturated());
        assert!(
            ob.panic_pending,
            "panic into a full ring must be held, not lost"
        );

        // Drain (recovery), then pump: the held panic goes out.
        let _ = drain(&c);
        ob.pump(&Rig::default(), true, false);
        assert!(
            drain(&c).contains(&Cmd::Panic),
            "a pending panic was never retried"
        );
        assert!(!ob.panic_pending, "panic delivered, flag must clear");
    }

    #[test]
    fn the_happy_path_sends_immediately_and_stays_clean() {
        let (p, c) = Ring::channel();
        let mut ob = Outbox::new(p, CH);
        let mut rig = Rig::default();
        rig.vals[2] = 77;
        ob.send_knob(&rig, 2);
        assert!(
            !ob.saturated(),
            "an uncontended send must not report saturation"
        );
        let (midi, _, _) = apply(&drain(&c));
        assert!(midi.windows(3).any(|w| w[2] == 77));
        // A pump with nothing pending is a no-op.
        ob.pump(&rig, true, false);
        assert!(
            drain(&c).is_empty(),
            "pump sent something with nothing dirty"
        );
    }
}
