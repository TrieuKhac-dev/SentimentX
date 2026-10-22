# -*- coding: utf-8 -*-
"""Runtime abstraction shared by every inference backend."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from ..specs import ModelSpec, Settings

UNKNOWN_LABEL = "unknown"
UNKNOWN_LABEL_VI = "Không đọc được"


@dataclass(frozen=True)
class AspectResult:
    """Prediction for a single aspect of a single text."""

    label: str
    label_vi: str
    code: int | None
    confidence: float | None
    probs: dict[str, float] | None
    quote: Optional[str] = None
    reason: Optional[str] = None


class Runtime(Protocol):
    """Protocol every inference backend must implement.

    Runtimes are constructed with no arguments; configuration is passed to
    :meth:`load`. ``check`` is optional: backends that cannot validate without
    loading weights simply inherit the default (no problems).
    """

    def load(self, spec: ModelSpec, settings: Settings) -> None: ...

    def warmup(self) -> None: ...

    def predict(
        self, texts: list[str], include_probs: bool = True
    ) -> list[dict[str, AspectResult]]: ...

    def unload(self) -> None: ...

    @property
    def metadata(self) -> dict: ...

    @classmethod
    def check(cls, spec: ModelSpec, settings: Settings) -> list[str]:
        """Validate the model without loading weights. Defaults to no problems."""
        return []


def code_to_result(
    code: int | None,
    labels: dict,
    confidence: float | None = None,
    probs: dict[str, float] | None = None,
) -> AspectResult:
    """Convert a numeric sentiment code to an :class:`AspectResult`.

    Codes are resolved through ``labels["codes"]`` so backends do not need to
    hard-code label names. ``None`` maps to the unknown/"unreadable" result.
    """
    labels = labels or {}
    if code is None:
        return AspectResult(UNKNOWN_LABEL, UNKNOWN_LABEL_VI, None, confidence, probs)

    codes = labels.get("codes", {})
    entry = codes.get(int(code)) or {}
    name = entry.get("name", UNKNOWN_LABEL)
    vi = entry.get("vi", UNKNOWN_LABEL_VI)
    return AspectResult(name, vi, int(code), confidence, probs)


def normalize_probs(probs: dict, labels: dict) -> dict[str, float]:
    """Map probability keys to label names and rescale them to sum to 1.

    Keys may be integer codes (``0``/``1``/``2``), string codes (``"0"``), or
    label names (``"positive"``). If the values already sum to 1 they are
    returned unchanged; otherwise they are rescaled.
    """
    labels = labels or {}
    codes = labels.get("codes", {})

    normalized: dict[str, float] = {}
    for key, value in probs.items():
        if isinstance(key, int) or (isinstance(key, str) and key.isdigit()):
            entry = codes.get(int(key)) or {}
            name = entry.get("name") or str(key)
        else:
            name = str(key)
        normalized[name] = float(value)

    total = sum(normalized.values())
    if total > 0 and abs(total - 1.0) > 1e-6:
        normalized = {name: value / total for name, value in normalized.items()}

    return normalized


__all__ = [
    "AspectResult",
    "Runtime",
    "code_to_result",
    "normalize_probs",
]