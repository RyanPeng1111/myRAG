"""Real HTTP/embedding integration checks against the local demo, no fake LLM."""
import json
from pathlib import Path
import time
import uuid
import httpx

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
checks = []

def check(name, condition):
    if not condition: raise AssertionError(name)
    checks.append(name)
    print("PASS", name, flush=True)

with httpx.Client(base_url=f"http://127.0.0.1:{cfg['port']}", timeout=180, trust_env=False) as client:
    check("health", client.get("/health").json()["status"] == "healthy")
    check("upstream UI", client.get("/webui/").status_code == 200)
    check("demo UI", client.get("/demo/").status_code == 200)
    result = client.post("/demo/search", json={"query": "有哪些降低電池溫升的實驗？", "limit": 6})
    result.raise_for_status()
    chunks = result.json()["data"]["chunks"]
    check("real semantic retrieval", len(chunks) > 0 and "ceramic" in chunks[0]["source"]["name"])
    check("Chinese chunk integrity", all("\ufffd" not in c["content"] for c in chunks))
    result = client.post("/demo/search", json={"query": "未塗層 48°C 陶瓷塗層 42°C", "limit": 6}).json()
    sources = [c["source"] for c in result["data"]["chunks"] if c.get("source", {}).get("images")]
    check("image source retrieval", bool(sources))
    image = client.get(sources[0]["images"][0])
    check("source image bytes", image.status_code == 200 and image.content.startswith(b"\x89PNG"))
    check("source document download", client.get(f"/demo/download/{sources[0]['id']}").status_code == 200)
    check("unconfigured LLM fails clearly", client.post("/demo/ask", json={"query": "比較實驗"}).status_code == 409)
    check("cross-origin writes rejected", client.post("/demo/search", json={"query": "研究"}, headers={"Origin": "https://untrusted.invalid"}).status_code == 403)
    check("source traversal rejected", client.get("/demo/sources/not-a-valid-id").status_code == 404)
    check("credentials not returned", "api_key" not in client.get("/demo/settings").json())
    raw = (root / "samples/01-ceramic-coating.md").read_bytes()
    dup = client.post("/demo/upload", files={"file": ("duplicate.md", raw)}).json()
    check("duplicate content not reindexed", dup["state"] == "already-imported")
    marker = "smoke-" + uuid.uuid4().hex
    content = f"Synthetic disposable lifecycle test: {marker}. This experiment evaluates ultrasonic welding of titanium.".encode()
    created = client.post("/demo/upload", files={"file": ("disposable-smoke.txt", content)}).json()
    doc_id = created["id"]
    for _ in range(80):
        states = client.get("/demo/sources").json()
        if next(x for x in states if x["id"] == doc_id)["state"] == "processed": break
        time.sleep(.5)
    else: raise AssertionError("lifecycle indexing timed out")
    before = client.post("/demo/search", json={"query": marker, "limit": 30}).json()["data"]["chunks"]
    check("uploaded fixture searchable", any(c.get("source", {}).get("id") == doc_id for c in before))
    removed = client.delete(f"/demo/sources/{doc_id}/index")
    removed.raise_for_status()
    check("index removal completed", removed.json()["state"] == "index-removed")
    after = client.post("/demo/search", json={"query": marker, "limit": 30}).json()["data"]["chunks"]
    check("deleted evidence no longer retrieved", all(c.get("source", {}).get("id") != doc_id for c in after))
    check("original retained after index removal", client.get(f"/demo/download/{doc_id}").status_code == 200)

(root / "logs/smoke-results.json").write_text(json.dumps({"passed": len(checks), "checks": checks}, indent=2), encoding="utf-8")
print(f"{len(checks)} integration checks passed.")
