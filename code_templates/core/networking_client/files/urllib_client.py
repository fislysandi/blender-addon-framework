"""Blocking urllib helpers; wrap calls in Blender timers or threads."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


@dataclass
class FetchResult:
    ok: bool
    status_code: Optional[int]
    payload: Optional[Any]
    error: Optional[str]
    headers: Dict[str, str]


def validate_url(target: str) -> str:
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use http(s) and include a host")
    return target


def build_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def decode_body(body: bytes) -> Any:
    try:
        return json.loads(body)
    except ValueError:
        return body.decode("utf-8", "replace")


def make_request(
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    body: Optional[bytes],
    timeout: float,
) -> FetchResult:
    request = Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = decode_body(response.read())
            return FetchResult(
                ok=True,
                status_code=response.status,
                payload=payload,
                error=None,
                headers=dict(response.getheaders()),
            )
    except (HTTPError, URLError, ValueError) as exc:
        return FetchResult(
            ok=False,
            status_code=getattr(exc, "code", None),
            payload=None,
            error=str(exc),
            headers={},
        )


def get_json(
    url: str,
    *,
    params: Optional[Mapping[str, Any]] = None,
    auth_token: Optional[str] = None,
    timeout: float = 10.0,
) -> FetchResult:
    safe_url = validate_url(url)
    query = urlencode(params or {})
    if query:
        safe_url = f"{safe_url}?{query}"
    headers = build_headers(auth_token)
    return make_request("GET", safe_url, headers=headers, body=None, timeout=timeout)


def post_json(
    url: str,
    *,
    payload: Any,
    auth_token: Optional[str] = None,
    timeout: float = 10.0,
) -> FetchResult:
    if not isinstance(payload, (Mapping, list)):
        raise ValueError("POST payload must be a mapping or list")
    body = json.dumps(payload).encode("utf-8")
    headers = build_headers(auth_token)
    headers["Content-Type"] = "application/json"
    return make_request(
        "POST", validate_url(url), headers=headers, body=body, timeout=timeout
    )


__all__ = ["FetchResult", "get_json", "post_json"]
