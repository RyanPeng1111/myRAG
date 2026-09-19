"""Single-process pacing for low-quota OpenAI-compatible providers."""
import asyncio
import time
import json
from urllib.parse import urlparse
import httpx
from fastapi import Request
from fastapi.responses import Response


def requests_per_minute(cfg):
    host = urlparse(cfg['llm'].get('base_url', '')).hostname
    default = {'generativelanguage.googleapis.com': 4, 'api.groq.com': 1}.get(host, 0)
    return max(0, int(cfg.get('llm_requests_per_minute', default)))


class Pacer:
    def __init__(self, rpm):
        self.interval = 60 / rpm
        self.next_request = 0.0
        self.lock = asyncio.Lock()

    async def wait(self):
        await asyncio.sleep(max(0, self.next_request - time.monotonic()))
        self.next_request = time.monotonic() + self.interval

    def feedback(self, status):
        if status in (429, 503):
            self.next_request = max(self.next_request, time.monotonic() + 65)


def install_gateway(app, cfg):
    rpm = requests_per_minute(cfg)
    if not rpm:
        return
    pacer = Pacer(rpm)
    daily_failure = None

    @app.post('/local/llm/chat/completions', include_in_schema=False)
    async def completion(request: Request):
        nonlocal daily_failure
        payload = await request.body()
        if urlparse(cfg['llm']['base_url']).hostname == 'api.groq.com':
            body = json.loads(payload)
            if str(body.get('model', '')).startswith('openai/gpt-oss-'):
                body.setdefault('reasoning_effort', cfg.get('groq_reasoning_effort', 'low'))
                if 'max_tokens' not in body and 'max_completion_tokens' not in body:
                    body['max_completion_tokens'] = int(cfg.get('groq_max_completion_tokens', 4096))
                payload = json.dumps(body).encode('utf-8')
        async with pacer.lock:
            if daily_failure is not None:
                return Response(daily_failure, status_code=429, media_type='application/json')
            await pacer.wait()
            async with httpx.AsyncClient(timeout=240) as client:
                response = await client.post(cfg['llm']['base_url'].rstrip('/') + '/chat/completions',
                    content=payload, headers={'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + cfg['llm'].get('api_key', '')})
            pacer.feedback(response.status_code)
            if response.status_code == 429 and 'PerDay' in response.text:
                daily_failure = response.content
        return Response(response.content, status_code=response.status_code,
                        media_type=response.headers.get('content-type', 'application/json'))
