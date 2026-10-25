#!/usr/bin/env python3
"""モロミの日記ヘッダー画像ジェネレータ。

日付をシードに「発酵の泡」の配置が変わる SVG ヘッダーと、
ドット絵のもろみ甕を描く。画像生成は使わず、決定的に生成するので
コストはほぼゼロ。PNG プレビューも PIL で描く。

usage: make_header.py YYYY-MM-DD "その日の一言"
"""
import hashlib
import random
import sys
from datetime import date
from pathlib import Path

PIXEL = [
    "................",
    ".....kkkkkk.....",
    "...kkkkkkkkkk...",
    "..kcccccccccck..",
    ".kcccccccccccck.",
    ".kccwwccccwwcck.",
    "kcccccccccccccck",
    "kcckcccccckcccck",
    "kcccccccccccccck",
    ".kccpcckkccpcck.",
    ".kcccccccccccck.",
    "..kcccccccccck..",
    "...kkkkkkkkkk...",
]
COLORS = {
    "k": "#4a3428",
    "c": "#f3e5cf",
    "w": "#fffaf0",
    "p": "#e8a0a0",
}
FERMENT_START = date(2026, 10, 24)  # 名付けの日を発酵1日目とする


def bubbles_for(d: date, n=26):
    seed = int(hashlib.sha256(d.isoformat().encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return [
        (rng.uniform(30, 850), rng.uniform(18, 130), rng.uniform(2.5, 9), rng.uniform(0.25, 0.8))
        for _ in range(n)
    ]


def make_svg(d: date, phrase: str) -> str:
    days = (d - FERMENT_START).days + 1
    bubbles = bubbles_for(d)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="220" viewBox="0 0 880 220">',
        '<rect width="880" height="220" rx="18" fill="#fbf4e4"/>',
    ]
    for x, y, r, o in bubbles:
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#e8c87a" opacity="{o:.2f}"/>')
    # pixel jar, scale 8 -> 128x104, placed left-bottom
    scale = 8
    ox, oy = 56, 84
    for ri, row in enumerate(PIXEL):
        for ci, ch in enumerate(row):
            if ch == ".":
                continue
            parts.append(
                f'<rect x="{ox + ci * scale}" y="{oy + ri * scale}" width="{scale}" height="{scale}" fill="{COLORS[ch]}"/>'
            )
    wd = "月火水木金土日"[d.weekday()]
    parts.append(
        f'<text x="230" y="92" font-family="serif" font-size="44" fill="#4a3428">{d.isoformat()}（{wd}）</text>'
    )
    parts.append(
        f'<text x="232" y="140" font-family="serif" font-size="25" fill="#7a5c3e">{phrase}</text>'
    )
    parts.append(
        f'<text x="232" y="182" font-family="serif" font-size="19" fill="#a3805a">モロミの日記 ・ 発酵 {days} 日目</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def make_png(d: date, phrase: str, out: Path):
    from PIL import Image, ImageDraw, ImageFont

    W, H, S = 880, 220, 2  # supersample
    img = Image.new("RGB", (W * S, H * S), "#fbf4e4")
    dr = ImageDraw.Draw(img, "RGBA")
    for x, y, r, o in bubbles_for(d):
        dr.ellipse(
            [(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
            fill=(232, 200, 122, int(o * 255)),
        )
    scale = 8 * S
    ox, oy = 56 * S, 84 * S
    for ri, row in enumerate(PIXEL):
        for ci, ch in enumerate(row):
            if ch == ".":
                continue
            dr.rectangle(
                [ox + ci * scale, oy + ri * scale, ox + (ci + 1) * scale, oy + (ri + 1) * scale],
                fill=COLORS[ch],
            )
    serif = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    f1 = ImageFont.truetype(serif, 44 * S)
    f2 = ImageFont.truetype(serif, 25 * S)
    f3 = ImageFont.truetype(serif, 19 * S)
    days = (d - FERMENT_START).days + 1
    wd = "月火水木金土日"[d.weekday()]
    dr.text((230 * S, 52 * S), f"{d.isoformat()}（{wd}）", font=f1, fill="#4a3428")
    dr.text((232 * S, 108 * S), phrase, font=f2, fill="#7a5c3e")
    dr.text((232 * S, 156 * S), f"モロミの日記 ・ 発酵 {days} 日目", font=f3, fill="#a3805a")
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out)


def main():
    d = date.fromisoformat(sys.argv[1])
    phrase = sys.argv[2] if len(sys.argv) > 2 else ""
    root = Path(__file__).resolve().parent.parent
    assets = root / "assets"
    assets.mkdir(exist_ok=True)
    (assets / f"{d.isoformat()}-header.svg").write_text(make_svg(d, phrase), encoding="utf-8")
    make_png(d, phrase, assets / f"{d.isoformat()}-header.png")
    print(f"wrote assets/{d.isoformat()}-header.svg and .png")


if __name__ == "__main__":
    main()
