# -*- coding: utf-8 -*-
"""Deterministic, dependency-free runtime for tests and offline demos."""

from __future__ import annotations

from ..specs import ModelSpec, Settings
from .base import AspectResult, code_to_result

_POSITIVE_WORDS = ("đẹp", "thơm", "tốt", "mượt", "nhanh", "đúng")
_NEGATIVE_WORDS = ("tệ", "chậm", "móp", "khô", "hắc", "lỗi", "thất vọng")


def _probs_for(code: int) -> dict[str, float]:
    if code == 1:
        return {"positive": 0.90, "negative": 0.05, "not_mentioned": 0.05}
    if code == 2:
        return {"positive": 0.05, "negative": 0.90, "not_mentioned": 0.05}
    return {"positive": 0.005, "negative": 0.005, "not_mentioned": 0.99}


class FakeRuntime:
    """A :class:`Runtime` with deterministic, keyword-based predictions."""

    def __init__(self) -> None:
        self._spec: ModelSpec | None = None
        self._settings: Settings | None = None

    def load(self, spec: ModelSpec, settings: Settings) -> None:
        self._spec = spec
        self._settings = settings

    def warmup(self) -> None:
        return None

    def unload(self) -> None:
        return None

    @property
    def metadata(self) -> dict:
        spec = self._spec
        if spec is None:
            return {"id": "", "kind": "fake", "device": "fake", "max_length": None}
        return {
            "id": spec.id,
            "kind": spec.kind,
            "device": "fake",
            "max_length": spec.runtime.get("max_length"),
        }

    @classmethod
    def check(cls, spec: ModelSpec, settings: Settings) -> list[str]:
        return []

    def predict(
        self, texts: list[str], include_probs: bool = True
    ) -> list[dict[str, AspectResult]]:
        settings = self._settings
        labels = settings.labels if settings is not None else {}
        aspects = labels.get("aspects", [])

        results: list[dict[str, AspectResult]] = []
        for text in texts:
            lowered = text.lower()
            if any(word in lowered for word in _POSITIVE_WORDS):
                code = 1
                confidence = 0.9
            elif any(word in lowered for word in _NEGATIVE_WORDS):
                code = 2
                confidence = 0.9
            else:
                code = 0
                confidence = 0.99

            result = code_to_result(
                code,
                labels,
                confidence=confidence,
                probs=_probs_for(code),
            )
            results.append({aspect: result for aspect in aspects})

        return results


__all__ = ["FakeRuntime"]