"""Sync requests helpers that should run on background workers or timers in Blender."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from requests.exceptions import RequestException
from urllib3.util import Retry


@dataclass
class ResponseEnvelope:
    ok: bool
    status_code: Optional[int]
    data: Optional[Any]
    error: Optional[str]
    headers: Dict[str, str]


def _json_or_text(response: Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def _retry_strategy(total: int = 3, backoff: float = 0.1) -> Retry:
    return Retry(
        total=total,
        backoff_factor=backoff,
        status_forcelist=[502, 503, 504],
        allowed_methods={"GET", "POST"},
    )


def _build_adapter() -> HTTPAdapter:
    return HTTPAdapter(max_retries=_retry_strategy())


class RequestsClient:
    def __init__(
        self,
        base_url: str,
        *,
        auth: Optional[AuthBase] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Tuple[float, float] = (3.05, 27),
        extra_retry_hosts: Iterable[str] = (),
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = Session()
        self.session.headers.update({"Accept": "application/json"})
        if headers:
            self.session.headers.update(headers)
        if auth:
            self.session.auth = auth
        adapter = _build_adapter()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        for host in extra_retry_hosts:
            self.session.mount(host, adapter)

    def attach_token(self, token: str) -> None:
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _dispatch(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_payload: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> ResponseEnvelope:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return ResponseEnvelope(
                True,
                response.status_code,
                _json_or_text(response),
                None,
                dict(response.headers),
            )
        except RequestException as exc:
            resp = getattr(exc, "response", None)
            return ResponseEnvelope(
                ok=False,
                status_code=getattr(resp, "status_code", None),
                data=None,
                error=str(exc),
                headers=dict(getattr(resp, "headers", {})) if resp else {},
            )

    def get_json(
        self, path: str, *, params: Optional[Mapping[str, Any]] = None
    ) -> ResponseEnvelope:
        return self._dispatch("GET", path, params=params)

    def post_json(self, path: str, *, payload: Any) -> ResponseEnvelope:
        if not isinstance(payload, (Mapping, list)):
            raise ValueError("Payload must be a mapping or list")
        return self._dispatch("POST", path, json_payload=payload)


__all__ = ["ResponseEnvelope", "RequestsClient"]
