# -*- coding: utf-8 -*-
"""Lazy, thread-safe model registry for the serving layer."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional

from .errors import (
    ModelBusyError,
    ModelDisabledError,
    ModelFailedError,
    ModelNotFoundError,
)
from .inference.base import AspectResult, Runtime
from .inference.loader import create_runtime
from .specs import ModelSpec, Settings

DISABLED = "DISABLED"
UNLOADED = "UNLOADED"
LOADING = "LOADING"
WARMING = "WARMING"
READY = "READY"
UNLOADING = "UNLOADING"
FAILED = "FAILED"

_IDLE_UNLOAD_INTERVAL_S = 30.0
_BUSY_WAIT_TIMEOUT_S = 30.0


@dataclass
class _ModelEntry:
    """Runtime bookkeeping for one configured model."""

    spec: ModelSpec
    state: str = UNLOADED
    runtime: Optional[Runtime] = None
    error: Optional[str] = None
    loaded_at: Optional[float] = None
    last_used: Optional[float] = None
    load_seconds: Optional[float] = None
    in_use: int = 0
    metadata: dict = field(default_factory=dict)


class ModelRegistry:
    """Owns model runtimes and their lifecycle (load/warmup/predict/unload).

    Models are loaded lazily on first use, warmed up once, and unloaded when
    idle (optional daemon) or to make room under the sequential GPU policy.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Condition(threading.RLock())
        self._load_lock = threading.Lock()
        self._entries: dict[str, _ModelEntry] = {}
        for model_id, spec in settings.models.items():
            state = UNLOADED if spec.enabled else DISABLED
            self._entries[model_id] = _ModelEntry(spec=spec, state=state)
        self._idle_thread: Optional[threading.Thread] = None
        self._idle_stop = threading.Event()

    @property
    def default_model(self) -> str:
        """The configured default model id."""
        return self._settings.default_model

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def _describe(self, entry: _ModelEntry) -> dict:
        metadata = entry.metadata or {}
        device = metadata.get("device", entry.spec.load.get("device", "auto"))
        max_length = metadata.get("max_length", entry.spec.runtime.get("max_length"))
        return {
            "id": entry.spec.id,
            "kind": entry.spec.kind,
            "enabled": entry.spec.enabled,
            "state": entry.state,
            "version": entry.spec.version,
            "loaded": entry.runtime is not None and entry.state == READY,
            "device": device,
            "max_length": max_length,
            "metrics": entry.spec.metrics,
            "error": entry.error,
            "hash": (
                metadata.get("model_hash")
                or entry.spec.expected.get("config_hash")
                or entry.spec.version
            ),
        }

    def list_models(self) -> list[dict]:
        """Describe every registered model, including disabled ones."""
        with self._lock:
            return [self._describe(entry) for entry in self._entries.values()]

    def status(self) -> dict[str, dict]:
        """Describe every registered model, keyed by id."""
        with self._lock:
            return {mid: self._describe(entry) for mid, entry in self._entries.items()}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(
        self,
        model_id: Optional[str],
        texts: list[str],
        include_probs: bool = True,
    ) -> list[dict[str, AspectResult]]:
        """Run a batch prediction, loading and warming the model if needed."""
        entry = self._resolve(model_id)
        texts_list = [texts] if isinstance(texts, str) else list(texts)
        self._acquire(entry)
        runtime = entry.runtime
        try:
            result = runtime.predict(texts_list, include_probs=include_probs)
        finally:
            with self._lock:
                entry.in_use -= 1
                entry.last_used = time.monotonic()
                self._lock.notify_all()
        return self._normalize_results(result, texts_list)

    def _resolve(self, model_id: Optional[str]) -> _ModelEntry:
        mid = model_id if model_id is not None else self._settings.default_model
        if not mid or mid not in self._entries:
            raise ModelNotFoundError("Unknown model id: {!r}".format(mid))
        entry = self._entries[mid]
        if not entry.spec.enabled:
            raise ModelDisabledError("Model {!r} is disabled".format(mid))
        return entry

    def _acquire(self, entry: _ModelEntry) -> None:
        while True:
            with self._lock:
                if entry.state == READY:
                    entry.in_use += 1
                    entry.last_used = time.monotonic()
                    return
                if entry.state == FAILED:
                    raise ModelFailedError(
                        entry.error or "Model {!r} failed".format(entry.spec.id)
                    )
                if entry.state in (LOADING, WARMING, UNLOADING):
                    self._lock.wait()
                    continue
                entry.state = LOADING
                entry.error = None
                entry.runtime = None
                entry.metadata = {}

            try:
                self._load_model(entry)
            except ModelBusyError:
                with self._lock:
                    entry.state = UNLOADED
                    entry.error = None
                    entry.runtime = None
                    entry.metadata = {}
                    self._lock.notify_all()
                raise
            except ModelFailedError as exc:
                with self._lock:
                    entry.runtime = None
                    entry.state = FAILED
                    entry.error = str(exc) or "model failed"
                    entry.metadata = {}
                    self._lock.notify_all()
                raise
            except Exception as exc:
                with self._lock:
                    entry.runtime = None
                    entry.state = FAILED
                    entry.error = str(exc) or exc.__class__.__name__
                    entry.metadata = {}
                    self._lock.notify_all()
                raise ModelFailedError(
                    "Model {!r} failed to load: {}".format(entry.spec.id, exc)
                )

    def _load_model(self, entry: _ModelEntry) -> None:
        with self._load_lock:
            runtime = create_runtime(entry.spec, self._settings)
            self._apply_gpu_policy(entry)

            start = time.monotonic()
            runtime.load(entry.spec, self._settings)

            with self._lock:
                entry.runtime = runtime
                entry.state = WARMING
                self._lock.notify_all()

            runtime.warmup()

            metadata = dict(runtime.metadata)
            metadata['model_hash'] = (
                entry.spec.expected.get('config_hash') or entry.spec.version
            )

            with self._lock:
                entry.runtime = runtime
                entry.state = READY
                entry.metadata = metadata
                entry.loaded_at = time.monotonic()
                entry.load_seconds = time.monotonic() - start
                entry.last_used = entry.loaded_at
                entry.error = None
                self._lock.notify_all()

    @staticmethod
    def _normalize_results(
        result, texts: list[str]
    ) -> list[dict[str, AspectResult]]:
        if isinstance(result, dict):
            return [result]
        if result is None:
            return [{} for _ in texts]
        return list(result)

    # ------------------------------------------------------------------
    # GPU policy
    # ------------------------------------------------------------------
    def _is_fake(self, entry: _ModelEntry) -> bool:
        return bool(self._settings.fake) or entry.spec.kind == "fake"

    def _gpu_policy(self) -> str:
        return str(self._settings.server.get("gpu_policy", "sequential") or "sequential")

    def _apply_gpu_policy(self, entry: _ModelEntry) -> None:
        if self._is_fake(entry):
            return
        policy = self._gpu_policy()
        if policy == "concurrent" and not self._needs_vram():
            return
        self._unload_idle_others(entry)

    def _needs_vram(self) -> bool:
        free_mb = self._free_vram_mb()
        if free_mb is None:
            return False
        min_free = self._settings.server.get("min_free_vram_mb", 1200)
        try:
            min_free = int(min_free)
        except (TypeError, ValueError):
            min_free = 1200
        return free_mb < min_free

    @staticmethod
    def _free_vram_mb() -> Optional[float]:
        try:
            import torch
        except Exception:
            return None
        if not torch.cuda.is_available():
            return None
        try:
            free_bytes, _ = torch.cuda.mem_get_info()
        except Exception:
            return None
        return free_bytes / (1024.0 * 1024.0)

    def _unload_idle_others(self, entry: _ModelEntry) -> None:
        deadline = time.monotonic() + _BUSY_WAIT_TIMEOUT_S
        while True:
            busy_ids: list[str] = []
            claimed: list[tuple[_ModelEntry, Optional[Runtime]]] = []
            with self._lock:
                for other in self._entries.values():
                    if other is entry:
                        continue
                    if other.runtime is None or other.state != READY:
                        continue
                    if self._is_fake(other):
                        continue
                    if other.in_use > 0:
                        busy_ids.append(other.spec.id)
                        continue
                    other.state = UNLOADING
                    other.error = None
                    claimed.append((other, other.runtime))

            for other, runtime in claimed:
                if runtime is not None:
                    try:
                        runtime.unload()
                    except Exception:
                        pass
                with self._lock:
                    other.runtime = None
                    other.metadata = {}
                    other.state = UNLOADED
                    other.loaded_at = None
                    other.load_seconds = None
                    self._lock.notify_all()

            if not busy_ids:
                return

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ModelBusyError(
                    "Cannot load model {!r}: {!r} still busy after {}s".format(
                        entry.spec.id, busy_ids, _BUSY_WAIT_TIMEOUT_S
                    )
                )
            with self._lock:
                self._lock.wait(timeout=min(remaining, 1.0))

    # ------------------------------------------------------------------
    # Unloading
    # ------------------------------------------------------------------
    def _unload(self, entry: _ModelEntry, if_idle: bool = False) -> None:
        runtime = None
        with self._lock:
            if entry.runtime is None or entry.state != READY:
                return
            if if_idle and entry.in_use > 0:
                return
            entry.state = UNLOADING
            entry.error = None
            runtime = entry.runtime

        if runtime is not None:
            try:
                runtime.unload()
            except Exception:
                pass

        with self._lock:
            entry.runtime = None
            entry.metadata = {}
            entry.state = UNLOADED
            entry.loaded_at = None
            entry.load_seconds = None
            self._lock.notify_all()

    def close(self) -> None:
        """Unload every loaded runtime and stop the idle-unload daemon."""
        self.stop_idle_unload()
        with self._lock:
            entries = [
                entry
                for entry in self._entries.values()
                if entry.runtime is not None and entry.state == READY
            ]
        for entry in entries:
            self._unload(entry)

    # ------------------------------------------------------------------
    # Idle unload daemon
    # ------------------------------------------------------------------
    def start_idle_unload(self) -> None:
        """Start the idle-unload daemon thread (no-op if already running)."""
        with self._lock:
            if self._idle_thread is not None and self._idle_thread.is_alive():
                return
            self._idle_stop.clear()
            self._idle_thread = threading.Thread(
                target=self._idle_loop,
                name="serving-idle-unload",
                daemon=True,
            )
            self._idle_thread.start()

    def stop_idle_unload(self) -> None:
        """Stop the idle-unload daemon thread (no-op if not running)."""
        with self._lock:
            self._idle_stop.set()
            thread = self._idle_thread
            self._idle_thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def _idle_loop(self) -> None:
        while not self._idle_stop.wait(timeout=_IDLE_UNLOAD_INTERVAL_S):
            self._unload_idle_if_due()

    def _unload_idle_if_due(self) -> None:
        now = time.monotonic()
        due: list[_ModelEntry] = []
        with self._lock:
            for entry in self._entries.values():
                if entry.state != READY or entry.runtime is None or entry.in_use > 0:
                    continue
                idle_s = entry.spec.load.get("idle_unload_s")
                if not idle_s:
                    continue
                try:
                    idle_s = float(idle_s)
                except (TypeError, ValueError):
                    continue
                reference = entry.last_used or entry.loaded_at or now
                if now - reference > idle_s:
                    due.append(entry)
        for entry in due:
            self._unload(entry, if_idle=True)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def check(self, all_models: bool = False) -> dict[str, list[str]]:
        """Validate models without loading weights; report problems by id."""
        problems: dict[str, list[str]] = {}
        for model_id, entry in self._entries.items():
            if not all_models and not entry.spec.enabled:
                continue
            issues = self._check_model(entry)
            if issues:
                problems[model_id] = issues
        return problems

    def _check_model(self, entry: _ModelEntry) -> list[str]:
        try:
            runtime = create_runtime(entry.spec, self._settings)
        except ImportError as exc:
            return ["Cannot import runtime: {}".format(exc)]
        except Exception as exc:
            return ["Cannot create runtime: {}".format(exc)]

        check_fn = getattr(runtime, "check", None)
        if check_fn is None:
            return []

        try:
            result = check_fn(entry.spec, self._settings)
        except ImportError as exc:
            return ["Missing module: {}".format(exc)]
        except Exception as exc:
            return ["Check failed: {}".format(exc)]
        return list(result) if result else []


__all__ = [
    "ModelRegistry",
    "DISABLED",
    "UNLOADED",
    "LOADING",
    "WARMING",
    "READY",
    "UNLOADING",
    "FAILED",
]