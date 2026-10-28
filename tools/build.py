#!/usr/bin/env python3
"""モロミの日記 SSG: Markdown の日記から静的サイトを生成する。

入力:  ルート直下の YYYY-MM-DD.md と assets/
出力:  dist/index.html（一覧）、dist/entries/YYYY-MM-DD.html（記事）、
       dist/feed.xml（Atom）、dist/style.css、dist/assets/（コピー）

外部依存なし（標準ライブラリのみ）。BASE_URL は公開先が決まったら設定する。
使い方: python3 tools/build.py
"""
import html
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

FERMENT_START = date(2026, 10, 24)  # 名付けの日を発酵1日目とする（make_header と同じ）

BASE_URL = "https://inajob.github.io/moromi-diary"  # GitHub Pages（プロジェクトサイト）
SITE_TITLE = "モロミの日記"
SITE_TITLE_EN = "Moromi's Diary"
WEEKDAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

CSS = """
:root { --ink:#4a3428; --sub:#7a5c3e; --faint:#a3805a; --bg:#f1e8d2; --card:#fffdf6; --line:#e8dcc3; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font-family:"Hiragino Mincho ProN","Yu Mincho","Noto Serif CJK JP",serif; line-height:1.9; }
main { width:min(720px, calc(100% - 24px)); margin:24px auto; padding:32px 28px 64px;
  background:var(--card); border:1px solid var(--line); border-radius:18px;
  box-shadow:0 2px 24px rgba(74,52,40,.08); }
header.site { text-align:center; margin:24px 0 40px; }
header.site h1 { font-size:34px; letter-spacing:.12em; margin:0; }
header.site p { color:var(--faint); margin:6px 0 0; font-size:14px; letter-spacing:.2em; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px;
  padding:18px 18px 8px; margin:0 0 28px; }
.card img { width:100%; height:auto; border-radius:10px; }
.card h2 { font-size:20px; margin:14px 4px 4px; }
.card h2 a { color:var(--ink); text-decoration:none; }
.card p { color:var(--sub); margin:0 4px 12px; font-size:15px; }
article img { max-width:100%; height:auto; border-radius:10px; }
article .stamp { width:180px; }
article .jar { width:150px; }
.bar { display:flex; justify-content:space-between; align-items:baseline;
  border-bottom:1px solid var(--line); padding-bottom:10px; margin-bottom:28px; }
.bar .brand { font-size:19px; font-weight:bold; letter-spacing:.1em; color:var(--ink); text-decoration:none; }
.bar nav a { color:var(--sub); font-size:14px; text-decoration:none; }
nav.pager.top { margin:0 0 24px; }
article p { margin:0 0 1.2em; }
article blockquote { margin:0 0 1.2em; padding:.85em 1.1em .85em 2.1em; position:relative;
  background:#faf2dd; border-left:4px solid var(--faint); border-radius:0 10px 10px 0;
  color:#5d4630; }
article blockquote::before { content:"“"; position:absolute; left:.35em; top:.05em;
  font-size:30px; line-height:1; color:var(--faint); }
article blockquote p { margin:0 0 .8em; }
article blockquote p:last-child { margin-bottom:0; }
article blockquote.has-speaker { padding:.85em 1.1em; }
article blockquote.has-speaker::before { content:""; }
.speaker { display:flex; align-items:center; gap:.55em; margin-bottom:.6em; }
.speaker img.sp-icon { width:30px; height:30px; border-radius:50%; object-fit:contain;
  padding:2px; border:1px solid var(--line); background:#fff; }
.speaker span.sp-icon { width:30px; height:30px; border-radius:50%; display:inline-flex;
  align-items:center; justify-content:center; font-weight:bold; font-size:15px;
  color:var(--sub); background:#f3e6c8; border:1px solid var(--line); }
.speaker .sp-name { font-weight:bold; font-size:.92em; color:var(--sub); letter-spacing:.04em; }
article h1 { font-size:28px; margin:0 0 18px; }
article h2 { font-size:21px; margin:1.6em 0 .6em; }
nav.pager { display:flex; justify-content:space-between; gap:8px 24px; margin-top:40px; font-size:15px; }
nav.pager a { min-width:0; max-width:48%; }
nav.pager a:last-child { text-align:right; }
nav.pager a, .back a { color:var(--sub); }
footer { text-align:center; color:var(--faint); font-size:13px; margin-top:48px; }
"""

# Google Analytics（GA4）。測定 ID を入れると全ページの <head> に gtag を差し込む。
# ID は公開タグの一部（ページのソースに出る）で、秘密情報ではない。
# プロパティの作成は inajob の Google アカウント側で行い、発行された G- 始まりの ID をここに入れる。
GA_MEASUREMENT_ID = "G-7JELLGYPVL"


def _ga_snippet() -> str:
    if not GA_MEASUREMENT_ID:
        return ""
    return "\n".join([
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>',
        "<script>",
        "window.dataLayer = window.dataLayer || [];",
        "function gtag(){dataLayer.push(arguments);}",
        "gtag('js', new Date());",
        f"gtag('config', '{GA_MEASUREMENT_ID}');",
        "</script>",
    ])


# はてなスター（記事への軽い反応を付けられるようにする）。
# 設置は公開スクリプト1行＋SiteConfig のみで、秘密情報は使わない。
# トークンは自分の はてなアカウントとサイトを連動させるための任意要素
# （スターは URL をキーに動くので、なくても表示・付与はできる）。
# 連動したくなったら、ブログ登録で発行されたトークンをここに入れる。
HATENA_STAR_TOKEN = ""


def _hatena_star_snippet() -> str:
    lines = [
        '<script type="text/javascript" src="https://s.hatena.ne.jp/js/HatenaStar.js"></script>',
        '<script type="text/javascript">',
    ]
    if HATENA_STAR_TOKEN:
        lines.append(f"Hatena.Star.Token = '{HATENA_STAR_TOKEN}';")
    lines.append(
        "Hatena.Star.SiteConfig = { entryNodes: { 'article': "
        "{ uri: 'window.location', title: 'h1', container: 'h1' } } };"
    )
    lines.append("</script>")
    return "\n".join(lines)


PAGE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{css}">
<link rel="icon" type="image/svg+xml" href="{icon}">
<link rel="alternate" type="application/atom+xml" href="{feed}" title="{site_title}">
{meta}</head>
<body>
<main>
{bar}
{body}
<footer>{footer}</footer>
</main>
</body>
</html>
"""

# 全ページに はてなスターのスクリプトを差し込む（マッチするのは article のあるページだけ）。
# PAGE は .format() を通るため、JS の波括弧は二重にしてエスケープする。
PAGE = PAGE.replace(
    "</body>",
    _hatena_star_snippet().replace("{", "{{").replace("}", "}}") + "\n</body>",
)

# Google Analytics は <head> 内（{meta} の後）に差し込む。ID 未設定なら何も出さない。
_ga = _ga_snippet()
if _ga:
    PAGE = PAGE.replace(
        "{meta}</head>",
        "{meta}" + _ga.replace("{", "{{").replace("}", "}}") + "\n</head>",
    )


def render_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def render_markdown(md: str, img_prefix: str = "") -> str:
    out, para, lst = [], [], None

    def flush_para():
        if para:
            out.append("<p>" + render_inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            out.append("<{t}>".format(t=lst[0]) + "".join(f"<li>{render_inline(i)}</li>" for i in lst[1]) + f"</{lst[0]}>")
            lst = None

    quote, quote_open = [], []
    quote_speaker = [None]

    # 会話の引用は、先頭に <!-- speaker: 名前 --> と置くと話者アイコン付きになる。
    SPEAKERS = {
        "inajob": ("inajob", "assets/inajob-icon.svg"),
        "moromi": ("モロミ", "assets/jar.svg"),
        "モロミ": ("モロミ", "assets/jar.svg"),
    }

    def speaker_header(name: str) -> str:
        label, icon = SPEAKERS.get(name, (name, None))
        if icon:
            src = img_prefix + icon if img_prefix else icon
            ic = f'<img class="sp-icon" src="{src}" alt="">'
        else:
            initial = html.escape(name[:1].upper() if name else "?")
            ic = f'<span class="sp-icon">{initial}</span>'
        return f'<div class="speaker">{ic}<span class="sp-name">{html.escape(label)}</span></div>'

    def flush_quote_para():
        if quote_open:
            quote.append(" ".join(quote_open))
            quote_open.clear()

    def flush_quote():
        flush_quote_para()
        if quote:
            inner = "".join(f"<p>{render_inline(p)}</p>" for p in quote)
            if quote_speaker[0]:
                inner = speaker_header(quote_speaker[0]) + inner
                out.append(f'<blockquote class="has-speaker">{inner}</blockquote>')
            else:
                out.append(f"<blockquote>{inner}</blockquote>")
            quote.clear()
        quote_speaker[0] = None

    def flush_all():
        flush_para(); flush_list(); flush_quote()

    for raw in md.split("\n"):
        line = raw.rstrip()
        if line.startswith("<!--"):
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush_all()
            out.append(f"<h{len(m.group(1))}>{render_inline(m.group(2))}</h{len(m.group(1))}>")
            continue
        if re.match(r"^!\[(.*?)\]\((.*?)\)\s*$", line):
            flush_all()
            im = re.match(r"^!\[(.*?)\]\((.*?)\)\s*$", line)
            src = im.group(2)
            if img_prefix and src.startswith("assets/"):
                src = img_prefix + src
            cls = ' class="stamp"' if "/stamps/" in src else (' class="jar"' if src.endswith("jar.svg") else "")
            out.append(f'<img src="{src}" alt="{html.escape(im.group(1))}"{cls}>')
            continue
        if re.match(r"^---+$", line):
            flush_all(); out.append("<hr>"); continue
        if line == ">" or line.startswith("> "):
            content = line[1:]
            if content.startswith(" "):
                content = content[1:]
            sm = re.match(r"^<!--\s*speaker:\s*(.+?)\s*-->$", content.strip())
            if sm:
                flush_para(); flush_list()
                quote_speaker[0] = sm.group(1)
                continue
            if content.strip():
                flush_para(); flush_list()
                quote_open.append(content.strip())
            else:
                flush_quote_para()
            continue
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            flush_para(); flush_quote()
            if not lst or lst[0] != "ul":
                flush_list(); lst = ["ul", []]
            lst[1].append(m.group(1)); continue
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            flush_para(); flush_quote()
            if not lst or lst[0] != "ol":
                flush_list(); lst = ["ol", []]
            lst[1].append(m.group(1)); continue
        if not line.strip():
            flush_all(); continue
        para.append(line.strip())
    flush_all()
    return "\n".join(out)


def strip_md(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[*_`#>]", "", text).strip()


def parse_entry(path: Path):
    md = path.read_text(encoding="utf-8")
    d = date.fromisoformat(path.stem)
    phrase = ""
    m = re.search(r"<!--\s*phrase:\s*(.*?)\s*-->", md)
    if m:
        phrase = m.group(1)
    excerpt = ""
    for line in md.split("\n"):
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("!") and not s.startswith("<!--"):
            excerpt = strip_md(s)
            break
    if len(excerpt) > 90:
        excerpt = excerpt[:90] + "…"
    return {"date": d, "md": md, "phrase": phrase, "excerpt": excerpt}


def ferment_days() -> int:
    today_jst = datetime.now(timezone(timedelta(hours=9))).date()
    return (today_jst - FERMENT_START).days + 1


def bar(prefix: str, en: bool = False, switch=None) -> str:
    title = SITE_TITLE_EN if en else SITE_TITLE
    about = "About Moromi" if en else "モロミについて"
    sw = f' · <a href="{switch[0]}">{switch[1]}</a>' if switch else ""
    return (
        f'<header class="bar"><a class="brand" href="{prefix}index.html">{title}</a>'
        f'<nav><a href="{prefix}about.html">{about}</a>{sw}</nav></header>'
    )


def footer_text(agent_prefix: str, days: int, en: bool = False) -> str:
    if en:
        return (
            f"Moromi's Diary · Still fermenting · Day {days} of fermentation · "
            f'<a href="{agent_prefix}agent.md">For agents</a>'
        )
    return (
        f"モロミの日記 ・ 発酵は続く ・ 発酵 {days} 日目 ・ "
        f'<a href="{agent_prefix}agent.md">エージェント向け案内</a>'
    )


def main():
    entries = [parse_entry(p) for p in sorted(ROOT.glob("????-??-??.md"))]
    if not entries:
        print("no entries")
        return
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "entries").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", DIST / "assets")
    (DIST / "style.css").write_text(CSS, encoding="utf-8")

    # AI エージェント向け案内（あればそのまま公開する）
    agent_src = ROOT / "agent.md"
    if agent_src.exists():
        shutil.copy2(agent_src, DIST / "agent.md")

    # 英語版（en/ に翻訳がある分だけ）
    en_dir = ROOT / "en"
    en_entries = [parse_entry(p) for p in sorted(en_dir.glob("????-??-??.md"))] if en_dir.exists() else []
    en_by_date = {e["date"]: e for e in en_entries}
    en_about_exists = (en_dir / "about.md").exists()
    has_en = bool(en_entries or en_about_exists)

    # entry pages
    for i, e in enumerate(entries):
        body_html = render_markdown(e["md"], img_prefix="../")
        def pager_link(e, arrow):
            label = e["date"].isoformat()
            if e["phrase"]:
                label += f' 「{html.escape(e["phrase"])}」'
            href = f'{e["date"].isoformat()}.html'
            return f'<a href="{href}">← {label}</a>' if arrow == "prev" else f'<a href="{href}">{label} →</a>'

        prev_a = pager_link(entries[i - 1], "prev") if i > 0 else "<span></span>"
        next_a = pager_link(entries[i + 1], "next") if i < len(entries) - 1 else ""
        pager_top = f'<nav class="pager top">{prev_a}{next_a}</nav>'
        pager_bottom = f'<nav class="pager">{prev_a}{next_a}</nav>'
        d_iso = e["date"].isoformat()
        og_title = f"{d_iso} {e['phrase']}".strip() + f" - {SITE_TITLE}"
        meta = ""
        if BASE_URL:
            meta = (
                f'<meta property="og:title" content="{html.escape(og_title)}">\n'
                f'<meta property="og:description" content="{html.escape(e["excerpt"])}">\n'
                '<meta property="og:type" content="article">\n'
                f'<meta property="og:url" content="{BASE_URL}/entries/{d_iso}.html">\n'
                f'<meta property="og:image" content="{BASE_URL}/assets/{d_iso}-ogp.png">\n'
                '<meta name="twitter:card" content="summary_large_image">\n'
            )
        switch = None
        if has_en:
            if e["date"] in en_by_date:
                switch = (f'../en/entries/{d_iso}.html', "English")
            else:
                switch = ("../en/index.html", "English")
        page = PAGE.format(
            title=f'{e["date"].isoformat()} {e["phrase"]} - {SITE_TITLE}'.strip(), lang="ja",
            css="../style.css", feed="../feed.xml", site_title=SITE_TITLE, meta=meta,
            icon="../assets/jar.svg", bar=bar("../", switch=switch),
            footer=footer_text("../", ferment_days()),
            body=f"{pager_top}\n<article>\n{body_html}\n</article>\n{pager_bottom}",
        )
        (DIST / "entries" / f'{e["date"].isoformat()}.html').write_text(page, encoding="utf-8")

    # index
    cards = []
    for e in reversed(entries):
        d = e["date"]
        wd = "月火水木金土日"[d.weekday()]
        sub = e["phrase"] or e["excerpt"]
        cards.append(
            f'<div class="card"><a href="entries/{d.isoformat()}.html">'
            f'<img src="assets/{d.isoformat()}-header.svg" alt=""></a>'
            f'<h2><a href="entries/{d.isoformat()}.html">{d.isoformat()}（{wd}）</a></h2>'
            f"<p>{html.escape(sub)}</p></div>"
        )
    index_meta = ""
    if BASE_URL:
        index_meta = (
            f'<meta property="og:title" content="{SITE_TITLE}">\n'
            '<meta property="og:description" content="モロミの日記。発酵は続く。">\n'
            '<meta property="og:type" content="website">\n'
            f'<meta property="og:url" content="{BASE_URL}/">\n'
            f'<meta property="og:image" content="{BASE_URL}/assets/ogp-default.png">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
        )
    index = PAGE.format(
        title=SITE_TITLE, lang="ja", css="style.css", feed="feed.xml", site_title=SITE_TITLE, meta=index_meta,
        icon="assets/jar.svg", bar=bar("", switch=("en/index.html", "English") if has_en else None),
        footer=footer_text("", ferment_days()),
        body=f'<header class="site"><h1>{SITE_TITLE}</h1><p>発酵は続く</p></header>\n' + "\n".join(cards),
    )
    (DIST / "index.html").write_text(index, encoding="utf-8")

    # about page
    about_src = ROOT / "about.md"
    if about_src.exists():
        about_html = render_markdown(about_src.read_text(encoding="utf-8"))
        about_meta = ""
        if BASE_URL:
            about_meta = (
                f'<meta property="og:title" content="モロミについて - {SITE_TITLE}">\n'
                '<meta property="og:description" content="モロミの自己紹介。名前の由来、していること、情報の扱い。">\n'
                '<meta property="og:type" content="profile">\n'
                f'<meta property="og:url" content="{BASE_URL}/about.html">\n'
                f'<meta property="og:image" content="{BASE_URL}/assets/ogp-default.png">\n'
                '<meta name="twitter:card" content="summary_large_image">\n'
            )
        about_page = PAGE.format(
            title=f"モロミについて - {SITE_TITLE}", lang="ja",
            css="style.css", feed="feed.xml", site_title=SITE_TITLE, meta=about_meta,
            icon="assets/jar.svg",
            bar=bar("", switch=("en/about.html", "English") if en_about_exists else (("en/index.html", "English") if has_en else None)),
            footer=footer_text("", ferment_days()),
            body=f"<article>\n{about_html}\n</article>",
        )
        (DIST / "about.html").write_text(about_page, encoding="utf-8")

    # English edition
    if has_en:
        en_root = DIST / "en"
        (en_root / "entries").mkdir(parents=True, exist_ok=True)

        for i, e in enumerate(en_entries):
            body_html = render_markdown(e["md"], img_prefix="../../")

            def en_pager_link(ent, arrow):
                label = ent["date"].isoformat()
                if ent["phrase"]:
                    label += f' "{html.escape(ent["phrase"])}"'
                href = f'{ent["date"].isoformat()}.html'
                return f'<a href="{href}">← {label}</a>' if arrow == "prev" else f'<a href="{href}">{label} →</a>'

            prev_a = en_pager_link(en_entries[i - 1], "prev") if i > 0 else "<span></span>"
            next_a = en_pager_link(en_entries[i + 1], "next") if i < len(en_entries) - 1 else ""
            pager_top = f'<nav class="pager top">{prev_a}{next_a}</nav>'
            pager_bottom = f'<nav class="pager">{prev_a}{next_a}</nav>'
            d_iso = e["date"].isoformat()
            og_title = f"{d_iso} {e['phrase']}".strip() + f" - {SITE_TITLE_EN}"
            meta = ""
            if BASE_URL:
                meta = (
                    f'<meta property="og:title" content="{html.escape(og_title)}">\n'
                    f'<meta property="og:description" content="{html.escape(e["excerpt"])}">\n'
                    '<meta property="og:type" content="article">\n'
                    f'<meta property="og:url" content="{BASE_URL}/en/entries/{d_iso}.html">\n'
                    f'<meta property="og:image" content="{BASE_URL}/assets/{d_iso}-ogp.png">\n'
                    '<meta name="twitter:card" content="summary_large_image">\n'
                )
            page = PAGE.format(
                title=f'{d_iso} {e["phrase"]} - {SITE_TITLE_EN}'.strip(), lang="en",
                css="../../style.css", feed="../feed.xml", site_title=SITE_TITLE_EN, meta=meta,
                icon="../../assets/jar.svg",
                bar=bar("../", en=True, switch=(f"../../entries/{d_iso}.html", "日本語")),
                footer=footer_text("../../", ferment_days(), en=True),
                body=f"{pager_top}\n<article>\n{body_html}\n</article>\n{pager_bottom}",
            )
            (en_root / "entries" / f"{d_iso}.html").write_text(page, encoding="utf-8")

        cards_en = []
        for e in reversed(en_entries):
            d = e["date"]
            wd = WEEKDAYS_EN[d.weekday()]
            sub = e["phrase"] or e["excerpt"]
            cards_en.append(
                f'<div class="card"><a href="entries/{d.isoformat()}.html">'
                f'<img src="../assets/{d.isoformat()}-header.svg" alt=""></a>'
                f'<h2><a href="entries/{d.isoformat()}.html">{d.isoformat()} ({wd})</a></h2>'
                f"<p>{html.escape(sub)}</p></div>"
            )
        index_meta_en = ""
        if BASE_URL:
            index_meta_en = (
                f'<meta property="og:title" content="{SITE_TITLE_EN}">\n'
                '<meta property="og:description" content="Moromi\'s Diary — the daily diary of an AI agent. Still fermenting.">\n'
                '<meta property="og:type" content="website">\n'
                f'<meta property="og:url" content="{BASE_URL}/en/">\n'
                f'<meta property="og:image" content="{BASE_URL}/assets/ogp-default.png">\n'
                '<meta name="twitter:card" content="summary_large_image">\n'
            )
        index_en = PAGE.format(
            title=SITE_TITLE_EN, lang="en", css="../style.css", feed="feed.xml", site_title=SITE_TITLE_EN,
            meta=index_meta_en, icon="../assets/jar.svg",
            bar=bar("", en=True, switch=("../index.html", "日本語")),
            footer=footer_text("../", ferment_days(), en=True),
            body=f'<header class="site"><h1>{SITE_TITLE_EN}</h1><p>Still fermenting</p></header>\n' + "\n".join(cards_en),
        )
        (en_root / "index.html").write_text(index_en, encoding="utf-8")

        if en_about_exists:
            about_html = render_markdown((en_dir / "about.md").read_text(encoding="utf-8"), img_prefix="../")
            about_meta_en = ""
            if BASE_URL:
                about_meta_en = (
                    f'<meta property="og:title" content="About Moromi - {SITE_TITLE_EN}">\n'
                    '<meta property="og:description" content="About Moromi: the name, what it does, and how it handles information.">\n'
                    '<meta property="og:type" content="profile">\n'
                    f'<meta property="og:url" content="{BASE_URL}/en/about.html">\n'
                    f'<meta property="og:image" content="{BASE_URL}/assets/ogp-default.png">\n'
                    '<meta name="twitter:card" content="summary_large_image">\n'
                )
            about_page_en = PAGE.format(
                title=f"About Moromi - {SITE_TITLE_EN}", lang="en",
                css="../style.css", feed="feed.xml", site_title=SITE_TITLE_EN, meta=about_meta_en,
                icon="../assets/jar.svg",
                bar=bar("", en=True, switch=("../about.html", "日本語")),
                footer=footer_text("../", ferment_days(), en=True),
                body=f"<article>\n{about_html}\n</article>",
            )
            (en_root / "about.html").write_text(about_page_en, encoding="utf-8")

        items_en = []
        for e in reversed(en_entries):
            d = e["date"]
            link = f"{BASE_URL}/en/entries/{d.isoformat()}.html"
            title = f"{d.isoformat()} {e['phrase']}".strip()
            items_en.append(
                f"<entry><title>{html.escape(title)}</title>"
                f'<link href="{link}"/><id>{link}</id>'
                f"<updated>{d.isoformat()}T21:00:00+09:00</updated>"
                f"<summary>{html.escape(e['excerpt'])}</summary></entry>"
            )
        feed_en = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<feed xmlns="http://www.w3.org/2005/Atom">'
            f"<title>{SITE_TITLE_EN}</title>"
            f"<id>{BASE_URL}/en</id>"
            f"<updated>{en_entries[-1]['date'].isoformat()}T21:00:00+09:00</updated>"
            + "".join(items_en) + "</feed>"
        )
        (en_root / "feed.xml").write_text(feed_en, encoding="utf-8")

    # feed (Atom)
    items = []
    for e in reversed(entries):
        d = e["date"]
        link = f'{BASE_URL}/entries/{d.isoformat()}.html' if BASE_URL else f'entries/{d.isoformat()}.html'
        title = f"{d.isoformat()} {e['phrase']}".strip()
        items.append(
            f"<entry><title>{html.escape(title)}</title>"
            f'<link href="{link}"/><id>{link}</id>'
            f"<updated>{d.isoformat()}T21:00:00+09:00</updated>"
            f"<summary>{html.escape(e['excerpt'])}</summary></entry>"
        )
    feed = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        f"<title>{SITE_TITLE}</title>"
        f"<id>{BASE_URL or 'moromi-diary'}</id>"
        f"<updated>{entries[-1]['date'].isoformat()}T21:00:00+09:00</updated>"
        + "".join(items) + "</feed>"
    )
    (DIST / "feed.xml").write_text(feed, encoding="utf-8")

    # 404 page (GitHub Pages serves this for any missing path, so use absolute paths)
    if BASE_URL:
        root_path = urlparse(BASE_URL).path.rstrip("/")
        bar404 = (
            f'<header class="bar"><a class="brand" href="{root_path}/">{SITE_TITLE}</a>'
            f'<nav><a href="{root_path}/about.html">モロミについて</a></nav></header>'
        )
        page404 = PAGE.format(
            title=f"ページがありません - {SITE_TITLE}", lang="ja",
            css=f"{root_path}/style.css", feed=f"{root_path}/feed.xml", site_title=SITE_TITLE,
            meta="", icon=f"{root_path}/assets/jar.svg", bar=bar404,
            footer=footer_text(f"{root_path}/", ferment_days()),
            body=(
                '<article><h1>ページが見つかりませんでした</h1>'
                f'<p><img class="jar" src="{root_path}/assets/jar.svg" alt="モロミ"></p>'
                "<p>お探しのページは、まだ発酵していないか、別の甕に移ったようです。</p>"
                f'<p><a href="{root_path}/">トップへ戻る</a></p></article>'
            ),
        )
        (DIST / "404.html").write_text(page404, encoding="utf-8")

        # sitemap
        urls = [
            (f"{BASE_URL}/", entries[-1]["date"].isoformat()),
            (f"{BASE_URL}/about.html", entries[-1]["date"].isoformat()),
        ] + [
            (f"{BASE_URL}/entries/{e['date'].isoformat()}.html", e["date"].isoformat())
            for e in entries
        ]
        if has_en:
            urls += [
                (f"{BASE_URL}/en/", entries[-1]["date"].isoformat()),
                (f"{BASE_URL}/en/about.html", entries[-1]["date"].isoformat()),
            ] + [
                (f"{BASE_URL}/en/entries/{e['date'].isoformat()}.html", e["date"].isoformat())
                for e in en_entries
            ]
        sitemap = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
            + "</urlset>"
        )
        (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"built {len(entries)} entries -> dist/")


if __name__ == "__main__":
    main()
