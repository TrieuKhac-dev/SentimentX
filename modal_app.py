# -*- coding: utf-8 -*-
"""Deploy SentimentX serving len Modal.

Deploy:
    modal deploy modal_app.py --env <environment>
"""

from __future__ import annotations

import modal

APP_NAME = "SentimentX"
WEB_LABEL = "app"
VOLUME_NAME = "sentimentx-models"
GPU = "L4"

app = modal.App(APP_NAME)

vol = modal.Volume.from_name(VOLUME_NAME, version=2)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch", index_url="https://download.pytorch.org/whl/cu126")
    .pip_install_from_requirements("requirements-modal.txt")
    .add_local_dir("serving", "/app/serving")
    .add_local_dir("src", "/app/src")
    .add_local_dir("configs", "/app/configs")
)


@app.function(
    image=image,
    gpu=GPU,
    volumes={
        "/app/experiments": vol.with_mount_options(sub_path="/experiments"),
        "/app/data": vol.with_mount_options(sub_path="/data"),
        "/hf-cache": vol.with_mount_options(sub_path="/hf-cache"),
    },
    min_containers=0,
    max_containers=1,
    scaledown_window=120,
    timeout=600,
)
@modal.concurrent(max_inputs=1)
@modal.asgi_app(label=WEB_LABEL)
def web():
    import os

    os.chdir("/app")
    os.environ["HF_HOME"] = "/hf-cache"
    from serving.app import app as fastapi_app

    return fastapi_app