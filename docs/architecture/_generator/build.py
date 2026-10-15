#!/usr/bin/env python3
"""Regenerate every architecture diagram: SVG, then a 2x PNG beside it.

    pip install -r requirements.txt
    python build.py

Output goes to ../diagrams by default, or to $DIAGRAM_OUT.
"""
import os, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("DIAGRAM_OUT", os.path.join(HERE, "..", "diagrams"))
os.makedirs(OUT, exist_ok=True)

scripts = sorted(glob.glob(os.path.join(HERE, "d[0-9][0-9]_*.py")))
if not scripts:
    sys.exit("no diagram scripts found next to build.py")

for s in scripts:
    print("==", os.path.basename(s))
    subprocess.run([sys.executable, s], check=True)

try:
    import cairosvg
except ImportError:
    print("\ncairosvg not installed, skipping PNG export")
    sys.exit(0)

for svg in sorted(glob.glob(os.path.join(OUT, "*.svg"))):
    png = svg[:-4] + ".png"
    cairosvg.svg2png(url=svg, write_to=png, scale=2.0)
    print("png", os.path.basename(png))
print("\ndone")
