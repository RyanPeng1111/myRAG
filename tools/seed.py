"""Load synthetic fixtures into a running instance; explicit, never auto-upload user files."""
import json
from pathlib import Path
import sys
import time
import httpx

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
with httpx.Client(base_url=f"http://127.0.0.1:{cfg['port']}", timeout=180, trust_env=False) as client:
    existing = {x["name"] for x in client.get("/demo/sources").json() if x["state"] in ("queued", "processed", "processing")}
    for path in sorted((root / "samples").iterdir()):
        if path.suffix not in (".md", ".pptx", ".docx", ".xlsx", ".pdf", ".png") or path.name in existing:
            continue
        with path.open("rb") as stream:
            response = client.post("/demo/upload", files={"file": (path.name, stream)})
        response.raise_for_status()
        print(path.name, response.json()["state"], flush=True)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        response = client.post("/demo/search", json={"query": "陶瓷塗層降低電池溫升", "limit": 4})
        if response.is_success and response.json().get("data", {}).get("chunks"):
            print("Semantic retrieval is working. Remaining ingestion can be viewed in /webui/.")
            break
        time.sleep(2)
    else:
        print("Index not ready within 240 seconds; inspect logs/.")
        sys.exit(1)
