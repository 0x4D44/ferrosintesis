# ferrosintesis-samples-grand

Embedded grand-piano attack/body bank for ferrosintesis: 54 mono 16-bit 44.1 kHz
WAVs (9 zones C2–C6 × 3 dynamics × 2 round robins), exposed as raw WAV bytes
(`get`). This is the sample source for the **GM 0 Acoustic Grand alternate**
(CC0=2) voice — a real Yamaha C5 concert grand, distinct from the CC0 VSCO
*upright* that is the GM 0 CC0=1 alternate.

Unlike the core/orchestral crates, this bank is **CC BY 3.0**, not CC0: the audio
is "Salamander Grand Piano V3" by Alexander Holm. The required attribution ships
as `NOTICE` — it is irrevocable and permits commercial use and redistribution, so
it flows to every downstream user while the ferrosintesis code stays MIT/Apache.
See `PROVENANCE.md` for the source archive, SHA-256 pin, license verification, and
the processing chain.

It is a separate crate so that `ferrosintesis-samples-core` stays under the
crates.io 10 MiB publish cap.

The WAVs under `samples/` are source, not build output. Regenerate only this bank
from the repo root:

```powershell
python3 tools/ferrosintesis-samples/prepare.py --only=grand
```

That scoped path fetches and SHA-256-verifies the pinned Salamander `.tar.bz2`,
decoded with Python's stdlib. A bare `prepare.py` invocation is the full
multi-bank workflow; it rewrites unrelated sample crates and needs their
additional tools.
