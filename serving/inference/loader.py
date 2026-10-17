# -*- coding: utf-8 -*-
"""Factory mapping a model ``kind`` to a concrete :class:`Runtime`.

Heavy dependencies (``torch``, ``transformers``) are imported lazily so that
importing this module never pulls in the ML stack.
"""

from __future__ import annotations

from collections.abc import Callable

from ..specs import ModelSpec, Settings
from .base import Runtime


def _load_encoder() -> type[Runtime]:
    from .encoder import EncoderRuntime

    return EncoderRuntime


def _load_llm() -> type[Runtime]:
    from .llm import LLMRuntime

    return LLMRuntime


def _load_tfidf() -> type[Runtime]:
    from .tfidf import TfidfRuntime

    return TfidfRuntime


def _load_fake() -> type[Runtime]:
    from .fake import FakeRuntime

    return FakeRuntime


LOADERS: dict[str, Callable[[], type[Runtime]]] = {
    "encoder": _load_encoder,
    "llm": _load_llm,
    "tfidf": _load_tfidf,
    "fake": _load_fake,
}

KNOWN_KINDS = tuple(LOADERS)


def create_runtime(spec: ModelSpec, settings: Settings) -> Runtime:
    """Instantiate the runtime matching ``spec.kind``.

    ``settings.fake`` (or ``kind == "fake"``) forces the deterministic
    :class:`FakeRuntime` regardless of the configured kind.
    """
    if settings.fake or spec.kind == "fake":
        kind = "fake"
    else:
        kind = spec.kind

    loader = LOADERS.get(kind)
    if loader is None:
        raise ValueError(
            "Unknown model kind {!r}; known kinds: {}".format(
                kind, ", ".join(KNOWN_KINDS)
            )
        )
    return loader()()


__all__ = ["LOADERS", "KNOWN_KINDS", "create_runtime"]