# Provenance - ferrosintesis-samples-orchestral2

Every WAV this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

Regenerate non-banjo families with `python3 tools/ferrosintesis-samples/prepare.py
--only=<non-banjo-family>` from the repository root.

Regenerate banjo with:

```powershell
python3 tools/ferrosintesis-samples/banjo_extract.py
```

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `banjo_*` | 24 | 5-string banjo (GM 105) onsets | **Owner-recorded** by Arthur (`samples/banjo/*.opus`), baked by `python3 tools/ferrosintesis-samples/banjo_extract.py` | CC0-1.0 |
| `eastpick_*` | 8 | Eastman E1D steel guitar, picked (GM 25) | **Owner-recorded** (Eastman E1D), committed per-zone cuts | CC0-1.0 |
| `eastpluck_*` | 8 | Eastman E1D steel guitar, plucked | **Owner-recorded** (Eastman E1D), committed per-zone cuts | CC0-1.0 |
| `glock_*` | 4 | Glockenspiel (GM 9) strikes | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `harp_*` | 11 | Harp (GM 46) plucks | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `marimba_*` | 10 | Marimba (GM 12) strikes | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `musicbox_*` | 11 | Music box (GM 10) strikes | Freesound pack **44539** "Hand Crank Music Box B (Notes)" by *moodyfingers* - per-sound table below | CC0-1.0 |
| `ocarina_*` | 3 | Ocarina (GM 79) sustains | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `recorder_*` | 7 | Recorder (GM 74) sustains | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `timpani_*` | 5 | Timpani (GM 47) strikes | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `tubular_*` | 9 | Tubular bells (GM 14) strikes | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `vibes_*` | 10 | Vibraphone (GM 11), soft mallets | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `viola_*` | 14 | Solo viola (GM 41) arco onsets | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `xylo_*` | 8 | Xylophone (GM 13) strikes | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |

## First-party committed-source checksums

SHA-256 pins for the owner-recorded performance archives and committed lossless
zone inputs under the repo-root `samples/` store. The provenance oracle derives
these files from `samples/*/`; adding another recording root or nested cut cannot
silently escape this table.

| Source file | SHA-256 |
|-------------|---------|
| `samples/acoustic-guitar-eastman-e1d/picked.opus` | `35e9e45b42a70f2fada2c9d93bf809d9046562fa3fa40cbac415ef75b92d926d` |
| `samples/acoustic-guitar-eastman-e1d/plucked.opus` | `16f5a8c7cde555441143243f264a03eff142cb8aafb6924236a82755a0396ce0` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_A#3.wav` | `85f06652f4ab43fa0b7f0c9ddb7e008313415af5069bb7d22dd08e1616f71b5d` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_A#4.wav` | `19bfda8712d10fe4eb92beb98f079d480fd46fcf52189999c47a908fc283b697` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_B2.wav` | `842d215bbd10c838c02318bb4862d565a01da21e59169903081df48a2d639373` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_B5.wav` | `f967a5ec2cd85331d0b5ac79b2bbdb20bfe9a46cd1c175a264aa20aee45cb018` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_E2.wav` | `5c4c063a9a27f8289910c5f7926edecc25ff07aaa633bb5d391da0a65316ef74` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_E3.wav` | `fda7798e27ad5e6e86cf55dee98e6b7dd1ae2ce79a7562125eb3c2828091d7e1` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_E4.wav` | `4ee8304d22420b5a15d55cd6d709975feb0cc33984fe74029bedf49baf2d719a` |
| `samples/acoustic-guitar-eastman-e1d/zones/picked_F5.wav` | `7239543f24687ed4378a8c0b2b71f543127f5abb9b936d810b16ef357d58a18c` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_A#2.wav` | `0ccb404059123b7054529b49decccd3f4e36dc9c38db517596b51be40c268575` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_A#3.wav` | `6e16b8cf495d5d0df1a589964cccfa5b249d4a28f43c0f7a5816a3978e03dae0` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_B4.wav` | `303ae094c66ae566edf1dc5c7650b2572f5e2c1e10494b4b3f9ddf64d5d04f23` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_B5.wav` | `180d61d77aae2c72cde8654c3177707a81408a4ccf3e07863e5f58e96c3b4446` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_E2.wav` | `a3d6fb94426726f21f846fde5e03c8417149506b629238eb23ebe9ade1475ff5` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_E3.wav` | `5c9fb1cca4287f5fd15931e2024194b51698e53fe97141c397ddf0bc54aae6b8` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_E4.wav` | `48c7545759708c6a630dce90639085e0ffa4b46a1bf38966cd319721e200ea60` |
| `samples/acoustic-guitar-eastman-e1d/zones/plucked_F5.wav` | `af393deec96e076ca04fb32d11e4ff1361e3492fbc0ec050cdf7864510ce61da` |
| `samples/banjo/banjo-5string-openG-2026-07-23.opus` | `e9f62de0234f2107b14624a8bcf63cf09646b92aecf70bab13543722ca41e56f` |

## GM 10 music box - per-sound licence record

The music box was declared CC0 by a code comment alone. The author's Freesound catalogue
mixes CC0, Attribution and Attribution-NonCommercial, so CC0 was **not** inferable at
account level. All eleven sounds were checked individually on 2026-07-24 and each sound
page states "Creative Commons 0". The record is committed here so the check is never
repeated (MM-BUG-KILN-00069 item 9).

That check no longer rests on someone having read eleven web pages. The pack's bundled
[`_readme_and_license_44539.txt`](../../tools/ferrosintesis-samples/freesound-src/_readme_and_license_44539.txt)
(SHA-256 `3e75a460120b3b5b7a87d3511d7dc1c45e639b189a0884303c2471470d347e08`) is now committed
verbatim, and it states "Creative Commons 0" for all 11 sounds — 11/11, no exceptions
(MM-REQ-KILN-00029). The manifest also pins the pack as 44539, which is what rules out the
near-miss noted below.

The `Sound`→`Note` column pairs were independently **verified by content**: each committed
source WAV was cross-correlated against the decoded pack originals and every row matched at
1.0000, runner-up never above 0.33. The upstream label is not always the sounding pitch —
sound 832342 is labelled `g6` upstream but measures G#6, which is why it is filed as G#6 here.

| Sound | Note | Licence |
|-------|------|---------|
| 832332 | A5 | Creative Commons 0 |
| 832333 | A6 | Creative Commons 0 |
| 832334 | B5 | Creative Commons 0 |
| 832335 | B6 | Creative Commons 0 |
| 832336 | C6 | Creative Commons 0 |
| 832337 | C7 | Creative Commons 0 |
| 832338 | D6 | Creative Commons 0 |
| 832339 | E5 | Creative Commons 0 |
| 832341 | F6 | Creative Commons 0 |
| 832342 | G#6 | Creative Commons 0 |
| 832392 | E6 | Creative Commons 0 |

Beware the near-miss: a *different* moodyfingers pack (40874, sound 732943) is also a
"Hand Crank Music Box" and is easy to confuse with the pinned 44539.

### Committed-source checksums

SHA-256 of each committed music-box source WAV under
`tools/ferrosintesis-samples/freesound-src/` (MM-REQ-KILN-00029 — these eleven previously
carried no hash).

| Source file | SHA-256 |
|-------------|---------|
| `musicbox_A5.wav` | `8b0ad0ce24ff58148f7e6b3c6ff55ad8225769885160ec2db4809126ad0a2717` |
| `musicbox_A6.wav` | `12ec5930f37a9b5aff8dfcec1497998c6d8b91cea140d0ad64f9fc4e9a3b025f` |
| `musicbox_B5.wav` | `f849bb15e2801fa777b1e1b74c5ff4893bd6594d1847e2f3e55220afbd3c1d87` |
| `musicbox_B6.wav` | `4140e8804c80e5d1ec9c13e1c9042f673055c5061b41eacac061295a62ded886` |
| `musicbox_C6.wav` | `2c6d2e2b438328d2d6b51d6816b34007a2bfa1207bab676cdc4a992beeed1059` |
| `musicbox_C7.wav` | `eca6609fe9300031a159a1501a4cac9acad84d79c310a726aa322066af17a8a4` |
| `musicbox_D6.wav` | `d59935877a0d9d02c9fc5f8fe406811b53c769380a0c83cac294f24daa7a77f1` |
| `musicbox_E5.wav` | `5ac847a57d4b281426fac561de4336c0806f0c7d10aab74c1b76dd5ea3196676` |
| `musicbox_E6.wav` | `8b793348ed0fa4bbe2722c54bd721c30854c2a64bd40d864c712e4fa8d4ac630` |
| `musicbox_F6.wav` | `0bb131859fefb0dfa3a276f0c617cce167f98d499bde847334d46ca7f75def46` |
| `musicbox_G#6.wav` | `5026d0f7fbac42e1fea46e2b90590f6bc99cb3f71d6f3c4b61634c15a5b3af85` |

**Retired source.** The banjo was previously baked from `sfzinstruments/ganjo` (CC0); that
route was retired on 2026-07-23 in favour of the owner recording and is kept in
`prepare.py` as history only.
