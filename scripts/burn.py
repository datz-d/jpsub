#!/usr/bin/env python3
"""Burn subtitle PNG overlays (plus optional bottom gradient) into a video.

Usage: burn.py <video> <cues.json> <png_dir> [-o out.mp4] [--gradient g.png] [--prefix c]

Encodes with libx264 crf 18, audio copied, faststart.
Also extracts 4 evenly spaced check frames (at cue midpoints) next to the output.
"""
import argparse
import json
import pathlib
import subprocess
import sys


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{r.stderr[-1500:]}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("cues")
    p.add_argument("png_dir")
    p.add_argument("-o", "--out")
    p.add_argument("--gradient")
    p.add_argument("--prefix", default="c")
    p.add_argument("--trim-start", type=float, default=0.0,
                   help="cut this many seconds off the head (e.g. black lead-in frames); cue times are shifted to match")
    a = p.parse_args()

    video = pathlib.Path(a.video)
    cues = json.loads(pathlib.Path(a.cues).read_text())
    pngs = [pathlib.Path(a.png_dir) / f"{a.prefix}{i:02d}.png" for i in range(len(cues))]
    missing = [str(f) for f in pngs if not f.exists()]
    if missing:
        sys.exit(f"missing PNGs: {missing[:5]}")
    out = pathlib.Path(a.out) if a.out else video.with_name(video.stem + "_JPsub.mp4")

    inputs = (["-ss", f"{a.trim_start:.4f}"] if a.trim_start > 0 else []) + ["-i", str(video)]
    cues = [[max(0.0, s - a.trim_start), max(0.0, e - a.trim_start), t] for s, e, t in cues]
    overlays = []
    idx = 1
    prev = "0:v"
    if a.gradient:
        inputs += ["-i", a.gradient]
        overlays.append(f"[{prev}][{idx}:v]overlay=0:0[g]")
        prev = "g"
        idx += 1
    for i, ((start, end, _), png) in enumerate(zip(cues, pngs)):
        inputs += ["-i", str(png)]
        label = "vout" if i == len(cues) - 1 else f"v{i}"
        overlays.append(
            f"[{prev}][{idx}:v]overlay=0:0:enable='between(t,{start},{end})'[{label}]"
        )
        prev = label
        idx += 1

    cmd = (
        ["ffmpeg", "-y", "-v", "error"]
        + inputs
        + ["-filter_complex", ";".join(overlays), "-map", "[vout]", "-map", "0:a?"]
        + ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy"]
        + ["-movflags", "+faststart", str(out)]
    )
    run(cmd)
    print(f"wrote {out}")

    picks = [cues[round(k * (len(cues) - 1) / 3)] for k in range(4)] if cues else []
    for n, (start, end, _) in enumerate(picks, 1):
        t = (start + end) / 2
        frame = out.with_name(f"check{n}.jpg")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(out),
             "-frames:v", "1", "-q:v", "3", str(frame)])
        print(f"{frame.name} @ {t:.1f}s")


if __name__ == "__main__":
    main()
