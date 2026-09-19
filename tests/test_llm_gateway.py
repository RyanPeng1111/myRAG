import unittest
from unittest.mock import patch, AsyncMock
from demo.llm_gateway import Pacer, requests_per_minute
from demo.llm_gateway import install_gateway
from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx


class RateLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_spacing_and_cooldown(self):
        with patch('demo.llm_gateway.time.monotonic', return_value=100), patch('demo.llm_gateway.asyncio.sleep', new_callable=AsyncMock) as sleep:
            pacer = Pacer(4)
            await pacer.wait()
            sleep.assert_awaited_with(0)
            await pacer.wait()
            sleep.assert_awaited_with(15)
            pacer.feedback(429)
            await pacer.wait()
            sleep.assert_awaited_with(65)
            pacer.feedback(503)
            self.assertEqual(pacer.next_request, 165)

    async def test_only_google_defaults_to_pacing(self):
        self.assertEqual(requests_per_minute({'llm': {'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai'}}), 4)
        self.assertEqual(requests_per_minute({'llm': {'base_url': 'https://internal.example/v1'}}), 0)


class DailyQuotaTests(unittest.TestCase):
    def test_daily_quota_does_not_repeat_external_calls(self):
        app = FastAPI()
        install_gateway(app, {'llm': {'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai', 'api_key': 'fixture'}})
        real_client = httpx.AsyncClient
        calls = []
        def reply(request):
            calls.append(request)
            return httpx.Response(429, json={'error': {'message': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}})
        def factory(**kwargs):
            return real_client(transport=httpx.MockTransport(reply), **kwargs)
        with patch('demo.llm_gateway.httpx.AsyncClient', side_effect=factory), TestClient(app) as client:
            for _ in range(3):
                self.assertEqual(client.post('/local/llm/chat/completions', json={'messages': []}).status_code, 429)
        self.assertEqual(len(calls), 1)
