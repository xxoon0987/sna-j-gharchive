# 01｜先看懂這個報告

## 我們到底在研究什麼？

開源軟體的工作可能由不同帳號完成：有人發現問題、有人回答、有人的修改被送出審查。這份報告把公開活動紀錄整理成關係圖，觀察「哪些帳號參與哪些專案」，以及不同活動的參與帳號有多少重疊。

例如甲帳號只在專案 X 留言，乙帳號同時在 X 和 Y 有活動。兩者都有參與，但乙在這個觀察範圍內具有跨專案位置。這個位置值得研究，卻不能單靠它斷言乙比較厲害，或真的促成兩個團隊合作。

## 三個研究問題

| 問題 | 使用的資料或方法 | 可以回答的事情 |
| --- | --- | --- |
| Issue、PR、Review 是不是同一批帳號？ | 比較帳號集合，計算 Jaccard | 兩種活動的參與帳號重疊程度 |
| 哪些帳號跨越專案？ | 帳號連到的不同儲存庫數與四種中心度 | 帳號在界定網絡內的位置 |
| 換一種活動，網絡會怎麼變？ | 固定時間與十個專案，切換事件類型 | 關係定義改變後，帳號數與連線如何改變 |

## 先分清楚四個東西

| 名詞 | 白話意思 | 本報告中的例子 |
| --- | --- | --- |
| GitHub | 存放程式、追蹤修改、協作開發的平台 | 專案可以有議題、PR 和審查紀錄 |
| 儲存庫（repository，簡稱 repo） | 一個專案的程式碼、文件與版本歷史所在的地方 | `huggingface/transformers` |
| 事件（event） | 平台記錄的一次特定動作 | 某帳號在某時關閉一張問題單 |
| 本組資料集 | 查詢與分析所用的事件紀錄集合 | 2025 年 1 月、十個 repo、五種事件 |

**十個 Hugging Face 儲存庫是研究對象；本組查詢取得的事件紀錄才是分析資料集。**

## 十個專案各在做什麼？

這十個 repo 位於 Hugging Face 的組織帳號下。以下是用途的概括介紹，連結可查看各專案的官方說明；本研究沒有分析它們的模型效能。

| 儲存庫 | 可以怎麼理解它的用途 |
| --- | --- |
| [Transformers](https://github.com/huggingface/transformers) | 載入、訓練與使用機器學習模型的工具 |
| [Datasets](https://github.com/huggingface/datasets) | 載入與處理資料集的程式庫；名稱叫 Datasets，但這個 GitHub repo 本身是工具專案 |
| [Tokenizers](https://github.com/huggingface/tokenizers) | 將文字轉成模型使用的 token，並提供相關處理工具 |
| [Accelerate](https://github.com/huggingface/accelerate) | 協助訓練程式在不同硬體或多個運算裝置上執行 |
| [Diffusers](https://github.com/huggingface/diffusers) | 使用與訓練擴散生成模型的工具 |
| [PEFT](https://github.com/huggingface/peft) | 用較少的可訓練參數微調模型的工具 |
| [TRL](https://github.com/huggingface/trl) | 提供語言模型訓練、微調與強化學習相關方法 |
| [Hugging Face Hub](https://github.com/huggingface/huggingface_hub) | 在程式中下載、上傳與管理 Hugging Face Hub 資源的客戶端程式庫 |
| [Smolagents](https://github.com/huggingface/smolagents) | 建立能使用工具的 AI agent 的程式庫 |
| [Text Generation Inference](https://github.com/huggingface/text-generation-inference) | 部署文字生成模型、提供推論服務的工具 |

公開 repo 可以讓外部帳號提議修改，但不是任何人都能直接覆寫主專案。外部貢獻者常在自己的分支或 fork 準備修改，再送 PR；有權限的維護者決定是否合併。PR 也可能修改文件或設定，不限於程式碼。

## 可以用這句話介紹報告

> 我們用 2025 年 1 月十個 Hugging Face 專案的公開 GitHub 事件，研究不同活動的帳號是否重疊，以及哪些帳號跨越專案。我們把事件轉成帳號與儲存庫的網絡，用 Jaccard 和四種中心度描述參與模式。

## 我們做了哪些分析工作？

1. 設定研究範圍：十個儲存庫、一個月、五種事件。
2. 從 ClickHouse 的 GH Archive 鏡像查詢需要的欄位。
3. 排除可辨識的自動化帳號事件。
4. 把事件整理成帳號集合與 0／1 參與矩陣。
5. 計算重疊、跨專案參與、四種中心度與每日平均。
6. 把結果做成能切換事件類型的網站，附上程式和解讀限制。

這是「既有資料的再分析」。資料的收集來源與本組的分析貢獻應分別交代。

[下一篇：資料來源、欄位與清理](02-data.md)
