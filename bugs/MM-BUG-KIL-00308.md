# MM-BUG-KIL-00308 — drumkit2 inventory oracles cannot detect a take permutation: names never bound to file bytes

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / drumkit2 test oracles
- **Raised:** 2026-08-19T09:33:20Z
- **Discovery source:** Agent
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-19T09:33:20Z, raised via `deltic bugs new`)

## Observation

No drumkit2 oracle ties an embedded NAME to the bytes of the file it names, so a
permutation of `include_bytes!` paths inside one articulation survives the whole
suite.

Static mutation: swap the paths on `crates/ferrosintesis-samples-drumkit2/src/lib.rs:32`
and `lib.rs:96`, so the entry named `china_vl1_rr1.flac` embeds
`../samples/china_vl5_rr1.flac` and vice versa. Walk-through:
- `inventory_matches_packaged_samples` (lib.rs:355) compares name *sets* against
  the directory; names are untouched.
- `every_sample_is_a_nonempty_bank_file_with_the_expected_size` (lib.rs:418): the
  aggregate sum is permutation-invariant, and line 429's
  `assert_eq!(get(name), Some(bytes))` compares each row with a lookup of that same
  row — true by construction.
- `every_bank_take_resolves_through_this_crates_source` (lib.rs:515) checks
  `SAMPLES[index].0 == name` and pointer identity through the same table — indices
  and names are untouched.
- `decoded_banks_are_valid_audio` (lib.rs:489) bounds duration and peak; both takes
  are healthy china recordings and pass.

Result: the softest china velocity layer plays the hardest recording and vice
versa, with every test green — on a box with no ears. The repo has already
recognised this class for pitch-named zones (MM-BUG-KILN-00201: "one AGGREGATE byte
size … the payloads are interchangeable"); drum takes are velocity-named rather
than pitch-named, so that fix does not cover them. `LaVoice` doctrine says velocity
layers encode timbre, so a layer swap is an audible timbre inversion, not a level
change. False-green oracle defect; the current table is correct (verified by name
today, and the sibling KILN-00201-style check does not exist here).

## Fix

Bind name to content where the directory is already enumerated:
in `inventory_matches_packaged_samples`, add per-entry
`assert_eq!(fs::read(samples_dir.join(name)).unwrap(), *bytes)`. That is derived
(no second hand-written list), works in the published package (`samples/**` ships),
and — since the 36 file lengths are distinct — also subsumes what the aggregate pin
catches for table-side swaps. An asset-side swap where the bake writes takes to the
wrong paths remains out of scope unless a per-take content statistic is added;
verify any such statistic (e.g. layer-brightness monotonicity) against the real
banks before pinning it. Prove the new assertion fails on the mutation above, then
restore. The same binding is worth porting to the sibling crate's inventory test.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Estimated effort: Small.
