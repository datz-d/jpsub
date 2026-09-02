#!/usr/bin/env python3
"""Render subtitle cues to transparent PNG overlays via headless Chrome.

Usage: render_cues.py <cues.json> <out_dir> -w 1920 -H 1080 [--prefix c] [--only 3,7]

cues.json: [[start_sec, end_sec, "line1\nline2"], ...]
Writes <out_dir>/<prefix>NN.html and <prefix>NN.png (transparent, full frame).
Font size and bottom margin scale from a 1080p baseline (46px / 56px)
by min(W, H) / 1080, so vertical 9:16 video gets the same visual weight.
"""
import argparse
import html
import json
import pathlib
import subprocess
import sys

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "sub.html"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cues")
    p.add_argument("out_dir")
    p.add_argument("-w", "--width", type=int, required=True)
    p.add_argument("-H", "--height", type=int, required=True)
    p.add_argument("--prefix", default="c")
    p.add_argument("--only", help="comma-separated cue indices to re-render")
    a = p.parse_args()

    cues = json.loads(pathlib.Path(a.cues).read_text())
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scale = min(a.width, a.height) / 1080
    tpl = TEMPLATE.read_text()
    only = {int(i) for i in a.only.split(",")} if a.only else None

    for i, (_, _, text) in enumerate(cues):
        if only is not None and i not in only:
            continue
        page = (
            tpl.replace("{{W}}", str(a.width))
            .replace("{{H}}", str(a.height))
            .replace("{{BOTTOM}}", str(round(56 * scale)))
            .replace("{{FONT_SIZE}}", str(round(46 * scale)))
            .replace("{{TEXT}}", html.escape(text))
        )
        hp = out / f"{a.prefix}{i:02d}.html"
        pp = out / f"{a.prefix}{i:02d}.png"
        hp.write_text(page)
        r = subprocess.run(
            [
                CHROME,
                "--headless=new",
                f"--screenshot={pp}",
                f"--window-size={a.width},{a.height}",
                "--default-background-color=00000000",
                "--hide-scrollbars",
                "--disable-gpu",
                f"file://{hp.resolve()}",
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0 or not pp.exists():
            sys.exit(f"chrome failed on cue {i}: {r.stderr[-500:]}")
        print(f"{pp.name}  [{text.splitlines()[0][:24]}]")
    print("rendered")


if __name__ == "__main__":
    main()
