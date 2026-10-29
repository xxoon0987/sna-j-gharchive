"""Render the six reviewed Markdown chapters as a portable static guide."""

from pathlib import Path
import html
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = [
    ("01-overview.md", "overview", "先看懂報告"),
    ("02-data.md", "data", "資料來源與內容"),
    ("03-methods.md", "methods", "網絡與數學"),
    ("04-results.md", "results", "結果與限制"),
    ("05-questions.md", "questions", "常見疑問"),
    ("06-reproduce.md", "reproduce", "重現與發布"),
]
REPO = "https://github.com/xxoon0987/sna-j-gharchive/blob/main/"


def render_chapter(filename: str, anchor: str) -> str:
    source = (ROOT / "guide" / filename).read_text(encoding="utf-8")
    # Keep one page-level h1; shift Markdown heading levels down one.
    source = re.sub(r"^(#{1,5}) ", r"\1# ", source, flags=re.M)
    rendered = markdown.markdown(source, extensions=["tables", "fenced_code"])
    for name, target, _ in CHAPTERS:
        rendered = rendered.replace(f'href="{name}"', f'href="#{target}"')
    rendered = rendered.replace('href="../docs/', 'href="./')
    rendered = rendered.replace('href="../analysis/', f'href="{REPO}analysis/')
    rendered = rendered.replace('href="../data/', f'href="{REPO}data/')
    rendered = rendered.replace('<table>', '<div class="table-scroll" tabindex="0" role="region" aria-label="可橫向捲動的資料表"><table>')
    rendered = rendered.replace('</table>', '</table></div>')
    return f'<section class="chapter" id="{anchor}">{rendered}</section>'


def main() -> None:
    nav = "".join(
        f'<a href="#{anchor}"><span>0{i}</span>{html.escape(label)}</a>'
        for i, (_, anchor, label) in enumerate(CHAPTERS, 1)
    )
    chapters = "\n".join(render_chapter(name, anchor) for name, anchor, _ in CHAPTERS)
    page = f'''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="從 Issue、PR、Review 到 Jaccard 與 eigenvector：第 J 組開源協作報告的完整白話導讀，附資料定義、算式、結果與重現步驟。">
  <meta name="theme-color" content="#12352f">
  <title>白話導讀｜開源協作地圖 · 第 J 組</title>
  <link rel="stylesheet" href="./guide.css">
</head>
<body>
  <a class="skip" href="#reading">跳至導讀內容</a>
  <header class="topbar"><a class="brand" href="./index.html">J<span>.</span> 開源協作地圖</a><nav aria-label="網站導覽"><a href="./index.html#network">互動報告 ↗</a><a href="https://github.com/xxoon0987/sna-j-gharchive">GitHub 專案 ↗</a></nav></header>
  <main>
    <div class="intro">
      <p class="eyebrow">GROUP J / READING GUIDE</p>
      <h1>先看懂，<br><em>再讀懂數字。</em></h1>
      <p class="lede">從「這份報告在做什麼」開始，一步一步理解公開活動如何變成網絡、指標與結論。</p>
      <p class="intro-note">研究：2025 年 1 月 · 10 個 Hugging Face 專案<br>整理：2026 年 10 月 · 固定資料，不即時追蹤</p>
      <div class="number-path" aria-label="帳號篩選條件">
        <div><strong>1,379</strong><span>研究資料裡的不同帳號</span></div><b aria-hidden="true">→</b>
        <div><strong>93</strong><span>其中，參與至少兩個專案</span></div><b aria-hidden="true">→</b>
        <div><strong>59</strong><span>其中，又同時參與兩類活動</span></div>
      </div>
      <p class="path-note">兩類活動＝Issue／討論，以及 PR／Review。93 包含在 1,379 裡；59 包含在 93 裡。</p>
    </div>
    <div class="reading-layout">
      <aside class="contents"><p class="eyebrow">閱讀路線</p><nav aria-label="章節目錄">{nav}</nav><p>第一次閱讀：從第 1 章開始。<br>準備答問：直接看第 5 章。<br>查計算參數：看第 3 章。</p><a class="download" href="./repro/centrality-scores.csv" download>下載完整中心度 CSV ↓</a></aside>
      <article id="reading">{chapters}</article>
    </div>
  </main>
  <footer><span>第 J 組 · 社會網絡分析報告</span><a href="./index.html">回到互動報告 →</a></footer>
</body>
</html>
'''
    (ROOT / "docs" / "guide.html").write_text(page, encoding="utf-8")
    print("Rendered 6 chapters to docs/guide.html")


if __name__ == "__main__":
    main()
