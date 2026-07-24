# Provenance - ferrosintesis-samples-orchestral2

Every WAV this crate packages, with the pinned source it was baked from. Machine-checked
by `crates/ferrosintesis/src/inventory.rs`: a family that ships without a row here fails
the build (MM-BUG-KILN-00069).

Regenerate with `python tools/ferrosintesis-samples/prepare.py --only=<family>` from the repository
root.

| Family | Files | Instrument | Source | Licence |
|--------|------:|------------|--------|---------|
| `banjo_*` | 8 | 5-string banjo (GM 105) onsets | **Owner-recorded** by Arthur (`samples/banjo/*.opus`), baked by `banjo_extract.py` | CC0-1.0 |
| `eastpick_*` | 12 | Eastman E1D steel guitar, picked (GM 25) | **Owner-recorded** (Eastman E1D), committed per-zone cuts | CC0-1.0 |
| `eastpluck_*` | 12 | Eastman E1D steel guitar, plucked | **Owner-recorded** (Eastman E1D), committed per-zone cuts | CC0-1.0 |
| `glock_*` | 6 | Glockenspiel (GM 9) strikes | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `harp_*` | 8 | Harp (GM 46) plucks | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `marimba_*` | 8 | Marimba (GM 12) strikes | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `musicbox_*` | 11 | Music box (GM 10) strikes | Freesound pack **44539** "Hand Crank Music Box B (Notes)" by *moodyfingers* - per-sound table below | CC0-1.0 |
| `ocarina_*` | 5 | Ocarina (GM 79) sustains | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `recorder_*` | 6 | Recorder (GM 74) sustains | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `timpani_*` | 6 | Timpani (GM 47) strikes | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `tubular_*` | 6 | Tubular bells (GM 14) strikes | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `vibes_*` | 6 | Vibraphone (GM 11), soft mallets | VCSL (Versilian Community Sample Library), pinned `c1ea7bcc3c7309650ab0da9d15c9cd1fbc4a4c7e` | CC0-1.0 |
| `viola_*` | 12 | Solo viola (GM 41) arco onsets | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |
| `xylo_*` | 6 | Xylophone (GM 13) strikes | VSCO-2 Community Edition, pinned `440300901dfe9275fd84e0b7763af1f8443ae62e` | CC0-1.0 |

## GM 10 music box - per-sound licence record

The music box was declared CC0 by a code comment alone. The author's Freesound catalogue
mixes CC0, Attribution and Attribution-NonCommercial, so CC0 was **not** inferable at
account level. All eleven sounds were checked individually on 2026-07-24 and each sound
page states "Creative Commons 0". The record is committed here so the check is never
repeated (MM-BUG-KILN-00069 item 9).

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

**Retired source.** The banjo was previously baked from `sfzinstruments/ganjo` (CC0); that
route was retired on 2026-07-23 in favour of the owner recording and is kept in
`prepare.py` as history only.
