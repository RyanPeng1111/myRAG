# Demo 驗證記錄

驗證日期：2026-09-19。環境：Windows x64、Python 3.12.14、CPU，路徑 `D:\proj\myRAG`。

## 已實測

- 原生啟動 LightRAG 1.5.7、上游 WebUI、研究搜尋 UI 與 REST API。
- 重啟後從磁碟載入索引，仍可搜尋中文研究範例；重複啟動同一資料夾會拒絕。
- `tests/test_parser.py` 的 5 項測試通過，涵蓋 PPTX、DOCX、XLSX、圖片與掃描式 PDF OCR。
- 另外 2 項 API 轉接契約測試通過（共 7 項單元／契約測試）：回答引用對應原圖，以及未啟用圖譜時拒絕圖譜查詢。這 2 項使用明確的上游回應 fixture，沒有呼叫或評估真實 LLM。
- `tools/smoke.py` 的 17 項 HTTP 整合檢查通過，涵蓋真實向量檢索、中文切塊完整性、圖片來源、原檔下载、缺少 LLM 時明確拒絕回答、跨來源寫入拒絕、無效來源 ID、密鑰不回傳、重複內容去重，以及上傳／查詢／移除索引生命週期。
- `pip check` 通過。
- 使用全新的 `.offline-test` 虛擬環境，以 `pip install --no-index --find-links wheelhouse -r requirements-win-py312.lock` 安裝成功；該環境的 `pip check` 通過。
- 在網路 socket 連線被測試程式拒絕時，該乾淨環境仍成功執行 384 維 CPU Embedding、tokenizer、上游匯入及 CPU OCR。
- 瀏覽器人工檢查研究搜尋、來源圖表預覽、文件清單與已建立索引狀態。
- 合成掃描 PDF 與 PNG 已匯入並建立索引；範例均非真實研究資料。
- `Stop.cmd` 使用的正常關閉入口已測試，伺服器記錄顯示 12 個儲存介面完成關閉；之後可重新啟動。

## 仍需在公司驗證

尚無公司 LLM 或 Embedding API 憑證，因此沒有測試真實公司 API 的認證、TLS、回答品質、圖片理解或 GraphRAG 抽取品質。現在可直接展示向量搜尋、文件與圖片來源；接上 LLM 後才有生成回答與知識圖譜。不能將此記錄當成一萬份文件的效能或正式環境驗收。

离線測試證明目前 Windows/Python 版本的本地依賴足夠，沒有保證公司的套件掃描政策、CPU 指令集或 Python 安裝環境相同。Python 3.12 x64 安裝資源需由公司核准；壓縮包不包含 Python 安裝程式。

重新驗證的命令見 README。整合測試會留下已移除索引的合成測試原檔，方便確認來源保留行為。
