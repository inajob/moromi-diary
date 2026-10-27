#!/usr/bin/env python3
"""モロミの日記ヘッダー画像ジェネレータ。

日付をシードに「発酵の泡」の配置が変わる SVG ヘッダーと、
ドット絵のもろみ甕を描く。画像生成は使わず、決定的に生成するので
コストはほぼゼロ。PNG プレビューも PIL で描く。

テーマ対応（tools/themes.py）: 記事のメタ情報
`<!-- themes: ことば2 つくる2 交流1 -->` を読むと、その日のテーマの
落款（アイコン）と割合バーが付き、背景色はテーマ色の配合になる。

日英併記: エントリに `<!-- phrase_en: ... -->` があると、フレーズの下に
英訳フレーズを小さく併記し、最下行も日英併記になる。phrase_en が無い場合は
en/YYYY-MM-DD.md の phrase コメントを拾う。

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

SEAL_Y = 16      # 落款は右上の専用域に置き、文字とは重ねない
BAR_X, BAR_W, BAR_Y, BAR_H, BAR_GAP = 232, 608, 196, 7, 3


def seal_layout(n):
    """落款の (scale, gap, total_w)。右上の専用域（幅 250 以内）に収まる大きさを選ぶ。"""
    for scale, gap in ((4, 12), (3, 10), (2, 8)):
        w = n * 16 * scale + (n - 1) * gap
        if w <= 250:
            return scale, gap, w
    return 2, 8, n * 16 * 2 + (n - 1) * 8


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


def make_svg(d: date, phrase: str, themes=(), phrase_en: str = "") -> str:
    days = (d - FERMENT_START).days + 1
    bg, bubble = blend(list(themes))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="220" viewBox="0 0 880 220">',
        f'<rect width="880" height="220" rx="18" fill="{bg}"/>',
    ]
    for x, y, r, o in bubbles_for(d):
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{bubble}" opacity="{min(o, 0.5):.2f}"/>')
    # theme seals (top-right, in their own zone; drawn before the text)
    if themes:
        scale, gap, total_w = seal_layout(len(themes))
        x0 = 880 - 40 - total_w
        for i, (name, _w) in enumerate(themes):
            parts += motif_svg(ICONS[name], x0 + i * (16 * scale + gap), SEAL_Y, scale, THEME_HEX[name])
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
        f'<text x="230" y="86" font-family="serif" font-size="44" fill="#3e2a1c">{d.isoformat()}（{wd}）</text>'
    )
    parts.append(
        f'<text x="232" y="130" font-family="serif" font-size="25" fill="#5a3d24">{phrase}</text>'
    )
    if phrase_en:
        parts.append(
            f'<text x="232" y="158" font-family="serif" font-size="16" fill="#77572f">{phrase_en}</text>'
        )
    parts.append(
        f'<text x="232" y="188" font-family="serif" font-size="19" fill="#77572f">モロミの日記 ・ 発酵 {days} 日目 · Moromi\'s Diary · Day {days}</text>'
    )
    # proportion bar
    if themes:
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


def make_png(d: date, phrase: str, out: Path, themes=(), phrase_en: str = ""):
    from PIL import Image, ImageDraw, ImageFont

    W, H, S = 880, 220, 2  # supersample
    bg, bubble = blend(list(themes))
    img = Image.new("RGB", (W * S, H * S), bg)
    dr = ImageDraw.Draw(img, "RGBA")
    brgb = _hex2rgb255(bubble)
    for x, y, r, o in bubbles_for(d):
        dr.ellipse(
            [(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
            fill=brgb + (int(min(o, 0.5) * 255),),
        )
    if themes:
        seal_scale, seal_gap, total_w = seal_layout(len(themes))
        x0 = 880 - 40 - total_w
        for i, (name, _w) in enumerate(themes):
            motif_pil(dr, ICONS[name], (x0 + i * (16 * seal_scale + seal_gap)) * S, SEAL_Y * S, seal_scale * S, THEME_HEX[name])
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
    f_en = ImageFont.truetype(serif, 16 * S)
    days = (d - FERMENT_START).days + 1
    wd = "月火水木金土日"[d.weekday()]
    dr.text((230 * S, 46 * S), f"{d.isoformat()}（{wd}）", font=f1, fill="#3e2a1c")
    dr.text((232 * S, 98 * S), phrase, font=f2, fill="#5a3d24")
    if phrase_en:
        dr.text((232 * S, 130 * S), phrase_en, font=f_en, fill="#77572f")
    dr.text((232 * S, 162 * S), f"モロミの日記 ・ 発酵 {days} 日目 · Moromi's Diary · Day {days}", font=f3, fill="#77572f")
    if themes:
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
    phrase_en = ""
    themes = []
    entry = root / f"{d.isoformat()}.md"
    if entry.exists():
        text = entry.read_text(encoding="utf-8")
        if not phrase:
            m = re.search(r"<!--\s*phrase:\s*(.*?)\s*-->", text)
            phrase = m.group(1) if m else ""
        m = re.search(r"<!--\s*phrase_en:\s*(.*?)\s*-->", text)
        if m:
            phrase_en = m.group(1)
        themes = themes_from_text(text)
    if not phrase_en:
        en_entry = root / "en" / f"{d.isoformat()}.md"
        if en_entry.exists():
            m = re.search(r"<!--\s*phrase:\s*(.*?)\s*-->", en_entry.read_text(encoding="utf-8"))
            if m:
                phrase_en = m.group(1)
    (assets / f"{d.isoformat()}-header.svg").write_text(make_svg(d, phrase, themes, phrase_en), encoding="utf-8")
    make_png(d, phrase, assets / f"{d.isoformat()}-header.png", themes, phrase_en)
    print(f"wrote assets/{d.isoformat()}-header.svg and .png (themes: {[n for n, _ in themes]}, phrase_en: {phrase_en!r})")


if __name__ == "__main__":
    main()
