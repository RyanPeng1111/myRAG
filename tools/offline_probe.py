"""Verify model inference/imports while this process refuses network connections."""
import os
from pathlib import Path
import socket

root = Path(__file__).resolve().parents[1]
os.environ["HF_HOME"] = str(root / ".cache/huggingface")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TIKTOKEN_CACHE_DIR"] = str(root / ".cache/tiktoken")

def denied(*args, **kwargs):
    raise AssertionError("Offline probe attempted network access")

socket.socket.connect = denied
socket.create_connection = denied
from fastembed import TextEmbedding
import tiktoken
from lightrag.api.lightrag_server import create_app
model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                      cache_dir=str(root / "models"), local_files_only=True, threads=2)
vector = next(model.embed(["離線研究搜尋"])); assert len(vector) == 384
for name in ("cl100k_base", "o200k_base"):
    assert tiktoken.get_encoding(name).encode("研究報告")
print("PASS offline model inference, tokenizers and upstream API import with network connections denied")
from rapidocr_onnxruntime import RapidOCR
result, _ = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)(str(root / "samples/synthetic-temperature-chart.png"))
assert result and any("48" in row[1] for row in result)
print("PASS offline CPU OCR with packaged model weights")
