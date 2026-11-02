# Gear World video tools

Python 3 + Pillow + numpy + ffmpeg. Each tool takes one JSON spec: `python3 <tool>.py spec.json`.
Output is 1080x1920, 30 fps, H.264 + AAC, with the Gear World Hub banner (`../../assets/brand-bg.jpg`), a `#ad` badge,
a price "burst" in the hook and an end card. Colours are navy / gold / orange / blue only (never red or green).
Example specs are in `examples/` (paths there are relative; point them at your own files).

| Tool | What it makes | Typical length |
|---|---|---|
| `solo.py` | One product: hook clip (text + price burst) → body clip (name, spec line, price, note) → end card with the product photo | 11–12 s |
| `reel2.py` (`"mode": "multi"`) | Several products: hook clip (+ optional price burst) → one clip per item with its own burst and label → grid end card with offer | 13–14 s |
| `story3.py` | Story: one 5 s clip with hook, price burst, label, note → short end card | 6.8 s |
| `hubreel.py` | Real screen recording of gearworldhub.com in a phone frame, with step captions and tap ripples (record with `giftfinder_rec.js`) | ~12 s |
| `biker.py` | Older 3-product reel (used by `solo.py` for its text boxes) | 12 s |
| `reel.py`, `montage.py` | Shared helpers (fonts, burst, banner, footer, end cards) | |

## Clips (fal)
- Scene image: `fal-ai/nano-banana-pro/edit` ($0.15/image), 9:16, 1K, with the retailer's product photo as reference. Keep the upper third free for text.
- Motion: `fal-ai/kling-video/v2.5-turbo/standard/image-to-video` ($0.042/s, durations "5" or "10", cfg_scale 0.6). A 10 s clip can feed both the hook (0–4 s) and the body (4.2–9.2 s) of `solo.py`.
- Typical cost: post ≈ $0.57 (1 image + 10 s), Story ≈ $0.36 (1 image + 5 s).

## Music
Mixkit tracks (free for commercial use), not stored here. Download with
`curl -sSL -o mkID.mp3 https://assets.mixkit.co/music/ID/ID.mp3`. Upbeat ones used so far (ID: start second):
158: 47 · 5: 44 or 90 · 91: 20 or 65 · 1012: 20 or 65 · 1076: 30 or 75 · 188: 71. Vary the track between videos.

## Pinterest 2:3
`ffmpeg -i in.mp4 -vf "scale=-2:1500,pad=1000:1500:(ow-iw)/2:0:color=0x0B1530" -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a copy out_pin23.mp4`

## Files
Publish finished videos to `media/` as `YYYYMMDD-p1-<site>-<product>-v1.mp4`, `-s1-` for Stories, `-pin23` for Pinterest.
Public URL: `https://raw.githubusercontent.com/evangelos-gif/gearworld-media/main/media/<file>`. Never delete files.
