# 06｜重現分析、資料版本與發布

## 先區分三件事

| 你想做什麼 | 需要什麼 | 能確認什麼 |
| --- | --- | --- |
| 閱讀或展示現有結果 | 瀏覽器與網站 | 已發布的資料與圖表 |
| 從同一份原始擷取檔重算 | 原始 JSONL、分析程式、套件版本 | 相同規則是否產生相同分析數字 |
| 重新向鏡像取得資料再算 | 網路、查詢與取得程式 | 現在的鏡像對同樣條件回傳什麼 |

第三項不保證和原始擷取檔完全相同。鏡像內容、欄位定義、公開服務的限制都可能改變。重新查詢和重算現有檔案應分別記錄。

## 專案提供什麼？

- `analysis/events.sql`：十個儲存庫 ID、五種事件與時間邊界。
- `analysis/fetch_events.py`：分四段查詢鏡像，儲存九個分析欄位。
- `analysis/analyze.py`：清理、建立集合與二模網絡、輸出統計及中心度。
- `docs/data.json`：網站使用的固定分析結果。
- `docs/repro/centrality-scores.csv`：93 個跨專案帳號的四項中心度。
- `data/provenance.json`：原始擷取檔的 SHA-256、列數與版本資訊。
- `guide/` 與 `analysis/build_guide.py`：導讀原稿與靜態網頁產生程式。

原始 `data/raw-events.jsonl` **未附在公開儲存庫**。只有這個儲存庫時，可以檢查分析程式與已發布結果，也可以重新查詢；若要針對原始擷取檔完全重算，仍須另取得該檔，並比對 SHA-256。雜湊能識別檔案版本，不能證明來源完整或內容正確。

## 安裝與重新取得

以下命令在專案根目錄執行。原分析環境是 Python 3.12.4、NetworkX 3.2.1；導讀產生使用 Markdown 3.4.1。

```bash
git clone https://github.com/xxoon0987/sna-j-gharchive.git
cd sna-j-gharchive
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis/fetch_events.py --output data/raw-events-new.jsonl
```

Windows 的啟用環境命令改用 `.venv\Scripts\activate`。公共鏡像服務可能限流、停用或改變資料表；程式失敗時應先確認服務和欄位，不能把不完整回應當成完整資料。程式使用公開示範帳號 `demo`，不是個人的 GitHub 憑證。

## 重新計算

```bash
python analysis/analyze.py --input data/raw-events-new.jsonl --output docs/data.json --centrality-csv docs/repro/centrality-scores.csv
python analysis/build_guide.py
python -m http.server 4173 --directory docs
```

再用瀏覽器開啟 `http://127.0.0.1:4173/`。不要直接雙擊 `index.html`，因為瀏覽器可能阻擋從本機檔案讀取 JSON。

**更新資料後，必須同步更新 README、六份導讀和講稿的數字及版本紀錄。** 這些文件是人工解釋，不會隨 JSON 自動改寫。`build_guide.py` 只將六份 Markdown 轉為網頁，不會重新分析資料。`docs/repro/` 的可下載程式也應與 `analysis/` 同步。

## 本次擷取的核對紀錄

時間是 UTC；每段含開始、不含結束。

| 查詢區間 | 原始事件列數 | 清理後列數 |
| --- | ---: | ---: |
| 1 月 1 日至 1 月 8 日 | 2,209 | 2,040 |
| 1 月 8 日至 1 月 15 日 | 3,342 | 3,099 |
| 1 月 15 日至 1 月 22 日 | 3,184 | 3,052 |
| 1 月 22 日至 2 月 1 日 | 4,820 | 4,551 |
| 合計 | **13,555** | **12,742** |

原取得程式為避開公開示範服務的單次 10,000 列限制而分段；每段實際列數均低於該限制。但**低於限制本身，不等於已證明完整**：原始擷取沒有額外保存每段 `COUNT(*)` 比對結果、原始事件 ID 或 HTTP 回應中繼資料；也沒有逐時 GH Archive 原檔的逐筆對照。這些是資料稽核仍可補強的部分。

原始取得時間沒有獨立記錄；分析輸出的產生時間為 `2026-10-22T09:05:02+00:00`。這是程式產出時間，不能當成下載時間。研究事件本身發生於 2025 年 1 月。

## 更嚴謹地擴充研究

1. 同時保存查詢條件、取得時間、HTTP 狀態與檔案雜湊。
2. 每段另查符合條件的總列數，和下載列數比較；超過上限就再縮短區間。
3. 若來源可提供，保留事件 ID 與帳號 ID，以便辨識重複和帳號改名。
4. 以相同時間、儲存庫和事件定義，比對 GH Archive 原始逐時檔。
5. 延長觀察期間、擴充樣本，再確認結論是否穩定。

這些是後續改進方向，**不是本次已完成的工作**。目前分析未進行隨機抽樣、顯著性檢定、因果推論或中心度門檻的敏感度分析。

## GitHub Pages 如何發布？

本專案使用靜態網站，不需要資料庫或伺服器程式。

1. GitHub 儲存庫 → **Settings → Pages**。
2. Source 選 **Deploy from a branch**。
3. Branch 選 **main**，資料夾選 **/docs**，儲存。
4. 等待 GitHub Pages 部署完成，開啟 [公開網站](https://xxoon0987.github.io/sna-j-gharchive/)。

之後把更新推送到 `main` 的 `docs/`，GitHub Pages 就會重新發布。網站使用相對路徑，因此可在 `/sna-j-gharchive/` 這個專案網址下正常讀取樣式與資料。`.nojekyll` 讓這份現成的 HTML／CSS／JavaScript 以靜態檔發布。

設定依據：[GitHub Pages 發布來源文件](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。
