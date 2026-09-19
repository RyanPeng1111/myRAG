"""Ask the loopback server to finish requests and persist stores before exiting."""
import json
from pathlib import Path
import time
import httpx

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
with httpx.Client(base_url=f"http://127.0.0.1:{cfg['port']}", trust_env=False, timeout=5) as client:
    try:
        response = client.post("/demo/shutdown")
        response.raise_for_status()
    except httpx.ConnectError:
        print("myRAG is already stopped.")
        raise SystemExit(0)
    print("Waiting for active requests and index writes to finish...", flush=True)
    for _ in range(120):
        time.sleep(1)
        try:
            client.get("/health")
        except httpx.ConnectError:
            print("Server no longer accepts connections. Wait for the instance lock to release before restarting.")
            break
    else:
        raise SystemExit("Shutdown is still pending. Check logs; do not force-kill during indexing.")
