from pathlib import Path
import importlib.metadata
import json
import sys

root = Path(__file__).resolve().parents[1]
errors = []
print("Python:", sys.version.split()[0], sys.executable)
for name in ("lightrag-hku", "fastembed", "onnxruntime", "fastapi", "rapidocr-onnxruntime"):
    try:
        print(name, importlib.metadata.version(name))
    except importlib.metadata.PackageNotFoundError:
        errors.append(f"Missing package: {name}")
try:
    import lightrag
    ui = Path(lightrag.__file__).parent / "api/webui/index.html"
    print("Upstream WebUI:", ui.exists())
    if not ui.exists(): errors.append("Missing upstream UI assets")
except ImportError:
    pass
config = root / "config.json"
if not config.exists(): config = root / "config.example.json"
cfg = json.loads(config.read_text(encoding="utf-8-sig"))
print("LLM configured:", bool(cfg["llm"]["base_url"] and cfg["llm"]["model"]))
print("Embedding mode:", cfg["embedding"]["mode"])
if cfg["embedding"]["mode"] == "local" and not list((root / "models").rglob("*.onnx")):
    errors.append("Missing embedding weights; run Prepare.ps1 online or copy models/ from prepared bundle")
if not list((root / ".cache/tiktoken").glob("*")):
    errors.append("Missing tokenizer cache; run Prepare.ps1 online or copy .cache/tiktoken/")
for error in errors: print("FAIL:", error)
print("READY" if not errors else "NOT READY")
sys.exit(bool(errors))
