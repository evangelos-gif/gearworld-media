#!/usr/bin/env python3
"""Add the Instagram 'Reply GIFT' box to an existing Story video (12 Nov 2026).
Finds when the end card starts (the 'Link in bio' line appears), finds the bottom of the
'Sold by ...' line, then draws giftbox.draw(verb='Reply') in the gap with a short fade-in.
Usage: python3 story_gift.py in.mp4 out.mp4"""
import os, subprocess, sys, importlib.util
import numpy as np
from PIL import Image
_HERE = os.path.dirname(os.path.abspath(__file__))
_g = importlib.util.spec_from_file_location("gb", os.path.join(_HERE, "giftbox.py")); gb = importlib.util.module_from_spec(_g); _g.loader.exec_module(gb)
W, H = 1080, 1920

def main():
    src, out = sys.argv[1], sys.argv[2]
    fps = eval(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", src]).decode().strip())
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    n = len(frames)
    # end card start: bright 'Link in bio' text in band y 1700-1770, x 60-780
    score = [(f[1700:1770, 60:780].min(axis=2) > 225).sum() for f in frames]
    thr = max(400, 0.5 * score[-1])
    k = n - 1
    while k > 0 and score[k - 1] >= thr: k -= 1
    end_start = k
    # bottom of the 'Sold by' line in the last frame (light text between y 1300 and 1620, centre columns)
    last = frames[-1].astype(int)
    rows = [y for y in range(1300, 1620) if ((last[y, 150:930].min(axis=1) > 150)).sum() > 6]
    top = (max(rows) + 26) if rows else 1400
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    start = end_start + int(0.2 * fps)
    for i, f in enumerate(frames):
        if i >= start:
            t = (i - start) / fps
            img = Image.fromarray(f).convert("RGBA")
            a = int(255 * gb.m.ease_out(t / 0.25))
            gb.draw(img, top, t, a, None, verb="Reply")
            enc.stdin.write(img.convert("RGB").tobytes())
        else:
            enc.stdin.write(f.tobytes())
    enc.stdin.close(); enc.wait()
    print(f"{os.path.basename(out)} frames={n} end_start={end_start/fps:.2f}s box_top={top}")

if __name__ == "__main__":
    main()
