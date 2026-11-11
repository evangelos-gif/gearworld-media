#!/usr/bin/env python3
"""Instagram 'Comment GIFT' end-card box (same look as the Manager's pilot, 11 Nov 2026).
Navy box with a gold/orange border:  "💬 Comment GIFT" / "and we'll DM you our Gift Finder 🎁",
then a gold line under it (site domain · one of the 13 Gear Worlds). Colours: navy / gold / orange only."""
import functools, math, os
from PIL import Image, ImageDraw, ImageFont
import importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
_m = importlib.util.spec_from_file_location("m", os.path.join(_HERE, "montage.py")); m = importlib.util.module_from_spec(_m); _m.loader.exec_module(m)
W, H = m.W, m.H
NAVY, INK, GOLD, ORANGE = m.NAVY, m.INK, m.GOLD, m.ORANGE
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

DOMAINS = {
    "Kids' Gear World": "kidsgearworld.com", "Travel Gear World": "travelgearworld.com",
    "Technology Gear World": "technologygearworld.com", "Women's Gear World": "womensgearworld.com",
    "Men's Gear World": "mensgearworld.com", "Home Gear World": "homegearworld.com",
    "Garden Gear World": "gardengearworld.com", "Construction Gear World": "constructiongearworld.com",
    "Car Gear World": "cargearworld.com", "Pets Gear World": "petsgearworld.com",
    "Gaming Gear World": "gaminggearworld.com", "Biker Gear World": "bikergearworld.com",
    "Sporty Gear World": "sportygearworld.com",
}


@functools.lru_cache(maxsize=8)
def emoji(ch, px):
    """Colour emoji as an RGBA image px tall (Noto Color Emoji only renders at 109 px, so scale)."""
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    bb = im.getbbox(); im = im.crop(bb)
    return im.resize((max(1, int(im.width * px / im.height)), px), Image.LANCZOS)


def _with_alpha(im, a):
    if a >= 255: return im
    im = im.copy(); al = im.getchannel("A").point(lambda v: v * a // 255); im.putalpha(al); return im


def draw(bg, top, t, a, site_line, bottom_limit=1606, site_y=1626):
    """Draw the box on bg (RGBA) starting at y=top. Shrinks to fit above bottom_limit.
    t = seconds into the end card (for the pop-in and the border pulse), a = alpha 0-255."""
    full_h = 198
    h = max(120, min(full_h, bottom_limit - top))
    s = h / full_h
    pop = 0.9 + 0.1 * m.ease_out(t / 0.35)
    bw, bh = 900 * s * pop, h * pop
    cx, cy = W / 2, top + h / 2
    x0, y0, x1, y1 = cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2
    d = ImageDraw.Draw(bg, "RGBA")
    mix = 0.5 + 0.5 * math.sin(2 * math.pi * t / 0.9)          # border gold <-> orange
    border = tuple(int(GOLD[i] * (1 - mix) + ORANGE[i] * mix) for i in range(3))
    d.rounded_rectangle([x0 + 4, y0 + 8, x1 + 4, y1 + 8], radius=int(30 * s), fill=(0, 0, 0, int(110 * a / 255)))
    d.rounded_rectangle([x0, y0, x1, y1], radius=int(30 * s), fill=(12, 22, 42, int(240 * a / 255)),
                        outline=border + (a,), width=max(3, int(5 * s)))
    # line 1: 💬 Comment GIFT
    f1 = m.font(int(62 * s * pop)); e1 = emoji("\U0001F4AC", int(54 * s * pop))
    w_c = d.textlength("Comment ", font=f1); w_g = d.textlength("GIFT", font=f1); gap = 16 * s
    tw = e1.width + gap + w_c + w_g; x = cx - tw / 2; ty = y0 + bh * 0.12
    bg.alpha_composite(_with_alpha(e1, a), (int(x), int(ty + 8 * s)))
    x += e1.width + gap
    d.text((x, ty), "Comment ", font=f1, fill=INK + (a,)); d.text((x + w_c, ty), "GIFT", font=f1, fill=GOLD + (a,))
    # line 2: and we'll DM you our Gift Finder 🎁
    f2 = m.font(int(36 * s * pop)); e2 = emoji("\U0001F381", int(38 * s * pop)); txt = "and we'll DM you our Gift Finder"
    w2 = d.textlength(txt, font=f2); tw2 = w2 + 12 * s + e2.width; x2 = cx - tw2 / 2; ty2 = y0 + bh * 0.58
    d.text((x2, ty2), txt, font=f2, fill=INK + (a,))
    bg.alpha_composite(_with_alpha(e2, a), (int(x2 + w2 + 12 * s), int(ty2 - 2 * s)))
    # gold line under the box
    if site_line:
        f3 = m.font(30); w3 = d.textlength(site_line, font=f3)
        d.text((W / 2 - w3 / 2, max(site_y, y1 + 18)), site_line, font=f3, fill=GOLD + (a,))
    return y1


def site_line_for(site):
    dom = DOMAINS.get(site)
    return f"{dom} · one of the 13 Gear Worlds" if dom else "gearworldhub.com · all 13 Gear Worlds in one search"
