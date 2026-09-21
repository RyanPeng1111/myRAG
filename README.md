# myRAG — 原生 Windows 研究知識庫 Demo

以 **LightRAG 1.5.7** 的伺服器、文件索引、向量檢索、圖譜引擎與管理 UI 為基底，增加 Windows 啟動流程、CPU Embedding/OCR、研究搜尋入口、Office 圖片及來源定位轉接。不是重寫 RAG 引擎。

## 目前 main：研究對話工作區

2026-09-19：UI／UX 改版已整合至 `main`。請下載 [main 完整 ZIP](https://github.com/RyanPeng1111/myRAG/archive/refs/heads/main.zip)，解壓後使用相同的 Bootstrap.cmd、Start.cmd 流程。沒有增加前端建置步驟或執行依賴；本次更新不變更 Embedding 模型、維度與既有文件索引格式，不必為改版重新匯入文件。

- 左側切換研究對話、文件資料庫與模型設定；中央提問，右側核對研究證據。
- 已設定 LLM 時預設「研究問答」；沒有 LLM 時預設「只找證據」。檢索方式在輸入框旁的「語意搜尋」選單內，可切換圖譜＋向量或圖譜全域；未啟用圖譜時會明確停用。
- Enter 送出、Shift + Enter 換行；範例問題只填入輸入框，送出後才呼叫 API。引用 `[1]`／`【1】` 可點擊定位右側片段，圖片可放大，來源可開啟或下載。
- 可在本次分頁中開啟與切換多個對話；對話暫存在瀏覽器記憶體，重新整理後清除。每次回答帶入最近 3 組成功問答，每則最多 6,000 字元。
- 對話上下文供 LLM 生成回答使用；文件檢索仍依照本次問題執行，尚未加入獨立的追問改寫模型。因此追問請保留實驗名稱或研究主題，避免只寫「那它呢」。
- 文件頁支援拖放／多檔上傳、逐檔進度、檔名／狀態篩選，每 10 秒更新狀態；單檔失敗不會阻擋後續檔案。原始文件的保留與移除索引行為沿用既有 API。

REST API 路徑不變；`POST /demo/ask` 新增可選的 `conversation_history` 陣列（最多 6 則 `user`／`assistant` 訊息，每則包含 `role`、`content`），原有呼叫方式仍可使用。

## 快速開始：下載 ZIP 安裝

公開儲存庫：[RyanPeng1111/myRAG](https://github.com/RyanPeng1111/myRAG)；使用 `main` 分支的 [完整 ZIP](https://github.com/RyanPeng1111/myRAG/archive/refs/heads/main.zip)。

需求：Windows x64、Python 3.12 x64。完整儲存庫包含約 440 MB 離線資源分片，GitHub 的 **Code → Download ZIP** 會一併包含這些檔案；安裝不需要 Git、Git LFS、Docker、GPU、WSL、Node.js 或額外資料庫。

1. 從 GitHub 的 **Code → Download ZIP** 取得整包，使用「解壓縮全部」解開至自選的專案資料夾。進入實際包含 `Bootstrap.cmd` 的資料夾；不要直接在 ZIP 預覽裡執行。
2. 雙擊 **Bootstrap.cmd**。它會驗證資源 SHA-256、解開模型與套件、建立 `.venv`，完全使用本地套件安裝，不連 PyPI 或 Hugging Face。
3. 若 Python 沒有登錄 `py` launcher，在命令提示字元執行 `Bootstrap.cmd "<Python312安裝目錄>\python.exe"`。
4. 雙擊 **Start.cmd**，保留服務視窗，開啟 **http://127.0.0.1:9621/demo/**。
5. 另雙擊 **Load-Samples.cmd** 匯入合成範例；等文件頁顯示「可供搜尋」後，即可測試向量搜尋、OCR 與來源圖片。
6. 在「模型設定」填入自訂 LLM 網址、API key、model name。儲存後用 Stop.cmd、Start.cmd 重啟，即可測試 RAG 問答。要建圖，開啟圖譜並對選定文件重建索引。

這是重現相同程式、模型與樣本的流程，不會攜帶開發者的 API key、LLM 快取或工作中的資料索引；LLM 回答與抽取結果不保證逐字相同。先在未設定 LLM 時載入樣本，可避免匯入時意外消耗外部 API 額度。使用本機 Embedding 時不需要額外 API。

若套件遭安全掃描或終端防護攔截，請依部署環境的管理政策處理。

## 已安裝版本如何更新（ZIP）

1. 等目前的文件匯入與索引處理完成，再執行 **Stop.cmd**，確認服務已結束。
2. 備份目前的 **config.json** 與整個 **data/** 資料夾，並保留舊版程式 ZIP。若有調整 ca_bundle 指向自訂憑證檔，也保留該檔案及路徑。
3. 下載並掃描最新的 **main ZIP**。先解壓到暫存資料夾，找到裡面實際含有 `Bootstrap.cmd` 的目錄。
4. 把該目錄的內容複製到原本專案資料夾，覆蓋同名程式檔；不要把 `myRAG-main` 整層塞進原目錄，也不要刪除原本整個專案資料夾。ZIP 不含 config.json、data/ 或 .venv/。
5. 執行 **Bootstrap.cmd**。既有設定與資料會保留；本次 UI 改版沒有新增套件，但重跑可檢查環境。若找不到 Python 3.12，改用 `Bootstrap.cmd "<Python312安裝目錄>\python.exe"`；可先執行 `py -0p` 查看啟動器認得的版本。
6. 執行 **Start.cmd**，開啟 `http://127.0.0.1:9621/demo/`，按 **Ctrl + F5** 更新瀏覽器快取。確認文件清單、搜尋與模型設定正常；已匯入資料不需要再執行 Load-Samples.cmd。

本次更新必須重啟 Python 服務，才能啟用新增的對話上下文 API。若要回復舊版，先停止服務，在另一個乾淨資料夾解壓舊版 ZIP、執行 Bootstrap.cmd，再還原更新前備份的 config.json 與 data/；不要讓兩份程式同時使用同一資料目錄或連接埠。

使用 Git 的開發者可在停止服務並備份後執行 `git switch main`、`git pull --ff-only`，再執行 Bootstrap.cmd 與 Start.cmd。

維護原則：往後每次合併 main，若有功能、安裝、設定、API 或資料格式變動，必須同步更新本 README，說明升級步驟、是否需要重建索引及回復方式。未來共用服務的選型與演進方向見 [ARCHITECTURE.md](ARCHITECTURE.md)；該文件是規劃，並非目前已接通的服務。

## 啟動與日常使用

在專案資料夾執行 Start.cmd，服務啟動後開啟：

**http://127.0.0.1:9621/demo/**

若服務已停止，雙擊 **Start.cmd**。資料會保留，停止時在服務視窗按 Ctrl+C。不要啟動多個相同資料目錄的服務。Start.cmd 不會調整 PowerShell 執行政策或防火牆。

也可雙擊 **Stop.cmd** 要求服務完成目前請求並保存索引後關閉，也適用於背景啟動的服務。儲存模型設定後，先 Stop.cmd，再 Start.cmd。正在匯入大型文件時請等候關閉完成。

可先問：

- 有哪些降低電池溫升的實驗？
- 未塗層 48°C 陶瓷塗層 42°C（會找到含原圖的 PPT）
- 比較陶瓷塗層與石墨散熱片的效果與限制
- 更換黏著劑會影響什麼？
- 新進研發人員如何確認實驗條件及單位？

全部範例數據均為**合成軟體測試資料**，並非真實研究成果。未設定 LLM 時只能搜尋證據，介面停用「研究問答」。不提供假回答或假知識圖譜。

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
| 自訂 LLM、視覺問答、圖譜抽取 | 接口已接線；各部署環境的端點與效果需另行驗證 |
| 自訂 Embedding API | OpenAI 相容模式可設定，各部署環境需另行驗證 |
| MinIO、Oracle、PostgreSQL | 本 demo 不需要，尚未整合 |
| 一萬份文件 / 多人權限 / 正式維運 | 尚未驗證；本地檔案儲存只供單機 demo |

解析限制：不讀 PPT 講者備註；PPT 頁面是解析內容檢視，未還原完整排版；Word 未還原頁碼與原始圖文順序；Excel 讀取公式文字而不計算公式，內嵌圖表/圖片尚未支援。PDF 未保證複雜版面的閱讀順序。OCR 是文字辨識，不代表理解圖表關係。舊版 `.doc/.ppt/.xls` 請先另存為新格式。SVG/EMF 等無法解碼的嵌入圖不會宣稱成功理解。

## Embedding、向量搜尋與知識圖譜如何運作

本節說明目前程式的實作。Embedding 可以理解成「把文字轉成可比對意思的數字」；Vector（向量）就是轉換結果；知識圖譜則記錄「哪些事物，彼此有什麼關係」。

### 預設 Embedding 模型與執行方式

| 項目 | 目前預設 |
|---|---|
| 模式 | `embedding.mode=local`，本機執行 |
| 模型 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| 執行工具 | FastEmbed + ONNX Runtime，使用 CPU |
| 輸出維度 | 384；每段輸入文字產生一組 384 個數字 |
| 模型位置 | `models/`；完整離線包由 Bootstrap 解開，執行時只載入本機模型 |
| CPU 執行緒 | `cpu_threads=4` |
| 本機 Embedding 批次大小 | 8 |
| LightRAG 文字切片 | `CHUNK_SIZE=200` tokens，重疊 `CHUNK_OVERLAP_SIZE=25` tokens |
| 傳給 LightRAG 的 Embedding token limit 設定 | `embedding.max_tokens=512` |
| 向量儲存 | NanoVectorDB，位於 `data/index/` 的本機檔案 |
| 圖譜儲存 | NetworkX，位於 `data/index/` 的本機檔案 |

上述值來自 [config.example.json](config.example.json)、[run.py](run.py) 與 [demo/extension.py](demo/extension.py)。實際部署以自己的 `config.json` 為準；`GET /demo/status` 可查看目前的 Embedding 模式、模型名稱及圖譜開關。

Token 是模型處理文字的單位，不等於中文字數。切片大小與 Embedding 輸入限制是不同設定；LightRAG 與 Embedding 模型也可能使用不同 tokenizer，因此 `max_tokens=512` 不能解讀成模型保證完整處理 512 個中文字。過長輸入仍需留意模型端的截斷。

例如「陶瓷塗層能降低電池溫升」會轉成類似 `[0.12, -0.08, 0.31, …]` 的向量（僅示意，並非實際輸出）。每個數字通常沒有可以直接命名的意思；不是第一格代表材料、第二格代表溫度。模型透過整組數字表達文字特徵，供後續相似度比對。

這是使用既有模型計算向量，**不會因上傳文件就重新訓練或微調模型**。預設不需要 GPU，也不需要額外的 Embedding API 或 API key。

### 上傳文件後，哪些內容會被轉成向量？

1. **解析文件**：myRAG 讀取文字、可支援的表格及嵌入圖片；各格式限制見「這一版的邊界」。
2. **將圖片內容轉成文字**：啟用 OCR 時，RapidOCR 辨識圖片文字；若已設定 LLM，程式也會嘗試請它描述圖片。只有端點支援視覺且呼叫成功，才會加入帶有核對標記的描述；目前每頁最多嘗試前 3 張圖片。
3. **保留來源**：把檔名、來源位置與解析文字交給 LightRAG，原檔與圖片另行保存，供搜尋結果回查。
4. **切成片段**：LightRAG 依設定切片，保留重疊文字，減少切斷上下文造成的資訊損失。
5. **計算並儲存向量**：文字片段經 Embedding 模型轉換後，寫入 NanoVectorDB。

目前是**文字 Embedding**：圖片參與搜尋的方式是 OCR 文字或模型圖片描述，不是直接將圖片像素建立成影像向量，也不提供「以圖找圖」。OCR 或圖片描述有誤，會連帶影響後續搜尋；須核對原圖。

### LightRAG、LLM 與 Embedding 各自負責什麼？

| 元件 | 負責的工作 |
|---|---|
| myRAG 整合層 | 文件上傳、解析、OCR、來源對應與操作介面 |
| LightRAG | 協調切片、模型呼叫、索引、圖譜合併及檢索 |
| Embedding 模型 | 把文字、查詢及圖譜相關描述轉成向量 |
| 設定的 LLM | 抽取實體與關係、分析查詢關鍵詞、根據證據生成回答 |
| NanoVectorDB / NetworkX | 分別保存向量與圖譜 |

本機模式下，LightRAG 透過同一個服務的 `POST /local/v1/embeddings` 呼叫 Embedding。這個 OpenAI 相容接口只是本機轉接，內部實際執行 FastEmbed；`EMBEDDING_BINDING=openai` **不表示預設把內容送到 OpenAI**。切到 `embedding.mode=api` 時，才使用指定的 Embedding API。

LLM 是另一組獨立設定。即使 Embedding 在本機，建圖、圖片描述及問答仍可能把相關內容送到你設定的 LLM 端點；「本機 Embedding」不等於所有功能完全離線。

### 啟用圖譜後，多做了哪些處理？

預設 `graph_enabled=false`，只建立文字向量索引。啟用圖譜並重啟後，新匯入的文字片段會由 **LightRAG 主動呼叫 LLM**，要求回傳實體名稱、類型、描述，以及實體之間的關係。LightRAG 再解析、合併並保存結果；LLM 不會自行主動呼叫 LightRAG 建圖。

例如「實驗 E01 使用陶瓷塗層」可能被抽成「實驗 E01」「陶瓷塗層」兩個節點，以及「使用」這條關係。分類由 LLM 依抽取提示詞判斷，不是 Embedding 自動分群；抽取結果仍須核對文件。

LightRAG 在圖譜索引流程中也會建立以下向量：

| 向量內容 | 搜尋用途 |
|---|---|
| 文件文字片段 | 找原文證據 |
| 實體名稱＋描述 | 找相關節點 |
| 關係關鍵詞＋兩端名稱＋描述 | 找相關關係 |

因此圖譜與向量可以合作：向量先找到語意相關的實體或關係，圖譜再提供相鄰資訊與原文來源。既有文件不會因打開開關就自動補建圖譜，需依「模型設定」的流程重新索引。

### 查詢時怎麼使用這些索引？

一般語意搜尋（`naive`）把問題轉成向量，使用餘弦相似度找出接近的文字片段。例如詢問「有哪些方法讓電池不要那麼熱」，有機會找到描述「降低電池溫升」的內容，不要求字面完全相同。相似度不是答案正確率，也不保證能精確區分實驗編號、數字或單位。

「圖譜＋向量」（`mix`）的大致流程是：

1. LightRAG 使用 LLM 抽取問題中的具體實體及主題／關係關鍵詞；已有可用快取時可重用。
2. 使用 Embedding，把問題與相關關鍵詞轉成查詢向量。
3. 結合三路檢索：實體向量搜尋與周邊關係、關係向量搜尋與兩端實體、直接的原文片段向量搜尋。
4. 依圖譜來源找回文字，合併、去重、篩選候選證據，並控制送入 LLM 的內容長度。myRAG 目前未啟用額外 Reranker。
5. 「研究問答」把整理後的證據交給 LLM 生成回答並帶回來源；「只找證據」則回傳檢索結果。

查詢會讀取**已建立的索引**，不會每次重新解析全部文件或重建圖譜。圖譜模式的「只找證據」仍可能為了查詢關鍵詞分析而呼叫 LLM；本機 `naive` 純檢索則不需要 LLM 生成答案。

### 更換模型與重建索引

更換 Embedding 模型後，即使輸出仍是 384 維，也不能直接混用舊向量，因為數字代表的語意座標可能不同。啟動器會檢查 `mode/model/dimension/base_url/max_tokens` 的設定指紋，變更時拒絕混用既有索引；同一 API 名稱背後若換了模型，這個檢查無法自動識別。

換模型、模式或相關設定前，請依「模型設定」備份並重建，不要刪除 `data/embedding-profile.json` 繞過檢查。**本節只是補充文件，未更換模型或修改索引格式；已安裝環境不必因本次 README 更新重新匯入或重啟。**

## 現在與未來企業共用版的架構

建議演進方向是 **Python / FastAPI + LightRAG + MinIO + PostgreSQL（含 pgvector）+ 自訂 LLM API**，共用階段可部署到 K8s。以下「未來建議」尚未實作；目前下載 ZIP 仍只需要 Windows、Python 3.12 與 CPU，不用先申請這些服務。

| 用途 | 現在本機版 | 未來建議 |
|---|---|---|
| UI、REST API、RAG 引擎 | Python、FastAPI、LightRAG | 保留並延伸 |
| 文件原檔、圖片、解析產物 | 本機資料夾 | MinIO / S3 |
| 文件目錄、版本、權限、對話 | 目錄與狀態用 JSON；對話在分頁記憶體；尚無完整版本與權限管理 | PostgreSQL 應用資料表 |
| 向量索引 | NanoVectorDB | PostgreSQL + pgvector（PGVectorStorage） |
| 知識圖譜 | NetworkX | PostgreSQL 一般資料表（PGTableGraphStorage） |
| LightRAG 文字片段、快取、文件狀態 | 本機 JSON | PGKVStorage、PGDocStatusStorage |
| 文件解析、建索引 | 與 API 同一服務內處理 | 獨立背景 worker，初期單一索引寫入者 |
| Embedding | CPU 本機模型，也可設定 API | 先沿用，有合適的 API 再評估切換 |
| LLM | 設定的 OpenAI 相容 API | 自訂 LLM API |
| 部署 | Windows 本機、單一服務程序 | 企業共用階段再上 K8s |

### 為什麼選這些技術？

使用 MinIO 保存原檔與圖片，讓 PostgreSQL 集中處理結構化資料、向量與圖譜，可減少需要維運的產品。LightRAG 已提供上述 PostgreSQL 儲存介面，PGTableGraphStorage 不要求 Neo4j 或 Apache AGE；但本專案仍需完成儲存轉接、資料搬遷與整合驗證，不能只換設定就視為可正式上線。[LightRAG 官方儲存文件](https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md)

PostgreSQL 與 pgvector 的供應及安裝權限仍要確認。目前鎖定的 LightRAG 版本沒有註冊 Oracle 後端；直接選它需要自行維護轉接。若部署政策只允許 Oracle，再確認版本、向量功能及開發成本。詳細取捨與官方來源見 [ARCHITECTURE.md](ARCHITECTURE.md)。

初期不增加 Redis、Elasticsearch、Neo4j 或 Milvus。任務可先以 PostgreSQL 任務表管理；待實際出現吞吐、精確搜尋、複雜圖譜查詢或向量效能瓶頸，再加入相應服務。任務表與 worker 的可靠領取、失敗重試及當機恢復都屬於後續開發，並非目前已有功能。

### 「背景解析與建索引」是 batch job 嗎？

是背景工作，但**不必等每天固定時間跑一批**。建議一般上傳採用「上傳後排入佇列，持續運作的 worker 接著處理」；大量歷史資料匯入或整批重建索引時，才使用批次排程。也不需要每上傳一份文件就啟動一個 Kubernetes Job。

```text
上傳文件 → 保存原檔、建立任務 → UI 顯示等待處理
                              ↓
                    背景 worker 領取任務
                              ↓
             解析文字／表格／圖片，需要時做 OCR
                              ↓
            保留來源位置 → 切分片段 → 計算 Embedding
                              ↓
                       寫入向量索引
                              ↓
            若啟用 GraphRAG：LLM 抽取實體與關係、建圖
                              ↓
                     UI 更新完成或失敗狀態
```

這是未來工作流程示意；不同格式可解析的內容仍受上方「這一版的邊界」限制。解析是把文件轉成可處理的內容；建索引是把這些內容整理成可檢索的片段、向量，以及選配的圖譜。兩者主要發生在匯入、文件更新或重建時。

使用者搜尋時，會將問題轉成查詢向量等檢索條件，讀取**已建立的索引**；不會每次重新解析整份文件。RAG 問答再把檢索證據交給 LLM 生成回答。

目前服務已有背景索引處理，但仍與網站 API 共用同一個 Python 服務，尚未拆成可獨立恢復的任務服務。未來拆開的目的，是讓耗時工作可以獨立重試、控制併發與擴充；「背景執行」不代表自動獲得當機恢復能力，這部分需要持久化任務與去重機制。

### 建議落地順序

1. **本機品質驗證**：先用具代表性的實際文件確認搜尋命中、表格與圖片解析、引用位置及 LLM 用量。
2. **小範圍共用**：接 MinIO、PostgreSQL、背景任務與身分驗證／文件權限；補上備份還原、刪除傳播及稽核。權限需涵蓋檢索、圖譜、原檔、圖片與快取。
3. **依負載擴充**：觀察分片數、圖譜規模、同時查詢人數、索引等待時間和查詢延遲，再決定增加 worker 或專用服務。不能只用「一萬份文件」決定架構。

換儲存後端需規劃搬遷與重建；換 Embedding 模型需重建向量。未來 K8s 若使用 Linux，須另外準備部署環境核准的 Linux 套件與 image，不能直接使用目前 Windows wheelhouse。完整規劃見 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 手動安裝與離線資源準備

需要 **Windows x64、Python 3.12 x64**。驗證版本為 Python 3.12.14。獨立 `.venv` 不修改全域套件。

有可用的套件來源時，在專案目錄執行：

```powershell
.\Setup.ps1
.\Prepare.ps1
.\Start.ps1
```

若 Python 不在 `py` launcher 裡：

```powershell
.\Setup.ps1 -Python '<Python312安裝目錄>\python.exe'
```

`Prepare.ps1` 是明確的連外準備階段，下載本機 Embedding 與 tokenizer；啟動階段使用本地模型，不臨時下載。OCR 模型包含於套件 wheel 中。企業 CA 可設定 `config.json` 的 `ca_bundle`，不關閉 TLS 驗證。

完整 Git 儲存庫已包含 `offline/` 資源分片；上述 Bootstrap.cmd 即可離線安裝。以下是維護者重新準備資源的替代流程：

```powershell
.\Prepare-Offline.ps1
```

離線安裝需準備以下項目：程式碼、`requirements-win-py312.lock`、`wheelhouse/`、`models/`、`.cache/tiktoken/`，以及 Python 3.12 x64 安裝資源。在目標環境執行：

```powershell
.\Setup.ps1 -Offline -Python '<Python312安裝目錄>\python.exe'
.\Start.ps1
```

不要複製 `.venv` 當作可攜環境，也不要把含憑證的 `config.json` 或使用者資料提交 GitHub。Nexus 可透過標準 pip 設定指定，套件來源的認證資訊不要寫在專案裡。

`dist/myRAG-source.zip` 現在包含程式碼與 `offline/` 分片，可解壓後直接使用 Bootstrap.cmd。`dist/myRAG-offline-resources.zip` 是同一批套件與模型的獨立資源包，供替代安裝流程使用，不必兩包都下載。`dist/manifest.json` 提供 SHA-256。這些包不含密鑰、使用者文件或 Python 安裝程式。可執行 `python tools/package.py` 重新打包；更新離線資源後，再執行 `python tools/split_resources.py` 更新 Git 分片。

## 模型設定

在 UI「模型設定」填入 **OpenAI 相容 Base URL、API key、model name**，儲存後重啟。網址要填供應商提供的 API base（通常以 `/v1` 結尾），不是 `/chat/completions` 完整路徑。金鑰只保存在本機 `config.json`，不回傳到瀏覽器，檔案已被 Git 忽略。

預設 `graph_enabled=false`，文件只建向量。打開圖譜後，新匯入文件才會呼叫 LLM 抽取關係。既有文件不會自動補建圖譜：先在文件清單移除該文件索引，再重新匯入。圖譜關係是模型抽取結果，不是已證實的因果。

Gemini 低額度保護：當 LLM 網址是 `generativelanguage.googleapis.com`，自動經由同一 Python 服務內的節流轉接，每分鐘最多約 4 次請求、同時 1 次。429／503 會使下一次請求至少延後 65 秒，再由上游重試機制重試。其他網址預設不啟用這項供應商專屬保護；可在 config.json 設定 `llm_requests_per_minute`（正整數，0 關閉）後重啟。此保護無法預知其他程式共用同一 Google 專案的用量，也不能解決每日額度用盡。啟用時串流回覆會先緩衝完整回應。

若建圖遇到 API 限流失敗，原檔仍在，不必重新上傳。待額度恢復後可呼叫 `POST /documents/reprocess_failed`；它會重試所有失敗／待處理文件並保留追蹤 ID。建圖會比單純向量索引慢，建議先測一份小文件。

若供應商回報 `PerDay` 每日額度耗盡，節流轉接會在本次服務執行期間記住該錯誤，不再反覆向外送出 LLM 請求。待供應商額度恢復後需重啟服務再重試。向量搜尋不受此限制。

Groq 免費額度保護：`api.groq.com` 預設每分鐘 1 次、同時 1 次請求。原因是建圖提示詞較長，實測單次約需 6,000 tokens，而帳號限制為每分鐘 8,000 tokens；只限制請求次數為每分鐘 30 次並不足夠。此保守節流不是精確 token 配額管理，單次超過可用 token 上限、每日用量或其他程式共用額度仍可能失敗。

Groq 的 `openai/gpt-oss-*` 模型若未指定相關參數，轉接預設 `reasoning_effort=low`、`max_completion_tokens=4096`，避免預設推理耗盡輸出額度卻沒有產生抽取文字；可用 config.json 的 `groq_reasoning_effort` 與 `groq_max_completion_tokens` 調整。

使用外部 Embedding API 時，修改 `config.json` 的 `embedding`：

```json
{
  "mode": "api",
  "base_url": "https://embedding.example.com/v1",
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

此版只綁定 `127.0.0.1`，供本機瀏覽器與 Agent 使用。沒有實作企業使用者權限，不應直接改成開放為多人共用服務。可用專案內的 `tools/doctor.py` 檢查環境。

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

smoke 會匯入一份明確標示的可丟棄測試文件，確認可搜尋後移除其索引；原檔仍保留。LLM 問答、自訂 API、實際研究效果與 GraphRAG 品質未由這些測試證明。

## 上游與延伸範圍

- LightRAG：https://github.com/HKUDS/LightRAG ，版本 1.5.7；檢查用原始碼 commit `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`。
- 執行時安裝相同版本的 PyPI wheel（含上游 UI），不需 Node/Bun。
- FastEmbed：https://github.com/qdrant/fastembed ，版本 0.8.0。
- RapidOCR：https://github.com/RapidAI/RapidOCR ，使用 `rapidocr-onnxruntime==1.4.4`。
- 自有程式位於 `demo/`、`web/`、`tools/` 與啟動腳本；未修改上游核心。`vendor/LightRAG` 僅供原始碼檢視，不是執行依賴。

部署時須遵循適用的套件、模型與授權審查，以及環境安全政策。
