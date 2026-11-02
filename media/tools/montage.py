#!/usr/bin/env python3
"""Gear World real-video montage: AI clip (≈8s) + hook, price burst, banner, end card, licensed music.
Usage: python3 montage.py spec.json   (spec has clip, photo, brand, out, texts, colours, track)
Colours: navy/gold/orange/blue only (no red/green)."""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

W, H, FPS = 1080, 1920, 30
NAVY = (8, 15, 28); INK = (246, 247, 250); MUTED = (190, 198, 212)
GOLD = (232, 180, 60); ORANGE = (255, 150, 40); BLUE = (60, 135, 235)

def font(size, bold=True):
    c = ["/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else \
        ["/usr/share/fonts/opentype/inter/Inter-Medium.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for p in c:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(d, text, f, width):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width: cur = t
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out

def text_block(d, text, y, size, fill, width=W - 140, bold=True, center=True, shadow=8, alpha=255):
    f = font(size, bold)
    for ln in wrap(d, text, f, width):
        tw = d.textlength(ln, font=f)
        x = (W - tw) / 2 if center else 70
        for dx, dy in ((0, 4), (3, 3), (-3, 3)):
            d.text((x + dx, y + dy), ln, font=f, fill=(0, 0, 0, int(200 * alpha / 255)))
        d.text((x, y), ln, font=f, fill=fill + (alpha,))
        y += int(size * 1.17)
    return y

def ease_out(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def banner_layer(brand):
    b = Image.open(brand).convert("RGB")
    top = ImageOps.fit(b, (W, 300), method=Image.LANCZOS, centering=(0.5, 0.5)).convert("RGBA")
    mask = Image.new("L", top.size, 255); md = ImageDraw.Draw(mask)
    for i in range(110):
        md.line([(0, 300 - 110 + i), (W, 300 - 110 + i)], fill=int(255 * (1 - i / 110)))
    top.putalpha(mask)
    return top

def pill(d, cx, y, text, size, bg, fg, alpha=255):
    f = font(size); tw = d.textlength(text, font=f)
    x0 = cx - tw / 2 - size * 0.6; x1 = cx + tw / 2 + size * 0.6
    d.rounded_rectangle([x0, y, x1, y + size * 1.55], radius=int(size * 0.78), fill=bg + (alpha,))
    d.text((cx - tw / 2, y + size * 0.22), text, font=f, fill=fg + (alpha,))
    return y + size * 1.55

def burst(img, cx, cy, t, col_a, col_b, price):
    """Price 'explosion': rays + ring + flash, then the price pops with overshoot."""
    if t < 0: return
    d = ImageDraw.Draw(img, "RGBA")
    if t < 0.9:
        r = 120 + 760 * ease_out(t / 0.9); a = int(255 * (1 - t / 0.9))
        for k in range(18):
            ang = 2 * math.pi * k / 18 + 0.15
            r0 = r * 0.35
            p = [(cx + r0 * math.cos(ang - 0.05), cy + r0 * math.sin(ang - 0.05)),
                 (cx + r * math.cos(ang), cy + r * math.sin(ang)),
                 (cx + r0 * math.cos(ang + 0.05), cy + r0 * math.sin(ang + 0.05))]
            d.polygon(p, fill=(col_a if k % 2 else col_b) + (a,))
        rr = 80 + 520 * ease_out(t / 0.6)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col_b + (int(a * 0.9),), width=14)
        if t < 0.25:
            fl = int(150 * (1 - t / 0.25))
            d.rectangle([0, 0, W, H], fill=(255, 245, 225, fl))
        # sparks
        rng = np.random.default_rng(7)
        for k in range(40):
            ang = rng.uniform(0, 2 * math.pi); sp = rng.uniform(300, 900)
            rr2 = sp * ease_out(t / 0.9)
            x = cx + rr2 * math.cos(ang); y = cy + rr2 * math.sin(ang); s = 6 + 6 * (1 - t / 0.9)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(col_a if k % 3 else (255, 255, 255)) + (a,))
    # price pop with overshoot
    s = 1.0 + 0.35 * math.sin(math.pi * min(t / 0.45, 1)) if t < 0.45 else 1.0
    size = int(118 * min(1.0, 0.25 + t / 0.2) * s) if t < 0.2 else int(118 * s)
    pill(d, cx, cy - size * 0.78, price, max(30, size), GOLD, NAVY)

def end_card(last_frame, spec, brand_img, t):
    bg = last_frame.filter(ImageFilter.GaussianBlur(26))
    bg = ImageEnhance.Brightness(bg).enhance(0.35).convert("RGBA")
    over = Image.new("RGBA", (W, H), NAVY + (120,)); bg.alpha_composite(over)
    bg.alpha_composite(brand_img, (0, 0))
    d = ImageDraw.Draw(bg, "RGBA")
    a = int(255 * ease_out(t / 0.25))
    # world chip
    f = font(36); lab = spec["site"].upper(); tw = d.textlength(lab, font=f)
    d.rounded_rectangle([(W - tw) / 2 - 26, 330, (W + tw) / 2 + 26, 392], radius=31, fill=tuple(spec["world_colour"]) + (a,))
    d.text(((W - tw) / 2, 340), lab, font=f, fill=NAVY + (a,))
    # real product photo on white panel
    ph = Image.open(spec["photo"]).convert("RGB")
    box = (110, 430, W - 110, 1140)
    panel = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (255, 255, 255))
    p2 = ImageOps.contain(ph, (panel.width - 60, panel.height - 60))
    panel.paste(p2, ((panel.width - p2.width) // 2, (panel.height - p2.height) // 2))
    m = Image.new("L", panel.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, panel.width, panel.height], radius=34, fill=a)
    bg.paste(panel, box[:2], m)
    y = text_block(d, spec["product"], 1175, 50, INK, alpha=a)
    y = pill(d, W / 2, y + 20, f"{spec['price']} on {spec['site']}", 54, GOLD, NAVY, alpha=a) + 26
    if spec.get("offer"):
        y = text_block(d, spec["offer"], y, 34, MUTED, bold=False, alpha=a) + 6
    d.text((70, H - 210), "Link in bio · gearworldhub.com", font=font(46), fill=INK + (a,))
    small = f"#ad · We may earn a commission · price checked {spec['checked']}, may change"
    d.text((70, H - 140), small, font=font(28, False), fill=MUTED + (a,))
    d.text((70, H - 96), "Scene AI-generated from the retailer's product photo", font=font(26, False), fill=MUTED + (a,))
    return bg.convert("RGB")

def main():
    spec = json.load(open(sys.argv[1]))
    clip, out = spec["clip"], spec["out"]
    brand_img = banner_layer(spec["brand"])
    clip_s = float(spec.get("clip_seconds", 8.0)); end_s = float(spec.get("end_seconds", 1.2))
    n_clip = int(round(clip_s * FPS)); n_end = int(round(end_s * FPS))
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", str(spec.get("clip_start", 0)), "-i", clip, "-t", f"{clip_s}",
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    tmp = tempfile.mkdtemp(); silent = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent],
        stdin=subprocess.PIPE)
    hook_t = float(spec.get("burst_at", 2.8)); hook_y = int(spec.get("hook_y", 1250))
    col_a = tuple(spec.get("burst_a", ORANGE)); col_b = tuple(spec.get("burst_b", BLUE))
    burst_y = int(spec.get("burst_y", 1020))
    last = None; i = 0
    while i < n_clip:
        raw = dec.stdout.read(W * H * 3)
        if len(raw) < W * H * 3: break
        fr = Image.frombytes("RGB", (W, H), raw); last = fr
        t = i / FPS
        img = fr.convert("RGBA")
        # bottom gradient for legibility
        g = Image.new("L", (1, H), 0)
        for yy in range(H):
            g.putpixel((0, yy), int(170 * max(0, (yy - H * 0.52) / (H * 0.48)) ** 1.3))
        if i == 0: main.grad = Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (g.resize((W, H)),))
        img.alpha_composite(main.grad)
        img.alpha_composite(brand_img, (0, 0))
        d = ImageDraw.Draw(img, "RGBA")
        # #ad chip
        f = font(30); d.rounded_rectangle([W - 140, 312, W - 40, 362], radius=25, fill=(255, 255, 255, 235)); d.text((W - 118, 318), "#ad", font=f, fill=NAVY)
        # hook 0..burst
        if t < hook_t + 0.3:
            a = int(255 * min(1, t / 0.35)) if t < hook_t else int(255 * max(0, 1 - (t - hook_t) / 0.3))
            dy = int(60 * (1 - ease_out(t / 0.5)))
            y = text_block(d, spec["hook"], hook_y + dy, 88, INK, alpha=a)
            if spec.get("hook_sub"):
                text_block(d, spec["hook_sub"], y + 8, 46, GOLD, alpha=a)
        # burst and price
        if t >= hook_t:
            tb = t - hook_t
            if tb < 1.2:
                burst(img, W / 2, burst_y, tb, col_a, col_b, spec["price"])
            else:
                d = ImageDraw.Draw(img, "RGBA")
                pill(d, W / 2, burst_y - 92, spec["price"], 118, GOLD, NAVY)
            # product line
            if tb > 0.6:
                a = int(255 * min(1, (tb - 0.6) / 0.4))
                d = ImageDraw.Draw(img, "RGBA")
                y = text_block(d, spec["product"], int(spec.get("product_y", 1330)), 56, INK, alpha=a)
                if spec.get("mid_line"):
                    text_block(d, spec["mid_line"], y + 10, 40, GOLD, alpha=a)
        d = ImageDraw.Draw(img, "RGBA")
        d.text((70, H - 120), f"{spec['site']} · link in bio", font=font(38), fill=INK + (235,))
        d.text((70, H - 70), f"#ad · price checked {spec['checked']}, may change", font=font(26, False), fill=MUTED + (230,))
        enc.stdin.write(img.convert("RGB").tobytes()); i += 1
    dec.stdout.close(); dec.wait()
    for k in range(n_end):
        enc.stdin.write(end_card(last, spec, brand_img, k / FPS).tobytes())
    enc.stdin.close(); enc.wait()
    total = (i + n_end) / FPS
    music = spec.get("music")
    if music:
        fo = max(0.0, total - 1.0)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(music["start"]), "-t", f"{total:.2f}", "-i", music["mp3"],
            "-filter_complex", f"[1:a]afade=t=in:d=0.2,afade=t=out:st={fo:.2f}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out], check=True)
    else:
        subprocess.run(["cp", silent, out], check=True)
    print(json.dumps({"out": out, "seconds": round(total, 2), "frames": i + n_end}))

main.grad = None
if __name__ == "__main__":
    main()
