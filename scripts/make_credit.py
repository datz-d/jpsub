#!/usr/bin/env python3
"""Render a translator credit lockup (logo + small role word) as a full-frame transparent PNG.

Usage: make_credit.py -w W -H H -o credit.png [--pos tr|tl] [--logo path] [--text "訳・字幕"] [--layout side|under]

Design (2026-09-09, researched against Economist/Vice/PIVOT/NewsPicks bugs):
  top-right, 60px inset at 1080p (EBU R95 graphics-safe is 5%), logo height 58px (~5.4% of frame),
  role word 16px / tracking .14em next to the logo (book-credit idiom "〇〇 訳"), opacity .88, no backdrop.
Overlay for the whole clip with burn.py --credit credit.png. All sizes scale with min(W,H)/1080.
"""
import argparse, pathlib, subprocess

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_LOGO = "/Users/datzdaito/Desktop/dena/brand/dna_logo_reverse.png"
DEFAULT_TEXT = "訳・字幕"

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}html,body{width:%(W)dpx;height:%(H)dpx;background:transparent;overflow:hidden;
font-family:"Hiragino Sans","Hiragino Kaku Gothic ProN",sans-serif;-webkit-font-smoothing:antialiased}
.w{position:absolute;top:%(pad)dpx;%(side)s:%(pad)dpx;display:flex;%(dir)s;align-items:%(align)s;gap:%(gap)dpx;opacity:.88}
.w img{height:%(logo)dpx;display:block}
.w span{color:#FBFBF4;font-size:%(fs)dpx;font-weight:500;letter-spacing:.1em;line-height:1;text-shadow:0 1px 2px rgba(0,0,0,.4);%(extra)s}
</style></head><body><div class="w"><img src="file://%(logo_path)s"><span>%(text)s</span></div></body></html>"""

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-w", type=int, required=True); p.add_argument("-H", type=int, required=True)
    p.add_argument("-o", required=True); p.add_argument("--pos", default="tr", choices=["tr", "tl"])
    p.add_argument("--logo", default=DEFAULT_LOGO); p.add_argument("--text", default=DEFAULT_TEXT)
    p.add_argument("--layout", default="side", choices=["side", "under"])
    a = p.parse_args()
    k = min(a.w, a.H) / 1080
    side = a.layout == "side"
    html = HTML % dict(W=a.w, H=a.H, pad=int(60*k), side="right" if a.pos == "tr" else "left",
                       dir="flex-direction:row" if side else "flex-direction:column",
                       align="flex-end" if side else ("flex-end" if a.pos == "tr" else "flex-start"),
                       gap=int((12 if side else 8)*k), logo=int(58*k), fs=int(16*k),
                       extra=("padding-bottom:%dpx" % int(24*k)) if side else "",
                       logo_path=a.logo, text=a.text)
    out = pathlib.Path(a.o); hp = out.with_suffix(".html"); hp.write_text(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    f"--window-size={a.w},{a.H}", f"--screenshot={out}", f"file://{hp.resolve()}"], capture_output=True)
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
