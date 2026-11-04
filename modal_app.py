# -*- coding: utf-8 -*-
"""Deploy SentimentX serving len Modal.

Deploy:
    modal deploy modal_app.py --env SentimentX
"""

from __future__ import annotations

import modal

APP_NAME = "SentimentX"
WEB_LABEL = "app"
VOLUME_NAME = "sentimentx-models"
GPU = ["L4", "A10G"]

QWEN_REPO = "Qwen/Qwen3-4B-Instruct-2507"
QWEN_DIR = "/app/data/models/Qwen3-4B-Instruct-2507"
CAFEBERT_REPO = "uitnlp/CafeBERT"
CAFEBERT_REVISION = "af76fcf2a04096b2b54b348a3e4eb48253c93c5d"
HF_HOME = "/root/.cache/huggingface"

app = modal.App(APP_NAME)

vol = modal.Volume.from_name(VOLUME_NAME, version=2)


def _pin_hf_ref() -> None:
    """Tao refs/main trong HF cache: tokenizer CafeBERT nap theo repo id, khong kem revision."""
    import os

    ref = os.path.join(HF_HOME, "hub", "models--uitnlp--CafeBERT", "refs", "main")
    if os.path.exists(ref):
        return
    os.makedirs(os.path.dirname(ref), exist_ok=True)
    with open(ref, "w", encoding="utf-8") as handle:
        handle.write(CAFEBERT_REVISION)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("torch", index_url="https://download.pytorch.org/whl/cu126")
    .pip_install_from_requirements("requirements-modal.txt")
    .run_commands(
        "HF_HOME={hf} python -c \"from huggingface_hub import snapshot_download; "
        "snapshot_download('{qwen}', local_dir='{qdir}')\"".format(
            hf=HF_HOME, qwen=QWEN_REPO, qdir=QWEN_DIR
        ),
        "HF_HOME={hf} python -c \"from huggingface_hub import snapshot_download; "
        "snapshot_download('{repo}', revision='{rev}')\"".format(
            hf=HF_HOME, repo=CAFEBERT_REPO, rev=CAFEBERT_REVISION
        ),
    )
    .add_local_dir("serving", "/app/serving")
    .add_local_dir("src", "/app/src")
    .add_local_dir("configs", "/app/configs")
)


@app.function(
    image=image,
    gpu=GPU,
    volumes={
        "/app/experiments": vol.with_mount_options(sub_path="/experiments"),
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
    import sys

    os.chdir("/app")
    sys.path.insert(0, "/app")
    os.environ["HF_HOME"] = HF_HOME
    os.environ["HF_HUB_OFFLINE"] = "1"
    _pin_hf_ref()
    from serving.app import app as fastapi_app

    return fastapi_app
