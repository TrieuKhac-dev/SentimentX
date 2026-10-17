# -*- coding: utf-8 -*-
"""Configuration models for the serving layer.

`ModelSpec` and `Settings` mirror `configs/serving.yaml` into plain dataclasses
so the rest of the serving layer does not need to touch YAML or path logic.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, List, Optional, Union

import yaml

known_kinds = {"encoder", "llm", "tfidf"}


@dataclass(frozen=True)
class ModelSpec:
    """A single serving model, mirroring one entry under ``models:``."""

    id: str
    kind: str
    enabled: bool
    version: str
    load: dict
    runtime: dict
    expected: dict
    metrics: Optional[dict] = None


@dataclass
class Settings:
    """The resolved serving configuration."""

    root: Path
    raw: dict
    server: dict
    labels: dict
    models: dict[str, ModelSpec]
    default_model: str
    enabled_models: List[str]
    fake: bool = False


def resolve_path(root: Path, value: Any) -> Path:
    """Return ``value`` as an absolute path, resolving relative values to ``root``."""
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _repo_root() -> Path:
    # serving/specs.py -> serving -> repo root.
    return Path(__file__).resolve().parents[1]


def _default_config_path() -> Path:
    return _repo_root() / "configs" / "serving.yaml"


def _normalize_override(models_override: Any) -> List[str]:
    if models_override is None:
        return []
    if isinstance(models_override, str):
        return [part.strip() for part in models_override.split(",") if part.strip()]
    return [str(part).strip() for part in list(models_override) if str(part).strip()]


def load_settings(
    config_path: Union[str, Path, None] = None,
    models_override: Any = None,
    default_override: Optional[str] = None,
    fake: bool = False,
) -> Settings:
    """Load and validate ``configs/serving.yaml`` into a :class:`Settings`.

    Parameters
    ----------
    config_path:
        Path to the serving YAML. Defaults to ``<repo root>/configs/serving.yaml``.
    models_override:
        Comma-separated string or list of model ids. When given, those ids are
        enabled and every other model is disabled. Unknown ids raise ValueError.
    default_override:
        Model id to force as the default model. It must be a known model; if it is
        disabled it gets enabled.
    fake:
        When True, an empty set of enabled models is allowed (used for tests).
    """
    root = _repo_root()
    path = Path(config_path) if config_path is not None else _default_config_path()

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    server = dict(raw.get("server") or {})
    labels = dict(raw.get("labels") or {})
    raw_models = dict(raw.get("models") or {})

    models: dict[str, ModelSpec] = {}
    for model_id, spec_raw in raw_models.items():
        spec_raw = dict(spec_raw or {})
        metrics = spec_raw.get("metrics")
        models[model_id] = ModelSpec(
            id=model_id,
            kind=spec_raw.get("kind", ""),
            enabled=bool(spec_raw.get("enabled", False)),
            version=spec_raw.get("version", ""),
            load=dict(spec_raw.get("load") or {}),
            runtime=dict(spec_raw.get("runtime") or {}),
            expected=dict(spec_raw.get("expected") or {}),
            metrics=dict(metrics) if metrics else None,
        )

    override_ids = _normalize_override(models_override)
    if override_ids:
        for model_id in override_ids:
            if model_id not in models:
                raise ValueError(
                    "Unknown model id in models_override: {!r}".format(model_id)
                )
        for model_id, spec in models.items():
            models[model_id] = replace(spec, enabled=model_id in override_ids)

    if default_override is not None:
        if default_override not in models:
            raise ValueError(
                "Unknown model id in default_override: {!r}".format(default_override)
            )
        spec = models[default_override]
        if not spec.enabled:
            models[default_override] = replace(spec, enabled=True)

    enabled_models = [model_id for model_id, spec in models.items() if spec.enabled]

    if not enabled_models and not fake:
        raise ValueError("No enabled serving models and fake=False")

    if default_override is not None:
        default_model = default_override
    else:
        default_model = server.get("default_model", "")
        if (
            not default_model
            or default_model not in models
            or not models[default_model].enabled
        ):
            default_model = enabled_models[0] if enabled_models else ""

    return Settings(
        root=root,
        raw=raw,
        server=server,
        labels=labels,
        models=models,
        default_model=default_model,
        enabled_models=enabled_models,
        fake=fake,
    )