#!/usr/bin/env python3
"""Render a translator credit badge (logo + text) as a full-frame transparent PNG.

Usage: make_credit.py -w W -H H -o credit.png [--pos tr|tl] [--logo path] [--text "翻訳：事業家のDNA（DeNA公式）"]

Overlay it for the whole clip with burn.py --credit credit.png. Size scales with min(W,H)/720.
"""
import argparse, pathlib, subprocess

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_LOGO = "/Users/datzdaito/Desktop/dena/brand/dna_logo_bubble.png"
DEFAULT_TEXT = "翻訳：事業家のDNA（DeNA公式）"

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}html,body{width:%(W)dpx;height:%(H)dpx;background:transparent;overflow:hidden;
font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif;-webkit-font-smoothing:antialiased}
.badge{position:absolute;top:%(pad)dpx;%(side)s:%(pad)dpx;display:flex;flex-direction:column;align-items:%(align)s;gap:%(gap)dpx}
.badge img{height:%(logo)dpx;display:block;filter:drop-shadow(0 2px 6px rgba(0,0,0,.45))}
.badge span{color:#FBFBF4;font-size:%(fs)dpx;font-weight:700;letter-spacing:.02em;text-shadow:0 1px 2px rgba(0,0,0,.9),0 0 10px rgba(0,0,0,.6)}
</style></head><body><div class="badge"><img src="file://%(logo_path)s"><span>%(text)s</span></div></body></html>"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", type=int, required=True); p.add_argument("-H", type=int, required=True)
    p.add_argument("-o", required=True); p.add_argument("--pos", default="tr", choices=["tr", "tl"])
    p.add_argument("--logo", default=DEFAULT_LOGO); p.add_argument("--text", default=DEFAULT_TEXT)
    a = p.parse_args()
    k = min(a.w, a.H) / 720
    html = HTML % dict(W=a.w, H=a.H, pad=int(28*k), side="right" if a.pos=="tr" else "left",
                       align="flex-end" if a.pos=="tr" else "flex-start", gap=int(8*k), logo=int(64*k), fs=int(18*k),
                       logo_path=a.logo, text=a.text)
    out = pathlib.Path(a.o); hp = out.with_suffix(".html"); hp.write_text(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    f"--window-size={a.w},{a.H}", f"--screenshot={out}", f"file://{hp.resolve()}"], capture_output=True)
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
