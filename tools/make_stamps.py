#!/usr/bin/env python3
"""日記用「挿絵スタンプ」: 16x16 の LED マトリクス風ドット絵パネルを SVG/PNG で生成する。

- 迷路スタンプは棒倒し法で本当に生成する（日付シード）。
  16x16 に合わせ、部屋は {1,3,...,15} の 8x8、右端と下端の壁はパネルの縁が兼ねる。
- 画像生成は使わない。決定的生成でコストほぼゼロ。
- 挿絵パターンの一つとして使う（他のパターンも今後追加してよい）。

usage: make_stamps.py YYYY-MM-DD
"""
import hashlib
import random
import sys
from datetime import date
from pathlib import Path

SIZE = 16  # 16x16 dots

MIC = [
    ".....######.....",
    "....########....",
    "....##....##....",
    "....##....##....",
    "....##....##....",
    "....##....##....",
    "....########....",
    ".....######.....",
    "..#..........#..",
    "..#..........#..",
    "...#........#...",
    "....########....",
    ".......##.......",
    ".......##.......",
    ".....######.....",
    "....########....",
]

HEART = [
    "................",
    "..###......###..",
    ".#####....#####.",
    ".##############.",
    ".##############.",
    ".##############.",
    ".##############.",
    "..############..",
    "...##########...",
    "....########....",
    ".....######.....",
    "......####......",
    ".......##.......",
    "................",
    "................",
    "................",
]


def bou_taoshi_maze(d: date):
    """16x16 グリッドに棒倒し法で完全迷路を作る。1=壁。

    部屋座標は {1,3,5,7,9,11,13,15}、壁座標は {0,2,...,14}。
    上端と左端は壁ドット、右端と下端はパネルの縁が壁を兼ねる。
    """
    seed = int(hashlib.sha256(("maze" + d.isoformat()).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    wall_coords = list(range(0, SIZE - 1, 2))  # 0,2,...,14
    g = [[0] * SIZE for _ in range(SIZE)]
    # 上端・左端の境界と柱
    for i in range(SIZE):
        g[0][i] = 1
        g[i][0] = 1
    for y in wall_coords[1:]:
        for x in wall_coords[1:]:
            g[y][x] = 1  # 柱
    # 棒倒し: 柱ごとに隣の壁スロットを1つ倒す（最上段の柱以外は上に倒さない）
    for y in wall_coords[1:]:
        for x in wall_coords[1:]:
            dirs = [(0, 1), (-1, 0), (1, 0)]
            if y == 2:
                dirs.append((0, -1))
            cands = []
            for dx, dy in dirs:
                wx, wy = x + dx, y + dy
                if 0 <= wx < SIZE and 0 <= wy < SIZE and g[wy][wx] == 0:
                    cands.append((wx, wy))
            if cands:
                wx, wy = rng.choice(cands)
                g[wy][wx] = 1
    return ["".join("#" if c else "." for c in row) for row in g]


def svg_panel(grid, color, path: Path):
    cell, r = 20, 7
    wh = SIZE * cell
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{wh}" height="{wh}" viewBox="0 0 {wh} {wh}">',
        f'<rect width="{wh}" height="{wh}" rx="24" fill="#101828"/>',
    ]
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            cx, cy = x * cell + cell // 2, y * cell + cell // 2
            fill = color if ch == "#" else "#26314a"
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def main():
    d = date.fromisoformat(sys.argv[1])
    root = Path(__file__).resolve().parent.parent
    out = root / "assets" / "stamps"
    out.mkdir(parents=True, exist_ok=True)
    stamps = [
        ("maze", bou_taoshi_maze(d), "#ffb020"),
        ("mic", MIC, "#4cc9f0"),
        ("heart", HEART, "#ff5a76"),
    ]
    for name, grid, color in stamps:
        assert len(grid) == SIZE and all(len(r) == SIZE for r in grid), name
        svg_panel(grid, color, out / f"{name}.svg")

    # combined PNG preview
    from PIL import Image, ImageDraw, ImageFont

    cell, S = 20, 2
    panel = SIZE * cell
    W, H = (panel * 3 + 32 * 2) * S, (panel + 44) * S
    img = Image.new("RGB", (W, H), "#fbf4e4")
    dr = ImageDraw.Draw(img)
    serif = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
    font = ImageFont.truetype(serif, 20 * S)
    labels = {"maze": "迷路（棒倒し生成）", "mic": "マイク", "heart": "ハート"}
    for i, (name, grid, color) in enumerate(stamps):
        ox = (i * (panel + 32)) * S
        dr.rounded_rectangle([ox, 0, ox + panel * S, panel * S], radius=24 * S, fill="#101828")
        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                cx = ox + (x * cell + cell // 2) * S
                cy = (y * cell + cell // 2) * S
                rr = 7 * S
                fill = color if ch == "#" else "#26314a"
                dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fill)
        dr.text((ox + 8 * S, (panel + 10) * S), labels[name], font=font, fill="#4a3428")
    img = img.resize((W // S, H // S), Image.LANCZOS)
    img.save(out / "preview.png")
    print("wrote 16x16 stamps:", ", ".join(n for n, _, _ in stamps))


if __name__ == "__main__":
    main()
