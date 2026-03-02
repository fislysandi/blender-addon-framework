"""Async httpx helpers tuned for Blender addons.

Run `AsyncHTTPXClient.fetch_json()` via Blender timers or background tasks so the UI thread is never blocked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

import httpx


@dataclass
class AsyncFetchResult:
    ok: bool
    status_code: Optional[int]
    data: Optional[Any]
    error: Optional[str]
    headers: Dict[str, str]


def _decode_body(body: bytes, headers: Mapping[str, str]) -> Any:
    if headers.get("content-type", "").startswith("application/json"):
        try:
            return json.loads(body)
        except ValueError:
            pass
    return body.decode("utf-8", "replace")


class AsyncHTTPXClient:
    def __init__(
        self,
        *,
        timeout: httpx.Timeout = httpx.Timeout(5.0, read=15.0),
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.client = httpx.AsyncClient(timeout=timeout)
        if headers:
            self.client.headers.update(headers)

    async def close(self) -> None:
        await self.client.aclose()

    def attach_token(self, token: str) -> None:
        self.client.headers["Authorization"] = f"Bearer {token}"

    async def fetch_json(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_payload: Optional[Any] = None,
    ) -> AsyncFetchResult:
        try:
            async with self.client.stream(
                method, url, params=params, json=json_payload
            ) as response:
                payload = _decode_body(await response.aread(), dict(response.headers))
                return AsyncFetchResult(
                    True, response.status_code, payload, None, dict(response.headers)
                )
        except httpx.HTTPError as exc:
            return AsyncFetchResult(
                False,
                getattr(exc, "response", None) and exc.response.status_code,
                None,
                str(exc),
                {},
            )

    async def get_json(
        self, url: str, *, params: Optional[Mapping[str, Any]] = None
    ) -> AsyncFetchResult:
        return await self.fetch_json("GET", url, params=params)

    async def post_json(self, url: str, *, payload: Any) -> AsyncFetchResult:
        if not isinstance(payload, (dict, list)):
            raise ValueError("Payload must be JSON-serializable")
        return await self.fetch_json("POST", url, json_payload=payload)


__all__ = ["AsyncFetchResult", "AsyncHTTPXClient"]
