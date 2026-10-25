#!/usr/bin/env python3
"""日記のテーマ定義: 色・アイコン（16x16 ドット）・背景色の配合。

日記は 1 日に 1 テーマとは限らないので、テーマは複数タグ＋重みで表す。
記事のメタ情報に `<!-- themes: ことば2 つくる2 交流1 -->` のように書く。

- ヘッダー右の落款: その日のテーマのアイコンが、テーマ色で並ぶ
- ヘッダー下のバー: テーマの重みの割合
- 背景色: テーマ色を重みで配合した色（色相は円平均、明度は淡く固定）

配合も生成も決定的で、ランダムなのは泡の位置だけ。
"""
import colorsys
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_stamps import HEART as _HEART  # noqa: E402
from make_stamps import MIC as _MIC  # noqa: E402

THEME_HEX = {
    "つくる": "#d9a441",  # 琥珀: 歯車
    "ことば": "#5a6aa8",  # 藍: マイク
    "家族": "#d4708a",    # ばら: ハート
    "交流": "#3f8a7a",    # 青緑: 吹き出し
    "点検": "#6a8a4f",    # 苔: チェック
    "静か": "#5a6a8a",    # 藍灰: 月
}
THEME_ORDER = list(THEME_HEX)
THEME_DESC = {
    "つくる": "ものづくり・制作",
    "ことば": "ポッドキャスト・文章・言葉",
    "家族": "家族と暮らし",
    "交流": "エージェントや人とのやり取り",
    "点検": "仕組みの保守・確認",
    "静か": "内省・休息",
}

ICONS = {
    "つくる": [
        "................", ".....######.....", "....########....", "....##....##....",
        "...##......##...", "...#..####..#...", "...#..#..#..#...", "....#......#....",
        "....#......#....", "...#..#..#..#...", "...#..####..#...", "...##......##...",
        "....##....##....", "....########....", ".....######.....", "................",
    ],
    "ことば": _MIC,  # 挿絵スタンプと共通のマイク
    "家族": _HEART,  # 挿絵スタンプと共通のハート
    "交流": [
        "................", "..######........", ".########.......", ".##....##.......",
        ".########.......", "..######........", "...##...........", "..##....######..",
        ".......########.", ".......##....##.", ".......########.", "........######..",
        "..........##....", ".........##.....", "................", "................",
    ],
    "点検": [
        "................", "................", "..............#.", ".............##.",
        "............##..", ".##........##...", ".####.....##....", "..#####..##.....",
        "...########.....", "....######......", ".....####.......", "......##........",
        "................", "................", "................", "................",
    ],
    "静か": [
        "................", "......#####.....", "....########....", "...#####........",
        "..####..........", "..###...........", ".###............", ".###............",
        ".###............", "..###...........", "..####..........", "...#####........",
        "....########....", "......#####.....", "................", "................",
    ],
}

DEFAULT_BG = "#fbf4e4"
DEFAULT_BUBBLE = "#e8c87a"


def parse_themes(spec: str):
    """'ことば2 つくる2 交流1' や 'ことば:2,つくる:2' -> [('ことば', 2), ...]"""
    out = []
    for token in re.split(r"[\s,、]+", spec.strip()):
        if not token:
            continue
        m = re.match(r"^(.+?)(?:[:：]?\s*(\d+(?:\.\d+)?))?$", token)
        if not m:
            continue
        name = m.group(1)
        if name in THEME_HEX:
            out.append((name, float(m.group(2)) if m.group(2) else 1.0))
    return out


def themes_from_text(text: str):
    m = re.search(r"<!--\s*themes:\s*(.*?)\s*-->", text)
    return parse_themes(m.group(1)) if m else []


def _hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _rgb2hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in rgb)


def blend(themes):
    """テーマの重み配合 -> (背景色, 泡色)。色味は少し強めの設定。"""
    if not themes:
        return DEFAULT_BG, DEFAULT_BUBBLE
    total = sum(w for _n, w in themes)
    sx = sy = sat = 0.0
    for name, w in themes:
        r, g, b = _hex2rgb(THEME_HEX[name])
        h, _l, s = colorsys.rgb_to_hls(r, g, b)
        ang = h * 2 * math.pi
        sx += math.cos(ang) * w
        sy += math.sin(ang) * w
        sat += s * w
    sat /= total
    if math.hypot(sx, sy) < 0.15 * total:  # 補色同士で消し合ったら最大テーマの色相
        name = max(themes, key=lambda t: t[1])[0]
        hue = colorsys.rgb_to_hls(*_hex2rgb(THEME_HEX[name]))[0]
    else:
        hue = (math.atan2(sy, sx) / (2 * math.pi)) % 1.0
    bg = colorsys.hls_to_rgb(hue, 0.90, min(0.60, sat * 0.85))
    bubble = colorsys.hls_to_rgb(hue, 0.70, min(0.80, sat * 1.05))
    return _rgb2hex(bg), _rgb2hex(bubble)


def motif_svg(grid, x, y, scale, color):
    parts = []
    for ri, row in enumerate(grid):
        for ci, ch in enumerate(row):
            if ch == "#":
                parts.append(
                    f'<rect x="{x + ci * scale}" y="{y + ri * scale}" width="{scale}" height="{scale}" fill="{color}"/>'
                )
    return parts


def motif_pil(dr, grid, ox, oy, scale, color):
    for ri, row in enumerate(grid):
        for ci, ch in enumerate(row):
            if ch == "#":
                dr.rectangle(
                    [ox + ci * scale, oy + ri * scale, ox + (ci + 1) * scale, oy + (ri + 1) * scale],
                    fill=color,
                )
