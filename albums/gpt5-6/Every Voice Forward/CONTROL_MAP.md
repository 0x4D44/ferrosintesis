# Ferrosintesis performance map

The controllers are part of the composition, not a compliance dump at the end of a file. The verifier distinguishes meaningful, non-default gestures from reset traffic.

## Continuous and switched controllers

| MIDI feature | Musical use | Principal tracks |
|---|---|---|
| **CC1 Mod wheel** | Leslie acceleration on organs; vibrato growth on strings, reeds, brass and leads | 1–5 |
| **CC2 Breath** | Wind and brass tone opening; pressure-shaped world instruments | 1–5 |
| **CC5 + CC65 Portamento** | Time plus enable switch for bass, guitar and synth-lead glides | 1, 3, 5 |
| **CC7 Volume** | Static channel balance and scene rebalancing | 1–5 |
| **CC10 Pan** | Ensemble placement and continuous orbital/autopan motion | 1–5 |
| **CC11 Expression** | Swells, sidechain-like pumps, brass crescendi and cathedral-organ reed rasp | 1–5 |
| **CC64 Sustain** | Piano resonance, harp bloom and finale chord support | 1, 5 |
| **CC66 Sostenuto** | Held piano tones under moving material | 1, 5 |
| **CC67 Soft / una corda** | Piano colour change and negative-space bridge | 1, 5 |
| **CC68 Legato** | Retuned ringing strings, wind slurs and lead transitions without re-attack | 1–5 |
| **CC70 Sound controller 1** | Ferrosintesis choir/voice vowel path: **mm → oo → ah → eh** | 2, 5 |
| **CC71 Resonance** | Filter-Q choreography and the high-energy edge of pad/FX rises | 1, 3–5 |
| **CC74 Brightness** | Guitar wah, lead opening and broad pad horizon sweeps | 1, 3–5 |
| **CC84 Portamento source** | Explicit lead glide source note | 3, 5 |
| **CC91 Reverb send** | Dry rhythmic fronts versus deep halls and effect-space transitions | 1–5 |
| **CC93 Chorus send** | String, choir, pad and ensemble width | 1–5 |
| **CC94 Delay send** | Echo throws, moving mallets, leads and scene effects | 1–5 |

Every track also carries authored channel pressure or bends; **Brighter Engines** uses polyphonic pressure on exposed violin notes.

## RPN, bend and pressure

| Feature | Use |
|---|---|
| **RPN 0 – Pitch-bend sensitivity** | Wider guitar, brass, wind and lead gestures; up to ±12 semitones where the arrangement needs it |
| **RPN 1 – Fine tuning** | Opposing few-cent offsets across bowed strings and the finale bridge, creating section width before chorus |
| **Pitch bend** | Guitar scoops, brass lip movement, wind breath-scoops, synth dives and the finale’s rising lead |
| **Channel pressure** | Growth inside sustained strings, choir, brass, winds and pads |
| **Polyphonic pressure** | Individual violin-note accents in track 2 |

## Ferrosintesis banked voices

| Bank MSB | Bank LSB | Program | Voice | Where used |
|---:|---:|---:|---|---|
| 2 | 0 | 19 | Cathedral pipe organ | Finale, including expression-driven swell |
| 0 | 96 | 25 | Owner-recorded mandolin variation | Tracks 4 and 5 |
| 0 | 19 | 99 | XG Hollow Release atmosphere variant | Finale’s second ascent |
| 1 | 0 | 109 | Modeled alternate bagpipe | Track 4 call-back |

## SysEx surface

Each track begins from an explicit interoperable state and then opts into Ferrosintesis’s modeled extensions:

- **GM System On**
- **GS Reset**
- **XG System On**
- **XG Hall 1** and **XG Chorus 1** effect types
- **XG Amp Simulator** as an insertion effect on selected guitar/lead parts
- **GS Use for Rhythm Part** to turn channel 9 (zero-based channel 8) into a second drum part for the all-47-key percussion parade, then turn it back off

## Coverage design

| Track | Programs | Musical family |
|---|---:|---|
| Daybreak Relay | 0–31 | Piano → chromatic percussion → organ/free reed → guitar |
| Brighter Engines | 32–63 | Bass → solo strings/harp/timpani → ensembles/choir → brass |
| Open-Sky Signal | 64–95 | Reed → pipe → lead → pad |
| The World in the Chorus | 96–127 | Synth FX → ethnic → melodic percussion → scene SFX |

The first four tracks therefore cover the whole melodic map without trying to stack 128 voices into one mix. The fifth track selects voices for musical compatibility rather than catalogue completeness.
