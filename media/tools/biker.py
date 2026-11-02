#!/usr/bin/env python3
"""Biker Gear World reel (31 Oct 2026): 3s hook with price burst + 6s ride + 3s end card with 3 products = 12s.
Colours: navy / gold / orange / blue only (no red/green). Usage: python3 biker.py spec.json"""
import json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageOps
import importlib.util
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_r = importlib.util.spec_from_file_location("r", _os.path.join(_HERE, "reel.py"))
r = importlib.util.module_from_spec(_r); _r.loader.exec_module(r)
m = r.m
W, H, FPS = m.W, m.H, m.FPS
NAVY, INK, MUTED, GOLD, ORANGE, BLUE = m.NAVY, m.INK, m.MUTED, m.GOLD, m.ORANGE, m.BLUE


def boxed(img, text, y, size, colour, a, pad=12, alpha_box=0.72, bold=True):
    d = ImageDraw.Draw(img, "RGBA"); f = m.font(size, bold); lines = m.wrap(d, text, f, W - 140)
    bh = len(lines) * int(size * 1.17) + 2 * pad
    d.rounded_rectangle([50, y - pad, W - 50, y - pad + bh], radius=22, fill=NAVY + (int(a * alpha_box),))
    return m.text_block(d, text, y, size, colour, bold=bold, alpha=a)


def end_card(bg, spec, brand, t):
    a = int(255 * m.ease_out(t / 0.25)); bg.alpha_composite(brand, (0, 0)); d = ImageDraw.Draw(bg, "RGBA")
    f = m.font(36); lab = spec["site"].upper(); tw = d.textlength(lab, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 26, 330, (W + tw) / 2 + 26, 392], radius=31, fill=tuple(spec["world_colour"]) + (a,))
    d.text(((W - tw) / 2, 340), lab, font=f, fill=NAVY + (a,))
    m.text_block(d, spec["end_title"], 418, 50, INK, alpha=a)
    y0, rh, gap = 500, 290, 22
    for i, it in enumerate(spec["items"]):
        ti = max(0.0, t - 0.12 * i); ai = int(255 * m.ease_out(ti / 0.3)); dx = int(80 * (1 - m.ease_out(ti / 0.45)))
        y = y0 + i * (rh + gap); x = 60 + dx
        d.rounded_rectangle([x - 10, y - 10, W - 50 + dx, y + rh + 10], radius=28, fill=NAVY + (int(ai * 0.55),))
        pw, ph = 400, rh
        panel = Image.new("RGB", (pw, ph), (255, 255, 255))
        p = ImageOps.contain(Image.open(it["photo"]).convert("RGB"), (pw - 16, ph - 16))
        panel.paste(p, ((pw - p.width) // 2, (ph - p.height) // 2))
        mk = Image.new("L", panel.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, pw, ph], radius=24, fill=ai)
        bg.paste(panel, (x, y), mk)
        tx = x + pw + 30; ty = y + 6
        d.text((tx, ty), it["name"], font=m.font(42), fill=INK + (ai,)); ty += 54
        d.text((tx, ty), it["spec"], font=m.font(28, False), fill=MUTED + (ai,)); ty += 42
        d.text((tx, ty), it["price"], font=m.font(58), fill=GOLD + (ai,)); ty += 74
        for ln in it["note"]:
            d.text((tx, ty), ln, font=m.font(27), fill=ORANGE + (ai,)); ty += 34
    y = y0 + 3 * (rh + gap) + 8
    m.text_block(d, spec["site_url"], y, 60, INK, alpha=a)
    m.text_block(d, spec["end_line"], y + 82, 32, MUTED, bold=False, alpha=a)
    d.text((70, H - 140), f"#ad · We may earn a commission · prices checked {spec['checked']}, may change", font=m.font(26, False), fill=MUTED + (a,))
    d.text((70, H - 98), spec["ai_note"], font=m.font(25, False), fill=MUTED + (a,))
    return bg


def main():
    spec = json.load(open(sys.argv[1])); brand = m.banner_layer(spec["brand"]); G = r.gradient()
    tmp = tempfile.mkdtemp(); silent = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    k = 0
    foot2 = f"#ad · price checked {spec['checked']}, may change"
    # ---- hook 0..3s: hook text pops in, then the price "explodes" in
    hk = spec["hook"]; hook_s = float(hk.get("seconds", 3.0))
    lay, centre = r.hook_layer(hk["text"], hk.get("sub"), int(hk.get("y", 380)))
    hs = spec["hook_clip"]; hf = r.frames(hs["clip"], hs.get("start", 0), hook_s)
    bt0 = float(hk.get("burst_at", 0.7)); by = int(hk.get("burst_y", 980))
    for j, f0 in enumerate(hf):
        t = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); r.chrome(img, brand)
        s = 1.28 - 0.28 * m.ease_out(t / 0.35)
        r.paste_scaled(img, lay, centre, s, int(255 * min(1, t / 0.12)))
        tb = t - bt0
        if tb >= 0:
            if tb < 1.2: r.burst(img, W / 2, by, tb, ORANGE, BLUE, spec["price"])
            else: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, by - 92, spec["price"], 118, GOLD, NAVY)
        r.footer(img, spec["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    # ---- ride 3..9s
    bs = spec["body_clip"]; bf = r.frames(bs["clip"], bs.get("start", 0), float(bs["seconds"]))
    for j, f0 in enumerate(bf):
        t = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); r.chrome(img, brand)
        a = int(255 * min(1, t / 0.3))
        y = boxed(img, spec["product"], int(spec.get("product_y", 400)), 50, INK, a)
        y = boxed(img, spec["spec_line"], y + 14, 40, GOLD, a, alpha_box=0.6)
        pf = float(spec.get("pill_fade_at", 3.2))          # fade the price pill before the rider's helmet reaches it
        ap = a if t < pf else int(a * max(0.0, 1 - (t - pf) / 0.4))
        if ap > 0: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, y + 14, spec["price"], 72, GOLD, NAVY, alpha=ap)
        if t > 0.8:
            a2 = int(255 * min(1, (t - 0.8) / 0.3))
            boxed(img, spec["legal_line"], int(spec.get("legal_y", 1640)), 34, INK, a2, pad=10, alpha_box=0.8, bold=False)
        r.footer(img, spec["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    last_src = bf[-int(FPS * 1.0):]
    # ---- end card 9..12s
    n_end = int(round(float(spec.get("end_seconds", 3.0)) * FPS))
    for j in range(n_end):
        bg = r.end_bg(last_src, j, n_end); enc.stdin.write(end_card(bg, spec, brand, j / FPS).convert("RGB").tobytes()); k += 1
    enc.stdin.close(); enc.wait()
    total = k / FPS; mu = spec["music"]; fod = float(mu.get("fade_out", 1.0)); fo = max(0.0, total - fod)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(mu["start"]), "-t", f"{total:.2f}", "-i", mu["mp3"],
        "-filter_complex", f"[1:a]afade=t=in:d={float(mu.get('fade_in', 0.15))},afade=t=out:st={fo:.2f}:d={fod},loudnorm=I={float(mu.get('lufs', -14))}:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", spec["out"]], check=True)
    print(json.dumps({"out": spec["out"], "seconds": round(total, 2)}))


if __name__ == "__main__":
    main()
