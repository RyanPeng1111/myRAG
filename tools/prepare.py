"""Explicit online preparation. Runtime never downloads embedding weights."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
os.environ["HF_HOME"] = str(ROOT / ".cache/huggingface")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["TIKTOKEN_CACHE_DIR"] = str(ROOT / ".cache/tiktoken")

if __name__ == "__main__":
    import tiktoken
    from fastembed import TextEmbedding
    cfg = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
    (ROOT / "models").mkdir(exist_ok=True)
    print("Preparing CPU multilingual embedding model...", flush=True)
    model = TextEmbedding(model_name=cfg["embedding"]["model"], cache_dir=str(ROOT / "models"), threads=4)
    vector = next(model.embed(["研究報告與實驗比較 / research experiments"]))
    if len(vector) != cfg["embedding"]["dimension"]:
        raise RuntimeError("Unexpected embedding dimension")
    print("Preparing tokenizer caches...", flush=True)
    for name in ("cl100k_base", "o200k_base"):
        tiktoken.get_encoding(name)
    print("Prepared. Copy models/ and .cache/tiktoken/ with the code for an offline installation.", flush=True)
