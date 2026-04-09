from __future__ import annotations

import json
import time
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .lottery_loader import parse_history_records


DEFAULT_PAGE_SIZE = 500
MAX_PAGE_SIZE = 5000
RATE_LIMIT_RETRIES = 2
RATE_LIMIT_BASE_DELAY = 1.0
RATE_LIMIT_MAX_DELAY = 5.0


def normalize_api_base_url(value: str) -> str:
    normalized = str(value or "").strip().rstrip("/")
    for suffix in ("/api/v1/mcp", "/api/v1", "/api"):
        if normalized.lower().endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized.rstrip("/")


class LotteryApiError(RuntimeError):
    pass


class LotteryApiClient:
    def __init__(
        self,
        api_base_url: str,
        token: str = "",
        opener: Callable[[Request], Any] | None = None,
        timeout: int = 30,
    ) -> None:
        self.api_base_url = normalize_api_base_url(api_base_url)
        self.token = str(token or "").strip()
        self.opener = opener or urlopen
        self.timeout = timeout

    def _get_retry_delay(self, exc: HTTPError, attempt: int) -> float:
        headers = getattr(exc, "headers", None)
        if headers:
            retry_after = headers.get("Retry-After")
            if retry_after not in (None, ""):
                try:
                    return max(0.0, min(float(retry_after), RATE_LIMIT_MAX_DELAY))
                except (TypeError, ValueError):
                    pass
        return min(RATE_LIMIT_BASE_DELAY * (2 ** max(attempt - 1, 0)), RATE_LIMIT_MAX_DELAY)

    def request_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_base_url:
            raise LotteryApiError("未配置 NEUXSBOT_API_BASE_URL")

        query = urlencode({k: v for k, v in (params or {}).items() if v not in (None, "", [])})
        url = f"{self.api_base_url}/api/v1/mcp/{path.lstrip('/')}"
        if query:
            url = f"{url}?{query}"

        request = Request(url, method="GET", headers={"Accept": "application/json"})
        if self.token:
            request.add_header("X-api-key", self.token)

        for attempt in range(1, RATE_LIMIT_RETRIES + 2):
            try:
                with self.opener(request) if self.opener is not urlopen else self.opener(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                break
            except HTTPError as exc:
                if exc.code == 429 and attempt <= RATE_LIMIT_RETRIES:
                    time.sleep(self._get_retry_delay(exc, attempt))
                    continue
                if exc.code == 429:
                    raise LotteryApiError("请求网站接口失败: HTTP 429 请求过于频繁，请稍后重试或降低调用频率") from exc
                raise LotteryApiError(f"请求网站接口失败: HTTP {exc.code} {exc.reason}") from exc
            except Exception as exc:
                raise LotteryApiError(f"请求网站接口失败: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LotteryApiError("网站接口返回了无法解析的 JSON") from exc

        if isinstance(payload, dict) and payload.get("message") and payload.get("code"):
            raise LotteryApiError(f"{payload.get('message')} ({payload.get('code')})")

        return payload

    def get_history_page(self, lottery_type: str, page: int = 1, limit: int = DEFAULT_PAGE_SIZE) -> dict[str, Any]:
        clamped_limit = min(max(int(limit or DEFAULT_PAGE_SIZE), 1), MAX_PAGE_SIZE)
        return self.request_json(
            "lottery/history",
            {
                "lotteryType": lottery_type,
                "page": int(page or 1),
                "limit": clamped_limit,
            },
        )

    def fetch_history_records(
        self,
        lottery_type: str,
        periods: int = 100,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:
        desired = max(int(periods or 100), 1)
        page = 1
        collected: list[dict[str, Any]] = []
        effective_page_size = min(max(int(page_size or DEFAULT_PAGE_SIZE), 1), MAX_PAGE_SIZE)

        while len(collected) < desired:
            envelope = self.get_history_page(lottery_type, page=page, limit=effective_page_size)
            rows = envelope.get("data") or []
            collected.extend(rows)

            meta = envelope.get("meta") or {}
            if not meta.get("hasMore") or not rows:
                break

            page += 1

        return parse_history_records(collected[:desired])
