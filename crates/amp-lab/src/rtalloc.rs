//! Test-only allocation counter for the audio callback.
//!
//! The lab's design contract is "no allocation on the audio thread after setup"
//! (MM-BUG-KILN-00082). That is not something source review can settle — the callback
//! runs through `RealtimeSynth` and `EngineCore`, and what allocates depends on retained
//! capacity, not on what the code looks like. So this counts.
//!
//! A `#[global_allocator]` sees every allocation in the test binary, which would be
//! useless noise. The counter is therefore ARMED per thread, around the measured region
//! only, so a parallel test harness cannot contaminate a measurement.
//!
//! The thread-local cells use `const` initialisers deliberately: a `thread_local!` with a
//! destructor registers one on first touch, and that registration allocates — inside the
//! allocator we are measuring.

use std::alloc::{GlobalAlloc, Layout, System};
use std::cell::Cell;

thread_local! {
    static ARMED: Cell<bool> = const { Cell::new(false) };
    static COUNT: Cell<usize> = const { Cell::new(0) };
}

pub struct Counting;

unsafe impl GlobalAlloc for Counting {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        bump();
        unsafe { System.alloc(layout) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        bump();
        unsafe { System.alloc_zeroed(layout) }
    }

    /// Counted separately from `alloc` on purpose: a `Vec` outgrowing its capacity
    /// reallocs, and that is exactly the "later command bursts exceed retained capacity"
    /// case this exists to catch.
    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        bump();
        unsafe { System.realloc(ptr, layout, new_size) }
    }
}

fn bump() {
    // `try_with` because a thread tearing down may have destroyed its TLS already.
    let _ = ARMED.try_with(|armed| {
        if armed.get() {
            let _ = COUNT.try_with(|c| c.set(c.get() + 1));
        }
    });
}

/// Count the allocations `f` makes on this thread.
pub fn measure<T>(f: impl FnOnce() -> T) -> (T, usize) {
    COUNT.with(|c| c.set(0));
    ARMED.with(|a| a.set(true));
    let out = f();
    ARMED.with(|a| a.set(false));
    (out, COUNT.with(|c| c.get()))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The counter must be able to say a non-zero number, or every "0 allocations"
    /// result below it is vacuous.
    #[test]
    fn the_counter_sees_a_known_allocation() {
        let (v, allocs) = measure(|| vec![0u8; 4096]);
        assert_eq!(v.len(), 4096);
        assert!(allocs >= 1, "counter missed an obvious Vec allocation");
        let (_, quiet) = measure(|| 2 + 2);
        assert_eq!(quiet, 0, "counter fires when nothing allocates");
    }
}
