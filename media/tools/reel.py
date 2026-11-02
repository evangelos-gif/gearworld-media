#!/usr/bin/env python3
"""Gear World reel v29: 3s hook + body (single product or N items) + moving end card, <=10s.
Colours: navy / gold / orange / blue only (no red/green). Usage: python3 reel.py spec.json"""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance
import importlib.util
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("m", _os.path.join(_HERE, "montage.py"))
m = importlib.util.module_from_spec(_s); _s.loader.exec_module(m)
W, H, FPS = m.W, m.H, m.FPS
NAVY, INK, MUTED, GOLD, ORANGE, BLUE = m.NAVY, m.INK, m.MUTED, m.GOLD, m.ORANGE, m.BLUE

def burst(img, cx, cy, t, col_a, col_b, price):
    """Price burst with a properly blended (translucent) flash; rays/ring/sparks as v28."""
    if t < 0: return
    if t < 0.2:
        img.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 225, int(90 * (1 - t / 0.2)))))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    if t < 0.9:
        r = 120 + 760 * m.ease_out(t / 0.9); a = int(255 * (1 - t / 0.9))
        for k in range(18):
            ang = 2 * math.pi * k / 18 + 0.15; r0 = r * 0.35
            p = [(cx + r0 * math.cos(ang - 0.05), cy + r0 * math.sin(ang - 0.05)), (cx + r * math.cos(ang), cy + r * math.sin(ang)),
                 (cx + r0 * math.cos(ang + 0.05), cy + r0 * math.sin(ang + 0.05))]
            d.polygon(p, fill=(col_a if k % 2 else col_b) + (a,))
        rr = 80 + 520 * m.ease_out(t / 0.6)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col_b + (int(a * 0.9),), width=14)
        rng = np.random.default_rng(7)
        for k in range(40):
            ang = rng.uniform(0, 2 * math.pi); sp = rng.uniform(300, 900); rr2 = sp * m.ease_out(t / 0.9)
            x = cx + rr2 * math.cos(ang); y = cy + rr2 * math.sin(ang); s = 6 + 6 * (1 - t / 0.9)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(col_a if k % 3 else (255, 255, 255)) + (a,))
    img.alpha_composite(lay)
    s = 1.0 + 0.35 * math.sin(math.pi * min(t / 0.45, 1)) if t < 0.45 else 1.0
    size = int(118 * min(1.0, 0.25 + t / 0.2) * s) if t < 0.2 else int(118 * s)
    m.pill(ImageDraw.Draw(img, "RGBA"), cx, cy - size * 0.78, price, max(30, size), GOLD, NAVY)

def frames(clip, start, secs):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(start), "-i", clip, "-t", str(secs),
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = len(p) // (W * H * 3)
    fr = [Image.frombytes("RGB", (W, H), p[i*W*H*3:(i+1)*W*H*3]) for i in range(n)]
    want = int(round(secs * FPS))
    while len(fr) < want: fr.append(fr[-1])          # pad by holding (rare, few frames)
    return fr[:want]

def gradient(top=0.5, strength=175):
    g = Image.new("L", (1, H), 0)
    for yy in range(H):
        g.putpixel((0, yy), int(strength * max(0, (yy - H * top) / (H * (1 - top))) ** 1.3))
    return Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (g.resize((W, H)),))

def hook_layer(text, sub, y):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay, "RGBA")
    f = m.font(92); lines = m.wrap(d, text, f, W - 120)
    hh = len(lines) * int(92 * 1.15) + (70 if sub else 0) + 40
    d.rounded_rectangle([40, y - 24, W - 40, y + hh], radius=34, fill=NAVY + (150,))
    yy = m.text_block(d, text, y, 92, INK, width=W - 120)
    if sub: m.text_block(d, sub, yy + 6, 46, GOLD, width=W - 120)
    return lay, (W / 2, y + hh / 2)

def paste_scaled(img, lay, centre, s, alpha):
    if alpha <= 0: return
    l = lay
    if abs(s - 1) > 1e-3:
        ls = lay.resize((int(W * s), int(H * s)), Image.BILINEAR)
        cx, cy = centre
        ox = int(cx - cx * s); oy = int(cy - cy * s)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(ls, (ox, oy), ls); l = canvas
    if alpha < 255:
        a = l.getchannel("A").point(lambda v: v * alpha // 255); l = l.copy(); l.putalpha(a)
    img.alpha_composite(l)

def chrome(img, brand):
    img.alpha_composite(brand, (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([W - 140, 312, W - 40, 362], radius=25, fill=(255, 255, 255, 235))
    d.text((W - 118, 318), "#ad", font=m.font(30), fill=NAVY)

def footer(img, line1, line2):
    d = ImageDraw.Draw(img, "RGBA")
    d.text((70, H - 122), line1, font=m.font(36), fill=INK + (240,))
    d.text((70, H - 72), line2, font=m.font(25, False), fill=MUTED + (230,))

def label_box(img, text, y, a, size=52):
    d = ImageDraw.Draw(img, "RGBA"); lf = m.font(size); lines = m.wrap(d, text, lf, W - 140)
    bh = len(lines) * int(size * 1.17) + 24
    d.rounded_rectangle([50, y - 12, W - 50, y - 12 + bh], radius=22, fill=NAVY + (int(a * 0.72),))
    return m.text_block(d, text, y, size, INK, alpha=a)

def end_bg(src, k, n):
    fr = src[k % len(src)] if (k // len(src)) % 2 == 0 else src[len(src) - 1 - k % len(src)]
    bg = ImageEnhance.Brightness(fr.filter(ImageFilter.GaussianBlur(24))).enhance(0.36).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), NAVY + (120,)))
    return bg

def end_single(bg, spec, brand, t):
    a = int(255 * m.ease_out(t / 0.25)); grow = 0.92 + 0.08 * m.ease_out(t / 0.6); lift = int(50 * (1 - m.ease_out(t / 0.5)))
    bg.alpha_composite(brand, (0, 0)); d = ImageDraw.Draw(bg, "RGBA")
    f = m.font(36); lab = spec["site"].upper(); tw = d.textlength(lab, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 26, 330, (W + tw) / 2 + 26, 392], radius=31, fill=tuple(spec["world_colour"]) + (a,))
    d.text(((W - tw) / 2, 340), lab, font=f, fill=NAVY + (a,))
    pw, ph = int((W - 220) * grow), int(700 * grow)
    panel = Image.new("RGB", (pw, ph), (255, 255, 255))
    p2 = ImageOps.contain(Image.open(spec["photo"]).convert("RGB"), (pw - 60, ph - 60))
    panel.paste(p2, ((pw - p2.width) // 2, (ph - p2.height) // 2))
    mk = Image.new("L", panel.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, pw, ph], radius=34, fill=a)
    bg.paste(panel, ((W - pw) // 2, 430 + (700 - ph) // 2 + lift), mk)
    y = m.text_block(d, spec["product"], 1170, 48, INK, alpha=a)
    pulse = 1 + 0.06 * math.sin(2 * math.pi * t / 0.8)
    y = m.pill(d, W / 2, y + 18, f"{spec['price']} on {spec['site']}", int(52 * pulse), GOLD, NAVY, alpha=a) + 22
    if spec.get("offer"):
        m.text_block(d, spec["offer"], y, 33, MUTED, bold=False, alpha=a)
    d.text((70, H - 210), "Link in bio · gearworldhub.com", font=m.font(46), fill=INK + (a,))
    d.text((70, H - 140), f"#ad · We may earn a commission · price checked {spec['checked']}, may change", font=m.font(27, False), fill=MUTED + (a,))
    d.text((70, H - 96), spec.get("ai_note", "Scene AI-generated from the retailer's product photo"), font=m.font(26, False), fill=MUTED + (a,))
    return bg

def end_multi(bg, spec, brand, t):
    a = int(255 * m.ease_out(t / 0.25)); bg.alpha_composite(brand, (0, 0)); d = ImageDraw.Draw(bg, "RGBA")
    tf = 58
    while tf > 40 and d.textlength(spec["title"], font=m.font(tf)) > W - 180: tf -= 2
    m.text_block(d, spec["title"], 318, tf, INK, alpha=a)
    cw, ch = 440, 430; xs = [(W - 2 * cw - 40) // 2, (W - 2 * cw - 40) // 2 + cw + 40]; ys = [420, 420 + ch + 40]
    for i, it in enumerate(spec["items"]):
        ti = max(0.0, t - 0.08 * i); ai = int(255 * m.ease_out(ti / 0.25)); dy = int(40 * (1 - m.ease_out(ti / 0.4)))
        x, y = xs[i % 2], ys[i // 2] + dy
        panel = Image.new("RGB", (cw, ch - 120), (255, 255, 255))
        ph = ImageOps.contain(Image.open(it["photo"]).convert("RGB"), (cw - 30, ch - 150))
        panel.paste(ph, ((cw - ph.width) // 2, (ch - 120 - ph.height) // 2))
        mk = Image.new("L", panel.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, cw, ch - 120], radius=26, fill=ai)
        bg.paste(panel, (x, y), mk)
        d.ellipse([x + 12, y + 12, x + 64, y + 64], fill=GOLD + (ai,)); f = m.font(34)
        d.text((x + 38 - d.textlength(str(i + 1), font=f) / 2, y + 17), str(i + 1), font=f, fill=NAVY + (ai,))
        d.text((x + 6, y + ch - 110), it["price"], font=m.font(40), fill=GOLD + (ai,))
        d.text((x + 6, y + ch - 62), it["site_short"], font=m.font(26, False), fill=MUTED + (ai,))
    m.text_block(d, spec["offer"], ys[1] + ch + 10, 33, INK, alpha=a)
    d.text((70, H - 205), "Link in bio · gearworldhub.com", font=m.font(44), fill=INK + (a,))
    d.text((70, H - 140), f"#ad · We may earn a commission · prices checked {spec['checked']}, may change", font=m.font(26, False), fill=MUTED + (a,))
    d.text((70, H - 98), spec.get("ai_note", "Scenes AI-generated from the retailers' product photos"), font=m.font(25, False), fill=MUTED + (a,))
    return bg

def main():
    spec = json.load(open(sys.argv[1])); brand = m.banner_layer(spec["brand"]); G = gradient()
    tmp = tempfile.mkdtemp(); silent = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    hk = spec["hook"]; hook_s = float(hk.get("seconds", 3.0))
    lay, centre = hook_layer(hk["text"], hk.get("sub"), int(hk.get("y", 400)))
    k = 0
    # ---- hook (0..3s)
    hs = spec["hook_clip"]; hf = frames(hs["clip"], hs.get("start", 0), hook_s)
    for j, f0 in enumerate(hf):
        t = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); chrome(img, brand)
        s = 1.28 - 0.28 * m.ease_out(t / 0.35)
        al = 255 if t < hook_s - 0.25 else int(255 * max(0, (hook_s - t) / 0.25))
        paste_scaled(img, lay, centre, s, int(255 * min(1, t / 0.12)) if t < 0.12 else al)
        footer(img, spec["footer1"], f"#ad · price checked {spec['checked']}, may change")
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    last_src = hf[-int(FPS * 0.8):]
    cols = [(ORANGE, BLUE), (BLUE, ORANGE), (GOLD, BLUE), (ORANGE, GOLD)]
    if spec["mode"] == "single":
        bs = spec["body_clip"]; bf = frames(bs["clip"], bs.get("start", 0), float(bs["seconds"]))
        for j, f0 in enumerate(bf):
            tb = j / FPS - 0.15; img = f0.convert("RGBA"); img.alpha_composite(G); chrome(img, brand)
            if tb >= 0:
                if tb < 1.2: burst(img, W / 2, int(spec.get("burst_y", 1560)), tb, *cols[0], spec["price"])
                else: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, int(spec.get("burst_y", 1560)) - 92, spec["price"], 118, GOLD, NAVY)
            if tb > 0.5:
                a = int(255 * min(1, (tb - 0.5) / 0.35))
                y = label_box(img, spec["product"], int(spec.get("product_y", 1260)), a, 50)
                if spec.get("mid_line"):
                    d = ImageDraw.Draw(img, "RGBA"); my = int(spec.get("mid_y", y + 6))
                    lf = m.font(42); ln = m.wrap(d, spec["mid_line"], lf, W - 140); bh = len(ln) * int(42 * 1.17) + 20
                    d.rounded_rectangle([50, my - 10, W - 50, my - 10 + bh], radius=20, fill=NAVY + (int(a * 0.6),))
                    m.text_block(d, spec["mid_line"], my, 42, GOLD, alpha=a)
            footer(img, spec["footer1"], f"#ad · price checked {spec['checked']}, may change")
            enc.stdin.write(img.convert("RGB").tobytes()); k += 1
        last_src = bf[-int(FPS * 1.0):]
        endfn = end_single
    else:
        seg = float(spec.get("seg_seconds", 1.4))
        for i, it in enumerate(spec["items"]):
            fr = frames(it["clip"], it.get("start", 0.6), seg)
            for j, f0 in enumerate(fr):
                tl = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); chrome(img, brand)
                d = ImageDraw.Draw(img, "RGBA"); f = m.font(40); lab = f"{i+1}/{len(spec['items'])}"
                d.rounded_rectangle([60, 312, 60 + d.textlength(lab, font=f) + 44, 372], radius=30, fill=GOLD + (240,)); d.text((82, 318), lab, font=f, fill=NAVY)
                bt = tl - 0.12
                if bt >= 0:
                    a = int(255 * min(1, bt / 0.2))
                    if bt < 0.9: burst(img, W / 2, 1560, bt, *cols[i % 4], it["price"])
                    else: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, 1560 - 92, it["price"], 112, GOLD, NAVY)
                    label_box(img, it["label"], 1300, a)
                footer(img, spec["offer_short"], f"#ad · {it['site']} · price checked {spec['checked']}, may change")
                enc.stdin.write(img.convert("RGB").tobytes()); k += 1
            last_src = fr
        endfn = end_multi
    n_end = int(round(float(spec.get("end_seconds", 1.5)) * FPS))
    for j in range(n_end):
        bg = end_bg(last_src, j, n_end); enc.stdin.write(endfn(bg, spec, brand, j / FPS).convert("RGB").tobytes()); k += 1
    enc.stdin.close(); enc.wait()
    total = k / FPS; mu = spec["music"]; fo = max(0.0, total - 1.0)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(mu["start"]), "-t", f"{total:.2f}", "-i", mu["mp3"],
        "-filter_complex", f"[1:a]afade=t=in:d=0.15,afade=t=out:st={fo:.2f}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", spec["out"]], check=True)
    print(json.dumps({"out": spec["out"], "seconds": round(total, 2)}))

if __name__ == "__main__":
    main()
