# -*- coding: utf-8 -*-
"""Starlette middleware for the serving layer.

All middleware here is deliberately small and depends only on Starlette's
request/response types. Error responses use the standard ``{"error": {...}}``
envelope so the frontend can render them consistently.
"""

from __future__ import annotations

import re
import uuid
from typing import Callable, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_ASCII_TOKEN_RE = re.compile(r"^[\x21-\x7e]{1,128}$")


def _error(
    status_code: int,
    code: str,
    message: str,
    request_id: Optional[str] = None,
) -> JSONResponse:
    payload: dict = {"error": {"code": code, "message": message}}
    if request_id is not None:
        payload["error"]["request_id"] = request_id
    return JSONResponse(payload, status_code=status_code)


async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    header = request.headers.get("x-request-id")
    if header and _ASCII_TOKEN_RE.fullmatch(header):
        request_id = header
    else:
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def body_limit_middleware(
    request: Request, call_next: Callable, max_body_bytes: int
) -> Response:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > max_body_bytes:
                return _error(
                    413,
                    "payload_too_large",
                    "Request body too large.",
                    getattr(request.state, "request_id", None),
                )
        except ValueError:
            pass
    return await call_next(request)


async def api_key_middleware(
    request: Request, call_next: Callable, api_key: str
) -> Response:
    path = request.url.path
    if path in ("/", "/health", "/static") or path.startswith("/static/"):
        return await call_next(request)
    if not api_key:
        return await call_next(request)

    provided = request.headers.get("x-api-key")
    if provided is not None and provided == api_key:
        return await call_next(request)

    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer ") and auth[len("Bearer "):] == api_key:
        return await call_next(request)

    return _error(
        401,
        "unauthorized",
        "Missing or invalid API key.",
        getattr(request.state, "request_id", None),
    )


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    return response


__all__ = [
    "api_key_middleware",
    "body_limit_middleware",
    "request_id_middleware",
    "security_headers_middleware",
]