//! A lock-free single-producer / single-consumer command ring.
//!
//! The UI thread produces, the audio thread consumes. Nothing here allocates,
//! locks or blocks, which is the whole point: a `Mutex` shared with a repainting
//! UI thread is the standard way to get audible dropouts.
//!
//! Hand-rolled on `std` atomics because a fixed-size queue of a small `Copy` enum
//! does not justify a dependency, and the realtime path is worth keeping short
//! enough to audit by eye.

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

/// What the UI can ask the audio thread to do.
///
/// Knobs, program and bank changes all travel as `Midi` — the exact bytes an
/// album would author — so the lab cannot drift from what a `.mid` produces.
/// Only the things that are genuinely not MIDI get their own variant.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Cmd {
    Midi(u8),
    Solo(bool),
    Play(bool),
    Panic,
}

const CAP: usize = 4096; // power of two; ~1300 three-byte CC messages

pub struct Ring {
    buf: Box<[std::cell::UnsafeCell<Cmd>]>,
    head: AtomicUsize, // producer writes
    tail: AtomicUsize, // consumer reads
}

// SAFETY: the head/tail protocol below gives the producer exclusive access to the
// slot at `head` and the consumer exclusive access to the slot at `tail`, and the
// two indices never designate the same slot at the same time (the queue is full
// at CAP-1 entries, so head never catches tail).
unsafe impl Send for Ring {}
unsafe impl Sync for Ring {}

impl Ring {
    /// Create the producer/consumer pair, like `mpsc::channel`.
    pub fn channel() -> (Producer, Consumer) {
        let buf = (0..CAP)
            .map(|_| std::cell::UnsafeCell::new(Cmd::Panic))
            .collect::<Vec<_>>()
            .into_boxed_slice();
        let ring = Arc::new(Ring {
            buf,
            head: AtomicUsize::new(0),
            tail: AtomicUsize::new(0),
        });
        (Producer(ring.clone()), Consumer(ring))
    }
}

pub struct Producer(Arc<Ring>);
pub struct Consumer(Arc<Ring>);

impl Producer {
    /// Push one command. Returns false if the ring is full (dropped rather than
    /// blocked — the UI must never wait on the audio thread).
    pub fn push(&self, c: Cmd) -> bool {
        let r = &*self.0;
        let head = r.head.load(Ordering::Relaxed);
        let next = (head + 1) % CAP;
        if next == r.tail.load(Ordering::Acquire) {
            return false; // full
        }
        // SAFETY: we are the only producer, and `head` is not readable by the
        // consumer until the `Release` store below publishes it.
        unsafe { *r.buf[head].get() = c };
        r.head.store(next, Ordering::Release);
        true
    }

    /// Push a whole MIDI message, all-or-nothing, so a CC can never be torn
    /// across a full-ring boundary and leave the parser mid-message.
    pub fn push_midi(&self, bytes: &[u8]) -> bool {
        let r = &*self.0;
        let head = r.head.load(Ordering::Relaxed);
        let tail = r.tail.load(Ordering::Acquire);
        let used = (head + CAP - tail) % CAP;
        if CAP - 1 - used < bytes.len() {
            return false;
        }
        for &b in bytes {
            self.push(Cmd::Midi(b));
        }
        true
    }
}

impl Consumer {
    /// Pop one command, or None if empty. Called only from the audio thread.
    pub fn pop(&self) -> Option<Cmd> {
        let r = &*self.0;
        let tail = r.tail.load(Ordering::Relaxed);
        if tail == r.head.load(Ordering::Acquire) {
            return None;
        }
        // SAFETY: we are the only consumer, and the producer will not overwrite
        // this slot until we publish the new tail below.
        let c = unsafe { *r.buf[tail].get() };
        r.tail.store((tail + 1) % CAP, Ordering::Release);
        Some(c)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_in_order() {
        let (p, c) = Ring::channel();
        for i in 0..100u8 {
            assert!(p.push(Cmd::Midi(i)));
        }
        for i in 0..100u8 {
            assert_eq!(c.pop(), Some(Cmd::Midi(i)));
        }
        assert_eq!(c.pop(), None);
    }

    #[test]
    fn reports_full_rather_than_blocking() {
        let (p, _c) = Ring::channel();
        let mut n = 0;
        while p.push(Cmd::Panic) {
            n += 1;
            assert!(n <= CAP, "push never reported full");
        }
        assert_eq!(n, CAP - 1);
    }

    #[test]
    fn midi_messages_are_all_or_nothing() {
        let (p, c) = Ring::channel();
        while p.push(Cmd::Panic) {} // fill
        assert!(
            !p.push_midi(&[0xB0, 99, 0x30]),
            "torn message into a full ring"
        );
        // drain two slots — still not enough for a 3-byte message
        c.pop();
        c.pop();
        assert!(!p.push_midi(&[0xB0, 99, 0x30]));
        c.pop();
        assert!(p.push_midi(&[0xB0, 99, 0x30]));
    }
}
