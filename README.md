# myRAG — 原生 Windows 研究知識庫 Demo

以 **LightRAG 1.5.7** 的伺服器、文件索引、向量檢索、圖譜引擎與管理 UI 為基底，增加 Windows 啟動流程、CPU Embedding/OCR、研究搜尋入口、Office 圖片及來源定位轉接。不是重寫 RAG 引擎。

## 公司電腦：下載 ZIP 後重現（建議使用這個流程）

公開儲存庫：[RyanPeng1111/myRAG](https://github.com/RyanPeng1111/myRAG)；使用 `main` 分支的 [完整 ZIP](https://github.com/RyanPeng1111/myRAG/archive/refs/heads/main.zip)。

需求：Windows x64、Python 3.12 x64。完整儲存庫包含約 440 MB 離線資源分片，GitHub 的 **Code → Download ZIP** 會一併包含這些檔案；公司電腦不需要 Git、Git LFS、Docker、GPU、WSL、Node.js 或額外資料庫。

1. 從 GitHub 的 **Code → Download ZIP** 取得整包，經公司掃描及核准流程帶入後，使用「解壓縮全部」解開至本機，例如 `D:\proj\myRAG`。進入實際包含 `Bootstrap.cmd` 的資料夾；不要直接在 ZIP 預覽裡執行。
2. 雙擊 **Bootstrap.cmd**。它會驗證資源 SHA-256、解開模型與套件、建立 `.venv`，完全使用本地套件安裝，不連 PyPI 或 Hugging Face。
3. 若 Python 沒有登錄 `py` launcher，在命令提示字元執行 `Bootstrap.cmd "C:\實際Python312路徑\python.exe"`。
4. 雙擊 **Start.cmd**，保留服務視窗，開啟 **http://127.0.0.1:9621/demo/**。
5. 另雙擊 **Load-Samples.cmd** 匯入合成範例；等文件頁顯示「已建立索引」後，即可測試向量搜尋、OCR 與來源圖片。
6. 在「模型設定」填入公司 LLM 網址、API key、model name。儲存後用 Stop.cmd、Start.cmd 重啟，即可測試 RAG 問答。要建圖，開啟圖譜並對選定文件重建索引。

這是重現相同程式、模型與樣本的流程，不會攜帶開發者的 API key、LLM 快取或工作中的資料索引；LLM 回答與抽取結果不保證逐字相同。先在未設定 LLM 時載入樣本，可避免匯入時意外消耗外部 API 額度。公司不必申請 Embedding API。

ZIP 更新方式：先停止服務，備份本機 `config.json` 與 `data/`，把新 ZIP 解壓到原本的專案資料夾並覆蓋程式檔，再重跑 Bootstrap.cmd。ZIP 不包含 config.json 與 data/，安裝程式也會保留它們；請不要刪除原本整個資料夾後再解壓。若偏好 Git，也可 clone／pull 後使用相同的三個 CMD 入口。若公司掃描或終端防護拒絕套件，需要依公司流程處理，本流程不會跳過安全檢查。

## 現在這台電腦怎麼用

專案位於 `D:\proj\myRAG`。如果服務仍運作，開啟：

**http://127.0.0.1:9621/demo/**

若服務已停止，雙擊 **Start.cmd**。資料會保留，停止時在服務視窗按 Ctrl+C。不要啟動多個相同資料目錄的服務。Start.cmd 不會調整 PowerShell 執行政策或防火牆。

也可雙擊 **Stop.cmd** 要求服務完成目前請求並保存索引後關閉，適用於這次預先啟動的背景服務。儲存模型設定後，先 Stop.cmd，再 Start.cmd。正在匯入大型文件時請等候關閉完成。

可先問：

- 有哪些降低電池溫升的實驗？
- 未塗層 48°C 陶瓷塗層 42°C（會找到含原圖的 PPT）
- 比較陶瓷塗層與石墨散熱片的效果與限制
- 更換黏著劑會影響什麼？
- 新進研發人員如何確認實驗條件及單位？

全部範例數據均為**合成軟體測試資料**，並非真實研究成果。未設定 LLM 時只能搜尋證據，介面停用「根據證據回答」。不提供假回答或假知識圖譜。

## 這一版的邊界

| 能力 | 狀態 |
|---|---|
| Windows / CPU / 不使用 Docker、WSL、Linux | 已實測啟動 |
| LightRAG 原生管理 UI、REST API | 保留 `/webui/`、`/docs` |
| 多語向量搜尋 | 本機 FastEmbed + ONNX Runtime，384 維 |
| Office/文件 | TXT、MD、PPTX、DOCX、XLSX、PDF、PNG、JPG |
| 圖片文字 | CPU RapidOCR，結果保留辨識標記，須核對原圖 |
| 圖片來源 | PPT/Word/PDF 嵌入圖片的 PNG 預覽＋原檔下載 |
| 來源位置 | PDF 頁碼、PPT 投影片、Excel 工作表/列/儲存格；Word 僅全文 |
| 公司 LLM、視覺問答、圖譜抽取 | 接口已接線，尚無公司端點，效果未驗證 |
| 公司 Embedding API | OpenAI 相容模式可設定，尚未在公司實測 |
| MinIO、Oracle、PostgreSQL | 本 demo 不需要，尚未整合 |
| 一萬份文件 / 多人權限 / 正式維運 | 尚未驗證；本地檔案儲存只供單機 demo |

解析限制：不讀 PPT 講者備註；PPT 頁面是解析內容檢視，未還原完整排版；Word 未還原頁碼與原始圖文順序；Excel 讀取公式文字而不計算公式，內嵌圖表/圖片尚未支援。PDF 未保證複雜版面的閱讀順序。OCR 是文字辨識，不代表理解圖表關係。舊版 `.doc/.ppt/.xls` 請先另存為新格式。SVG/EMF 等無法解碼的嵌入圖不會宣稱成功理解。

## 第一次安裝 / 帶入公司

需要 **Windows x64、Python 3.12 x64**。已驗證的本機 Python 為 3.12.14；不直接使用本機其他專案的 Python 3.14。獨立 `.venv` 不修改全域套件。

有可用的套件來源時，在專案目錄執行：

```powershell
.\Setup.ps1
.\Prepare.ps1
.\Start.ps1
```

若 Python 不在 `py` launcher 裡：

```powershell
.\Setup.ps1 -Python 'D:\Python312\python.exe'
```

`Prepare.ps1` 是明確的連外準備階段，下載本機 Embedding 與 tokenizer；啟動階段使用本地模型，不臨時下載。OCR 模型包含於套件 wheel 中。企業 CA 可設定 `config.json` 的 `ca_bundle`，不關閉 TLS 驗證。

完整 Git 儲存庫已包含 `offline/` 資源分片；上述 Bootstrap.cmd 即可離線安裝。以下是維護者重新準備資源的替代流程：

```powershell
.\Prepare-Offline.ps1
```

帶入以下項目：程式碼、`requirements-win-py312.lock`、`wheelhouse/`、`models/`、`.cache/tiktoken/`，以及公司核准的 Python 3.12 x64 安裝資源。在內網執行：

```powershell
.\Setup.ps1 -Offline -Python 'D:\Python312\python.exe'
.\Start.ps1
```

不要複製 `.venv` 當作可攜環境，也不要把你個人的 `config.json` 或真實公司資料提交 GitHub。Nexus 可透過標準 pip 設定指定，公司認證資訊不要寫在專案裡。

`dist/myRAG-source.zip` 現在包含程式碼與 `offline/` 分片，可解壓後直接使用 Bootstrap.cmd。`dist/myRAG-offline-resources.zip` 是同一批套件與模型的獨立資源包，供替代安裝流程使用，不必兩包都下載。`dist/manifest.json` 提供 SHA-256。這些包不含密鑰、使用者文件或 Python 安裝程式。可執行 `python tools/package.py` 重新打包；更新離線資源後，再執行 `python tools/split_resources.py` 更新 Git 分片。

## 模型設定

在 UI「模型設定」填入 **OpenAI 相容 Base URL、API key、model name**，儲存後重啟。網址要填供應商提供的 API base（通常以 `/v1` 結尾），不是 `/chat/completions` 完整路徑。金鑰只保存在本機 `config.json`，不回傳到瀏覽器，檔案已被 Git 忽略。

預設 `graph_enabled=false`，文件只建向量。打開圖譜後，新匯入文件才會呼叫 LLM 抽取關係。既有文件不會自動補建圖譜：先在文件清單移除該文件索引，再重新匯入。圖譜關係是模型抽取結果，不是已證實的因果。

Gemini 低額度保護：當 LLM 網址是 `generativelanguage.googleapis.com`，自動經由同一 Python 服務內的節流轉接，每分鐘最多約 4 次請求、同時 1 次。429／503 會使下一次請求至少延後 65 秒，再由上游重試機制重試。公司內網網址預設不啟用；可在 config.json 設定 `llm_requests_per_minute`（正整數，0 關閉）後重啟。此保護無法預知其他程式共用同一 Google 專案的用量，也不能解決每日額度用盡。啟用時串流回覆會先緩衝完整回應。

若建圖遇到 API 限流失敗，原檔仍在，不必重新上傳。待額度恢復後可呼叫 `POST /documents/reprocess_failed`；它會重試所有失敗／待處理文件並保留追蹤 ID。建圖會比單純向量索引慢，建議先測一份小文件。

若供應商回報 `PerDay` 每日額度耗盡，節流轉接會在本次服務執行期間記住該錯誤，不再反覆向外送出 LLM 請求。待供應商額度恢復後需重啟服務再重試。向量搜尋不受此限制。

Groq 免費額度保護：`api.groq.com` 預設每分鐘 1 次、同時 1 次請求。原因是建圖提示詞較長，實測單次約需 6,000 tokens，而帳號限制為每分鐘 8,000 tokens；只限制請求次數為每分鐘 30 次並不足夠。此保守節流不是精確 token 配額管理，單次超過可用 token 上限、每日用量或其他程式共用額度仍可能失敗。

Groq 的 `openai/gpt-oss-*` 模型若未指定相關參數，轉接預設 `reasoning_effort=low`、`max_completion_tokens=4096`，避免預設推理耗盡輸出額度卻沒有產生抽取文字；可用 config.json 的 `groq_reasoning_effort` 與 `groq_max_completion_tokens` 調整。

公司提供 Embedding 時，修改 `config.json` 的 `embedding`：

```json
{
  "mode": "api",
  "base_url": "https://company-host/v1",
  "api_key": "YOUR_KEY",
  "model": "YOUR_EMBEDDING_MODEL",
  "dimension": 1024,
  "max_tokens": 512
}
```

維度必須與實際模型一致。切換 Embedding 模型/端點後，啟動器會拒絕混用既有索引。請先停機備份 `data/`，把整個 `data/` 移到另一個備份目錄，再啟動並重新匯入原始文件。**不要只刪 profile 檔案繞過檢查。** 本 demo 不提供跨模型自動遷移。

## 文件操作與 API

請從 **myRAG 文件資料庫** 匯入，才能建立完整的圖片／來源對應。直接使用 LightRAG 進階管理上傳仍可索引，但不會自動獲得本整合層的原圖來源資訊。

- `POST /demo/upload`：multipart `file`；回傳 tracking IDs。送入佇列不等於索引完成。
- `GET /demo/sources`：查詢原檔與即時索引狀態。
- `POST /demo/search`：純檢索；`{"query":"降低電池溫升","mode":"naive","limit":6}`。
- `POST /demo/ask`：LLM 問答；未設定模型時回傳 409，不產生模擬答案。
- `GET /demo/sources/{id}`：解析內容、來源位置及圖片 metadata。
- `GET /demo/download/{id}`：下載原始文件。
- `DELETE /demo/sources/{id}/index`：移除索引；原檔與圖片保留，能下載後重新匯入。
- `/query/data`、`/query`、`/query/stream`：上游 REST API。

```powershell
$body = @{ query = '有哪些降低電池溫升的實驗？'; mode = 'naive'; limit = 6 } | ConvertTo-Json
Invoke-RestMethod 'http://127.0.0.1:9621/demo/search' -Method Post -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

上游 `file_path` 以內部來源 ID 命名；`/demo/search` 額外提供使用者檔名、位置、source URL 及圖片 URL。影像查詢目前是 OCR／圖片描述的文字檢索，不是跨模態「以圖找圖」。

## 資料與維護

- `data/index/`：LightRAG 檔案型索引、圖譜與狀態。
- `data/sources/`：原始文件、圖片預覽、解析 metadata。
- `data/inputs/`：交給上游處理的文字中介檔。
- `models/`：Embedding 權重。
- `logs/`：診斷與測試結果，可能包含文件內容，不要隨意對外分享。
- `config.json`：含模型密鑰；與資料分開保護。

備份前先停機，完整複製 `data/`，另備份設定及模型。還原使用相同套件鎖定版本與 Embedding 模型。不能在服務寫入時直接拷貝部分 JSON 檔作為可靠備份。

此版只綁定 `127.0.0.1`，供本機瀏覽器與 Agent 使用。沒有實作企業使用者權限，不應直接改成對全公司公開。可用專案內的 `tools/doctor.py` 檢查環境。

## 驗證

本機已執行的項目及尚未驗證的範圍見 [VERIFICATION.md](VERIFICATION.md)。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools\offline_probe.py
# 服務啟動後，先準備並匯入合成範例：
.\.venv\Scripts\python.exe tools\make_samples.py
.\.venv\Scripts\python.exe tools\seed.py
.\.venv\Scripts\python.exe tools\smoke.py
```

smoke 會匯入一份明確標示的可丟棄測試文件，確認可搜尋後移除其索引；原檔仍保留。LLM 問答、公司 API、真實研究效果與 GraphRAG 品質未由這些測試證明。

## 上游與延伸範圍

- LightRAG：https://github.com/HKUDS/LightRAG ，版本 1.5.7；檢查用原始碼 commit `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`。
- 執行時安裝相同版本的 PyPI wheel（含上游 UI），不需 Node/Bun。
- FastEmbed：https://github.com/qdrant/fastembed ，版本 0.8.0。
- RapidOCR：https://github.com/RapidAI/RapidOCR ，使用 `rapidocr-onnxruntime==1.4.4`。
- 自有程式位於 `demo/`、`web/`、`tools/` 與啟動腳本；未修改上游核心。`vendor/LightRAG` 僅供原始碼檢視，不是執行依賴。

帶入企業的資源仍需遵循公司的套件、模型與授權審查。本專案不要求跳過掃描或解除公司安全設定。
