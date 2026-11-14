#!/usr/bin/env python3
"""Pinterest image pin, 1000x1500 (2:3), made for Pinterest search (14 Nov 2026, «ΕΓΚΡΙΝΩ PINTEREST ΕΙΚΟΝΕΣ»).
Navy background with the Gear World Hub banner, a search-style headline (what people type, not a question hook),
the retailer's product photo on a white card, product name, price pill, seller + price-check small print, site line.
Colours: navy / gold / orange / blue / white only (never red or green).
Usage: python3 pin_image.py spec.json
spec: {"photo": path or https URL, "headline": "Cordless impact wrench for wheel nuts", "product": "Einhell ... ",
       "price": "£122.95", "site": "Construction Gear World", "seller": "Tooled Up", "checked": "14 Nov 2026",
       "out": "out.jpg"}"""
import io, json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageOps
import importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
_m = importlib.util.spec_from_file_location("m", os.path.join(_HERE, "montage.py")); m = importlib.util.module_from_spec(_m); _m.loader.exec_module(m)
_g = importlib.util.spec_from_file_location("gb", os.path.join(_HERE, "giftbox.py")); gb = importlib.util.module_from_spec(_g); _g.loader.exec_module(gb)
PW, PH = 1000, 1500
NAVY, INK, MUTED, GOLD, ORANGE, BLUE = m.NAVY, m.INK, m.MUTED, m.GOLD, m.ORANGE, m.BLUE
UA = "GearWorldQA-bot/1.0 (+read-only check)"
BRAND = os.path.join(_HERE, "..", "..", "assets", "brand-bg.jpg")


def load_photo(src):
    if src.startswith("http"):
        raw = subprocess.run(["curl", "-sS", "-L", "-m", "30", "-A", UA, src], capture_output=True, check=True).stdout
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    return Image.open(src).convert("RGBA")


def lines(d, text, f, width, max_lines):
    out = m.wrap(d, text, f, width)
    if len(out) > max_lines:
        out = out[:max_lines]; out[-1] = out[-1].rstrip(",.;:") + "…"
    return out


def main():
    s = json.load(open(sys.argv[1]))
    img = Image.new("RGBA", (PW, PH), NAVY + (255,))
    # banner (same Gear World Hub banner as the videos), fading into navy
    b = ImageOps.fit(Image.open(BRAND).convert("RGB"), (PW, 260), method=Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", b.size, 255); md = ImageDraw.Draw(mask)
    for i in range(100):
        md.line([(0, 160 + i), (PW, 160 + i)], fill=int(255 * (1 - i / 100)))
    b.putalpha(mask); img.alpha_composite(b, (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # #ad badge
    fa = m.font(30); tw = d.textlength("#ad", font=fa)
    d.rounded_rectangle([PW - 40 - tw - 28, 28, PW - 40, 28 + 52], radius=26, fill=(255, 255, 255, 235))
    d.text((PW - 40 - tw - 14, 36), "#ad", font=fa, fill=NAVY)
    # headline (search words)
    y = 250
    fh = m.font(64)
    for ln in lines(d, s["headline"], fh, PW - 120, 2):
        w = d.textlength(ln, font=fh); d.text(((PW - w) / 2, y), ln, font=fh, fill=INK); y += 76
    # product photo on a white card
    y += 18; card_h = 640 if y < 360 else 580
    cx0, cx1 = 70, PW - 70
    d.rounded_rectangle([cx0, y, cx1, y + card_h], radius=34, fill=(255, 255, 255, 255))
    ph = load_photo(s["photo"]); ph = ImageOps.contain(ph, (cx1 - cx0 - 80, card_h - 80), method=Image.LANCZOS)
    img.alpha_composite(ph, (int((PW - ph.width) / 2), int(y + (card_h - ph.height) / 2)))
    y += card_h + 30
    # product name
    fp = m.font(40)
    for ln in lines(d, s["product"], fp, PW - 140, 2):
        w = d.textlength(ln, font=fp); d.text(((PW - w) / 2, y), ln, font=fp, fill=INK); y += 50
    # price pill
    y += 14
    y = m.pill(d, PW / 2, y, f'{s["price"]} on {s["site"]}', 46, GOLD, NAVY) + 26
    # small print and site line
    fs = m.font(26, False)
    sp = f'Sold by {s["seller"]} (not by Gear World) · price checked {s["checked"]}, may change'
    for ln in lines(d, sp, fs, PW - 140, 2):
        w = d.textlength(ln, font=fs); d.text(((PW - w) / 2, y), ln, font=fs, fill=MUTED); y += 34
    fl = m.font(30); site_line = gb.site_line_for(s["site"])
    w = d.textlength(site_line, font=fl); d.text(((PW - w) / 2, PH - 78), site_line, font=fl, fill=GOLD)
    fsm = m.font(22, False); t2 = "We may earn a commission from qualifying purchases."
    w = d.textlength(t2, font=fsm); d.text(((PW - w) / 2, PH - 40), t2, font=fsm, fill=MUTED)
    img.convert("RGB").save(s["out"], quality=90)
    print(json.dumps({"out": s["out"], "bottom_of_text": y}))


if __name__ == "__main__":
    main()
