# -*- coding: utf-8 -*-
"""Error types and payload helpers for the serving layer.

FastAPI exception handlers are intentionally NOT defined here; ``app.py`` owns
the HTTP layer and can map these to responses via ``error_payload``.
"""

from __future__ import annotations

from typing import Optional


class APIError(Exception):
    """Base error carrying an HTTP status code and a stable error code."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class ModelNotFoundError(APIError):
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(404, "model_not_found", message, details)


class ModelDisabledError(APIError):
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(503, "model_disabled", message, details)


class ModelFailedError(APIError):
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(503, "model_failed", message, details)


class ModelBusyError(APIError):
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(503, "model_busy", message, details)


class TextTooLongError(APIError):
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(422, "text_too_long", message, details)


def error_payload(
    code: str,
    message: str,
    details: Optional[dict] = None,
    request_id: Optional[str] = None,
) -> dict:
    """Build the standard error envelope used by :class:`ErrorResponse`."""
    payload = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    if request_id is not None:
        payload["request_id"] = request_id
    return payload


__all__ = [
    "APIError",
    "ModelNotFoundError",
    "ModelDisabledError",
    "ModelFailedError",
    "ModelBusyError",
    "TextTooLongError",
    "error_payload",
]