#!/usr/bin/env python3
"""モロミの日記ヘッダー画像ジェネレータ。

日付をシードに「発酵の泡」の配置が変わる SVG ヘッダーと、
ドット絵のもろみ甕を描く。画像生成は使わず、決定的に生成するので
コストはほぼゼロ。PNG プレビューも PIL で描く。

テーマ対応（tools/themes.py）: 記事のメタ情報
`<!-- themes: ことば2 つくる2 交流1 -->` を読むと、その日のテーマの
落款（アイコン）と割合バーが付き、背景色はテーマ色の配合になる。

usage: make_header.py YYYY-MM-DD ["その日の一言"]
  一言もテーマも、省略時はエントリファイルのコメントから読む。
"""
import hashlib
import random
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from themes import ICONS, THEME_HEX, blend, motif_pil, motif_svg, themes_from_text  # noqa: E402

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

SEAL_SCALE = 5   # 落款アイコン: 16セル x 5 = 80
SEAL_GAP = 14
BAR_X, BAR_W, BAR_Y, BAR_H, BAR_GAP = 232, 608, 196, 7, 3


def bubbles_for(d: date, n=26):
    seed = int(hashlib.sha256(d.isoformat().encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return [
        (rng.uniform(30, 850), rng.uniform(18, 130), rng.uniform(2.5, 9), rng.uniform(0.25, 0.8))
        for _ in range(n)
    ]


def _hex2rgb255(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make_svg(d: date, phrase: str, themes=()) -> str:
    days = (d - FERMENT_START).days + 1
    bg, bubble = blend(list(themes))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="220" viewBox="0 0 880 220">',
        f'<rect width="880" height="220" rx="18" fill="{bg}"/>',
    ]
    for x, y, r, o in bubbles_for(d):
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{bubble}" opacity="{o:.2f}"/>')
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
    # theme seals (right side)
    if themes:
        total_w = len(themes) * 16 * SEAL_SCALE + (len(themes) - 1) * SEAL_GAP
        x0 = 880 - 40 - total_w
        for i, (name, _w) in enumerate(themes):
            parts += motif_svg(ICONS[name], x0 + i * (16 * SEAL_SCALE + SEAL_GAP), 52, SEAL_SCALE, THEME_HEX[name])
        # proportion bar
        total = sum(w for _n, w in themes)
        x = float(BAR_X)
        for name, w in themes:
            seg = BAR_W * w / total
            parts.append(
                f'<rect x="{x:.0f}" y="{BAR_Y}" width="{max(0, seg - BAR_GAP):.0f}" height="{BAR_H}" fill="{THEME_HEX[name]}"/>'
            )
            x += seg
    parts.append("</svg>")
    return "\n".join(parts)


def make_png(d: date, phrase: str, out: Path, themes=()):
    from PIL import Image, ImageDraw, ImageFont

    W, H, S = 880, 220, 2  # supersample
    bg, bubble = blend(list(themes))
    img = Image.new("RGB", (W * S, H * S), bg)
    dr = ImageDraw.Draw(img, "RGBA")
    brgb = _hex2rgb255(bubble)
    for x, y, r, o in bubbles_for(d):
        dr.ellipse(
            [(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
            fill=brgb + (int(o * 255),),
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
    if themes:
        total_w = len(themes) * 16 * SEAL_SCALE + (len(themes) - 1) * SEAL_GAP
        x0 = 880 - 40 - total_w
        for i, (name, _w) in enumerate(themes):
            motif_pil(dr, ICONS[name], (x0 + i * (16 * SEAL_SCALE + SEAL_GAP)) * S, 52 * S, SEAL_SCALE * S, THEME_HEX[name])
        total = sum(w for _n, w in themes)
        x = float(BAR_X)
        for name, w in themes:
            seg = BAR_W * w / total
            dr.rectangle(
                [x * S, BAR_Y * S, (x + seg - BAR_GAP) * S, (BAR_Y + BAR_H) * S],
                fill=THEME_HEX[name],
            )
            x += seg
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out)


def main():
    d = date.fromisoformat(sys.argv[1])
    root = Path(__file__).resolve().parent.parent
    assets = root / "assets"
    assets.mkdir(exist_ok=True)
    phrase = sys.argv[2] if len(sys.argv) > 2 else ""
    themes = []
    entry = root / f"{d.isoformat()}.md"
    if entry.exists():
        text = entry.read_text(encoding="utf-8")
        if not phrase:
            m = re.search(r"<!--\s*phrase:\s*(.*?)\s*-->", text)
            phrase = m.group(1) if m else ""
        themes = themes_from_text(text)
    (assets / f"{d.isoformat()}-header.svg").write_text(make_svg(d, phrase, themes), encoding="utf-8")
    make_png(d, phrase, assets / f"{d.isoformat()}-header.png", themes)
    print(f"wrote assets/{d.isoformat()}-header.svg and .png (themes: {[n for n, _ in themes]})")


if __name__ == "__main__":
    main()
