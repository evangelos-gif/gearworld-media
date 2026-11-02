#!/usr/bin/env python3
"""Real-motion Story (~6.8s): one 5s fal clip with hook, price burst, product label and note, then a short end card.
Colours: navy / gold / orange / blue only (no red/green). Usage: python3 story3.py spec.json"""
import json, os, subprocess, sys, tempfile
from PIL import ImageDraw
import importlib.util
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_r = importlib.util.spec_from_file_location("r", _os.path.join(_HERE, "reel.py")); r = importlib.util.module_from_spec(_r); _r.loader.exec_module(r)
_b = importlib.util.spec_from_file_location("b", _os.path.join(_HERE, "biker.py")); b = importlib.util.module_from_spec(_b); _b.loader.exec_module(b)
m = r.m; W, H, FPS = m.W, m.H, m.FPS
NAVY, INK, MUTED, GOLD, ORANGE, BLUE = m.NAVY, m.INK, m.MUTED, m.GOLD, m.ORANGE, m.BLUE


def main():
    s = json.load(open(sys.argv[1])); brand = m.banner_layer(s["brand"]); G = r.gradient()
    tmp = tempfile.mkdtemp(); silent = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    k = 0; foot2 = f"#ad · price checked {s['checked']}, may change"
    lay, centre = r.hook_layer(s["hook"], s.get("sub"), int(s.get("hook_y", 330)))
    fr = r.frames(s["clip"], s.get("start", 0), float(s.get("clip_seconds", 4.9)))
    by = int(s.get("burst_y", 1680)); bt0 = float(s.get("burst_at", 0.9))
    for j, f0 in enumerate(fr):
        t = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); r.chrome(img, brand)
        r.paste_scaled(img, lay, centre, 1.28 - 0.28 * m.ease_out(t / 0.35), int(255 * min(1, t / 0.12)))
        tb = t - bt0
        if tb >= 0:
            if tb < 1.2: r.burst(img, W / 2, by, tb, ORANGE, BLUE, s["price"])
            else: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, by - 92, s["price"], 104, GOLD, NAVY)
        if t > 2.2:
            a = int(255 * min(1, (t - 2.2) / 0.3))
            y = b.boxed(img, s["product"], int(s["label_y"]), 44, INK, a)
            if t > 2.7:
                a2 = int(255 * min(1, (t - 2.7) / 0.3))
                b.boxed(img, s["note"], int(s.get("note_y", y + 16)), 32, GOLD, a2, pad=10, alpha_box=0.8, bold=False)
        r.footer(img, s["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    last_src = fr[-int(FPS * 1.0):]
    n_end = int(round(float(s.get("end_seconds", 1.9)) * FPS))
    for j in range(n_end):
        bg = r.end_bg(last_src, j, n_end); t = j / FPS
        bg = r.end_single(bg, s, brand, t)
        a = int(255 * m.ease_out(t / 0.25)); m.text_block(ImageDraw.Draw(bg, "RGBA"), s["end_line"], H - 300, 34, GOLD, alpha=a)
        enc.stdin.write(bg.convert("RGB").tobytes()); k += 1
    enc.stdin.close(); enc.wait()
    total = k / FPS; mu = s["music"]; fo = max(0.0, total - 0.8)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(mu["start"]), "-t", f"{total:.2f}", "-i", mu["mp3"],
        "-filter_complex", f"[1:a]afade=t=in:d=0.1,afade=t=out:st={fo:.2f}:d=0.8,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", s["out"]], check=True)
    print(json.dumps({"out": s["out"], "seconds": round(total, 2)}))


if __name__ == "__main__":
    main()
