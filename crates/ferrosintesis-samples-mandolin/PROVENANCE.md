# Provenance — ferrosintesis-samples-mandolin

## Packaged family inventory

| Family | Files |
|--------|------:|
| `mandolin_*` | 40 |

`mandolin_*.wav` — owner-recorded mandolin pluck onsets, recorded by the repository owner on
**2026-07-24** on his own instrument, dedicated **CC0 1.0 Universal** (public domain). The owner
holds the recording and grants it to the public domain; no third-party licence applies.

## Source

One continuous take, `DR0000_0202.wav` (24-bit / 48 kHz stereo, 2:40, 44.1 MB), **zero clipped
samples**. Ten fretboard positions, four takes each. Where a note was fluffed the owner replayed
all four, so **the last four takes of each note are the keepers**. The raw take is not committed
(44 MB, owner-personal); the trimmed per-note cuts in
`tools/ferrosintesis-samples/mandolin-src/` are the committed input, and `samples/*.wav` here is
the baked output.

A first session (`DR0000_0198`, 2026-07-23) captured three dynamic passes instead. It was
superseded: see "Why round robins and not dynamics" below.

## Positions

Ten zones from three hand positions, chosen so no two coincide in pitch — the courses are a
fifth apart and the frets a semitone, so open/5th and 10th/12th never collide, whereas the 7th
fret would have duplicated the next open string exactly.

| Zone | Course / fret | Nominal | rr1 | rr2 | rr3 | rr4 |
|------|---------------|---------|-----|-----|-----|-----|
| G3 | G open  |  196.00 |  195.57 |  195.74 |  195.84 |  195.61 |
| C4 | G 5th   |  261.63 |  264.95 |  264.82 |  264.59 |  264.64 |
| D4 | D open  |  293.66 |  292.93 |  292.65 |  293.03 |  293.33 |
| G4 | D 5th   |  392.00 |  394.37 |  395.11 |  394.68 |  394.98 |
| A4 | A open  |  440.00 |  440.41 |  439.28 |  440.40 |  439.17 |
| D5 | A 5th   |  587.33 |  591.60 |  591.17 |  591.36 |  590.84 |
| E5 | E open  |  659.26 |  658.52 |  656.88 |  657.51 |  656.93 |
| A5 | E 5th   |  880.00 |  883.17 |  883.72 |  882.60 |  883.22 |
| D6 | E 10th  | 1174.66 | 1182.91 | 1181.88 | 1181.48 | 1181.42 |
| E6 | E 12th  | 1318.51 | 1328.92 | 1328.13 | 1327.97 | 1327.72 |

Roots are **measured, not nominal**. The open strings are in tune (within a few cents) but the
fretted notes run sharp — up to **+22 cents at the 5th fret on the thickest course** — which is
normal fretting-pressure behaviour on a short-scale instrument. `LaVoice` repitches from the
measured root, so the bank plays in tune regardless. Take-to-take spread within a zone is
~2–5 cents: the same note played four times, not four different notes.

## Round robins

**Four takes per zone, one dynamic.** `rr1` is the earliest of the four and the order is
meaningful — the takes were played with alternating pick direction, so cycling them strictly
(never randomly) reproduces a real player's down/up alternation. The engine selects with a
per-`(channel, key)` strike counter, so consecutive strikes of the same key step
0→1→2→3→0… deterministically.

### Why round robins and not dynamics

A mandolin cannot be played at meaningfully different dynamics — the owner's own finding, and
the first session's three-pass recording confirmed it numerically: the loud and normal passes'
spectral centroids were indistinguishable (6/10 sign consistency across the ten zones, median
shift +0.09 harmonics — a coin flip). The soft/loud split was weak but real (8/10, median +0.56
harmonics, sign test p≈0.055). Spending the recording budget on take variety rather than dynamic
layers was therefore the better trade for this instrument.

## Processing (one-time, deterministic)

1. Locate each note by onset detection; identify its pitch by a matched harmonic comb with a
   **sub-harmonic veto** *and* a **missing-fundamental (octave-up) correction**. Both are
   load-bearing here: five of the ten zones are octave pairs, and a small mandolin body barely
   radiates the low G3 fundamental, so its 2nd harmonic dominates and the note reads as G4. The
   plain sub-harmonic veto cannot catch that — there is nothing at f0/2 to detect when the
   fundamental is *missing*. The tell is energy at the candidate's **odd-half-harmonics**
   (1.5× and 2.5× f0), which are the octave-below note's 3rd and 5th harmonics.
2. Per zone, keep the **last four credible** takes. "Credible" excludes anything more than 15 dB
   below that note's own strongest take (fret squeak, handling, quiet fluffs). Each onset's level
   is measured in a window that **ends before the next onset** — a fixed window lets a quiet
   onset absorb a following loud pluck's level and masquerade as a real take.
3. Re-anchor each keeper onto the loudest attack within 0.35 s. The onset detector's 0.176 s
   refractory can hide the real pluck behind a quiet precursor, which would otherwise bury a
   +40 dB attack ~0.17 s inside the sample.
4. Downmix to mono, resample 48 kHz → 44.1 kHz (64-tap Blackman-windowed sinc, cutoff at the
   output Nyquist), dither to 16-bit (TPDF). No normalisation at this stage.
5. `prepare.py --only=mandolin` then trims to onset, keeps 0.9 s, applies the squared fade-out,
   peak-normalises to 0.9 and measures the root — the same chain every other onset bank uses.

Every cut is verified before baking: correct note (scored against its octave neighbours), clean
onset and tail, no second attack inside the 0.9 s keep window, no clipping.

## Committed-source checksums

SHA-256 of each committed per-note cut under `tools/ferrosintesis-samples/mandolin-src/`
(MM-REQ-KILN-00029). These are owner-recorded CC0 performances with no third-party licence
obligation, so the hashes are integrity evidence, not licence evidence: the raw take is not
committed, which makes these 40 cuts the irreplaceable master for this bank.

| Source file | SHA-256 |
|-------------|---------|
| `mandolin_A4_rr1.wav` | `f0b0fa3792b6c1544f7f898888fbd88b23e0c14c879520bab926912a2d62d335` |
| `mandolin_A4_rr2.wav` | `30a4f3b28a5ea1768f6a0f48f55e0698c49d1642324760bb463e4db599decdac` |
| `mandolin_A4_rr3.wav` | `49471d7ecd48dd6fd7452b5f8b677484ea71405ea7b5e658451531d7ca29a95d` |
| `mandolin_A4_rr4.wav` | `bd837c1533368ce6745067807125c33977a097f3db12eca58e188eda72802139` |
| `mandolin_A5_rr1.wav` | `a192f705e714f53bd153a0868b6b314fe0c123584db411212bb8f6871da8d8e7` |
| `mandolin_A5_rr2.wav` | `556196c3005245f8a6f5e84c9cc3a79088b1342eea3c7a98554d15901dd4fc8e` |
| `mandolin_A5_rr3.wav` | `e0806ea19516e05075b8acca2e44bfa166d796d9126d202b2cb82ad57f174099` |
| `mandolin_A5_rr4.wav` | `2d6867e6ab32142f5dbe624e83e6dd7dcd36f6c09278f682b2ce2944a6aa1449` |
| `mandolin_C4_rr1.wav` | `6c22cb254877fc51d2e58f61fe89aeac1d36e4c8abe27f081f54cf1afbf0ca20` |
| `mandolin_C4_rr2.wav` | `b06aa07d242de79319487879d7c22f7a285d89a75714cd95aa1d90812dd81142` |
| `mandolin_C4_rr3.wav` | `3caff04092a490eb00f7edf8fd9090c891d0ff62835004b53418ea1c578e24e5` |
| `mandolin_C4_rr4.wav` | `e668ab68d1da49ffed1f6815c41cfe68e9d77fb28011afc1dcd36336d8c92c9a` |
| `mandolin_D4_rr1.wav` | `e0e74cb38a592ed73741fd2179dda36a24a414baeaacdbf92478025b9a943633` |
| `mandolin_D4_rr2.wav` | `a9723b7c5ee83dcd0b3c56ea6ced62e636f599770bdd4cff16320560c1303e10` |
| `mandolin_D4_rr3.wav` | `c84e7ddeb31faecaf097a716f9b66288631d2f64fa5f572ae604c361d3a98faf` |
| `mandolin_D4_rr4.wav` | `23bcf1b5680391223f1ed534f084b01b749fd84fdf96f62806964c201aa66821` |
| `mandolin_D5_rr1.wav` | `304ee19e13b212a49386373974d389ca6052046288eb0979ec056b0feab668b4` |
| `mandolin_D5_rr2.wav` | `7f3a79b023e312b116a612597fd3b54764fa6d6da8ba4dca4b9aa1e7655535ea` |
| `mandolin_D5_rr3.wav` | `bfb4a2f65e02ca0d3b4c1db86dfa081a3bfa681711a0984a3f804234415d1c36` |
| `mandolin_D5_rr4.wav` | `03283bbfe75f64e31fec02fcf73d478e76d8ab5cff59e741a13637b1be68f4e0` |
| `mandolin_D6_rr1.wav` | `c29ef8ded7b804028582395ee79e913b1927454648b464eab5e824125db49ecf` |
| `mandolin_D6_rr2.wav` | `e463d47df29545eaa9a5419a3f514a6b068b87f37c7b9369739f61ee57953e9c` |
| `mandolin_D6_rr3.wav` | `178d6e31a15cbf41e6c74f9cd55f0939648e3bb625cc7f54fc954344eed76360` |
| `mandolin_D6_rr4.wav` | `4a1028f199216c868793c8d0a20072a11740bf85e0dcf738fe4e1f99c1dca732` |
| `mandolin_E5_rr1.wav` | `c585766f0a455ecda86cfd896a400010f06146562840a06ddd2d478216c33e5a` |
| `mandolin_E5_rr2.wav` | `8349e582e5edf1e9ede642485b2f2b34a164d32c4cd8d6d3830f166ccb9e5d0a` |
| `mandolin_E5_rr3.wav` | `b29899ef836188ca5d89be4faa762a53564494ea4d11875d026bc81d02d7e12f` |
| `mandolin_E5_rr4.wav` | `dc78d77619b9a36806727fcff60e3938e555bb4a9005c88cad2c4a12a12b8b8d` |
| `mandolin_E6_rr1.wav` | `d7acef320dcc270eba81d4c96f4039e8bb905abe35abe34d9de4010148ccf0da` |
| `mandolin_E6_rr2.wav` | `114d84a62316be6772266f49b8900862931c454caddaa169f565b98e14621991` |
| `mandolin_E6_rr3.wav` | `17bb99408780a613834c098c6acc7b647e87f7d4ec7285ec6009817d5becf9d9` |
| `mandolin_E6_rr4.wav` | `5f7a3ea18acdf3814945e19e2484bda2a580ff4b8b0a309c14674e52778e53f6` |
| `mandolin_G3_rr1.wav` | `70a0b59f4e77c0dd34098ed7249bccf9505249982b1d20372a6ab362561a23f8` |
| `mandolin_G3_rr2.wav` | `482b40af5b1d8359edf1426e8a5d97e7e2f63ee562d4dfa75007f3ea31dc27a5` |
| `mandolin_G3_rr3.wav` | `8c247018279ac6aa5f22b1730fd6f3881779c46a904082c4946c6aafd70d6d88` |
| `mandolin_G3_rr4.wav` | `169c093937ebcc54110b299fb0ece9574979795261bb52328f6a9cf4a3a494ed` |
| `mandolin_G4_rr1.wav` | `38cca1aade1f65a4d51cef311d37a7a17f91db26284fdadbf88d97b0c6c0bf92` |
| `mandolin_G4_rr2.wav` | `21d1671af4e071fb5eddbc669a271316e9a647e13196c71453e5f7ca480bd6f4` |
| `mandolin_G4_rr3.wav` | `202851b63bc4df84d922f078f48155a1ea6af0a0dd482a2d50b7d20af14bd83c` |
| `mandolin_G4_rr4.wav` | `1609520c6ab2ad976a8b8f2562ccf91752bdf7e4ac2075a6e30bacc5ce44fb1a` |
