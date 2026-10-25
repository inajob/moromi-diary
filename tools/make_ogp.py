#!/usr/bin/env python3
"""モロミの日記 OGP 画像ジェネレータ（1200x630 PNG）。

og:image は SVG に対応していないので、ヘッダーと同じ画材（泡・甕・明朝）を
PIL で 1200x630 に組み直して PNG にする。画像生成は使わず決定的に生成する。

usage:
  make_ogp.py YYYY-MM-DD "その日の一言"   # assets/YYYY-MM-DD-ogp.png
  make_ogp.py default                     # assets/ogp-default.png
  make_ogp.py all                         # 全エントリ分（フレーズは md のコメントから）
"""
import hashlib
import random
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_header import COLORS, FERMENT_START, PIXEL  # noqa: E402

W, H, S = 1200, 630, 2
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
BG = "#fbf4e4"


def bubbles(d: date, n=42):
    seed = int(hashlib.sha256(("ogp" + d.isoformat()).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return [
        (rng.uniform(20, W - 20), rng.uniform(16, H - 16), rng.uniform(4, 17), rng.uniform(0.2, 0.75))
        for _ in range(n)
    ]


def draw_jar(dr, ox, oy, scale):
    for ri, row in enumerate(PIXEL):
        for ci, ch in enumerate(row):
            if ch == ".":
                continue
            dr.rectangle(
                [ox + ci * scale, oy + ri * scale, ox + (ci + 1) * scale, oy + (ri + 1) * scale],
                fill=COLORS[ch],
            )


def fit_font(dr, text, start_px, max_width):
    from PIL import ImageFont

    px = start_px
    while px > 20:
        f = ImageFont.truetype(SERIF, px * S)
        if dr.textlength(text, font=f) <= max_width * S:
            return f
        px -= 2
    return ImageFont.truetype(SERIF, 20 * S)


def render(d, phrase, out: Path):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (W * S, H * S), BG)
    dr = ImageDraw.Draw(img, "RGBA")
    for x, y, r, o in bubbles(d):
        dr.ellipse(
            [(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
            fill=(232, 200, 122, int(o * 255)),
        )
    # jar: 16x13 cells, scale 24 -> 384x312, right side
    draw_jar(dr, 736 * S, 176 * S, 24 * S)

    def text(x, y, s, px, fill):
        dr.text((x * S, y * S), s, font=ImageFont.truetype(SERIF, px * S), fill=fill)

    days = (d - FERMENT_START).days + 1
    wd = "月火水木金土日"[d.weekday()]
    text(78, 84, "モロミの日記", 34, "#a3805a")
    text(76, 138, f"{d.isoformat()}（{wd}）", 62, "#4a3428")
    if phrase:
        f = fit_font(dr, phrase, 56, 600)
        dr.text((78 * S, 268 * S), phrase, font=f, fill="#7a5c3e")
    text(78, 512, f"発酵 {days} 日目", 30, "#a3805a")
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out)
    print(f"wrote {out.name}")


def render_default(out: Path):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (W * S, H * S), BG)
    dr = ImageDraw.Draw(img, "RGBA")
    for x, y, r, o in bubbles(FERMENT_START):
        dr.ellipse(
            [(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
            fill=(232, 200, 122, int(o * 255)),
        )
    draw_jar(dr, 716 * S, 159 * S, 24 * S)
    dr.text((78 * S, 208 * S), "モロミの日記", font=ImageFont.truetype(SERIF, 84 * S), fill="#4a3428")
    dr.text((80 * S, 330 * S), "発酵は続く", font=ImageFont.truetype(SERIF, 40 * S), fill="#7a5c3e")
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out)
    print(f"wrote {out.name}")


def main():
    root = Path(__file__).resolve().parent.parent
    assets = root / "assets"
    assets.mkdir(exist_ok=True)
    arg = sys.argv[1]
    if arg == "default":
        render_default(assets / "ogp-default.png")
    elif arg == "all":
        for md in sorted(root.glob("????-??-??.md")):
            m = re.search(r"<!--\s*phrase:\s*(.*?)\s*-->", md.read_text(encoding="utf-8"))
            render(date.fromisoformat(md.stem), m.group(1) if m else "", assets / f"{md.stem}-ogp.png")
    else:
        d = date.fromisoformat(arg)
        phrase = sys.argv[2] if len(sys.argv) > 2 else ""
        render(d, phrase, assets / f"{d.isoformat()}-ogp.png")


if __name__ == "__main__":
    main()
