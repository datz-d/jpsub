#!/usr/bin/env python3
"""Bottom black gradient overlay PNG for subtitle legibility.

Profile measured from a reference cinema-subtitle grade:
transparent down to 2/3 height, then alpha = MAX_ALPHA * t^GAMMA to the bottom.

Usage: make_gradient.py -w 1920 -H 1080 -o gradient.png
"""
import argparse

from PIL import Image

MAX_ALPHA = 0.82
GAMMA = 1.25
START = 2 / 3  # fraction of height where the gradient begins


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", "--width", type=int, required=True)
    p.add_argument("-H", "--height", type=int, required=True)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--max-alpha", type=float, default=MAX_ALPHA)
    a = p.parse_args()

    w, h = a.width, a.height
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y0 = int(h * START)
    for y in range(y0, h):
        t = (y - y0) / max(1, h - 1 - y0)
        alpha = round(255 * a.max_alpha * t**GAMMA)
        row = Image.new("RGBA", (w, 1), (0, 0, 0, alpha))
        im.paste(row, (0, y))
    im.save(a.out)
    print(f"wrote {a.out} ({w}x{h})")


if __name__ == "__main__":
    main()
