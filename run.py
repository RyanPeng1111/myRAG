"""Native Windows entry point. Uses the upstream LightRAG server and UI."""
import json
import os
from pathlib import Path
import sys
import secrets

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)


def configure():
    config_path = ROOT / "config.json"
    if not config_path.exists():
        config_path.write_bytes((ROOT / "config.example.json").read_bytes())
    cfg = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not 1024 <= int(cfg["port"]) <= 65535:
        raise ValueError("port must be between 1024 and 65535")
    for folder in ("data/inputs", "data/index", "data/sources", "models", "logs", ".cache/tiktoken", ".cache/huggingface"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    emb = cfg["embedding"]
    if emb["mode"] not in ("local", "api"):
        raise ValueError("embedding.mode must be local or api")
    fingerprint = {k: emb.get(k) for k in ("mode", "model", "dimension", "base_url", "max_tokens")}
    fingerprint_path = ROOT / "data/embedding-profile.json"
    if fingerprint_path.exists() and json.loads(fingerprint_path.read_text()) != fingerprint:
        raise RuntimeError("Embedding profile changed. Back up data and choose a new data directory/rebuild the index; never mix vector spaces. See README.md.")
    if emb["mode"] == "api" and not emb.get("base_url"):
        raise ValueError("API embedding requires base_url")
    if cfg["graph_enabled"] and not cfg["llm"].get("base_url"):
        raise ValueError("Graph indexing requires a configured LLM")
    token_path = ROOT / "data/local-token-secret.txt"
    if not token_path.exists():
        token_path.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    env = {
        "HOST": "127.0.0.1", "PORT": str(cfg["port"]), "WORKERS": "1",
        "TOKEN_SECRET": token_path.read_text(encoding="utf-8"),
        "WORKING_DIR": str(ROOT / "data/index"), "INPUT_DIR": str(ROOT / "data/inputs"),
        "LOG_DIR": str(ROOT / "logs"), "TIKTOKEN_CACHE_DIR": str(ROOT / ".cache/tiktoken"),
        "HF_HOME": str(ROOT / ".cache/huggingface"), "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false",
        "LLM_BINDING": "openai", "LLM_BINDING_HOST": cfg["llm"].get("base_url") or "http://127.0.0.1:9/v1",
        "LLM_BINDING_API_KEY": cfg["llm"].get("api_key") or "not-configured",
        "LLM_MODEL": cfg["llm"].get("model") or "not-configured",
        "EMBEDDING_BINDING": "openai", "EMBEDDING_MODEL": emb["model"],
        "EMBEDDING_BINDING_HOST": f"http://127.0.0.1:{cfg['port']}/local/v1" if emb["mode"] == "local" else emb["base_url"],
        "EMBEDDING_BINDING_API_KEY": emb.get("api_key") or "local-only",
        "EMBEDDING_DIM": str(emb["dimension"]), "EMBEDDING_TOKEN_LIMIT": str(emb["max_tokens"]),
        "EMBEDDING_USE_BASE64": "false", "EMBEDDING_SEND_DIM": "false",
        "EMBEDDING_FUNC_MAX_ASYNC": "1", "EMBEDDING_BATCH_NUM": "8", "EMBEDDING_TIMEOUT": "180",
        "CHUNK_SIZE": "200", "CHUNK_OVERLAP_SIZE": "25", "MAX_PARALLEL_INSERT": "1", "MAX_ASYNC_LLM": "2",
        "LIGHTRAG_KV_STORAGE": "JsonKVStorage", "LIGHTRAG_VECTOR_STORAGE": "NanoVectorDBStorage",
        "LIGHTRAG_GRAPH_STORAGE": "NetworkXStorage", "LIGHTRAG_DOC_STATUS_STORAGE": "JsonDocStatusStorage",
        "LIGHTRAG_PARSER": "*:legacy-R" + ("" if cfg["graph_enabled"] else "!"),
        "RERANK_BINDING": "null", "COSINE_THRESHOLD": "0.1", "SUMMARY_LANGUAGE": "Traditional Chinese",
        "CORS_ORIGINS": f"http://127.0.0.1:{cfg['port']},http://localhost:{cfg['port']}",
        "WEBUI_TITLE": "myRAG · LightRAG", "DOCX_SMART_HEADING": "false",
    }
    if cfg.get("ca_bundle"):
        ca = Path(cfg["ca_bundle"]).resolve(strict=True)
        env.update(SSL_CERT_FILE=str(ca), REQUESTS_CA_BUNDLE=str(ca))
    os.environ.update(env)
    from demo.llm_gateway import requests_per_minute
    if requests_per_minute(cfg):
        os.environ['LLM_BINDING_HOST'] = f"http://127.0.0.1:{cfg['port']}/local/llm"
        os.environ['MAX_ASYNC_LLM'] = '1'
    # Upstream checks existence; all effective settings above remain in process memory.
    (ROOT / ".env").touch(exist_ok=True)
    fingerprint_path.write_text(json.dumps(fingerprint, indent=2), encoding="utf-8")
    return cfg


def main():
    # File-backed stores must never be opened by two instances in this workspace.
    (ROOT / "logs").mkdir(exist_ok=True)
    instance_lock = (ROOT / "logs/instance.lock").open("a+b")
    instance_lock.seek(0, 2)
    if instance_lock.tell() == 0:
        instance_lock.write(b"1")
        instance_lock.flush()
    instance_lock.seek(0)
    if sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(instance_lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise SystemExit("myRAG is already running in this folder. Open http://127.0.0.1:9621/demo/ or stop it before restarting.")
    cfg = configure()
    import asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    from lightrag.api.config import initialize_config, global_args
    initialize_config()
    from lightrag.api.lightrag_server import create_app, configure_logging
    configure_logging()
    app = create_app(global_args)
    from demo.extension import install
    import uvicorn
    from fastapi import BackgroundTasks
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=cfg["port"], log_level="info"))

    @app.post("/demo/shutdown", include_in_schema=False)
    async def shutdown(background_tasks: BackgroundTasks):
        background_tasks.add_task(setattr, server, "should_exit", True)
        return {"message": "Stopping myRAG gracefully."}

    from demo.llm_gateway import install_gateway
    install_gateway(app, cfg)
    install(app, cfg, ROOT)
    print(f"\nmyRAG: http://127.0.0.1:{cfg['port']}/demo/\nCtrl+C to stop. Data stays in {ROOT / 'data'}\n", flush=True)
    server.run()


if __name__ == "__main__":
    main()
