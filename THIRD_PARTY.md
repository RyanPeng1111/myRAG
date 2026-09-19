# Third-party components

This repository extends LightRAG; it does not replace its indexing engine.

- LightRAG 1.5.7: https://github.com/HKUDS/LightRAG — upstream MIT license; source reference commit `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`.
- FastEmbed 0.8.0: https://github.com/qdrant/fastembed — see the package license included in its wheel.
- RapidOCR ONNX Runtime 1.4.4: https://github.com/RapidAI/RapidOCR — see the package license included in its wheel.
- Multilingual embedding model: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 . Quantized ONNX distribution: https://huggingface.co/qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q . Model cards identify Apache-2.0 licensing.

`requirements-win-py312.lock` is the complete pinned Python dependency inventory. Offline resource parts include the original Python wheel archives and their bundled license metadata. Unpack `wheelhouse/` using Bootstrap.cmd to inspect these artifacts during internal review. Review each dependency and model under your organization's approval process; this inventory does not replace license or vulnerability review.

The sample research reports and numbers are synthetic testing fixtures. User documents, credentials, logs, and LLM response caches are excluded from this repository.
