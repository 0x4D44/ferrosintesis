#!/usr/bin/env python3
"""
build.py — regenerate the whole album *Vigil*.

Runs every tracks/NN_*.py in order (each renders its own midi/NN - Title.mid),
then prints a one-line summary per track and the total album running time.

    python build.py
"""
import os
import sys
import glob
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TRACKS_DIR = os.path.join(HERE, 'tracks')
MIDI_DIR = os.path.join(HERE, 'midi')


def main():
    mods = sorted(glob.glob(os.path.join(TRACKS_DIR, '[0-9][0-9]_*.py')))
    if not mods:
        print('no track modules found in tracks/')
        return 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    failures = []
    print(f'Building {len(mods)} tracks...\n')
    for m in mods:
        name = os.path.basename(m)
        r = subprocess.run([sys.executable, m], capture_output=True, text=True, env=env)
        line = (r.stdout.strip().splitlines() or [''])[0]
        if r.returncode != 0:
            failures.append(name)
            print(f'  FAIL {name}\n{r.stderr.strip()[-800:]}')
        else:
            print(f'  ok   {line}')

    # album running time
    try:
        from mido import MidiFile
        total = 0.0
        mids = sorted(glob.glob(os.path.join(MIDI_DIR, '*.mid')))
        for f in mids:
            total += MidiFile(f).length
        mm = int(total // 60)
        print(f'\nAlbum: {len(mids)} tracks, total {mm}:{total - mm*60:05.2f} ({total:.0f}s)')
    except Exception as e:
        print(f'(could not total album length: {e})')

    if failures:
        print(f'\n{len(failures)} FAILED: {failures}')
        return 1
    print('\nAll tracks built cleanly.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
