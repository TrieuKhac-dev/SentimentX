# -*- coding: utf-8 -*-
"""FastAPI application for the SentimentX ABSA serving layer."""

from __future__ import annotations

import argparse
import asyncio
import functools
import hashlib
import json
import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

import uvicorn

from . import __version__
from .cache import TTLCache
from .config import load_settings
from .errors import APIError, ModelDisabledError, ModelNotFoundError, error_payload
from .middleware import (
    api_key_middleware,
    body_limit_middleware,
    request_id_middleware,
    security_headers_middleware,
)
from .schemas import PredictRequest, PredictResponse

logger = logging.getLogger("serving")

_SERVING_DIR = Path(__file__).resolve().parent


def _import_model_registry():
    """Import ``ModelRegistry`` lazily so importing this module never loads models."""
    from .registry import ModelRegistry

    return ModelRegistry


def _import_load_coordinator():
    """Import ``ModelLoadCoordinator`` lazily so app import stays lightweight."""
    from .load_coordinator import ModelLoadCoordinator

    return ModelLoadCoordinator


class _LoadModelDisabledError(ModelDisabledError):
    """409 variant of the disabled-model error used by the load endpoint."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.status_code = 409


def _aspect_to_dict(aspect: Any) -> Dict[str, Any]:
    if isinstance(aspect, dict):
        return {
            "label": aspect.get("label", ""),
            "label_vi": aspect.get("label_vi", ""),
            "code": aspect.get("code"),
            "confidence": aspect.get("confidence"),
            "probs": aspect.get("probs"),
            "quote": aspect.get("quote"),
            "reason": aspect.get("reason"),
        }
    return {
        "label": getattr(aspect, "label", ""),
        "label_vi": getattr(aspect, "label_vi", ""),
        "code": getattr(aspect, "code", None),
        "confidence": getattr(aspect, "confidence", None),
        "probs": getattr(aspect, "probs", None),
        "quote": getattr(aspect, "quote", None),
        "reason": getattr(aspect, "reason", None),
    }


def _cache_key(model_id: str, version: str, text: str, include_probs: bool) -> str:
    raw = "\x00".join((model_id, version or "", text, "1" if include_probs else "0"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def create_app(settings=None, registry=None) -> FastAPI:
    """Build the FastAPI application.

    ``settings`` and ``registry`` may be injected for tests; when omitted the
    configuration is loaded from ``configs/serving.yaml`` and the registry is
    constructed inside the lifespan (so importing this module never loads models).
    """
    if settings is None:
        settings = load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        reg = registry
        if reg is None:
            reg = _import_model_registry()(settings)
        app.state.registry = reg
        load_coordinator = _import_load_coordinator()(reg)
        app.state.load_coordinator = load_coordinator
        load_coordinator.start()

        if settings.server.get("eager_default", True) and settings.default_model:
            try:
                reg.predict(settings.default_model, ["__warmup__"], include_probs=False)
            except Exception:
                logger.warning("Eager warmup of default model failed", exc_info=True)

        if hasattr(reg, "start_idle_unload"):
            reg.start_idle_unload()
        try:
            yield
        finally:
            load_coordinator.stop()
            if hasattr(reg, "stop_idle_unload"):
                reg.stop_idle_unload()
            if hasattr(reg, "close"):
                reg.close()

    app = FastAPI(title="SentimentX ABSA Serving", version=__version__, lifespan=lifespan)

    app.state.settings = settings
    app.state.registry = registry
    app.state.started_at = time.time()

    cache_cfg = settings.raw.get("cache") or {}
    app.state.cache = (
        TTLCache(
            max_entries=int(cache_cfg.get("max_entries", 512)),
            ttl_s=float(cache_cfg.get("ttl_s", 900)),
        )
        if cache_cfg.get("enabled", False)
        else None
    )

    max_body_bytes = int(settings.server.get("max_body_bytes", 1048576))

    api_key = os.environ.get("SERVING_API_KEY") or ""
    if api_key:
        app.add_middleware(
            BaseHTTPMiddleware, dispatch=functools.partial(api_key_middleware, api_key=api_key)
        )
    app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers_middleware)
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=functools.partial(body_limit_middleware, max_body_bytes=max_body_bytes),
    )
    app.add_middleware(BaseHTTPMiddleware, dispatch=request_id_middleware)

    templates = Jinja2Templates(directory=str(_SERVING_DIR / "templates"))
    static_dir = _SERVING_DIR / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def index(request: Request) -> Any:
        reg = request.app.state.registry
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "models": reg.list_models(),
                "default_model": reg.default_model,
                "app_version": __version__,
            },
        )

    @app.get("/health")
    async def health(request: Request) -> Dict[str, Any]:
        reg = request.app.state.registry
        models = reg.list_models()
        ready = any(bool(m.get("enabled")) for m in models)

        gpu: Optional[Dict[str, Any]] = None
        try:
            import torch
        except Exception:
            torch = None
        if torch is not None:
            try:
                if torch.cuda.is_available():
                    gpu = {
                        "available": True,
                        "device_count": torch.cuda.device_count(),
                        "name": torch.cuda.get_device_name(0),
                    }
                else:
                    gpu = {"available": False, "device_count": 0}
            except Exception:
                gpu = None

        return {
            "status": "ok" if ready else "unavailable",
            "ready": ready,
            "version": __version__,
            "models": reg.status(),
            "gpu": gpu,
        }

    @app.get("/models")
    async def list_models(request: Request) -> Dict[str, Any]:
        return {"models": request.app.state.registry.list_models()}

    @app.post("/models/{model_id}/load", status_code=202)
    async def load_model(request: Request, model_id: str) -> JSONResponse:
        reg = request.app.state.registry

        infos = {m["id"]: m for m in reg.list_models()}
        if model_id not in infos:
            raise ModelNotFoundError("Unknown model: {!r}".format(model_id))
        if not infos[model_id].get("enabled"):
            raise _LoadModelDisabledError(
                "Model {!r} is disabled.".format(model_id)
            )

        coordinator = getattr(request.app.state, "load_coordinator", None)
        if coordinator is None:
            coordinator = _import_load_coordinator()(reg)
            coordinator.start()
            request.app.state.load_coordinator = coordinator

        payload = await asyncio.to_thread(coordinator.request, model_id)
        return JSONResponse(status_code=202, content=payload)

    async def _run_predict(
        request: Request, req: PredictRequest, forced_model: Optional[str] = None
    ) -> PredictResponse:
        reg = request.app.state.registry
        model_id = forced_model or req.model or reg.default_model

        infos = {m["id"]: m for m in reg.list_models()}
        if model_id not in infos:
            raise ModelNotFoundError("Unknown model: {!r}".format(model_id))
        info = infos[model_id]
        if not info.get("enabled"):
            raise ModelDisabledError("Model {!r} is disabled.".format(model_id))

        texts: List[str] = [req.text] if req.text is not None else list(req.texts)
        version = info.get("version") or ""
        model_hash = info.get("hash") or ""
        device = info.get("device") or ""

        cache = request.app.state.cache
        cache_key = None
        if cache is not None and len(texts) == 1:
            cache_key = _cache_key(model_id, version, texts[0], req.include_probs)
            cached = cache.get(cache_key)
            if cached is not None:
                return PredictResponse(
                    request_id=_request_id(request),
                    model=model_id,
                    model_version=version,
                    model_hash=model_hash,
                    device=device,
                    latency_ms=0.0,
                    batch_size=1,
                    results=cached,
                    cache_hit=True,
                )

        start = time.perf_counter()
        raw_results = await asyncio.to_thread(reg.predict, model_id, texts, req.include_probs)
        latency_ms = (time.perf_counter() - start) * 1000.0

        results = list(raw_results)
        if len(results) > len(texts):
            results = results[: len(texts)]
        elif len(results) < len(texts):
            results.extend([{} for _ in range(len(texts) - len(results))])

        items: List[Dict[str, Any]] = []
        for text, aspects in zip(texts, results):
            converted = {
                key: _aspect_to_dict(value) for key, value in (aspects or {}).items()
            }
            readable = all(pred.get("code") is not None for pred in converted.values())
            items.append({"text": text, "aspects": converted, "readable": readable})

        if cache_key is not None:
            cache.set(cache_key, items)

        return PredictResponse(
            request_id=_request_id(request),
            model=model_id,
            model_version=version,
            model_hash=model_hash,
            device=device,
            latency_ms=round(latency_ms, 3),
            batch_size=len(texts),
            results=items,
            cache_hit=False,
        )

    @app.post("/predict", response_model=PredictResponse)
    async def predict(request: Request, req: PredictRequest) -> PredictResponse:
        return await _run_predict(request, req)

    @app.post("/predict/hybrid", include_in_schema=False)
    async def predict_hybrid() -> JSONResponse:
        return JSONResponse(
            {
                "error": {
                    "code": "hybrid_not_implemented",
                    "message": "Hybrid fusion chưa được bật trong P0.",
                }
            },
            status_code=501,
        )

    @app.post("/predict/{model_id}", response_model=PredictResponse)
    async def predict_model(
        request: Request, model_id: str, req: PredictRequest
    ) -> PredictResponse:
        return await _run_predict(request, req, forced_model=model_id)

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            {
                "error": error_payload(
                    exc.code, exc.message, exc.details, _request_id(request)
                )
            },
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {key: value for key, value in item.items() if key not in ("input", "ctx", "url")}
            for item in exc.errors()
        ]
        return JSONResponse(
            {
                "error": error_payload(
                    "validation_error",
                    "Invalid request.",
                    {"errors": errors},
                    _request_id(request),
                )
            },
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return JSONResponse(
            {
                "error": error_payload(
                    "internal_error", "Internal server error.", None, _request_id(request)
                )
            },
            status_code=500,
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="SentimentX ABSA serving layer")
    parser.add_argument("--config", default=None, help="Path to serving.yaml")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--model", default=None, help="Comma-separated model ids to enable")
    parser.add_argument("--default", dest="default_model", default=None, help="Force a default model id")
    parser.add_argument("--fake", action="store_true", help="Allow an empty set of enabled models")
    parser.add_argument("--check", action="store_true", help="Check enabled models then exit")
    parser.add_argument("--check-all", action="store_true", help="Check all models then exit")
    parser.add_argument("--log-level", default=None)

    args = parser.parse_args()

    settings = load_settings(
        args.config,
        models_override=args.model,
        default_override=args.default_model,
        fake=args.fake,
    )

    if args.check or args.check_all:
        reg = _import_model_registry()(settings)
        result = reg.check(all_models=args.check_all)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if hasattr(reg, "close"):
            reg.close()
        has_errors = any(bool(errors) for errors in result.values())
        sys.exit(2 if has_errors else 0)
        return

    app = create_app(settings)

    host = args.host or str(settings.server.get("host", "127.0.0.1"))
    port = args.port if args.port is not None else int(settings.server.get("port", 8000))
    log_level = args.log_level or str(settings.server.get("log_level", "info"))

    uvicorn.run(app, host=host, port=port, workers=1, log_level=log_level)


app = create_app()


if __name__ == "__main__":
    main()
