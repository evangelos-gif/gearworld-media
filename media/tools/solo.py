#!/usr/bin/env python3
"""Single-product real-motion reel: hook clip (text + price burst) -> body clip (name/spec/price/note) -> end card (big photo).
Colours: navy / gold / orange / blue only (no red/green). Usage: python3 solo.py spec.json"""
import json, os, subprocess, sys, tempfile
from PIL import ImageDraw
import importlib.util
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_r = importlib.util.spec_from_file_location("r", _os.path.join(_HERE, "reel.py")); r = importlib.util.module_from_spec(_r); _r.loader.exec_module(r)
_b = importlib.util.spec_from_file_location("b", _os.path.join(_HERE, "biker.py")); b = importlib.util.module_from_spec(_b); _b.loader.exec_module(b)
_g = importlib.util.spec_from_file_location("gb", _os.path.join(_HERE, "giftbox.py")); gb = importlib.util.module_from_spec(_g); _g.loader.exec_module(gb)
m = r.m; W, H, FPS = m.W, m.H, m.FPS
NAVY, INK, MUTED, GOLD, ORANGE, BLUE = m.NAVY, m.INK, m.MUTED, m.GOLD, m.ORANGE, m.BLUE


def main():
    spec = json.load(open(sys.argv[1])); brand = m.banner_layer(spec["brand"]); G = r.gradient()
    tmp = tempfile.mkdtemp(); silent = os.path.join(tmp, "v.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    k = 0; foot2 = f"#ad · price checked {spec['checked']}, may change"
    hk = spec["hook"]; hook_s = float(hk.get("seconds", 3.5))
    lay, centre = r.hook_layer(hk["text"], hk.get("sub"), int(hk.get("y", 380)))
    hs = spec["hook_clip"]; hf = r.frames(hs["clip"], hs.get("start", 0), hook_s)
    bt0 = float(hk.get("burst_at", 0.8)); by = int(hk.get("burst_y", 1560))
    for j, f0 in enumerate(hf):
        t = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); r.chrome(img, brand)
        r.paste_scaled(img, lay, centre, 1.28 - 0.28 * m.ease_out(t / 0.35), int(255 * min(1, t / 0.12)))
        tb = t - bt0
        if tb >= 0:
            if tb < 1.2: r.burst(img, W / 2, by, tb, ORANGE, BLUE, spec["price"])
            else: m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, by - 92, spec["price"], 118, GOLD, NAVY)
        r.footer(img, spec["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    bs = spec["body_clip"]; bf = r.frames(bs["clip"], bs.get("start", 0), float(bs["seconds"]))
    for j, f0 in enumerate(bf):
        t = j / FPS; img = f0.convert("RGBA"); img.alpha_composite(G); r.chrome(img, brand)
        if t < 0.18:   # quick light flash on the cut
            from PIL import Image
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 248, 235, int(110 * (1 - t / 0.18)))))
        a = int(255 * min(1, t / 0.3))
        y = b.boxed(img, spec["product"], int(spec.get("product_y", 380)), 50, INK, a)
        y = b.boxed(img, spec["spec_line"], y + 14, 40, GOLD, a, alpha_box=0.6)
        m.pill(ImageDraw.Draw(img, "RGBA"), W / 2, y + 14, spec["price"], 72, GOLD, NAVY, alpha=a)
        if spec.get("note_line") and t > 0.8:
            a2 = int(255 * min(1, (t - 0.8) / 0.3))
            b.boxed(img, spec["note_line"], int(spec.get("note_y", 1640)), 34, INK, a2, pad=10, alpha_box=0.8, bold=False)
        r.footer(img, spec["footer1"], foot2)
        enc.stdin.write(img.convert("RGB").tobytes()); k += 1
    last_src = bf[-int(FPS * 1.0):]
    n_end = int(round(float(spec.get("end_seconds", 2.6)) * FPS))
    for j in range(n_end):
        bg = r.end_bg(last_src, j, n_end); t = j / FPS
        bg = r.end_single(bg, spec, brand, t)
        if spec.get("gift_box"):   # Instagram: pilot-style "Comment GIFT" box (11 Nov 2026)
            a = int(255 * m.ease_out(t / 0.25))
            gb.draw(bg, bg.info.get("end_y", 1385) + 20, t, a, spec.get("gift_site_line") or gb.site_line_for(spec["site"]))
        elif spec.get("end_line"):
            a = int(255 * m.ease_out(t / 0.25)); m.text_block(ImageDraw.Draw(bg, "RGBA"), spec["end_line"], H - 300, 34, GOLD, alpha=a)
        enc.stdin.write(bg.convert("RGB").tobytes()); k += 1
    enc.stdin.close(); enc.wait()
    total = k / FPS; mu = spec["music"]; fod = float(mu.get("fade_out", 1.0)); fo = max(0.0, total - fod)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-ss", str(mu["start"]), "-t", f"{total:.2f}", "-i", mu["mp3"],
        "-filter_complex", f"[1:a]afade=t=in:d=0.15,afade=t=out:st={fo:.2f}:d={fod},loudnorm=I={float(mu.get('lufs', -14))}:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", spec["out"]], check=True)
    print(json.dumps({"out": spec["out"], "seconds": round(total, 2)}))


if __name__ == "__main__":
    main()
