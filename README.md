# 開源協作地圖｜第 J 組社會網絡分析

**我們想知道：在十個 Hugging Face 專案裡，參與議題、討論、PR 與審查的帳號是否重疊？哪些帳號跨越不同專案？**

我們把 2025 年 1 月的公開 GitHub 活動紀錄整理成「帳號與專案的關係」，用網絡圖和數學指標描述參與模式。本研究沒有訓練 AI 模型，也沒有評分誰的程式能力最好。

**[開啟互動報告網站](https://xxoon0987.github.io/sna-j-gharchive/)** · **[閱讀完整白話導讀](https://xxoon0987.github.io/sna-j-gharchive/guide.html)** · **[四人 20 分鐘講稿](presentation/FULL_SCRIPT_20MIN.md)**

網站為公開的 GitHub Pages 靜態網站。觀看者不需要登入 ChatGPT，也不需要開啟製作者的電腦。網站使用固定研究資料，不會即時追蹤 GitHub 使用者。

## 從哪裡開始讀？

| 你想了解什麼 | 閱讀位置 |
| --- | --- |
| 完全沒有背景，想先知道報告在做什麼 | [01｜先看懂這個報告](guide/01-overview.md) |
| Issue、PR、Review 是什麼？原始資料長什麼樣？ | [02｜資料來源、欄位與清理](guide/02-data.md) |
| 連線、93、59、Jaccard 和 eigenvector 怎麼算？ | [03｜從事件到網絡與數學](guide/03-methods.md) |
| 結果代表什麼？有哪些不能推論的地方？ | [04｜結果與限制](guide/04-results.md) |
| 想準備老師可能問的問題 | [05｜常見疑問](guide/05-questions.md) |
| 想重新計算、更新網站或檢查參數 | [06｜重現與發布步驟](guide/06-reproduce.md) |

每份說明先用白話解釋，再列出定義、算式或來源。A、B、C 帳號例子是教學用的虛構例子；研究數值來自本專案的分析輸出。

## 用一分鐘理解

把十個開源專案想成十個工作小組。有人提出問題，有人回覆，有人送出修改提案，也有人審查修改。GitHub 會留下其中一些公開活動的紀錄。

本組限定「哪十個專案、哪一個月、哪幾種事件」，再問三件事：

1. 同時有 Issue 與 PR 活動的帳號有多少？
2. 哪些帳號在兩個以上專案留下紀錄？
3. 如果只看 Issue，或只看 Review，看到的關係是否不同？

流程是：**公開事件 → 查詢需要的範圍 → 排除可辨識自動化帳號 → 整理帳號與專案的關係 → 計算指標 → 用網站解釋結果。**

## 最重要的數字

| 數字 | 正確意思 |
| --- | --- |
| 13,555 | 鏡像查詢回傳的所選事件列數；不是整個 GH Archive 的大小 |
| 813 | 被排除的可辨識自動化帳號事件列數；不是 813 個帳號 |
| 12,742 | 清理後保留的事件列數；不保證每筆都由真人操作 |
| 1,379 | 保留事件中出現的不同帳號名稱數；不是事件數 |
| 93 | 上述帳號中，參與至少兩個選定專案的帳號數 |
| 59 | 93 個帳號中，同時有「Issue／留言」及「PR／Review」兩類活動的帳號數 |

**1,379 個帳號 → 其中 93 個跨專案 → 其中 59 個又跨兩類活動。**

其中 1,286 個帳號只參與一個選定專案；93 個跨專案帳號中的另外 34 個沒有同時滿足兩類活動條件。「參與」一律指選定期間內有符合條件的公開事件。

## 主要發現

- Issue 與 PR 的帳號交集是 125、聯集是 801，所以 Jaccard 是 `125 / 801 ≈ 0.156`。這表示聯集中約 15.6% 的帳號兩種活動都有，不是「15.6% 的 Issue 被做成 PR」。
- PR 與 Review 的 Jaccard 是 0.291，Issue 與 Review 是 0.107。三組中，PR 與 Review 的帳號集合比較接近，但仍不是完全同一批。
- 四種中心度使用同一張跨專案核心網絡：93 個帳號、10 個儲存庫、229 條二元連線。不同指標量測不同位置，所以排序可能不同。

詳見[結果與限制](guide/04-results.md)。這些結果描述固定研究範圍，不能直接推論個人的能力、因果影響或整個 GitHub。

## 與老師要求的對照

| 報告要求 | 本專案的內容與證據 |
| --- | --- |
| 資料來源 | GH Archive 公開事件，透過 ClickHouse 公開鏡像取得；保留 [SQL](analysis/events.sql) 與 [取得程式](analysis/fetch_events.py) |
| 資料內容 | [9 個欄位、5 種原始事件、4 個展示分類](guide/02-data.md)，以及時間與專案邊界 |
| 基本數學運算 | [0／1 矩陣、加總、集合交聯集、Jaccard、每日平均](guide/03-methods.md) |
| 課文的類似部分 | W02「女性 × 社交活動」對照「帳號 × 儲存庫」；W06 四種中心度 |
| 用什麼找重要資訊 | Degree、closeness、betweenness、eigenvector 的定義、參數及 [93 個帳號分數](docs/repro/centrality-scores.csv) |
| 可檢查的結論 | [分析程式](analysis/analyze.py)、[網站資料](docs/data.json)、[資料版本紀錄](data/provenance.json)、[重現說明](guide/06-reproduce.md) |

## 檔案結構

```text
README.md             GitHub 首頁與閱讀入口
guide/                六份說明的 Markdown 原稿
docs/                 GitHub Pages 網站、圖表資料與下載檔
analysis/             查詢、分析及導讀產生程式
data/provenance.json  研究範圍、擷取檔雜湊與環境紀錄
presentation/         四人講稿與報告流程
requirements.txt      Python 套件版本
```

原始事件擷取檔沒有上傳；可用查詢程式重新取得相同範圍。網站與分數表含研究範圍內的公開 GitHub 帳號名稱，因此不是匿名資料。重新查詢可能因鏡像或服務更新而不同，詳見[重現說明](guide/06-reproduce.md)。

## 來源

- [GH Archive](https://www.gharchive.org/)與 [GitHub 事件定義](https://docs.github.com/en/rest/using-the-rest-api/github-event-types)。
- [ClickHouse 鏡像匯入程式](https://github.com/ClickHouse/sql.clickhouse.com/blob/main/load_scripts/github_events/ingest.sh)：資料來源與欄位轉換。
- [課程 W02](https://sna-studio-course-tw.cs-lee.chatgpt.site/week/2)、[課程 W06](https://sna-studio-course-tw.cs-lee.chatgpt.site/week/6)：雙模網絡與中心度。
- [NetworkX 3.2 中心度文件](https://networkx.org/documentation/networkx-3.2/reference/algorithms/centrality.html)。

研究期間為 2025 年 1 月（UTC），網站與說明整理於 2026 年。本專案為課程報告，與 Hugging Face、GitHub、GH Archive 無官方隸屬關係。
