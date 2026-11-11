#!/usr/bin/env python3
"""Hub screen-recording reel: 2.2s hook intro (blurred first frame, hook + burst) -> real screen recording of gearworldhub.com
inside a phone frame with step captions and tap ripples -> 2s end card. Colours: navy / gold / orange / blue only.
Usage: python3 hubreel.py spec.json"""
import json, os, subprocess, sys, tempfile, math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import importlib.util
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_r = importlib.util.spec_from_file_location("r", _os.path.join(_HERE, "reel.py")); r = importlib.util.module_from_spec(_r); _r.loader.exec_module(r)
m = r.m; W, H, FPS = m.W, m.H, m.FPS
NAVY, INK, MUTED, GOLD, ORANGE, BLUE = m.NAVY, m.INK, m.MUTED, m.GOLD, m.ORANGE, m.BLUE


def main():
    s = json.load(open(sys.argv[1])); brand = m.banner_layer(s["brand"])
    meta = json.load(open(s["meta"])); fr = meta["frames"]; taps = meta["taps"]; base = os.path.dirname(s["meta"])
    rec_dur = fr[-1]["t"] + 0.4
    sc = float(s.get("scale", 0.72)); pw, ph = int(1080 * sc), int(1920 * sc); px, py = (W - pw) // 2, int(s.get("phone_y", 430))
    mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw, ph], radius=46, fill=255)
    shadow = Image.new("RGBA", (pw + 80, ph + 80), (0, 0, 0, 0)); ImageDraw.Draw(shadow).rounded_rectangle([40, 40, pw + 40, ph + 40], radius=50, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bgbase = Image.new("RGBA", (W, H), NAVY + (255,))
    cache = {}
    def frame_at(t):
        i = 0
        while i + 1 < len(fr) and fr[i + 1]["t"] <= t: i += 1
        f = os.path.join(base, os.path.basename(fr[i]["f"]))
        if f not in cache:
            if len(cache) > 6: cache.clear()
            cache[f] = Image.open(f).convert("RGB").resize((pw, ph), Image.LANCZOS)
        return cache[f]
    tmp = tempfile.mkdtemp(); silent = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    k = 0; foot2 = s["foot2"]
    # ---- intro: blurred first frame + hook + burst
    first = Image.open(os.path.join(base, os.path.basename(fr[0]["f"]))).convert("RGB")
    blur = ImageEnhance.Brightness(first.filter(ImageFilter.GaussianBlur(28))).enhance(0.45).convert("RGBA")
    lay, centre = r.hook_layer(s["hook"], s.get("sub"), int(s.get("hook_y", 470)))
    n_in = int(round(float(s.get("intro", 2.2)) * FPS))
    for j in range(n_in):
        t = j / FPS; z = 1 + 0.05 * t; bw, bh = int(W * z), int(H * z)
        img = blur.resize((bw, bh)).crop(((bw - W) // 2, (bh - H) // 2, (bw - W) // 2 + W, (bh - H) // 2 + H))
        r.chrome(img, brand)
        r.paste_scaled(img, lay, centre, 1.28 - 0.28 * m.ease_out(t / 0.35), int(255 * min(1, t / 0.12)))
        tb = t - float(s.get("burst_at", 0.7)); by = int(s.get("burst_y", 1450))
        if tb >= 0:
            if tb < 1.2: r.burst(img, W / 2, by, tb, ORANGE, BLUE, s["burst"])
            else: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, by - 92, s["burst"], 118, GOLD, NAVY)
        r.footer(img, s["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    # ---- recording
    n_rec = int(round(rec_dur * FPS)); caps = s["captions"]
    for j in range(n_rec):
        t = j / FPS; img = bgbase.copy(); r.chrome(img, brand)
        a_in = min(1.0, t / 0.25); yy = int(py + 60 * (1 - m.ease_out(a_in)))
        img.alpha_composite(shadow, (px - 40, yy - 30))
        img.paste(frame_at(t), (px, yy), mask)
        d = ImageDraw.Draw(img, "RGBA")
        for tp in taps:                      # tap ripple
            dt = t - tp["t"]
            if 0 <= dt < 0.6:
                cx = px + tp["x"] * sc; cy = yy + tp["y"] * sc; rr = 18 + 70 * m.ease_out(dt / 0.6); al = int(230 * (1 - dt / 0.6))
                d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=ORANGE + (al,), width=8)
                d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=ORANGE + (int(al * 0.8),))
        cap = None
        for c in caps:
            if t >= c["t"]: cap = c["text"]
        if cap:
            f = m.font(46); tw = d.textlength(cap, font=f)
            d.rounded_rectangle([(W - tw) / 2 - 30, 330, (W + tw) / 2 + 30, 402], radius=36, fill=GOLD + (245,))
            d.text(((W - tw) / 2, 340), cap, font=f, fill=NAVY)
        r.footer(img, s["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    # ---- end card
    last = frame_at(rec_dur)
    endsrc = [ImageEnhance.Brightness(Image.new("RGB", (W, H), NAVY)).enhance(1.0)]
    n_end = int(round(float(s.get("end_seconds", 2.0)) * FPS))
    for j in range(n_end):
        t = j / FPS; a = int(255 * m.ease_out(t / 0.25))
        bg = Image.new("RGBA", (W, H), NAVY + (255,)); bg.alpha_composite(brand, (0, 0)); d = ImageDraw.Draw(bg, "RGBA")
        y = m.text_block(d, s["end_title"], 520, 72, INK, alpha=a)
        y = m.text_block(d, s["end_sub"], y + 30, 44, GOLD, alpha=a)
        pulse = 1 + 0.05 * math.sin(2 * math.pi * t / 0.8)
        y = m.pill(d, W / 2, y + 60, "gearworldhub.com", int(64 * pulse), GOLD, NAVY, alpha=a)
        if s.get("gift_box"):   # Instagram: pilot-style "Comment GIFT" box (11 Nov 2026)
            import importlib.util as _iu
            _g = _iu.spec_from_file_location("gb", os.path.join(os.path.dirname(os.path.abspath(__file__)), "giftbox.py")); gb = _iu.module_from_spec(_g); _g.loader.exec_module(gb)
            top = y + 50; gb.draw(bg, top, t, a, s.get("gift_site_line", "gearworldhub.com · all 13 Gear Worlds in one search"),
                                  bottom_limit=top + 198, site_y=top + 222)
        else:
            m.text_block(d, s["end_line"], y + 50, 40, INK, alpha=a)
        d.text((70, H - 205), "Link in bio · gearworldhub.com", font=m.font(44), fill=INK + (a,))
        d.text((70, H - 140), s["end_small1"], font=m.font(26, False), fill=MUTED + (a,))
        d.text((70, H - 98), s["end_small2"], font=m.font(25, False), fill=MUTED + (a,))
        enc.stdin.write(bg.convert("RGB").tobytes()); k += 1
    enc.stdin.close(); enc.wait()
    total = k / FPS; mu = s["music"]; fo = max(0.0, total - 1.0)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(mu["start"]), "-t", f"{total:.2f}", "-i", mu["mp3"],
        "-filter_complex", f"[1:a]afade=t=in:d=0.15,afade=t=out:st={fo:.2f}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", s["out"]], check=True)
    print(json.dumps({"out": s["out"], "seconds": round(total, 2)}))


if __name__ == "__main__":
    main()
