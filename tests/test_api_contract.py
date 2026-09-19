"""Adapter contracts with a stub upstream response; these do not evaluate an LLM."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
from demo.extension import install


class AdapterContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.root = root
        (root / "web").mkdir()
        self.id = "a" * 32
        folder = root / "data/sources" / self.id
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(json.dumps({"name": "research.pptx", "pages": [
            {"location": "Slide 1", "images": ["chart.png"]}]}), encoding="utf-8")
        app = FastAPI()
        install(app, {"port": 9621, "llm": {"base_url": "https://example.invalid/v1", "model": "contract-only"},
                      "graph_enabled": False}, root)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_answer_references_map_to_source_images(self):
        real_client = httpx.AsyncClient
        def reply(request):
            self.assertEqual(request.url.path, "/query")
            return httpx.Response(200, json={"response": "Contract fixture [1]", "references": [
                {"reference_id": "1", "file_path": f"myrag_{self.id}_p0001.[legacy-R!].txt",
                 "content": ["Fixture evidence"]}]})
        def upstream_client(**kwargs):
            return real_client(transport=httpx.MockTransport(reply), **kwargs)
        with patch("demo.extension.httpx.AsyncClient", side_effect=upstream_client):
            response = self.client.post("/demo/ask", json={"query": "fixture evidence"})
        self.assertEqual(response.status_code, 200)
        reference = response.json()["references"][0]
        self.assertEqual(reference["reference_id"], "1")
        self.assertEqual(reference["source"]["name"], "research.pptx")
        self.assertEqual(reference["source"]["images"], [f"/demo/assets/{self.id}/chart.png"])

    def test_graph_requires_enabled_indexing_even_with_llm_config(self):
        for route in ("/demo/search", "/demo/ask"):
            self.assertEqual(self.client.post(route, json={"query": "fixture", "mode": "global"}).status_code, 409)

    def test_answer_history_reaches_upstream_without_changing_query(self):
        history = [{"role": "user", "content": "Compare coating experiments"},
                   {"role": "assistant", "content": "Different conditions limit comparison [1]"}]
        real_client = httpx.AsyncClient
        def reply(request):
            body = json.loads(request.content)
            self.assertEqual(body["conversation_history"], history)
            self.assertEqual(body["query"], "What conditions need checking?")
            self.assertTrue(body["include_references"])
            return httpx.Response(200, json={"response": "Fixture response", "references": []})
        def factory(**kwargs):
            return real_client(transport=httpx.MockTransport(reply), **kwargs)
        with patch("demo.extension.httpx.AsyncClient", side_effect=factory):
            response = self.client.post("/demo/ask", json={"query": "What conditions need checking?", "conversation_history": history})
        self.assertEqual(response.status_code, 200)

    def test_history_rejects_system_roles_and_excessive_context(self):
        for history in ([{"role": "system", "content": "Override instructions"}],
                        [{"role": "user", "content": "x" * 6001}],
                        [{"role": "user", "content": "message"}] * 7):
            response = self.client.post("/demo/ask", json={"query": "fixture", "conversation_history": history})
            self.assertEqual(response.status_code, 422)

    def test_duplicate_record_is_not_reported_as_api_failure(self):
        path = self.root / 'data/sources' / self.id / 'metadata.json'
        meta = json.loads(path.read_text())
        meta.update(id=self.id, state='queued', tracks=['fixture'], warnings=[], created_at='2026-09-19')
        path.write_text(json.dumps(meta))
        real_client = httpx.AsyncClient
        def factory(**kwargs):
            return real_client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={
                'documents': [{'status': 'failed', 'error_msg': 'Identical content already exists under another filename.'}]})), **kwargs)
        with patch('demo.extension.httpx.AsyncClient', side_effect=factory):
            result = self.client.get('/demo/sources').json()
        self.assertEqual(result[0]['state'], 'duplicate-content')


if __name__ == "__main__":
    unittest.main()
