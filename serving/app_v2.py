# -*- coding: utf-8 -*-
"""Second-generation UI entrypoint for the SentimentX ABSA serving layer."""

from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse

from .app import create_app

app = create_app()


@app.get("/predict-v2", include_in_schema=False)
async def predict_v2() -> FileResponse:
    return FileResponse(
        Path(__file__).resolve().parent / "static" / "v2" / "index.html",
        headers={"Cache-Control": "no-store"},
    )