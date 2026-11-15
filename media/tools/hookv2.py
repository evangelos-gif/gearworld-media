#!/usr/bin/env python3
"""Hooks v2 (Manager 13 Nov 2026) on top of solo.py / story3.py / hubreel.py, without changing them.
- The hook is on screen from frame 0, in an opaque navy box, Inter ExtraBold 92 px, max 2 lines.
- One word of the hook in orange: write it as *word* in the spec. The subtitle is blue.
- Motion in 0-0.35 s: the scene "punches" 1.12 -> 1.0 while the banner stays still.
Usage: python3 hookv2.py solo|story|hub spec.json"""
import sys, os, importlib.util
from PIL import Image, ImageDraw
_HERE = os.path.dirname(os.path.abspath(__file__))

def load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(_HERE, name + ".py"))
    mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod); return mod

kind, spec = sys.argv[1], sys.argv[2]
mod = load({"solo": "solo", "story": "story3", "hub": "hubreel"}[kind])
r = mod.r; m = r.m; W, H, FPS = m.W, m.H, m.FPS

def hook_layer(text, sub, y):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    size = 92; f = m.font(size)
    words = text.split(); plain = " ".join(w.replace("*", "") for w in words)
    lines = m.wrap(d, plain, f, W - 130)
    while len(lines) > 2 and size > 70:
        size -= 4; f = m.font(size); lines = m.wrap(d, plain, f, W - 130)
    hot = {w.replace("*", "").strip(".,?!:'") for w in words if w.startswith("*")}
    lh = int(size * 1.15); fs = m.font(46)
    hh = len(lines) * lh + (66 if sub else 0) + 44
    d.rounded_rectangle([36, y - 26, W - 36, y + hh], radius=34, fill=m.NAVY + (238,), outline=m.GOLD + (255,), width=4)
    yy = y
    for ln in lines:
        x = (W - d.textlength(ln, font=f)) / 2
        for w in ln.split(" "):
            col = m.ORANGE if w.strip(".,?!:'") in hot else m.INK
            d.text((x, yy), w, font=f, fill=col + (255,)); x += d.textlength(w + " ", font=f)
        yy += lh
    if sub:
        tw = d.textlength(sub, font=fs); d.text(((W - tw) / 2, yy + 8), sub, font=fs, fill=(110, 175, 255, 255))
    return lay, (W / 2, y + hh / 2)

def paste_scaled(img, lay, centre, s, alpha):
    img.alpha_composite(lay)          # full size, full opacity from frame 0

_frames = r.frames; _first = [True]
def frames(clip, start, secs):
    fr = _frames(clip, start, secs)
    if _first[0]:
        _first[0] = False; n = int(0.35 * FPS)
        for i in range(min(n, len(fr))):
            s = 1.12 - 0.12 * m.ease_out(i / n)
            big = fr[i].resize((int(W * s), int(H * s)), Image.BILINEAR)
            ox, oy = (big.width - W) // 2, (big.height - H) // 2
            fr[i] = big.crop((ox, oy, ox + W, oy + H))
    return fr

r.hook_layer = hook_layer; r.paste_scaled = paste_scaled; r.frames = frames
sys.argv = [sys.argv[0], spec]
mod.main()
