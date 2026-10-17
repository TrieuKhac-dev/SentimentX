# -*- coding: utf-8 -*-
"""Encoder runtime cho các model ``kind: encoder`` (CafeBERT LoRA).

Nạp checkpoint LoRA (``model/best``) của đường huấn luyện encoder, gắn lên base
``uitnlp/CafeBERT``, rồi suy luận 7 khía cạnh x 3 mã nhãn cho từng review.

Torch/transformers/peft được import BÊN TRONG hàm (giống ``src/training/lora.py``) để
``check()`` chạy được trên máy chưa cài chúng - nó chỉ đọc file và thăm dò HF cache.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from serving.errors import ModelFailedError
from serving.inference.base import AspectResult
from serving.specs import ModelSpec, Settings, resolve_path

REQUIRED_FILES = (
    "adapter_model.safetensors",
    "adapter_config.json",
    "head.pt",
    "head_config.json",
)

EXPECTED_N_ASPECTS = 7
EXPECTED_N_CODES = 3
EXPECTED_CODES = (0, 1, 2)

DOWNLOAD_HINT = "python scripts/download_encoder.py"


class EncoderRuntime:
    """Runtime dùng chung cho mọi model ``kind: encoder`` (LoRA)."""

    kind = "encoder"

    def __init__(self) -> None:
        self.model = None
        self.head = None
        self.device = "cpu"
        self.max_length = 256
        self.segmenter = "none"
        self.head_config: dict = {}
        self._code_labels: dict = {}
        self._spec: Optional[ModelSpec] = None
        self._checkpoint = ""
        self._base = ""
        self._model_hash = ""

    # --- load ---------------------------------------------------------

    def load(self, spec: ModelSpec, settings: Settings) -> None:
        ckpt = resolve_path(settings.root, spec.runtime.get("checkpoint", ""))
        missing = [name for name in REQUIRED_FILES if not (ckpt / name).is_file()]
        if missing:
            raise ModelFailedError(
                "encoder {}: checkpoint {} thiếu file: {}".format(
                    spec.id, ckpt, ", ".join(missing)
                ),
                details={"checkpoint": str(ckpt), "missing": missing},
            )

        adapter_config = self._read_json(ckpt / "adapter_config.json")
        head_config = self._read_json(ckpt / "head_config.json")
        head_problems = self._head_problems(spec, settings, head_config)
        if head_problems:
            raise ModelFailedError(
                "encoder {}: head_config.json không khớp: {}".format(
                    spec.id, "; ".join(head_problems)
                ),
                details={"problems": head_problems},
            )

        base_value = str(spec.runtime.get("base") or "")
        if not base_value:
            raise ModelFailedError("encoder {}: thiếu `runtime.base`.".format(spec.id))
        base_path = self._resolve_base(spec, base_value)
        device = self._resolve_device(spec)

        found = {
            "dtype": str(spec.runtime.get("dtype") or "float16"),
            "quantization": "none",
            "lora_r": int(adapter_config.get("r") or 0),
            "lora_alpha": int(adapter_config.get("lora_alpha") or 0),
            "lora_dropout": float(adapter_config.get("lora_dropout") or 0.0),
            "target_modules": [
                str(item) for item in adapter_config.get("target_modules") or []
            ],
            "head_aspect_marker": bool(head_config.get("aspect_marker", False)),
            "max_length": int(spec.runtime.get("max_length") or 256),
            "segmenter": str(spec.runtime.get("segmenter") or "none"),
            "source": base_path,
            "checkpoint": base_value,
        }

        from src.training import lora

        model, head = lora.build_model(
            found, device, adapter_dir=str(ckpt), source=base_path, trainable=False
        )
        if device == "cuda":
            model = model.to(device)
        model.eval()

        self.model = model
        self.head = head
        self.device = device
        self.max_length = int(found["max_length"])
        self.segmenter = str(found["segmenter"])
        self.head_config = head_config
        self._code_labels = self._build_code_labels(settings)
        self._spec = spec
        self._checkpoint = str(ckpt)
        self._base = base_value
        self._model_hash = str((spec.expected or {}).get("config_hash") or "")

    def _read_json(self, path: Path) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle) or {}
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelFailedError(
                "encoder: không đọc được {}: {}".format(path, exc),
                details={"path": str(path)},
            ) from exc

    @classmethod
    def _head_problems(cls, spec: ModelSpec, settings: Settings, head_config: dict) -> List[str]:
        problems = []
        if int(head_config.get("n_aspects") or 0) != EXPECTED_N_ASPECTS:
            problems.append("n_aspects != {}".format(EXPECTED_N_ASPECTS))
        if int(head_config.get("n_codes") or 0) != EXPECTED_N_CODES:
            problems.append("n_codes != {}".format(EXPECTED_N_CODES))
        if [int(code) for code in head_config.get("codes") or []] != list(EXPECTED_CODES):
            problems.append("codes != {}".format(list(EXPECTED_CODES)))
        if list(head_config.get("aspects") or []) != list(settings.labels.get("aspects") or []):
            problems.append("aspects khác settings.labels['aspects']")
        if bool(head_config.get("aspect_marker", False)):
            problems.append("aspect_marker phải là false")
        return problems

    def _resolve_base(self, spec: ModelSpec, base_value: str) -> str:
        path = Path(base_value)
        if path.exists():
            return str(path)
        try:
            from huggingface_hub import snapshot_download

            return snapshot_download(
                repo_id=base_value,
                revision=spec.runtime.get("base_revision"),
                local_files_only=bool(spec.runtime.get("local_files_only", True)),
            )
        except Exception as exc:
            raise ModelFailedError(
                "encoder {}: base model {!r} chưa có (đường dẫn không tồn tại và HF cache "
                "thiếu). Chạy: {}".format(spec.id, base_value, DOWNLOAD_HINT),
                details={"error": str(exc)},
            ) from exc

    def _resolve_device(self, spec: ModelSpec) -> str:
        value = str(spec.load.get("device") or "auto").strip().lower()
        if value != "auto":
            return value
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"

    def _build_code_labels(self, settings: Settings) -> dict:
        labels = {}
        for code, info in (settings.labels.get("codes") or {}).items():
            info = dict(info or {})
            labels[int(code)] = {
                "name": str(info.get("name") or ""),
                "vi": str(info.get("vi") or ""),
            }
        return labels

    def _code_name(self, code: int) -> str:
        return self._code_labels.get(int(code), {}).get("name", "")

    def _code_vi(self, code: int) -> str:
        return self._code_labels.get(int(code), {}).get("vi", "")

    # --- predict ------------------------------------------------------

    def warmup(self) -> None:
        self.predict(["son đẹp"], include_probs=True)

    def predict(self, texts: List[str], include_probs: bool = True) -> List[dict]:
        import torch
        from src.preprocessing import cafebert

        inputs = cafebert.build_inputs(
            list(texts), max_length=self.max_length, segmenter=self.segmenter
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.inference_mode():
            logits = self.model(**inputs)
        probabilities = torch.softmax(logits.float(), dim=-1).cpu()

        codes = [int(code) for code in self.head_config["codes"]]
        aspects = [str(name) for name in self.head_config["aspects"]]

        results = []
        for batch_index in range(probabilities.size(0)):
            item = {}
            for aspect_index, aspect in enumerate(aspects):
                position = int(probabilities[batch_index, aspect_index].argmax().item())
                code = int(codes[position])
                confidence = float(probabilities[batch_index, aspect_index, position].item())
                probs = None
                if include_probs:
                    probs = {
                        self._code_name(codes[i]): float(
                            probabilities[batch_index, aspect_index, i].item()
                        )
                        for i in range(len(codes))
                    }
                item[aspect] = AspectResult(
                    label=self._code_name(code),
                    label_vi=self._code_vi(code),
                    code=code,
                    confidence=confidence,
                    probs=probs,
                )
            results.append(item)
        return results

    # --- unload / metadata -------------------------------------------

    def unload(self) -> None:
        self.model = None
        self.head = None
        if self.device == "cuda":
            import torch

            torch.cuda.empty_cache()

    @property
    def metadata(self) -> dict:
        return {
            "id": self._spec.id if self._spec else "",
            "kind": self.kind,
            "device": self.device,
            "max_length": self.max_length,
            "segmenter": self.segmenter,
            "checkpoint": self._checkpoint,
            "base": self._base,
            "model_hash": self._model_hash,
        }

    # --- check --------------------------------------------------------

    @classmethod
    def check(cls, spec: ModelSpec, settings: Settings) -> List[str]:
        problems: List[str] = []
        ckpt = resolve_path(settings.root, spec.runtime.get("checkpoint", ""))
        for name in REQUIRED_FILES:
            if not (ckpt / name).is_file():
                problems.append("encoder {}: thiếu {}".format(spec.id, ckpt / name))

        head_path = ckpt / "head_config.json"
        if head_path.is_file():
            try:
                with open(head_path, "r", encoding="utf-8") as handle:
                    head_config = json.load(handle) or {}
            except (OSError, json.JSONDecodeError) as exc:
                problems.append(
                    "encoder {}: không đọc được head_config.json: {}".format(spec.id, exc)
                )
            else:
                problems.extend(cls._head_problems(spec, settings, head_config))

        base_value = str(spec.runtime.get("base") or "")
        if not base_value:
            problems.append("encoder {}: thiếu `runtime.base`.".format(spec.id))
        else:
            base_path = Path(base_value)
            if not base_path.exists():
                try:
                    from huggingface_hub import snapshot_download

                    snapshot_download(
                        repo_id=base_value,
                        revision=spec.runtime.get("base_revision"),
                        local_files_only=bool(spec.runtime.get("local_files_only", True)),
                    )
                except Exception as exc:
                    problems.append(
                        "encoder {}: base model {!r} chưa có (chạy `{}`): {}".format(
                            spec.id, base_value, DOWNLOAD_HINT, exc
                        )
                    )
        return problems