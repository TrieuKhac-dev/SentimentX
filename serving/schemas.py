# -*- coding: utf-8 -*-
"""Pydantic v2 request/response schemas for the serving API."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator

MAX_TEXTS = 16


class AspectPrediction(BaseModel):
    """Prediction for a single aspect of a single text."""

    label: str
    label_vi: str
    code: Optional[int] = None
    confidence: Optional[float] = None
    probs: Optional[Dict[str, float]] = None


class PredictionItem(BaseModel):
    """Full prediction for one input text."""

    text: str
    aspects: Dict[str, AspectPrediction]
    readable: bool = True
    raw_answer: Optional[str] = None


class PredictRequest(BaseModel):
    """Prediction request: exactly one of ``text`` or ``texts`` must be set."""

    model: Optional[str] = None
    text: Optional[str] = None
    texts: Optional[List[str]] = None
    include_probs: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_payload(self) -> "PredictRequest":
        if self.text is not None and self.texts is not None:
            raise ValueError("Provide exactly one of 'text' or 'texts', not both")
        if self.text is None and self.texts is None:
            raise ValueError("Provide exactly one of 'text' or 'texts'")

        if self.text is not None:
            if not self.text.strip():
                raise ValueError("'text' must not be empty")
        else:
            if len(self.texts) > MAX_TEXTS:
                raise ValueError(
                    "'texts' must contain at most {} items".format(MAX_TEXTS)
                )
            for item in self.texts:
                if not item or not item.strip():
                    raise ValueError("Each item in 'texts' must be non-empty")

        return self


class PredictResponse(BaseModel):
    """Response for a batch prediction."""

    request_id: str
    model: str
    model_version: str
    model_hash: str
    device: str
    latency_ms: float
    batch_size: int
    results: List[PredictionItem]
    cache_hit: bool = False


class ModelInfo(BaseModel):
    """Describes one serving model and its current runtime state."""

    id: str
    kind: str
    enabled: bool
    state: str
    version: str
    loaded: bool
    device: Optional[str] = None
    max_length: Optional[int] = None
    metrics: Optional[dict] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health-check payload."""

    status: str
    ready: bool
    version: str
    models: Dict[str, dict]
    gpu: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: dict


__all__ = [
    "AspectPrediction",
    "PredictionItem",
    "PredictRequest",
    "PredictResponse",
    "ModelInfo",
    "HealthResponse",
    "ErrorResponse",
]