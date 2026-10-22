# -*- coding: utf-8 -*-
"""Latest-wins coordinator for background model loads.

A single daemon worker thread loads the most recently requested model through
``ModelRegistry.preload``. Requests return immediately with a generation number
and the model's current state, so an API caller can preload a model without
running a prediction.

A load already in progress cannot be cancelled: model loading and warmup are
hardware work with no safe mid-flight abort. If a newer request arrives while a
model is loading, the worker lets that load finish, skips any intermediate
queued models, and then loads the newest request. This is cooperative
latest-wins, not hard cancellation. Failures are recorded once and do not retry
in a loop; a later request starts a new attempt.
"""

from __future__ import annotations

import threading
from typing import Optional

_QUEUED = "QUEUED"
_LOADING = "LOADING"
_READY = "READY"
_FAILED = "FAILED"
_QUEUED_REGISTRY_STATES = {"UNLOADED", "UNLOADING", "DISABLED"}


class ModelLoadCoordinator:
    """Serialize background model loads with latest-wins semantics."""

    def __init__(self, registry) -> None:
        self._registry = registry
        self._cond = threading.Condition()
        self._thread: Optional[threading.Thread] = None
        self._stop = False
        self._generation = 0
        self._handled_generation = 0
        self._requested_model: Optional[str] = None
        self._last_state = _QUEUED
        self._last_error: Optional[str] = None

    def start(self) -> None:
        """Start the worker thread (no-op if it is already running)."""
        with self._cond:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop = False
            self._thread = threading.Thread(
                target=self._run,
                name="serving-model-load",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop the worker thread and wait briefly for it to exit."""
        with self._cond:
            self._stop = True
            thread = self._thread
            self._cond.notify_all()
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)

    def request(self, model_id: str) -> dict:
        """Queue ``model_id`` and return its generation and current state."""
        with self._cond:
            self._generation += 1
            generation = self._generation
            self._requested_model = model_id
            state = self._registry_state(model_id)
            self._last_state = state
            self._last_error = None
            if state == _READY:
                self._handled_generation = generation
            self._cond.notify_all()
            return {
                "model_id": model_id,
                "generation": generation,
                "state": state,
            }

    def status(self) -> dict:
        """Return the coordinator's latest request, state, and error."""
        with self._cond:
            return {
                "model_id": self._requested_model,
                "generation": self._generation,
                "state": self._last_state,
                "error": self._last_error,
            }

    def _registry_state(self, model_id: str) -> str:
        status_fn = getattr(self._registry, "status", None)
        if status_fn is None:
            return _QUEUED
        try:
            info = (status_fn() or {}).get(model_id) or {}
        except Exception:
            return _QUEUED
        state = str(info.get("state") or "UNLOADED")
        if state in _QUEUED_REGISTRY_STATES:
            return _QUEUED
        return state

    def _run(self) -> None:
        while True:
            with self._cond:
                while not self._stop and self._generation <= self._handled_generation:
                    self._cond.wait()
                if self._stop:
                    return
                generation = self._generation
                model_id = self._requested_model

            if model_id is None:
                self._mark_handled(generation)
                continue

            if self._registry_state(model_id) == _READY:
                self._mark_handled(generation)
                continue

            with self._cond:
                if self._generation == generation and self._requested_model == model_id:
                    self._last_state = _LOADING

            try:
                self._registry.preload(model_id)
            except Exception as exc:
                self._record_failure(model_id, generation, exc)
                continue
            self._record_success(model_id, generation)

    def _mark_handled(self, generation: int) -> None:
        with self._cond:
            self._handled_generation = max(self._handled_generation, generation)
            self._cond.notify_all()

    def _record_success(self, model_id: str, generation: int) -> None:
        with self._cond:
            self._handled_generation = max(self._handled_generation, generation)
            if self._generation == generation or self._requested_model == model_id:
                self._last_state = _READY
                self._last_error = None
            self._cond.notify_all()

    def _record_failure(self, model_id: str, generation: int, exc: Exception) -> None:
        error = str(exc) or exc.__class__.__name__
        with self._cond:
            self._handled_generation = max(self._handled_generation, generation)
            self._last_error = error
            if self._generation == generation or self._requested_model == model_id:
                self._last_state = _FAILED
            self._cond.notify_all()


__all__ = ["ModelLoadCoordinator"]