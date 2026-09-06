"""OpenAI 兼容本地多模态服务客户端。"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AIServiceError(RuntimeError):
    """本地 AI 服务调用异常。"""


@dataclass(frozen=True, slots=True)
class AISettings:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 60


class LocalAIClient:
    def __init__(self, settings: AISettings) -> None:
        self.settings = settings
        self.base_url = settings.base_url.rstrip("/")

    def verify(self) -> str:
        """验证服务健康状态以及 API key 鉴权。"""
        health_url = self.base_url[:-3] if self.base_url.endswith("/v1") else self.base_url
        payload = self._request_url("GET", f"{health_url}/health")
        status = str(payload.get("status", "")).lower()
        if status not in {"ok", "ready", "idle"}:
            raise AIServiceError(f"本地 AI 尚未就绪：{payload.get('status', '未知状态')}")
        models_payload = self._request("GET", "/models")
        models = models_payload.get("data", [])
        count = len(models) if isinstance(models, list) else 0
        return f"本地 AI 正常，鉴权通过（可用模型 {count} 个）"

    def extract(self, png_bytes: bytes, prompt: str) -> str:
        image_data = base64.b64encode(png_bytes).decode("ascii")
        body = {
            "model": self.settings.model,
            "temperature": 0,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                ],
            }],
        }
        payload = self._request("POST", "/chat/completions", body)
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIServiceError("本地 AI 返回了无法识别的响应结构") from exc
        if not isinstance(content, str) or not content.strip():
            raise AIServiceError("本地 AI 未返回任何特征字符串")
        return content

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request_url(method, f"{self.base_url}{path}", body)

    def _request_url(self, method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            url,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code in {401, 403}:
                raise AIServiceError(
                    "本地 AI 服务鉴权失败，请检查 common.env 中的 API key"
                ) from exc
            raise AIServiceError(f"本地 AI 请求失败（HTTP {exc.code}）：{detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise AIServiceError(f"无法连接本地 AI：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise AIServiceError("本地 AI 返回的不是有效 JSON") from exc
        if not isinstance(result, dict):
            raise AIServiceError("本地 AI 返回的 JSON 根节点不是对象")
        return result
