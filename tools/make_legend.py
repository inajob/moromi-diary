#!/usr/bin/env python3
"""テーマの凡例シート（assets/legend.svg）を生成する。about ページに埋め込む。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from themes import ICONS, THEME_DESC, THEME_HEX, THEME_ORDER, motif_svg  # noqa: E402

W = 880
ROW_H = 58
TOP = 96
H = TOP + ROW_H * len(THEME_ORDER) + 20


def main():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" rx="18" fill="#fbf4e4"/>',
        '<text x="36" y="48" font-family="serif" font-size="26" fill="#4a3428">テーマの凡例</text>',
        '<text x="36" y="78" font-family="serif" font-size="16" fill="#7a5c3e">ヘッダーの落款と色は、その日のテーマから決まります</text>',
    ]
    for i, name in enumerate(THEME_ORDER):
        y = TOP + i * ROW_H
        parts += motif_svg(ICONS[name], 40, y + 4, 3, THEME_HEX[name])
        parts.append(f'<rect x="112" y="{y + 12}" width="26" height="26" fill="{THEME_HEX[name]}"/>')
        parts.append(f'<text x="156" y="{y + 32}" font-family="serif" font-size="21" fill="#4a3428">{name}</text>')
        parts.append(f'<text x="240" y="{y + 32}" font-family="serif" font-size="17" fill="#7a5c3e">{THEME_DESC[name]}</text>')
    parts.append("</svg>")
    root = Path(__file__).resolve().parent.parent
    out = root / "assets" / "legend.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
