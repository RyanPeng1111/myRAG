# myRAG 架構與共用服務演進建議

更新日期：2026-09-19。本文件區分目前已實作功能與後續建議；企業服務尚未接通。下載 main ZIP 仍可在 Windows、Python 3.12、CPU 上使用，不需要新增資料庫。

## 目前本機版

瀏覽器的研究工作區與 LightRAG 管理介面，呼叫同一個 Python FastAPI 服務。底層使用 LightRAG 1.5.7；Office/PDF 解析、CPU OCR、CPU Embedding 都在本機執行。LLM 則呼叫設定中的 OpenAI 相容 API。

| 項目 | 目前實作 |
|---|---|
| UI | 靜態 HTML/CSS/JavaScript，不需 Node.js 建置或 CDN |
| 後端 | Python、FastAPI、LightRAG，單一服務程序 |
| 原始文件及衍生圖片 | `data/sources/`；索引輸入位於 `data/inputs/` |
| 文件狀態、文字片段、快取 | `data/index/` 下的 JSON 檔案 |
| 向量 | NanoVectorDB，本機檔案 |
| 圖譜 | NetworkX，本機檔案 |
| Embedding | FastEmbed / ONNX Runtime，CPU、多語模型、384 維；也可設定自訂 API |
| OCR | RapidOCR，CPU |
| 對話 | 本次瀏覽器分頁記憶體，重新整理後清除 |
| 設定 | 本機 `config.json`，不納入 Git 或公開 ZIP |

現在的啟動器固定使用上述本機儲存，來源 API 也直接讀取檔案。不能只更改幾個環境變數就宣稱已完成企業部署，更不能把這份本機資料目錄交給多個副本同時寫入。現階段未驗證一萬份文件的容量或多人服務。

## 技術首選：保留應用，加上 MinIO 與 PostgreSQL

建議保留 **Python / FastAPI / LightRAG**，使用 **S3 / MinIO**，新增一套 **PostgreSQL + pgvector**。企業共用階段再部署到 K8s。這是未來演進方案，不是執行本機 demo 的前置要求。

| 層次 | 建議 | 原因及必要工作 |
|---|---|---|
| 原檔、圖片、解析產物 | MinIO / S3 | 大型檔案放物件儲存；新增儲存轉接層，保留文件 ID、版本、頁碼及來源映射 |
| 文件目錄、版本、權限、對話、任務 | PostgreSQL 的應用資料表 | 從散落檔案移到可查詢、備份、有交易的資料；需設計 schema 與遷移工具 |
| LightRAG KV 與文件狀態 | PGKVStorage、PGDocStatusStorage | 使用上游已有介面；與應用資料表明確區分 |
| 向量 | PGVectorStorage / pgvector | 與關聯資料同一套資料庫，減少要維運的產品 |
| 圖譜 | PGTableGraphStorage | 用一般 PostgreSQL 資料表保存圖譜，初期不要求 Neo4j 或 Apache AGE |
| 文件解析與建索引 | 獨立背景 worker，初期單一索引寫入者 | 網頁不必等待長時間解析；新增持久化任務、失敗重試、去重、取消及當機恢復 |
| API / UI | 保留 FastAPI 與現有工作區 | 現有純檢索及 RAG API 可延續，補上身分驗證、配額、稽核及相容性驗證 |
| 模型 | 自訂 LLM API；CPU Embedding 起步 | 有外部 Embedding API 再評估切換；無 GPU 不阻礙第一階段驗證 |
| 部署 | K8s、受控的映像儲存庫及監控 | 先以小規模共用服務起步，再依測量結果增加副本 |

LightRAG 上游文件列出 PostgreSQL 的四類儲存介面；PGTableGraphStorage 不需 AGE。這些介面也出現在本專案鎖定版本的儲存註冊表中，但本專案尚未實測 PostgreSQL 整合。實作時須選定部署環境允許、上游支援的 PostgreSQL 版本，建立獨立整合測試，不能用上游支援取代本專案驗收。[LightRAG API Server 文件](https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md)

pgvector 是 PostgreSQL 擴充套件，需要資料庫環境允許安裝；不是一般 SQL 帳號就一定能自行啟用。這是未來要向平台團隊確認的少數必要前置之一。[pgvector 官方文件](https://github.com/pgvector/pgvector)

## 為什麼沒有直接選 Oracle？

目前鎖定的 LightRAG 1.5.7 儲存註冊表沒有 Oracle 後端。選 Oracle 作為整個 RAG 儲存層，需要自行維護轉接、查詢語意與版本相容性，開發成本通常比沿用上游介面高。

Oracle 新版具有 AI Vector Search，但部署環境的版本、可用功能及權限需個別確認，不能假設既有 Oracle 就能直接接上。[Oracle AI Vector Search 官方說明](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/overview-ai-vector-search.html)

因此：若部署環境可提供 PostgreSQL，優先用它整合 RAG 儲存；若部署政策只允許 Oracle，再確認版本並評估轉接成本，不急著改寫引擎。只有確實需要整合既有業務資料時，才讓 Oracle 同時參與，避免不必要的多資料庫維運。PostgreSQL 是否容易取得，仍是選型前需要確認的條件。

## 暫時不增加的服務

- **Redis / RabbitMQ / Kafka**：第一個共用版本可用 PostgreSQL 任務表與 worker 管理工作。這部分目前沒有實作，必須補上任務領取、租約、重試與冪等處理；吞吐或跨服務需求出現後再評估獨立佇列。
- **Elasticsearch**：先測實驗編號、材料型號、中英文專有名詞及單位的搜尋品質。如果需要更成熟的詞彙搜尋、中文斷詞與複雜篩選，再評估；向量搜尋不能保證這類精確匹配。
- **Neo4j**：只有當圖譜查詢、複雜路徑分析或圖譜管理需求超出現有介面時再引入。GraphRAG 不等於必須有獨立圖譜資料庫。
- **Qdrant / Milvus**：向量數量、查詢延遲或負載隔離確實需要專用服務時再評估，不因為文件達到一萬份就直接增加。

## 分階段落地

### 1. 現在：真實文件品質驗證

保留 Windows 本機架構，先驗證研究報告、PPT、表格和圖片。建立一組由 RD 確認答案與來源的問題，涵蓋實驗尋找、比較、新人問答、影響分析與靈感探索。記錄搜尋命中、引用位置、解析缺漏、回答時間及 LLM 用量。不要只看知識圖譜是否漂亮。

### 2. 小範圍共用：先處理資料與身分

接 MinIO、PostgreSQL、背景工作與組織身分系統。雖然 demo 延後權限，正式分享給多人前仍應落實文件及知識庫存取控制：檢索候選、圖譜關係、原檔、圖片、下載與快取都要一致限制，不能只在生成回答後遮字。LightRAG workspace 也不能直接當作完整的企業 ACL。

初期以單一索引寫入 worker 降低併發風險。API 增加副本前，要移除本機鎖與共享檔案假設，確認各儲存介面、快取和索引更新的跨程序行為。補上版本化資料庫遷移、備份及實際還原演練、文件刪除傳播、密鑰管理、稽核與錯誤監控。

### 3. 成長後：用數據決定加什麼

觀察分片數、向量數、圖譜節點與邊數、同時查詢人數、索引等待時間、P95 延遲、LLM 限流與成本。文件數本身不是容量模型。依瓶頸增加 worker、Embedding 服務、重排序或專用搜尋服務，並以同一組研究問題比較品質。

實驗比較與 impact 分析需要穩定的實驗／材料／條件／結果欄位、單位、版本與實體消歧。LLM 抽出的關係只能當候選證據；關聯不代表因果，換圖譜資料庫也不會自動解決研究可信度問題。

## 從本機版搬遷的注意事項

1. 停止寫入，備份 config、原檔、解析產物及完整索引，保留可回復的舊版。
2. 建立來源儲存與中繼資料介面，再搬到 MinIO 與 PostgreSQL，保留文件 ID、版本與來源位置，驗證每個引用都能打開正確內容。
3. 在新的資料庫／workspace 中重建索引並驗證。不要把更換 storage class 當成自動遷移；上游並未提供任意儲存後端之間的完整自動搬遷。
4. 換 Embedding 模型或維度須重建向量，保存模型版本與索引設定，禁止混用。原始文件是可重建的基礎，索引不是唯一資料備份。
5. 新舊版本用相同問題比對檢索、引用、刪除與權限後再切流量，保留回復程序。
6. K8s 常用 Linux 容器；目前的 Windows x64 離線 wheelhouse 不能直接搬進 Linux。未來以核准的基底、受控套件來源與模型建立 image，再經映像儲存庫及掃描流程發布；不要求現在的本機 demo 改用 Docker 或 WSL。

資料搬遷限制與上游儲存配置參考：[LightRAG 儲存文件](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)。以上連結指向上游現行文件，實作仍以本專案鎖定版本及目標環境驗證結果為準。
