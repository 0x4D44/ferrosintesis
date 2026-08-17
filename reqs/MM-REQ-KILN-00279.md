# MM-REQ-KILN-00279 — Share one loudness-normalization policy across buffered and disk-backed rendering

- **State:** Draft
- **Priority:** Should
- **Area:** ferrosintesis / loudness normalization architecture
- **Raised:** 2026-08-17T09:42:29Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-17T09:42:29Z, raised via `deltic reqs new`)

## Statement

Statement: The ferrosintesis buffered and disk-backed loudness-normalization paths must share one authoritative policy for iteration, target tolerance, gain application, true-peak ceiling enforcement, limiter attack/release configuration, and convergence. Storage-specific traversal may remain separate, but policy decisions and tuning constants must not be reimplemented in engine.rs, loudness.rs, and scratch.rs. A non-vacuous oracle must vary at least one policy parameter or inject an already-on-target over-ceiling signal and prove both adapters make the same decision independently of comparing two copies that can share the same bug.

Rationale: engine.rs:4361-4409 and scratch.rs:147-203 independently implement the normalization loop. loudness.rs:484-489 exposes limiter_config, but the buffered limit_pass at :494-540 recomputes attack/release while scratch.rs:236-254 consumes the helper. scratch.rs:181-186 records that the existing parity test missed MM-BUG-CRUCIBLE-00031 because both implementations shared the same skipped-ceiling defect. This is proven drift risk, not stylistic cleanup.

Proposed effort: Medium-Heavy. Leave acceptance traceability for Gate 1.

## Notes
