# -*- coding: utf-8 -*-
"""LLM serving runtime for the Qwen3-4B prompt model (``qwen3_4b_exp009``).

This runtime wraps the evaluation-time prompt pipeline (``src/evaluation/runner``
and ``src/preprocessing/qwen``) so the local Qwen3-4B-Instruct-2507 checkpoint can
serve aspect predictions through the same prompt, few-shot examples and system
block used to produce the experiment's published metrics.

``torch`` and ``transformers`` are imported lazily inside ``load`` so importing
this module stays cheap; the model is loaded with 4-bit quantization to fit a 6 GB
GPU. Prediction is done one text at a time to keep JSON parsing simple and
deterministic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from serving.errors import ModelFailedError, TextTooLongError
from serving.inference.base import AspectResult
from serving.specs import ModelSpec, Settings

from src.evaluation import parse, runner
from src.preprocessing import qwen

MODEL_ID = "qwen3-4b-instruct-2507"

_REQUIRED_FILES = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "generation_config.json",
    "model.safetensors.index.json",
)


def _shard_filenames(index_path: Path) -> list[str]:
    """Shard file names referenced by ``model.safetensors.index.json``."""
    with index_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    weight_map = data.get("weight_map") or {}
    return sorted({str(name) for name in weight_map.values()})


def _missing_model_files(model_dir: Path) -> list[str]:
    """Local checkpoint files that are absent, returned in a stable order."""
    missing: list[str] = []
    for name in _REQUIRED_FILES:
        if not (model_dir / name).is_file():
            missing.append(name)
    index_path = model_dir / "model.safetensors.index.json"
    if index_path.is_file():
        for name in _shard_filenames(index_path):
            if not (model_dir / name).is_file():
                missing.append(name)
    return missing


def _build_label_map(settings: Settings) -> dict[str, Any]:
    """Build the dataset-style label map expected by the prompt pipeline.

    ``qwen.build_inputs``/``qwen.encode`` read ``label_to_id`` to render the label
    guide and ``aspects`` to describe the task. Code 0 is the dataset's empty null
    label (not mentioned), not the serving name ``not_mentioned`` used for output
    labels, so the rendered prompt matches the experiment exactly.
    """
    aspects = [str(name) for name in settings.labels["aspects"]]
    codes = settings.labels["codes"]
    label_to_id: dict[str, int] = {}
    id_to_label: dict[str, str] = {}
    labels: list[str] = []
    for code, meta in sorted(codes.items(), key=lambda item: int(item[0])):
        code_int = int(code)
        key = "" if code_int == 0 else str(meta["name"])
        label_to_id[key] = code_int
        id_to_label[str(code_int)] = key
        if code_int != 0:
            labels.append(str(meta["name"]))
    return {
        "aspects": aspects,
        "labels": labels,
        "label_to_id": label_to_id,
        "id_to_label": id_to_label,
    }


class LLMRuntime:
    """Serving runtime for the Qwen3-4B prompt model."""

    def __init__(self) -> None:
        self.spec: Optional[ModelSpec] = None
        self.model_dir: Optional[Path] = None
        self.model: Any = None
        self.tokenizer: Any = None
        self.info: dict[str, Any] = {}
        self.aspects: list[str] = []
        self.codes: list[int] = [0, 1, 2]
        self.label_map: dict[str, Any] = {}
        self._code_meta: dict[int, dict[str, str]] = {}
        self.prompt_id: str = ""
        self.prompt_sha: str = ""
        self.quantization: str = "4bit"
        self.dtype_name: str = "float16"
        self.max_length: int = 2304
        self.max_new_tokens: int = 400
        self.do_sample: bool = False

    def load(self, spec: ModelSpec, settings: Settings) -> None:
        """Load the model, tokenizer and prompt described by ``spec``."""
        self.spec = spec
        runtime = spec.runtime

        model_dir = settings.root / runtime["model_dir"]
        self.model_dir = model_dir
        missing = _missing_model_files(model_dir)
        if missing:
            raise ModelFailedError(
                "Model directory {} is incomplete: {}".format(
                    model_dir, ", ".join(missing)
                ),
                details={"missing": missing},
            )

        if runtime.get("local_files_only"):
            os.environ["HF_HUB_OFFLINE"] = "1"

        self.quantization = str(runtime.get("quantization", "4bit"))
        self.dtype_name = str(runtime.get("dtype", "float16"))
        self.max_length = int(runtime.get("max_length", 2304))
        self.max_new_tokens = int(runtime.get("max_new_tokens", 400))
        self.do_sample = bool(runtime.get("do_sample", False))

        model, tokenizer, info = runner.load(
            quant=self.quantization,
            model_name=str(model_dir),
            dtype_name=self.dtype_name,
        )
        self.model = model
        self.tokenizer = tokenizer
        self.info = info
        tokenizer.padding_side = "left"

        prompt_path = str(settings.root / runtime["prompt"])
        examples = (
            str(settings.root / runtime["examples"]) if runtime.get("examples") else None
        )
        system = (
            str(settings.root / runtime["system"]) if runtime.get("system") else None
        )
        prompt = qwen.load_prompt(prompt_path, examples=examples, system=system)
        qwen.use_prompt(prompt)
        self.prompt_id = str(prompt.name)
        self.prompt_sha = str(prompt.sha)

        self.aspects = [str(name) for name in settings.labels["aspects"]]
        self.codes = [0, 1, 2]
        self.label_map = _build_label_map(settings)
        self._code_meta = {
            int(code): dict(meta) for code, meta in settings.labels["codes"].items()
        }

    def warmup(self) -> None:
        """Run one short prediction to prime CUDA and the tokenizer."""
        self.predict(["son đẹp"])

    def predict(
        self, texts: list[str], include_probs: bool = True
    ) -> list[dict[str, AspectResult]]:
        """Predict aspects for each text, one text at a time.

        ``include_probs`` is accepted for interface parity; the LLM returns no
        probability distribution, so ``confidence`` and ``probs`` stay ``None``.
        """
        generation = runner.settings(
            quant=self.quantization,
            max_new_tokens=self.max_new_tokens,
            do_sample=self.do_sample,
            seed=42,
        )
        results: list[dict[str, AspectResult]] = []
        for text in texts:
            encoded = qwen.encode(
                [text],
                aspects=self.aspects,
                label_map=self.label_map,
                prompt_name=self.prompt_id,
                model_id=MODEL_ID,
            )
            length = len(encoded[0]) if encoded and encoded[0] else 0
            if length > self.max_length:
                raise TextTooLongError(
                    "Text needs {} tokens, exceeding max_length {}".format(
                        length, self.max_length
                    ),
                    details={"tokens": length, "max_length": self.max_length},
                )
            inputs = qwen.build_inputs(
                [text],
                max_length=self.max_length,
                aspects=self.aspects,
                label_map=self.label_map,
                prompt_name=self.prompt_id,
                model_id=MODEL_ID,
            )
            answers, _lengths, _elapsed = runner.generate(
                inputs, self.model, self.tokenizer, generation
            )
            labels, _info = parse.parse_labels(
                answers[0], self.aspects, self.codes, require_all=True
            )
            evidence = parse.parse_evidence(answers[0], self.aspects)
            results.append(self._aspect_results(labels, evidence))
        return results

    def _aspect_results(
        self, labels: dict[str, int], evidence: Optional[dict] = None
    ) -> dict[str, AspectResult]:
        """Convert parsed codes into per-aspect ``AspectResult`` objects."""
        evidence = evidence or {}
        out: dict[str, AspectResult] = {}
        for aspect in self.aspects:
            entry = evidence.get(aspect) or {}
            quote = entry.get("quote")
            reason = entry.get("reason")
            code = labels.get(aspect)
            if code in self.codes:
                meta = self._code_meta.get(int(code), {})
                out[aspect] = AspectResult(
                    label=str(meta.get("name", "unknown")),
                    label_vi=str(meta.get("vi", "Không đọc được")),
                    code=int(code),
                    confidence=None,
                    probs=None,
                    quote=quote,
                    reason=reason,
                )
            else:
                out[aspect] = AspectResult(
                    label="unknown",
                    label_vi="Không đọc được",
                    code=None,
                    confidence=None,
                    probs=None,
                    quote=quote,
                    reason=reason,
                )
        return out

    def unload(self) -> None:
        """Release the model and tokenizer and free CUDA memory."""
        self.model = None
        self.tokenizer = None
        self.info = {}
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _device(self) -> str:
        if self.model is None:
            return "auto"
        try:
            return str(next(self.model.parameters()).device)
        except (StopIteration, AttributeError):
            return "auto"

    @property
    def metadata(self) -> dict[str, Any]:
        """Describe the runtime for the registry and API responses."""
        return {
            "id": self.spec.id if self.spec else "",
            "kind": "llm",
            "device": self._device(),
            "max_length": self.max_length,
            "quantization": self.quantization,
            "prompt_id": self.prompt_id,
            "prompt_sha": self.prompt_sha,
            "model_dir": str(self.model_dir) if self.model_dir else "",
            "model_hash": self.spec.expected.get("config_hash", "") if self.spec else "",
        }

    @classmethod
    def check(cls, spec: ModelSpec, settings: Settings) -> list[str]:
        """Verify local artifacts without loading model weights.

        Returns a list of human-readable problems; an empty list means the model
        directory, prompt files and prompt/examples/system hash prefixes are all
        consistent with ``configs/serving.yaml``.
        """
        problems: list[str] = []
        runtime = spec.runtime

        model_dir = settings.root / runtime["model_dir"]
        for name in _missing_model_files(model_dir):
            problems.append("missing model file: {}".format(model_dir / name))

        prompt_rel = runtime.get("prompt")
        examples_rel = runtime.get("examples")
        system_rel = runtime.get("system")
        prompt_path = settings.root / prompt_rel if prompt_rel else None
        examples_path = settings.root / examples_rel if examples_rel else None
        system_path = settings.root / system_rel if system_rel else None

        for label, path in (
            ("prompt", prompt_path),
            ("examples", examples_path),
            ("system", system_path),
        ):
            if path is not None and not path.is_file():
                problems.append("missing {} file: {}".format(label, path))

        if prompt_path is not None and prompt_path.is_file():
            try:
                prompt = qwen.load_prompt(
                    str(prompt_path),
                    examples=str(examples_path) if examples_path else None,
                    system=str(system_path) if system_path else None,
                )
                cls._check_sha(
                    problems, "prompt_sha", prompt.sha, runtime.get("prompt_sha")
                )
                if "examples" in prompt.placeholders:
                    cls._check_sha(
                        problems,
                        "examples_sha",
                        (prompt.examples_info() or {}).get("sha"),
                        runtime.get("examples_sha"),
                    )
                if "system_prompt" in prompt.placeholders:
                    cls._check_sha(
                        problems,
                        "system_sha",
                        (prompt.system_info() or {}).get("sha"),
                        runtime.get("system_sha"),
                    )
            except Exception as exc:
                problems.append("failed to load prompt: {}".format(exc))
        return problems

    @staticmethod
    def _check_sha(
        problems: list[str], field: str, actual: Any, expected: Any
    ) -> None:
        if not expected:
            return
        prefix = str(actual or "")[:8]
        if prefix != str(expected):
            problems.append(
                "{} mismatch: expected {}, got {}".format(field, expected, prefix)
            )