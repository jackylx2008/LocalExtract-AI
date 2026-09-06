from __future__ import annotations

import json

from local_extract_ai.modules.ai_client import AISettings, LocalAIClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps(self.payload).encode()


def test_verify_uses_health_endpoint(monkeypatch):
    requests = []

    def fake_open(request, **_kwargs):
        requests.append(request.full_url)
        return FakeResponse({"status": "ok"})

    monkeypatch.setattr("local_extract_ai.modules.ai_client.urlopen", fake_open)
    client = LocalAIClient(AISettings("http://127.0.0.1:8080/v1", "local", "demo"))

    assert client.verify() == "本地 AI 正常"
    assert requests == ["http://127.0.0.1:8080/health"]


def test_extract_reads_assistant_content(monkeypatch):
    response = {"choices": [{"message": {"content": "ABC-123"}}]}
    authorization = []

    def fake_open(request, **_kwargs):
        authorization.append(request.get_header("Authorization"))
        return FakeResponse(response)

    monkeypatch.setattr("local_extract_ai.modules.ai_client.urlopen", fake_open)
    client = LocalAIClient(AISettings("http://127.0.0.1:8080/v1", "test-secret", "demo"))

    assert client.extract(b"png", "extract") == "ABC-123"
    assert authorization == ["Bearer test-secret"]
