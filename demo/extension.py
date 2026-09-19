import asyncio
import base64
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
from urllib.parse import urlparse
import uuid
from typing import Literal

import httpx
from fastapi import File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .parser import SUPPORTED, parse_document, enrich_ocr


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class Search(BaseModel):
    query: str = Field(min_length=2, max_length=5000)
    limit: int = Field(default=6, ge=1, le=30)
    mode: str = "naive"
    conversation_history: list[ConversationMessage] = Field(default_factory=list, max_length=6)


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str
    encoding_format: str = "float"


def install(app, cfg, root: Path):
    sources = root / "data/sources"
    model_lock = threading.Lock()
    ingest_lock = asyncio.Lock()
    model = None
    llm_ready = bool(cfg["llm"].get("base_url") and cfg["llm"].get("model"))
    origin = f"http://127.0.0.1:{cfg['port']}"
    allowed_origins = {origin, f"http://localhost:{cfg['port']}"}
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

    @app.middleware("http")
    async def check_origin(request: Request, call_next):
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            supplied = request.headers.get("origin")
            if supplied and supplied not in allowed_origins:
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Cross-origin writes are not allowed"}, status_code=403)
        return await call_next(request)

    async def upstream(method, path, **kwargs):
        async with httpx.AsyncClient(base_url=origin, timeout=180, trust_env=False) as client:
            response = await client.request(method, path, **kwargs)
        if response.is_error:
            raise HTTPException(502, f"LightRAG returned HTTP {response.status_code}. See logs; no credentials are displayed.")
        return response.json()

    def get_meta(doc_id):
        if not re.fullmatch(r"[0-9a-f]{32}", doc_id):
            raise HTTPException(404, "Unknown source")
        path = sources / doc_id / "metadata.json"
        if not path.exists():
            raise HTTPException(404, "Unknown source")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_meta(meta):
        path = sources / meta["id"] / "metadata.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    async def tracked_docs(meta):
        docs = []
        for track in meta.get("tracks", []):
            if track:
                result = await upstream("GET", f"/documents/track_status/{track}")
                docs.extend(result.get("documents", []))
        return docs

    def encode(texts):
        nonlocal model
        with model_lock:
            from fastembed import TextEmbedding
            if model is None:
                model = TextEmbedding(model_name=cfg["embedding"]["model"], cache_dir=str(root / "models"),
                                      threads=cfg["cpu_threads"], local_files_only=True)
            return [v.tolist() for v in model.embed(texts, batch_size=8)]

    @app.post("/local/v1/embeddings")
    async def embeddings(body: EmbeddingRequest):
        if cfg["embedding"]["mode"] != "local":
            raise HTTPException(409, "Local embedding is disabled")
        if body.model != cfg["embedding"]["model"]:
            raise HTTPException(400, "Embedding model mismatch")
        texts = [body.input] if isinstance(body.input, str) else body.input
        if not texts or len(texts) > 64 or any(not isinstance(t, str) or len(t) > 20000 for t in texts):
            raise HTTPException(400, "Expected 1–64 text inputs of at most 20000 characters")
        vectors = await run_in_threadpool(encode, texts)
        if body.encoding_format == "base64":
            import numpy as np
            vectors = [base64.b64encode(np.asarray(v, dtype="<f4").tobytes()).decode() for v in vectors]
        elif body.encoding_format != "float":
            raise HTTPException(400, "Unsupported encoding_format")
        return {"object": "list", "model": body.model,
                "data": [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vectors)],
                "usage": {"prompt_tokens": 0, "total_tokens": 0}}

    @app.get("/demo/status")
    async def status():
        return {"base": "LightRAG 1.5.7", "llm_ready": llm_ready, "graph_enabled": cfg["graph_enabled"],
                "embedding_mode": cfg["embedding"]["mode"], "embedding_model": cfg["embedding"]["model"],
                "ocr_enabled": cfg.get("ocr_enabled", True),
                "source_count": len(list(sources.glob("*/metadata.json"))), "storage": "local-files-demo",
                "notice": "Single-process local demo. Fine-grained permissions and production scale are not validated."}

    @app.get("/demo/settings")
    async def settings():
        disk = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
        return {"base_url": disk["llm"]["base_url"], "model": disk["llm"]["model"],
                "has_api_key": bool(disk["llm"]["api_key"]), "graph_enabled": disk["graph_enabled"]}

    @app.post("/demo/settings")
    async def save_settings(request: Request):
        if "application/json" not in request.headers.get("content-type", ""):
            raise HTTPException(415, "JSON required")
        body = await request.json()
        url = str(body.get("base_url", "")).strip().rstrip("/")
        parts = urlparse(url)
        if url and (parts.scheme not in ("http", "https") or not parts.netloc or parts.username or parts.password):
            raise HTTPException(400, "Use an HTTP(S) base URL without embedded credentials")
        disk = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
        disk["llm"]["base_url"] = url
        disk["llm"]["model"] = str(body.get("model", "")).strip()
        if body.get("api_key"):
            disk["llm"]["api_key"] = str(body["api_key"])
        disk["graph_enabled"] = bool(body.get("graph_enabled", False))
        if disk["graph_enabled"] and not (url and disk["llm"]["model"]):
            raise HTTPException(400, "Graph indexing requires LLM URL and model")
        temp = root / "config.json.tmp"
        temp.write_text(json.dumps(disk, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(root / "config.json")
        return {"message": "已儲存。請停止再啟動；既有文件不會自動重新建圖。金鑰僅保存在本機 config.json。"}

    def enrich(result):
        data = result.get("data", {})
        for chunk in [*data.get("chunks", []), *(result.get("references") or [])]:
            match = re.search(r"myrag_([0-9a-f]{32})_p(\d+)", chunk.get("file_path", ""))
            if match:
                try:
                    meta = get_meta(match[1])
                    page_number = int(match[2])
                    page = meta["pages"][page_number - 1]
                    chunk["source"] = {"id": match[1], "name": meta["name"], "location": page["location"],
                        "page": page_number, "url": f"/demo/source.html?id={match[1]}&page={page_number}",
                        "images": [f"/demo/assets/{match[1]}/{name}" for name in page["images"]]}
                except (HTTPException, IndexError, KeyError):
                    pass
        return result

    @app.post("/demo/search")
    async def search(body: Search):
        if body.mode not in ("naive", "mix", "local", "global", "hybrid"):
            raise HTTPException(400, "Unknown retrieval mode")
        if body.mode != "naive" and not (llm_ready and cfg["graph_enabled"]):
            raise HTTPException(409, "Graph retrieval requires a configured LLM and indexed graph")
        result = await upstream("POST", "/query/data", json={"query": body.query, "mode": body.mode,
                                 "chunk_top_k": body.limit, "top_k": body.limit, "enable_rerank": False})
        return enrich(result)

    @app.post("/demo/ask")
    async def ask(body: Search):
        if not llm_ready:
            raise HTTPException(409, "尚未設定 LLM。請先使用搜尋，或設定模型後重啟。")
        if body.mode not in ("naive", "mix", "local", "global", "hybrid"):
            raise HTTPException(400, "Unknown retrieval mode")
        if body.mode != "naive" and not cfg["graph_enabled"]:
            raise HTTPException(409, "Enable graph indexing and reimport documents before graph retrieval")
        result = await upstream("POST", "/query", json={"query": body.query, "mode": body.mode,
                                 "chunk_top_k": body.limit, "enable_rerank": False,
                                 "include_references": True, "include_chunk_content": True,
                                 "conversation_history": [message.model_dump() for message in body.conversation_history],
                                 "user_prompt": "請用繁體中文。每個研究結論附來源，區分實驗證據、推論及資料缺口。勿把不同條件的結果當成公平比較。"})
        return enrich(result)

    @app.get("/demo/sources")
    async def list_sources():
        items = []
        for path in sources.glob("*/metadata.json"):
            meta = json.loads(path.read_text(encoding="utf-8"))
            summary = {k: meta.get(k) for k in ("id", "name", "created_at", "state", "warnings", "tracks")}
            if meta["state"] in ("queued", "partial-failure"):
                try:
                    docs = await tracked_docs(meta)
                    states = [d["status"] for d in docs]
                    if states and all(s == "processed" for s in states):
                        summary["state"] = "processed"
                    elif "failed" in states:
                        summary["state"] = "failed"
                        error_text = ' '.join(str(d.get('error_msg', '')) for d in docs if d.get('status') == 'failed')
                        if all(d.get('status') == 'failed' and 'Identical content already exists' in str(d.get('error_msg', '')) for d in docs):
                            summary['state'] = 'duplicate-content'
                            summary['warnings'] = [*(summary.get('warnings') or []), '內容與另一筆文件相同，未另建索引；請查看原始那筆文件的處理狀態。']
                        elif any(s in error_text for s in ('429', 'RateLimitError', 'RESOURCE_EXHAUSTED')):
                            summary['warnings'] = [*(summary.get('warnings') or []), 'LLM 請求額度或頻率受限，原檔仍保留；請等候額度恢復後重試建索引。']
                        elif any(s in error_text for s in ('503', 'UNAVAILABLE')):
                            summary['warnings'] = [*(summary.get('warnings') or []), 'LLM 服務暫時忙碌，原檔仍保留；請稍後重試建索引。']
                    elif states:
                        summary["state"] = "processing"
                    else:
                        summary["state"] = "index-missing"
                except HTTPException:
                    summary["state"] = "status-unavailable"
            items.append(summary)
        return sorted(items, key=lambda x: x["created_at"], reverse=True)

    @app.delete("/demo/sources/{doc_id}/index")
    async def remove_index(doc_id: str):
        async with ingest_lock:
            meta = get_meta(doc_id)
            docs = await tracked_docs(meta)
            ids = list({d["id"] for d in docs})
            if ids:
                response = await upstream("DELETE", "/documents/delete_document", json={"doc_ids": ids, "delete_file": True, "delete_llm_cache": True})
                if response.get("status") != "deletion_started":
                    raise HTTPException(409, "文件處理中，請完成後重試移除。")
                for _ in range(120):
                    remaining = await tracked_docs(meta)
                    if not remaining:
                        break
                    await asyncio.sleep(.5)
                else:
                    raise HTTPException(409, "移除尚未完成，請查看 LightRAG 管理介面；未標記完成。")
            meta["state"] = "index-removed"
            save_meta(meta)
            return {"state": "index-removed", "message": "索引已移除；原始文件與圖片仍保存在本機，可下載後重新匯入。"}

    @app.get("/demo/sources/{doc_id}")
    async def source(doc_id: str):
        return get_meta(doc_id)

    @app.get("/demo/download/{doc_id}")
    async def download(doc_id: str):
        meta = get_meta(doc_id)
        return FileResponse(sources / doc_id / meta["stored_name"], filename=meta["name"], media_type="application/octet-stream")

    @app.get("/demo/assets/{doc_id}/{filename}")
    async def asset(doc_id: str, filename: str):
        meta = get_meta(doc_id)
        if filename not in {x for p in meta["pages"] for x in p["images"]}:
            raise HTTPException(404, "Unknown image")
        return FileResponse(sources / doc_id / filename, media_type="image/png")

    @app.post("/demo/upload")
    async def upload(file: UploadFile = File(...)):
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in SUPPORTED:
            raise HTTPException(400, "Supported: TXT, MD, PDF, DOCX, PPTX, XLSX, PNG, JPG. Legacy Office files must be converted first.")
        raw = await file.read(30 * 1024 * 1024 + 1)
        if len(raw) > 30 * 1024 * 1024:
            raise HTTPException(413, "Demo upload limit is 30 MB")
        async with ingest_lock:
            digest = hashlib.sha256(raw).hexdigest()
            for existing in sources.glob("*/metadata.json"):
                old = json.loads(existing.read_text(encoding="utf-8"))
                if old.get("sha256") == digest and old.get("state") == "queued":
                    docs = await tracked_docs(old)
                    if docs and all(d["status"] != "failed" for d in docs):
                        return {"id": old["id"], "name": old["name"], "state": "already-imported", "tracks": old["tracks"], "warnings": ["相同內容已匯入，未重複建立索引。"]}
                    if docs and any(d['status'] == 'failed' for d in docs):
                        raise HTTPException(409, '相同內容已有失敗紀錄，請重試原紀錄，或先移除原紀錄的索引再匯入；不需要重複上傳。')
            doc_id = uuid.uuid4().hex
            folder = sources / doc_id
            folder.mkdir()
            path = folder / ("original" + suffix)
            path.write_bytes(raw)
            try:
                pages = await run_in_threadpool(parse_document, path, folder)
            except Exception as exc:
                raise HTTPException(422, f"Parsing failed ({type(exc).__name__}). File may be encrypted, damaged, or unsupported.") from exc
            warnings = []
            if cfg.get("ocr_enabled", True) and any(p["images"] for p in pages):
                warnings.extend(await run_in_threadpool(enrich_ocr, pages, folder))
            if suffix == ".xlsx":
                warnings.append("Excel 本版讀取儲存格與公式文字；不執行公式、不解析工作表內嵌圖片。")
            if suffix == ".docx":
                warnings.append("Word 本版定位到全文，未還原頁碼及圖文順序。")
            if suffix == ".pptx":
                warnings.append("投影片提供文字／圖片內容檢視，未還原完整投影片排版；不讀講者備註。")
            # Optional real VLM call only after user configures a company endpoint.
            if llm_ready:
                from openai import AsyncOpenAI
                from .llm_gateway import requests_per_minute
                llm_url = origin + '/local/llm' if requests_per_minute(cfg) else cfg['llm']['base_url']
                client = AsyncOpenAI(base_url=llm_url, api_key=cfg["llm"].get("api_key") or "unused", timeout=240, max_retries=1)
                try:
                    for page in pages:
                        for filename in page["images"][:3]:
                            image_b64 = base64.b64encode((folder / filename).read_bytes()).decode()
                            try:
                                response = await client.chat.completions.create(model=cfg["llm"]["model"], messages=[{"role": "user", "content": [
                                    {"type": "text", "text": "描述研究圖表中的文字、座標、單位、條件及趨勢。看不清楚就說看不清楚，不猜測精確數字。"},
                                    {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_b64}}]}])
                                page["text"] += "\n[模型圖像描述，須核對原圖]\n" + (response.choices[0].message.content or "")
                            except Exception:
                                warnings.append(f"{page['location']} 的圖像理解失敗；已保留原圖，未將其當成已讀懂內容。")
                        if len(page["images"]) > 3:
                            warnings.append(f"{page['location']} 本版只分析前 3 張圖，其餘仍保留。")
                finally:
                    await client.close()
            elif any(p["images"] for p in pages):
                warnings.append("尚未設定視覺 LLM：圖片可 OCR 與保存，但不做圖表語意理解。")
            empty = sum(not p["text"].strip() for p in pages)
            if empty:
                warnings.append(f"有 {empty} 個頁面／區段無可索引文字；可能是 OCR 未辨識、空白或不支援的版面。")
            meta = {"id": doc_id, "sha256": digest, "name": Path(file.filename or "document").name, "stored_name": path.name,
                    "created_at": datetime.now(timezone.utc).isoformat(), "pages": pages,
                    "state": "parsing", "tracks": [], "warnings": warnings}
            save_meta(meta)
            try:
                for number, page in enumerate(pages, 1):
                    if not page["text"].strip():
                        continue
                    hint = "[legacy-R]" if cfg["graph_enabled"] else "[legacy-R!]"
                    filename = f"myrag_{doc_id}_p{number:04d}.{hint}.txt"
                    text = f"文件：{meta['name']}\n來源位置：{page['location']}\n\n{page['text']}"
                    result = await upstream("POST", "/documents/upload", files={"file": (filename, text.encode("utf-8"), "text/plain")})
                    meta["tracks"].append(result.get("track_id"))
                meta["state"] = "queued" if meta["tracks"] else "no-indexable-text"
            except Exception:
                meta["state"] = "partial-failure"
                raise
            finally:
                save_meta(meta)
            return {k: meta[k] for k in ("id", "name", "state", "tracks", "warnings")}

    app.mount("/demo", StaticFiles(directory=root / "web", html=True), name="demo-ui")
