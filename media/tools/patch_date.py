#!/usr/bin/env python3
"""Change the 'price checked <date>' small print inside an existing reel/story video, frame by frame (14 Nov 2026).
Two small-print lines (drawn by reel.footer() and reel.end_single()) are handled:
  footer line 2:  '#ad · price checked OLD, may change'                               Inter Medium ~25, bottom left
  end card:       '#ad · We may earn a commission · price checked OLD, may change'    Inter Medium ~27, bottom left
In every frame each old line is searched for (any size 22-34 px, any spot in the bottom 360 px, so animated
footers that zoom in are found too), removed with inpainting and redrawn with the new date at the same size,
position, colour and opacity. Frames where the line is not visible are left untouched. Audio is copied.
Usage: python3 patch_date.py in.mp4 out.mp4 "5 Nov 2026" "14 Nov 2026" """
import os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920                # set from the input in main(); 1000x1500 Pinterest cuts (pin23) are the 9:16 reel scaled by S
S = 1.0
MUTED = (190, 198, 212)
FONT = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
Y0, X1 = H - 360, W              # search region: y >= Y0, x < X1
THRESH = 0.55

def lines(old, new):
    return [  # (old, new, sizes to try, alpha)
        (f"#ad · price checked {old}, may change", f"#ad · price checked {new}, may change", np.arange(22, 34.1, 0.5) * S, 230),
        (f"#ad · We may earn a commission · price checked {old}, may change",
         f"#ad · We may earn a commission · price checked {new}, may change", np.arange(24, 30.1, 0.5) * S, 255),
    ]

def template(text, size):
    f = ImageFont.truetype(FONT, size); l, t, r, b = f.getbbox(text)
    im = Image.new("L", (r - l + 2, b - t + 2), 0); ImageDraw.Draw(im).text((1 - l, 1 - t), text, font=f, fill=255)
    return np.array(im), l - 1, t - 1

def main():
    global W, H, S, Y0, X1
    src, out, old, new = sys.argv[1:5]
    W, H = map(int, subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src]).decode().strip().split(","))
    S = min(W / 1080, H / 1920); Y0, X1 = H - int(round(360 * S)), W
    fps = eval(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src]).decode().strip())
    raw = subprocess.check_output(["ffmpeg", "-nostdin", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    specs = []
    for ot, nt, sizes, alpha in lines(old, new):
        specs.append(dict(old=ot, new=nt, alpha=alpha, tpl=[(float(s),) + template(ot, float(s)) for s in sizes]))
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    counts = [0, 0]; log = []
    for fi, f in enumerate(frames):
        img = f.copy(); found_end = False
        for k in (1, 0):   # end-card line first; the footer never shows on the end card
            sp = specs[k]
            if k == 0 and found_end: continue
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)[Y0:, :X1]
            best = (-1, None)
            for size, tp, l, t in sp["tpl"]:
                if tp.shape[0] >= gray.shape[0] or tp.shape[1] >= gray.shape[1]: continue
                res = cv2.matchTemplate(gray, tp, cv2.TM_CCOEFF_NORMED)
                _, mx, _, loc = cv2.minMaxLoc(res)
                if mx > best[0]: best = (mx, (size, loc[0] - l, Y0 + loc[1] - t))
            if best[0] < THRESH and k == 0:
                # footer sliding in from the bottom edge: match only the top 3/4, 1/2 or 2/5 of the letters
                g2 = cv2.copyMakeBorder(gray, 0, 40, 0, 0, cv2.BORDER_CONSTANT, value=0)
                for size, tp, l, t in sp["tpl"]:
                    for frac in (0.75, 0.5, 0.4):
                        part = tp[: max(4, int(tp.shape[0] * frac))]
                        res = cv2.matchTemplate(g2, part, cv2.TM_CCOEFF_NORMED)
                        _, mx, _, loc = cv2.minMaxLoc(res)
                        if mx > max(best[0], 0.7) and Y0 + loc[1] + tp.shape[0] > H - 4:   # only where it really runs off the bottom
                            best = (mx, (size, loc[0] - l, Y0 + loc[1] - t))
            if best[0] < THRESH: continue
            size, x, y = best[1]
            fnt = ImageFont.truetype(FONT, size)
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((x, y), sp["old"], font=fnt, fill=255)
            mask = cv2.dilate((np.array(m) > 30).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
            img = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)
            pil = Image.fromarray(img).convert("RGBA")
            ImageDraw.Draw(pil, "RGBA").text((x, y), sp["new"], font=fnt, fill=MUTED + (sp["alpha"],))
            img = np.array(pil.convert("RGB")); counts[k] += 1
            if k == 1: found_end = True
            if fi < 14 or fi % 60 == 0: log.append(f"f{fi}:{'F' if k == 0 else 'E'} s={size} x={x} y={y} c={best[0]:.2f}")
        enc.stdin.write(img.tobytes())
    enc.stdin.close(); enc.wait()
    print(f"{os.path.basename(out)} {W}x{H}: frames={len(frames)} footer-patched={counts[0]} endcard-patched={counts[1]}")
    print("   " + " | ".join(log[:18]))

if __name__ == "__main__":
    main()
