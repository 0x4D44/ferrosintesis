#!/usr/bin/env python3
"""Build track 2 - Windowlit Water."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import generate_track

generate_track(2)
