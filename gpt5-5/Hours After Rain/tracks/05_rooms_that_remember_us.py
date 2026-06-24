#!/usr/bin/env python3
"""Build track 05 - Rooms That Remember Us."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import generate_track

generate_track(5)
