#!/usr/bin/env python3
"""Build track 7 - Midnight Engine."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import generate_track

generate_track(7)
