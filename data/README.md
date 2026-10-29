# 資料版本

`provenance.json` 記錄本次研究快照的範圍、列數、檔案 SHA-256 與環境。

原始事件擷取檔未上傳。若要重算相同原始檔，須另取得檔案並比對 SHA-256；若重新向鏡像查詢，結果可能隨鏡像更新而不同。雜湊只用來辨識檔案版本，不能證明資料完整性。

可公開閱讀的分析結果在 [`docs/data.json`](../docs/data.json)，中心度表在 [`docs/repro/centrality-scores.csv`](../docs/repro/centrality-scores.csv)。這些結果包含公開 GitHub 帳號名稱，不是匿名資料。

取得與重算步驟見 [06｜重現分析](../guide/06-reproduce.md)。
