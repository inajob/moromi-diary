#!/usr/bin/env python3
"""挿絵シーン試作: コロコロ迷路を上から見た SVG イラスト。

迷路そのものは make_stamps の棒倒し法で生成し、木箱・ビー玉・ネジを
SVG の基本図形で描く。画像生成は使わない。

usage: scene_maze.py YYYY-MM-DD   # assets/scenes/maze-box.svg
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_stamps import bou_taoshi_maze  # noqa: E402

W, H = 680, 660
BOX_X, BOX_Y, BOX = 90, 56, 500
FLOOR_INSET = 26
CELL = (BOX - FLOOR_INSET * 2) // 16  # 28
FX, FY = BOX_X + FLOOR_INSET, BOX_Y + FLOOR_INSET


def main():
    d = date.fromisoformat(sys.argv[1])
    grid = bou_taoshi_maze(d)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<defs>",
        '<radialGradient id="ball" cx="35%" cy="30%" r="80%">',
        '<stop offset="0%" stop-color="#ffffff"/><stop offset="55%" stop-color="#aeb8c2"/>'
        '<stop offset="100%" stop-color="#5a636e"/></radialGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="20" fill="#fdf9ef"/>',
        # box and floor
        f'<rect x="{BOX_X}" y="{BOX_Y}" width="{BOX}" height="{BOX}" rx="18" fill="#e0aa6e" stroke="#8a5a2b" stroke-width="6"/>',
        f'<rect x="{FX}" y="{FY}" width="{CELL*16}" height="{CELL*16}" fill="#f8ecd4"/>',
    ]
    # maze walls as blocks
    for gy, row in enumerate(grid):
        for gx, ch in enumerate(row):
            if ch == "#":
                parts.append(
                    f'<rect x="{FX + gx*CELL}" y="{FY + gy*CELL}" width="{CELL}" height="{CELL}" fill="#b07a3f"/>'
                )
    # start and goal cells
    floors = [(gx, gy) for gy, row in enumerate(grid) for gx, ch in enumerate(row) if ch == "."]
    sx, sy = floors[0]
    gx2, gy2 = floors[-1]
    cx, cy = FX + sx * CELL + CELL // 2, FY + sy * CELL + CELL // 2
    parts.append(f'<ellipse cx="{cx+4}" cy="{cy+6}" rx="11" ry="5" fill="#00000022"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="url(#ball)"/>')
    ex, ey = FX + gx2 * CELL + CELL // 2, FY + gy2 * CELL + CELL // 2
    parts.append(f'<line x1="{ex}" y1="{ey+10}" x2="{ex}" y2="{ey-12}" stroke="#4a3428" stroke-width="3"/>')
    parts.append(f'<path d="M {ex} {ey-12} L {ex+15} {ey-7} L {ex} {ey-2} Z" fill="#d94f4f"/>')
    # screws at the four corners of the box
    for px, py in [
        (BOX_X + 15, BOX_Y + 15),
        (BOX_X + BOX - 15, BOX_Y + 15),
        (BOX_X + 15, BOX_Y + BOX - 15),
        (BOX_X + BOX - 15, BOX_Y + BOX - 15),
    ]:
        parts.append(f'<circle cx="{px}" cy="{py}" r="9" fill="#c0c6cc" stroke="#7a8288" stroke-width="2"/>')
        parts.append(
            f'<line x1="{px-6}" y1="{py}" x2="{px+6}" y2="{py}" stroke="#7a8288" stroke-width="2"/>'
            f'<line x1="{px}" y1="{py-6}" x2="{px}" y2="{py+6}" stroke="#7a8288" stroke-width="2"/>'
        )
    parts.append(
        f'<text x="{W//2}" y="618" text-anchor="middle" font-family="serif" font-size="30" fill="#4a3428">コロコロ迷路</text>'
    )
    parts.append("</svg>")
    root = Path(__file__).resolve().parent.parent
    out = root / "assets" / "scenes"
    out.mkdir(parents=True, exist_ok=True)
    (out / "maze-box.svg").write_text("\n".join(parts), encoding="utf-8")
    print("wrote assets/scenes/maze-box.svg")


if __name__ == "__main__":
    main()
