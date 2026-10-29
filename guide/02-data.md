# 02｜資料來源、欄位與清理

## 資料從哪裡來？

[GH Archive](https://www.gharchive.org/)封存 GitHub Events API 的公開活動紀錄，官方按小時提供壓縮的 JSON 事件檔。本組使用 ClickHouse 的公開 `github.github_events` 鏡像查詢需要的範圍，回傳格式是 `JSONEachRow`，儲存成 `.jsonl` 檔：每一行是一筆事件物件。

[ClickHouse 的公開匯入程式](https://github.com/ClickHouse/sql.clickhouse.com/blob/main/load_scripts/github_events/ingest.sh)顯示它從 GH Archive 的逐時檔取得資料並整理欄位。本組沒有自行下載全部逐時壓縮檔，也沒有逐筆比對鏡像與官方原檔，因此不能宣稱兩者完全一致或完整無遺漏。

採用鏡像本身不必然比較不精確；要確認完整性，需要檢查期間、篩選、欄位轉換、回傳限制與原始紀錄。下載更多不相關資料，也不會自動改善本研究的精確性。

## 這份資料涵蓋什麼？

| 條件 | 本組的設定 |
| --- | --- |
| 開始時間 | 2025-01-01 00:00:00 UTC，包含這個時間 |
| 結束時間 | 2025-02-01 00:00:00 UTC，不包含這個時間 |
| 專案 | 前一篇列出的十個 Hugging Face 儲存庫，以固定 repo ID 查詢 |
| 事件 | IssuesEvent、IssueCommentEvent、PullRequestEvent、PullRequestReviewEvent、PullRequestReviewCommentEvent |
| 沒有納入 | PushEvent、星號、fork 等其他事件；私人與線下活動 |
| 查詢方式 | 分成 1–7、8–14、15–21、22–31 日四段 |

這是 UTC 的一月，與台灣時間零時起訖的一月不同。日期屬於 2025 年；報告網站整理於 2026 年。

## 原始資料不是三個勾選欄位

原始資料是一筆筆活動。以下為**虛構教學例子**，不是研究中的原始列：

| 時間 | 觸發事件的帳號 | 儲存庫 | 事件類型 | 動作 |
| --- | --- | --- | --- | --- |
| 1 月 3 日 | A | 專案 X | IssuesEvent | opened |
| 1 月 5 日 | A | 專案 X | PullRequestEvent | opened |
| 1 月 8 日 | B | 專案 Y | PullRequestReviewEvent | created |
| 1 月 9 日 | A | 專案 Y | IssueCommentEvent | created |

同一個帳號可能出現很多次。分析時，才把它轉成「這個帳號是否有 Issue 活動」「是否參與某個專案」等 0／1 欄位。1 表示至少有一筆符合條件紀錄；0 表示這份選定資料中沒有這種紀錄。

## 我們實際擷取的 9 個欄位

| 欄位 | 白話解釋 | 使用時要注意 |
| --- | --- | --- |
| `repo_id` | 儲存庫識別碼 | 用它指定研究範圍 |
| `repo_name` | 儲存庫名稱，包含擁有者 | 分析程式檢查名稱是否在選定清單 |
| `event_type` | 事件類型 | 決定分到 Issue、討論、PR 或 Review |
| `actor_login` | 觸發這筆事件的帳號名稱 | 不一定是 Issue 或 PR 的原作者 |
| `creator_user_login` | 鏡像從 payload 整理出的建立者名稱 | 意義依事件而變；留言事件通常是留言作者，不能一律當成原議題作者 |
| `action` | opened、closed、created 等動作 | 本研究依事件類型納入，沒有再只篩選 opened |
| `review_state` | 審查狀態欄位 | 主網絡未用狀態區分核准或要求修改 |
| `event_time_utc` | 事件發生的 UTC 時間 | 用於期間與時間切片 |
| `number` | 儲存庫內的議題或 PR 編號 | 必須搭配 repo 才有意義；不是跨 GitHub 的唯一事件編號 |

資料沒有擷取留言正文、完整修改內容、GitHub event ID、actor ID 或是否合併等欄位。因此無法用這份擷取資料直接判斷每筆 PR 最後是否成功、內容品質、真人身分或完整事件去重。帳號名稱改變也沒有另外做身分合併。

## Issue、PR、Review 到底是什麼？

| 類別 | 白話情境 | 本組計入的活動 | 不能直接當成什麼 |
| --- | --- | --- | --- |
| Issue（議題） | 「這裡有錯誤」「希望增加功能」等問題單 | IssuesEvent；本快照有開啟、關閉、重新開啟 | 已解決問題、已修改程式碼 |
| 討論 | 在 issue 或 PR 下留言 | IssueCommentEvent | 全部都是 issue 留言，或留言一定回給原作者 |
| PR（Pull Request） | 已準備一份修改，請專案考慮合併 | PullRequestEvent；本快照有開啟、關閉、重新開啟 | 只有口頭建議、已成功合併，或每位事件觸發者都是 PR 作者 |
| Review（審查） | 對 PR 提交審查或留下程式碼審查留言 | PullRequestReviewEvent 加 PullRequestReviewCommentEvent | 只點開瀏覽、一次事件就等於一份完整審查 |

PR 可以包含文件、設定與程式碼等修改。GitHub 的帳號角色不是固定職業：同一帳號可以同時出現在多個類別。[GitHub 官方事件定義](https://docs.github.com/en/rest/using-the-rest-api/github-event-types)可用來核對事件觸發者與 payload。

## 資料清理做了什麼？

| 步驟 | 事件列數 |
| --- | ---: |
| 原查詢回傳 | 13,555 |
| 排除名稱以 `[bot]` 結尾 | −405 |
| 排除文件建置帳號 `HuggingFaceDocBuilderDev` | −408 |
| 保留 | **12,742** |

名稱尾碼比對不分大小寫；文件建置帳號依固定名稱排除，辨識依據見 [Hugging Face doc-builder](https://github.com/huggingface/doc-builder)。本快照缺少 `actor_login` 的列數是 0；程式遇到空帳號時也會略過。原程式的 `humanRows` 是歷史欄位名稱，應讀成「清理後保留列數」，不能保證全部來自真人。

清理不會把同一帳號的重複活動刪成一筆；一個帳號提議題又留言，本來就可能有兩筆事件。擷取時未保留唯一 event ID，沒有進行依 event ID 去重，也不能把欄位恰好相同的兩列直接判定成重複資料。

## 五種事件為什麼變成四類？

| 原始事件類型 | 清理後列數 | 網站分類 |
| --- | ---: | --- |
| IssuesEvent | 1,070 | Issue |
| IssueCommentEvent | 4,474 | 討論 |
| PullRequestEvent | 1,874 | PR |
| PullRequestReviewEvent | 2,941 | Review |
| PullRequestReviewCommentEvent | 2,383 | Review |
| 合計 | **12,742** | Review 合計為 5,324 |

列數相加可以得到總事件數；各類「不同帳號數」因為帳號重疊，不能直接相加當成總人數。

[下一篇：從事件到網絡與數學](03-methods.md)
