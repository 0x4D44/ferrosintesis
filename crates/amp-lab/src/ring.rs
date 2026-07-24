//! A lock-free single-producer / single-consumer command ring.
//!
//! The UI thread produces, the audio thread consumes. Nothing here allocates,
//! locks or blocks, which is the whole point: a `Mutex` shared with a repainting
//! UI thread is the standard way to get audible dropouts.
//!
//! Hand-rolled on `std` atomics because a fixed-size queue of a small `Copy` enum
//! does not justify a dependency, and the realtime path is worth keeping short
//! enough to audit by eye.

use std::cell::Cell;
use std::marker::PhantomData;
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
        (
            Producer(ring.clone(), PhantomData),
            Consumer(ring, PhantomData),
        )
    }
}

/// The write end. `Send` (it is handed to whichever thread produces) but
/// deliberately **not** `Sync`.
///
/// `Ring`'s `unsafe impl Sync` is sound only under a genuine single-producer /
/// single-consumer discipline, and nothing but this marker enforces it. Without it,
/// `Producer` inherited `Sync` from its `Arc<Ring>`, so safe code could share
/// `&Producer` across scoped threads or an `Arc<Producer>`: two `push()` calls would
/// load the same head, both pass the capacity check and both write the same
/// `UnsafeCell<Cmd>` — a data race, and undefined behaviour, reachable without a single
/// `unsafe` block at the call site (MM-BUG-KILN-00080).
///
/// `PhantomData<Cell<()>>` is the marker of choice because `Cell` is exactly "`Send`,
/// never `Sync`". Taking `&mut self` on the push methods would also work, but it would
/// push exclusive ownership through every caller to state something the type system can
/// say once, here.
pub struct Producer(Arc<Ring>, PhantomData<Cell<()>>);

/// The read end. `Send`, not `Sync`, for the mirror-image reason: two concurrent
/// `pop()` calls could claim the same tail, letting the producer reuse a slot while
/// another reader is still reading it.
pub struct Consumer(Arc<Ring>, PhantomData<Cell<()>>);

/// Compile-time proof of the endpoints' auto-traits: `Send`, and **not** `Sync`.
///
/// This cannot be a runtime test. The contract is that a program which shares an
/// endpoint across threads must FAIL TO COMPILE, and a test that runs has already
/// compiled. If someone later adds a field that reintroduces `Sync` — or deletes the
/// `PhantomData` as an unused-looking marker — the build stops here rather than in a
/// data race nobody can reproduce.
mod auto_traits {
    use super::{Consumer, Producer};
    use std::marker::PhantomData;

    const fn assert_send<T: Send>() {}

    /// Asserting a NEGATIVE bound needs an inversion: `NOT_SYNC` is `true` from the
    /// blanket trait impl, and `false` for `T: Sync`, because an inherent associated
    /// const shadows a trait one when its bound is satisfied.
    struct IsSync<T>(PhantomData<T>);
    trait NotSyncFallback {
        const NOT_SYNC: bool = true;
    }
    impl<T> NotSyncFallback for IsSync<T> {}
    impl<T: Sync> IsSync<T> {
        const NOT_SYNC: bool = false;
    }

    const _: () = assert_send::<Producer>();
    const _: () = assert_send::<Consumer>();
    const _: () = assert!(
        IsSync::<Producer>::NOT_SYNC,
        "Producer is Sync: safe code can now share the write end across threads, and \
         two concurrent push() calls race on the same slot"
    );
    const _: () = assert!(
        IsSync::<Consumer>::NOT_SYNC,
        "Consumer is Sync: safe code can now share the read end across threads, and two \
         concurrent pop() calls can claim the same slot"
    );
    /// Positive control. Without it the two assertions above would still pass if the
    /// inversion silently stopped working and `NOT_SYNC` were always `true`.
    const _: () = assert!(
        !IsSync::<u32>::NOT_SYNC,
        "the !Sync assertions are vacuous — the inversion no longer detects a Sync type"
    );
}

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

    /// How many more commands the ring can accept right now.
    ///
    /// Lets a caller preflight a multi-command snapshot as one unit — push it only when
    /// the WHOLE thing fits, so it can never be partially applied
    /// (MM-BUG-KILN-00083). Like the `push_midi` preflight, it is a lower bound from the
    /// producer's view: the consumer can only make room, never take it.
    pub fn free(&self) -> usize {
        let r = &*self.0;
        let head = r.head.load(Ordering::Relaxed);
        let tail = r.tail.load(Ordering::Acquire);
        let used = (head + CAP - tail) % CAP;
        CAP - 1 - used
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

    /// The endpoints still cross threads in the shape the app actually uses: the
    /// consumer is MOVED to the audio thread while the producer stays on the UI
    /// thread. `!Sync` must forbid SHARING an endpoint, not moving one — a marker
    /// that broke this would break the lab.
    #[test]
    fn one_endpoint_per_thread_still_works() {
        let (p, c) = Ring::channel();
        let reader = std::thread::spawn(move || {
            let mut got = Vec::new();
            while got.len() < 200 {
                if let Some(cmd) = c.pop() {
                    got.push(cmd);
                }
            }
            got
        });
        let mut sent = 0u32;
        while sent < 200 {
            if p.push(Cmd::Midi((sent % 128) as u8)) {
                sent += 1;
            }
        }
        let got = reader.join().expect("consumer thread");
        assert_eq!(got.len(), 200);
        for (i, cmd) in got.iter().enumerate() {
            assert_eq!(*cmd, Cmd::Midi((i % 128) as u8), "out of order at {i}");
        }
    }

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
