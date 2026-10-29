#!/usr/bin/env python3
"""日記挿絵ストック: アイソメトリック・アイコン集。

部品定義（box / slab / dots_on_face …）＋配置のスペックから SVG を決定的に
生成する。画像生成は使わない。~/workspace/iso-demo の方式を小さな単体
モチーフ用に縮めたもの。

usage: make_iso_stock.py [name ...]   # 省略時は全部を assets/iso/ へ
"""
import sys
from pathlib import Path

W, H, Z = 64, 32, 30           # tile width, tile height, height unit (px)
OX, OY = 240, 76               # origin offset
CW, CH = 480, 224              # canvas
STROKE = "rgba(60,40,20,.18)"


def iso(x, y, z=0.0):
    return (OX + (x - y) * W / 2, OY + (x + y) * H / 2 - z * Z)


def pts(points):
    return " ".join(f"{iso(*p)[0]:.1f},{iso(*p)[1]:.1f}" for p in points)


def poly(points, fill, extra=""):
    return f'<polygon points="{pts(points)}" fill="{fill}" stroke="{STROKE}" {extra}/>'


def box(x, y, w, d, h, top, left, right, z0=0.0):
    """Rectangular box: footprint w(x) by d(y) at (x,y), from z0 up by h.
    left = +y face, right = +x face (iso-demo の cube と同じ向き)."""
    t = [(x, y, z0 + h), (x + w, y, z0 + h), (x + w, y + d, z0 + h), (x, y + d, z0 + h)]
    l = [(x, y + d, z0), (x + w, y + d, z0), (x + w, y + d, z0 + h), (x, y + d, z0 + h)]
    r = [(x + w, y, z0), (x + w, y + d, z0), (x + w, y + d, z0 + h), (x + w, y, z0 + h)]
    return poly(l, left) + poly(r, right) + poly(t, top)


def slab(x, y, w, d, z, fill):
    """Flat top-face plate at height z."""
    return poly([(x, y, z), (x + w, y, z), (x + w, y + d, z), (x, y + d, z)], fill)


def circle(x, y, z, r, fill, extra=""):
    cx, cy = iso(x, y, z)
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" {extra}/>'


def line(p1, p2, stroke, width=2):
    a, b = iso(*p1), iso(*p2)
    return (f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
            f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round"/>')


def path(points, stroke, width=2.5):
    d = " L ".join(f"{iso(*p)[0]:.1f} {iso(*p)[1]:.1f}" for p in points)
    return (f'<path d="M {d}" fill="none" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def floor():
    out = []
    for x in range(3):
        for y in range(3):
            fill = "#e9c69c" if (x + y) % 2 == 0 else "#dfba8d"
            out.append(slab(x, y, 1, 1, 0, fill))
    return "".join(out)


def frame(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{CH}" '
            f'viewBox="0 0 {CW} {CH}">'
            f'<rect width="{CW}" height="{CH}" rx="28" fill="#fdf9ef"/>'
            + floor() + body + "</svg>")


# ---------------------------------------------------------------- motifs

def jar():
    """発酵甕。胴・肩・首・蓋を積み、泡を浮かべる。前面に目。"""
    b = []
    b.append(box(0.75, 0.75, 1.5, 1.5, 0.22, "#8a5a33", "#6f4525", "#5f3b1f"))          # 台
    b.append(box(0.62, 0.62, 1.76, 1.76, 1.05, "#dcb87e", "#c49a63", "#a87f4c", z0=0.22))  # 胴
    b.append(box(0.78, 0.78, 1.44, 1.44, 0.28, "#e6c88f", "#cfa96e", "#b8894f", z0=1.27))  # 肩
    b.append(box(1.02, 1.02, 0.96, 0.96, 0.30, "#dcb87e", "#c49a63", "#a87f4c", z0=1.55))  # 首
    b.append(box(0.92, 0.92, 1.16, 1.16, 0.14, "#8a5a33", "#6f4525", "#5f3b1f", z0=1.85))  # 蓋
    # 目（+y 面）
    b.append(circle(1.15, 2.38, 0.95, 4.5, "#4a3428"))
    b.append(circle(1.85, 2.38, 0.95, 4.5, "#4a3428"))
    # 泡
    for (x, y, z, r) in [(1.0, 1.0, 2.35, 7), (1.55, 0.8, 2.6, 5), (0.8, 1.5, 2.75, 4), (1.9, 1.3, 2.5, 3.5)]:
        b.append(circle(x, y, z, r, "#bfe0ea", 'fill-opacity="0.75" stroke="#8fb9c9"'))
    return "".join(b)


def plotter():
    """卓上ペンプロッタ。土台・レール・ガントリ・ペンと、紙の上の線。"""
    b = []
    b.append(box(0.3, 0.5, 2.4, 2.0, 0.12, "#caa06a", "#a87f4c", "#96703f"))               # 土台
    b.append(slab(0.5, 0.72, 2.0, 1.56, 0.13, "#fffdf6"))                                  # 紙
    b.append(path([(0.75, 1.9, 0.14), (1.1, 1.35, 0.14), (1.5, 1.75, 0.14),
                   (1.9, 1.1, 0.14), (2.25, 1.5, 0.14)], "#d94f4f"))                        # 描いた線
    b.append(box(0.3, 0.5, 2.4, 0.2, 0.42, "#39434f", "#232b34", "#2b333d", z0=0.12))        # 手前レール
    b.append(box(0.3, 2.3, 2.4, 0.2, 0.42, "#39434f", "#232b34", "#2b333d", z0=0.12))        # 奥レール
    b.append(box(1.28, 0.55, 0.24, 1.9, 0.3, "#7a9cc6", "#5b7ea8", "#4c6c92", z0=0.54))     # ガントリ
    b.append(box(1.24, 1.28, 0.32, 0.44, 0.34, "#c96f4a", "#a34e30", "#8f4227", z0=0.84))   # キャリッジ
    b.append(box(1.38, 1.44, 0.09, 0.09, 0.55, "#f2f2f2", "#d8d8d8", "#c4c4c4", z0=0.3))    # ペン
    b.append(poly([(1.38, 1.44, 0.3), (1.47, 1.44, 0.3), (1.47, 1.53, 0.3),
                   (1.38, 1.53, 0.3), (1.425, 1.485, 0.13)], "#4a3428"))                   # ペン先
    return "".join(b)


def led():
    """LEDマトリクスパネル。脚付きの板にハートのドット。"""
    b = []
    b.append(box(0.55, 1.32, 0.5, 0.3, 0.3, "#39434f", "#232b34", "#2b333d"))               # 脚
    b.append(box(1.95, 1.32, 0.5, 0.3, 0.3, "#39434f", "#232b34", "#2b333d"))
    b.append(box(0.4, 1.3, 2.2, 0.16, 1.5, "#39434f", "#26303a", "#1d252e", z0=0.3))        # パネル
    heart = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]
    for r, row in enumerate(heart):
        for c, ch in enumerate(row):
            if ch == "X":
                b.append(circle(0.72 + c * 0.27, 1.47, 1.58 - r * 0.21, 4.2, "#ff5d73"))
    return "".join(b)


def nas():
    """NASタワーとラズパイ基板。"""
    b = []
    b.append(box(0.45, 0.6, 1.05, 1.5, 2.0, "#4a4f57", "#33373d", "#26292e"))               # タワー
    for i, z in enumerate((1.55, 1.05)):                                                   # ドライブ枠（+y 面）
        b.append(poly([(0.6, 2.11, z), (1.35, 2.11, z), (1.35, 2.11, z - 0.34),
                       (0.6, 2.11, z - 0.34)], "#565d66"))
    b.append(circle(0.68, 2.11, 0.62, 3.5, "#7ed957"))
    b.append(circle(0.68, 2.11, 0.4, 3.5, "#ffb84d"))
    b.append(box(1.75, 1.15, 1.35, 0.95, 0.09, "#3f9e4d", "#2f7a3c", "#276832", z0=0.02))   # 基板
    b.append(box(2.05, 1.35, 0.5, 0.5, 0.1, "#2b2b2b", "#1d1d1d", "#171717", z0=0.11))      # SoC
    b.append(box(2.72, 1.25, 0.3, 0.34, 0.14, "#c0c6cc", "#9aa2a9", "#848c93", z0=0.11))    # ポート
    b.append(box(1.85, 1.78, 0.28, 0.24, 0.12, "#c0c6cc", "#9aa2a9", "#848c93", z0=0.11))
    return "".join(b)


def mic():
    """卓上マイク。台座・ポール・カプセルとグリルの線。"""
    b = []
    b.append(box(0.95, 0.95, 1.1, 1.1, 0.12, "#4a4f57", "#33373d", "#26292e"))              # 台座
    b.append(box(1.44, 1.44, 0.12, 0.12, 1.15, "#6a7076", "#565b61", "#45494e", z0=0.12))   # ポール
    b.append(box(1.28, 1.28, 0.44, 0.44, 0.95, "#7a9cc6", "#5b7ea8", "#4c6c92", z0=1.27))   # カプセル
    for z in (1.5, 1.72, 1.94):
        b.append(line((1.28, 1.73, z), (1.72, 1.73, z), "#39434f", 2))
    b.append(circle(1.5, 1.73, 1.36, 3, "#ff5d73"))                                        # 録音ランプ
    return "".join(b)


def books():
    """本の山。3冊積み、表紙色とページの境が見えるように。"""
    b = []
    b.append(box(0.5, 0.7, 2.0, 1.5, 0.3, "#b84a39", "#96392c", "#7e2f24"))                 # 1冊目
    b.append(slab(0.56, 0.76, 1.88, 1.38, 0.24, "#f3e9d2"))
    b.append(box(0.62, 0.82, 1.76, 1.3, 0.27, "#2e7f86", "#25666c", "#1d545a", z0=0.3))     # 2冊目
    b.append(slab(0.68, 0.88, 1.64, 1.18, 0.51, "#f3e9d2"))
    b.append(box(0.78, 0.95, 1.5, 1.12, 0.25, "#d9a441", "#b5852f", "#9c7126", z0=0.57))    # 3冊目
    b.append(slab(0.84, 1.01, 1.38, 1.0, 0.76, "#f3e9d2"))
    b.append(poly([(2.05, 1.5, 0.82), (2.2, 1.5, 0.82), (2.2, 1.5, 0.3),
                   (2.05, 1.5, 0.3)], "#d94f4f"))                                          # しおり紐（+x 面）
    return "".join(b)


def mug():
    """湯気の立つマグ。取っ手は +x 面の C 字パス。"""
    b = []
    b.append(box(0.7, 0.8, 1.6, 1.5, 0.07, "#ead9bd", "#c9b18a", "#b39b6f"))                # ソーサー
    b.append(box(0.9, 0.95, 1.2, 1.2, 0.85, "#e8ddc8", "#d2694f", "#b34a30", z0=0.07))      # 本体
    b.append(slab(0.98, 1.03, 1.04, 1.04, 0.93, "#5a3a22"))                                # コーヒー面
    b.append(path([(2.1, 1.55, 0.78), (2.42, 1.55, 0.7), (2.48, 1.55, 0.48),
                   (2.42, 1.55, 0.28), (2.1, 1.55, 0.24)], "#8f4227", 6))                  # 取っ手
    for dx in (0.0, 0.45):
        b.append(path([(1.2 + dx, 1.35, 1.25), (1.08 + dx, 1.35, 1.52),
                       (1.24 + dx, 1.35, 1.78), (1.12 + dx, 1.35, 2.02)], "#7d99a6", 4))   # 湯気
    return "".join(b)


def plant():
    """観葉植物。テラコッタ鉢に層状の葉。"""
    b = []
    b.append(box(1.0, 1.05, 1.0, 1.0, 0.18, "#d97e57", "#b85f3d", "#a34e30"))               # 鉢の縁
    b.append(box(1.08, 1.13, 0.84, 0.84, 0.55, "#cf7350", "#a34e30", "#8f4227", z0=0.18))   # 鉢
    b.append(slab(1.12, 1.17, 0.76, 0.76, 0.74, "#5a4230"))                                # 土
    for i, (dx, s, col) in enumerate([(0, 1.05, "#57a324"), (0.1, 0.85, "#6abe30"), (0.2, 0.6, "#7ed957")]):
        z = 0.82 + i * 0.26
        b.append(slab(0.98 + dx, 1.03 + dx, s, s, z, col))
    return "".join(b)


def printer():
    """3Dプリンタ。ベッド・柱・天板・ヘッドと出力途中の立方体。"""
    b = []
    b.append(box(0.4, 0.4, 2.2, 2.2, 0.16, "#4a4f57", "#33373d", "#26292e"))                # ベッド
    b.append(box(0.4, 0.4, 0.16, 0.16, 2.0, "#8b9096", "#6e7378", "#5b5f64", z0=0.16))       # 柱
    b.append(box(2.04, 0.4, 0.16, 0.16, 2.0, "#8b9096", "#6e7378", "#5b5f64", z0=0.16))
    b.append(box(0.4, 0.4, 2.2, 0.16, 0.18, "#8b9096", "#6e7378", "#5b5f64", z0=2.16))       # 天板
    b.append(box(0.48, 0.44, 1.64, 0.12, 0.14, "#8b9096", "#6e7378", "#5b5f64", z0=1.72))   # Xバー
    b.append(box(1.22, 0.42, 0.5, 0.4, 0.52, "#c96f4a", "#a34e30", "#8f4227", z0=1.2))      # ヘッド
    b.append(poly([(1.38, 0.55, 1.2), (1.56, 0.55, 1.2), (1.56, 0.7, 1.2),
                   (1.38, 0.7, 1.2), (1.47, 0.62, 0.97)], "#4a3428"))                       # ノズル
    b.append(box(1.2, 1.25, 0.55, 0.55, 0.4, "#7a9cc6", "#5b7ea8", "#4c6c92", z0=0.16))     # 出力物
    return "".join(b)


def console_():
    """携帯ゲーム機。画面にドットの迷路、ボタンと十字キー。"""
    b = []
    b.append(box(0.3, 0.75, 2.4, 1.5, 0.22, "#8f7ab8", "#71589c", "#5f4884"))               # 本体
    b.append(slab(0.95, 0.95, 1.25, 1.1, 0.23, "#26303a"))                                 # 画面枠
    b.append(slab(1.03, 1.03, 1.09, 0.94, 0.24, "#bfe0ea"))                                # 画面
    for (dx, dy) in [(0.12, 0.12), (0.36, 0.12), (0.36, 0.36), (0.36, 0.6), (0.6, 0.6), (0.84, 0.6)]:
        b.append(slab(1.03 + dx, 1.03 + dy, 0.18, 0.18, 0.25, "#57a324"))                  # 迷路ドット
    b.append(box(0.45, 1.28, 0.34, 0.12, 0.05, "#4a4f57", "#33373d", "#26292e", z0=0.22))   # 十字キー横
    b.append(box(0.56, 1.17, 0.12, 0.34, 0.05, "#4a4f57", "#33373d", "#26292e", z0=0.22))   # 十字キー縦
    b.append(circle(2.32, 1.15, 0.24, 5, "#d94f4f"))
    b.append(circle(2.48, 1.42, 0.24, 5, "#d9a441"))
    return "".join(b)


def board():
    """マイコンボード。基板にメインIC・ピンヘッダ・USBコネクタとLED。"""
    b = []
    b.append(box(0.35, 0.75, 2.3, 1.5, 0.08, "#2b4a67", "#1f364d", "#182a3d"))             # 基板
    b.append(box(0.38, 1.28, 0.24, 0.44, 0.13, "#c0c6cc", "#9aa2a9", "#848c93", z0=0.02))  # USBコネクタ
    b.append(box(0.95, 1.18, 0.6, 0.6, 0.12, "#2b2b2b", "#1d1d1d", "#171717", z0=0.08))    # メインIC
    b.append(box(1.78, 1.52, 0.34, 0.34, 0.09, "#2b2b2b", "#1d1d1d", "#171717", z0=0.08))  # フラッシュ
    b.append(box(1.82, 1.06, 0.3, 0.2, 0.06, "#c0c6cc", "#9aa2a9", "#848c93", z0=0.08))    # クリスタル
    for i in range(7):                                                                      # ピンヘッダ（両長辺）
        x = 0.62 + i * 0.28
        b.append(box(x, 0.84, 0.15, 0.15, 0.1, "#e8c96a", "#b5852f", "#9c7126", z0=0.08))
        b.append(box(x, 2.01, 0.15, 0.15, 0.1, "#e8c96a", "#b5852f", "#9c7126", z0=0.08))
    b.append(circle(2.38, 1.02, 0.1, 3.5, "#ff5d73"))                                      # LED
    b.append(circle(2.38, 1.98, 0.1, 3, "#7ed957"))                                        # 電源LED
    return "".join(b)


def bouldering():
    """ボルダリング壁とマット。色とりどりのホールド。"""
    b = []
    b.append(box(0.35, 1.9, 2.3, 0.9, 0.14, "#57b8a2", "#41937f", "#357664"))               # マット
    b.append(box(0.4, 0.55, 2.2, 0.16, 2.1, "#aebdc9", "#8fa2b3", "#76899c"))                # 壁
    holds = [(0.65, 1.7, "#d94f4f"), (1.15, 1.95, "#d9a441"), (1.7, 1.6, "#57a324"),
             (2.15, 1.9, "#7a9cc6"), (0.85, 1.15, "#d9a441"), (1.45, 1.25, "#d94f4f"),
             (2.0, 1.05, "#57a324"), (1.05, 0.6, "#7a9cc6"), (1.8, 0.5, "#d94f4f"),
             (2.3, 1.35, "#e08e63")]
    for (x, z, col) in holds:
        b.append(circle(x, 0.72, z, 5.5, col))
    return "".join(b)


ICONS = {
    "jar": jar,
    "plotter": plotter,
    "led": led,
    "nas": nas,
    "mic": mic,
    "books": books,
    "mug": mug,
    "plant": plant,
    "printer": printer,
    "console": console_,
    "bouldering": bouldering,
    "board": board,
}


def main():
    names = sys.argv[1:] or list(ICONS)
    out = Path(__file__).resolve().parent.parent / "assets" / "iso"
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        svg = frame(ICONS[name]())
        (out / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"wrote assets/iso/{name}.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
