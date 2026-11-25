# -*- coding: utf-8 -*-
"""Chạy đánh giá ABSA thực tế (Shopee) cho một mô hình serving, chỉ suy luận.

Hàm công khai duy nhất là :func:`run_experiment`. Không huấn luyện, không sửa trọng số,
không ghi vào thư mục kết quả chính thức của ``experiments/``.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

ASPECTS = ("stayingpower", "texture", "smell", "price", "colour", "shipping", "packing")
LABELS = {0: "not_mentioned", 1: "positive", 2: "negative"}
TASK = {"label_space": "binary", "neutral_policy": "drop", "not_mentioned": "separate"}
SCORER_NAMES = ["accuracy", "aspect_detection", "prf", "aggregate"]
PAPER_NAMES = ["accuracy", "prf", "aggregate"]

CAFEBERT_CHECKPOINT_FILES = (
    "adapter_model.safetensors",
    "adapter_config.json",
    "head.pt",
    "head_config.json",
)
CAFEBERT_BASE_FILES = ("config.json",)
QWEN_MODEL_FILES = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "generation_config.json",
    "model.safetensors.index.json",
)

_MODEL_DEFAULTS = {
    "cafebert_exp027": {"chunk": 16, "include_probs": True, "family": "cafebert"},
    "qwen3_4b_exp009": {"chunk": 1, "include_probs": False, "family": "qwen"},
}

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from serving.config import load_settings
from serving.registry import ModelRegistry
import src.evaluation.scorers as scorers


def _as_path(value: Optional[Any]) -> Optional[Path]:
    if value is None or str(value).strip() == "":
        return None
    return Path(value).expanduser()


def _unique_paths(values) -> list[Path]:
    seen, out = set(), []
    for item in values:
        path = _as_path(item)
        if path is None:
            continue
        key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _missing_files(directory: Path, required) -> list[str]:
    return [name for name in required if not (directory / name).is_file()]


def _qwen_missing(directory: Path) -> list[str]:
    missing = _missing_files(directory, QWEN_MODEL_FILES)
    index = directory / "model.safetensors.index.json"
    if index.is_file():
        try:
            payload = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            missing.append("model.safetensors.index.json ({})".format(exc))
            return missing
        shards = {str(name) for name in (payload.get("weight_map") or {}).values()}
        for shard in sorted(shards):
            if not (directory / shard).is_file():
                missing.append(shard)
    return missing


def _pick_artifact(candidates, missing_fn, label, model_id, instructions) -> Path:
    candidates = _unique_paths(candidates)
    for candidate in candidates:
        if candidate.is_dir() and not missing_fn(candidate):
            return candidate

    lines = []
    for candidate in candidates:
        if not candidate.is_dir():
            lines.append("  - {} (không có thư mục)".format(candidate))
            continue
        missing = missing_fn(candidate)
        if missing:
            lines.append("  - {} (thiếu: {})".format(candidate, ", ".join(missing)))
        else:
            lines.append("  - {}".format(candidate))
    raise FileNotFoundError(
        "Không tìm thấy {} cho mô hình '{}'.\nĐã thử:\n{}\n{}".format(
            label, model_id, "\n".join(lines), instructions
        )
    )


def _pick_optional(candidates, missing_fn) -> Optional[Path]:
    for candidate in _unique_paths(candidates):
        if candidate.is_dir() and not missing_fn(candidate):
            return candidate
    return None


def _prepare_runtime(spec, model_id: str, drive_root: Optional[Path], code_dir: Path) -> dict:
    family = _MODEL_DEFAULTS[model_id]["family"]
    resolved = {}

    if family == "cafebert":
        checkpoint_candidates = []
        if drive_root is not None:
            checkpoint_candidates.extend([
                drive_root / "models" / "cafebert_exp027" / "best",
                drive_root / "models" / "cafebert_exp027",
            ])
        configured = str(spec.runtime.get("checkpoint") or "").strip()
        if configured:
            configured_path = Path(configured)
            checkpoint_candidates.append(
                configured_path if configured_path.is_absolute() else code_dir / configured_path
            )
        checkpoint_candidates.extend(
            sorted(code_dir.glob("experiments/cafebert/lora/exp027/results/*/model/best"))
        )
        checkpoint = _pick_artifact(
            checkpoint_candidates,
            lambda path: _missing_files(path, CAFEBERT_CHECKPOINT_FILES),
            "checkpoint CafeBERT exp027",
            model_id,
            "Hãy đặt thư mục best/ gồm adapter_model.safetensors, adapter_config.json, head.pt "
            "và head_config.json vào <Drive>/SentimentX/models/cafebert_exp027/best/ rồi chạy lại.",
        )
        spec.runtime["checkpoint"] = str(checkpoint)
        resolved["checkpoint"] = str(checkpoint)

        base_candidates = []
        if drive_root is not None:
            base_candidates.append(drive_root / "models" / "cafebert-base")
        base_candidates.append(code_dir / "data" / "models" / "cafebert-base")
        base = _pick_optional(
            base_candidates,
            lambda path: _missing_files(path, CAFEBERT_BASE_FILES),
        )
        if base is not None:
            spec.runtime["base"] = str(base)
            resolved["base"] = str(base)
        else:
            resolved["base"] = str(spec.runtime.get("base") or "")
            print(
                "Ghi chú: không thấy base CafeBERT cục bộ; giữ mặc định {!r} và dựa vào HF cache. "
                "Nếu cache thiếu, bước kiểm tra sẽ báo lỗi kèm hướng dẫn.".format(
                    resolved["base"]
                )
            )
    else:
        candidates = []
        if drive_root is not None:
            candidates.extend([
                drive_root / "models" / "Qwen3-4B-Instruct-2507",
                drive_root / "data" / "models" / "Qwen3-4B-Instruct-2507",
            ])
        candidates.append(code_dir / "data" / "models" / "Qwen3-4B-Instruct-2507")
        model_dir = _pick_artifact(
            candidates,
            _qwen_missing,
            "thư mục mô hình Qwen3-4B-Instruct-2507",
            model_id,
            "Hãy đặt đầy đủ config.json, tokenizer, generation_config.json, "
            "model.safetensors.index.json và các shard .safetensors vào "
            "<Drive>/SentimentX/models/Qwen3-4B-Instruct-2507/ rồi chạy lại.",
        )
        spec.runtime["model_dir"] = str(model_dir)
        resolved["model_dir"] = str(model_dir)

    return resolved


def _load_dataset(data_path: Path) -> pd.DataFrame:
    if not data_path.is_file():
        raise FileNotFoundError("Không tìm thấy CSV: {}".format(data_path))

    frame = pd.read_csv(
        data_path,
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
    )

    required = ("text",) + ASPECTS
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(
            "CSV thiếu cột bắt buộc: {}. Cột đang có: {}.".format(
                ", ".join(missing), ", ".join(str(name) for name in frame.columns)
            )
        )

    blank = frame["text"].str.strip().eq("")
    if blank.any():
        print(
            "Bỏ {} dòng có text rỗng (chỉ lọc text rỗng, không sửa nội dung).".format(
                int(blank.sum())
            )
        )
        frame = frame.loc[~blank].copy()
    if frame.empty:
        raise ValueError("CSV không còn dòng nào sau khi lọc text rỗng.")

    for aspect in ASPECTS:
        numeric = pd.to_numeric(frame[aspect], errors="coerce")
        if numeric.isna().any():
            indexes = frame.index[numeric.isna()].tolist()[:10]
            raise ValueError(
                "Cột '{}' có nhãn không phải số ở dòng {}.".format(aspect, indexes)
            )
        codes = numeric.astype(int)
        invalid = ~codes.isin([0, 1, 2])
        if invalid.any():
            indexes = frame.index[invalid].tolist()[:10]
            raise ValueError(
                "Cột '{}' có nhãn ngoài 0/1/2 ở dòng {}.".format(aspect, indexes)
            )
        frame[aspect] = codes

    return frame


def _row_ids(frame: pd.DataFrame) -> list:
    if "row_id" not in frame.columns:
        return list(range(len(frame)))
    ids = []
    for value in frame["row_id"].tolist():
        text = str(value).strip()
        ids.append(int(text) if text.lstrip("-").isdigit() else text)
    return ids


def _predict_chunked(registry, model_id: str, texts: list[str], chunk: int, include_probs: bool):
    predictions, errors = [], []
    for start in range(0, len(texts), chunk):
        batch = texts[start:start + chunk]
        try:
            results = registry.predict(model_id, batch, include_probs=include_probs)
            if not isinstance(results, list) or len(results) != len(batch):
                raise RuntimeError(
                    "số kết quả {} khác số dòng {}".format(
                        len(results) if isinstance(results, list) else "?", len(batch)
                    )
                )
            predictions.extend(results)
            continue
        except Exception as exc:
            print(
                "  Khối dòng {}-{} lỗi ({}); thử lại từng dòng.".format(
                    start, start + len(batch) - 1, exc
                )
            )
        for offset, text in enumerate(batch):
            index = start + offset
            try:
                one = registry.predict(model_id, [text], include_probs=include_probs)
                if not one:
                    raise RuntimeError("không có kết quả")
                predictions.append(one[0])
            except Exception as row_exc:
                predictions.append(None)
                errors.append(
                    {"index": index, "error": "{}: {}".format(type(row_exc).__name__, row_exc)}
                )
    return predictions, errors


def _cell(prediction, aspect: str):
    if prediction is None:
        return None, None, None, None, None
    result = prediction.get(aspect)
    if result is None:
        return None, None, None, None, None
    return result.code, result.label, result.confidence, result.quote, result.reason


def _predictions_frame(frame: pd.DataFrame, row_ids, texts, predictions) -> pd.DataFrame:
    columns = {"row_id": row_ids, "text": texts}
    if "url" in frame.columns:
        columns["url"] = frame["url"].tolist()
    for aspect in ASPECTS:
        columns["gold_" + aspect] = frame[aspect].astype(int).tolist()
        cells = [_cell(prediction, aspect) for prediction in predictions]
        columns["pred_" + aspect] = [cell[0] for cell in cells]
        columns["pred_" + aspect + "_label"] = [cell[1] for cell in cells]
        columns["pred_" + aspect + "_confidence"] = [cell[2] for cell in cells]
        columns["pred_" + aspect + "_quote"] = [cell[3] for cell in cells]
        columns["pred_" + aspect + "_reason"] = [cell[4] for cell in cells]
    return pd.DataFrame(columns)


def _gold_rows(frame: pd.DataFrame) -> list[dict]:
    return [
        {aspect: int(frame.iloc[index][aspect]) for aspect in ASPECTS}
        for index in range(len(frame))
    ]


def _pred_rows(predictions) -> list[Optional[dict]]:
    rows = []
    for prediction in predictions:
        if prediction is None:
            rows.append(None)
            continue
        row = {}
        for aspect in ASPECTS:
            result = prediction.get(aspect)
            row[aspect] = None if result is None else result.code
        rows.append(row)
    return rows


def run_experiment(model_id, data_path, out_root, drive_root, code_dir, chunk=None) -> dict:
    if model_id not in _MODEL_DEFAULTS:
        raise ValueError(
            "model_id phải là một trong {}; nhận được {!r}.".format(
                ", ".join(_MODEL_DEFAULTS), model_id
            )
        )

    defaults = _MODEL_DEFAULTS[model_id]
    if chunk is None:
        chunk = defaults["chunk"]
    try:
        chunk = int(chunk)
    except (TypeError, ValueError):
        raise ValueError("chunk phải là số nguyên dương; nhận được {!r}.".format(chunk))
    if chunk < 1:
        raise ValueError("chunk phải >= 1; nhận được {}.".format(chunk))

    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data_path = Path(data_path)
    out_root = Path(out_root)
    code_dir = Path(code_dir) if code_dir is not None else _REPO_ROOT
    drive_root = Path(drive_root) if drive_root is not None else None

    frame = _load_dataset(data_path)
    print("Dữ liệu: {} dòng, {} khía cạnh.".format(len(frame), len(ASPECTS)))

    csv_sha = hashlib.sha256(data_path.read_bytes()).hexdigest()

    settings = load_settings(models_override=[model_id])
    spec = settings.models[model_id]
    artifacts = _prepare_runtime(spec, model_id, drive_root, code_dir)

    run_id = hashlib.sha256((spec.version + csv_sha).encode("utf-8")).hexdigest()[:8]
    out_dir = out_root / model_id / run_id

    row_ids = _row_ids(frame)
    texts = frame["text"].tolist()

    registry = ModelRegistry(settings)
    try:
        problems = registry.check(all_models=False)
        if problems:
            details = "\n".join(
                "- {}: {}".format(model, issue)
                for model, issues in problems.items()
                for issue in issues
            )
            raise RuntimeError("Kiểm tra mô hình thất bại, không chạy suy luận:\n" + details)

        print(
            "Suy luận {} dòng, chunk={}, include_probs={} ...".format(
                len(texts), chunk, defaults["include_probs"]
            )
        )
        predictions, errors = _predict_chunked(
            registry, model_id, texts, chunk, defaults["include_probs"]
        )
    finally:
        registry.close()

    predictions_frame = _predictions_frame(frame, row_ids, texts, predictions)
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.csv"
    predictions_frame.to_csv(predictions_path, index=False, encoding="utf-8-sig")

    errors_path = out_dir / "errors.csv"
    if errors:
        error_frame = pd.DataFrame(
            [{"row_id": row_ids[item["index"]], "error": item["error"]} for item in errors]
        )
        error_frame.to_csv(errors_path, index=False, encoding="utf-8-sig")
        errors_file = errors_path
    else:
        if errors_path.exists():
            errors_path.unlink()
        errors_file = None

    gold_rows = _gold_rows(frame)
    pred_rows = _pred_rows(predictions)

    run_info = {
        "model": model_id,
        "model_id": model_id,
        "model_version": spec.version,
        "run_id": run_id,
        "split": "realworld",
        "dataset": "shoppe_absa",
        "data_path": str(data_path),
        "csv_sha256": csv_sha,
        "chunk": chunk,
        "include_probs": bool(defaults["include_probs"]),
        "artifacts": dict(artifacts),
        "started_at": started_at,
        "n_rows": int(len(frame)),
        "n_errors": len(errors),
    }

    samples = scorers.Samples.build(
        ASPECTS,
        gold_rows,
        pred_rows,
        task=dict(TASK),
        labels=dict(LABELS),
        sample_ids=texts,
        meta=dict(run_info),
    )
    written = scorers.write(
        out_dir,
        samples,
        names=list(SCORER_NAMES),
        paper=list(PAPER_NAMES),
        save_confusion=True,
        save_plots=False,
        extra=dict(run_info),
    )

    metrics_path = out_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    scores = metrics.get("scores") or {}
    accuracy = dict(scores.get("accuracy") or {})
    detection = dict(scores.get("aspect_detection") or {})

    elapsed = round(time.perf_counter() - started, 3)
    files = {"predictions": str(predictions_path)}
    if errors_file is not None:
        files["errors"] = str(errors_file)
    files.update({name: str(path) for name, path in written.items()})

    run_meta = dict(run_info)
    run_meta.update({
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seconds": elapsed,
        "out_dir": str(out_dir),
        "files": files,
        "accuracy": accuracy,
        "scores": scores,
    })
    run_meta_path = out_dir / "run_meta.json"
    run_meta_path.write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    files["run_meta"] = str(run_meta_path)

    print("")
    print("=" * 72)
    print("Mô hình       : {}".format(model_id))
    print("Phiên bản     : {}".format(spec.version))
    print("Run id        : {}".format(run_id))
    print("Thư mục       : {}".format(out_dir))
    print(
        "Accuracy      : macro={} micro={} ({} ô)".format(
            accuracy.get("macro"), accuracy.get("micro"), accuracy.get("cells")
        )
    )
    print(
        "Nhận diện     : F1 macro={} F1 micro={}".format(
            (detection.get("macro") or {}).get("f1"),
            (detection.get("micro") or {}).get("f1"),
        )
    )
    print("Dòng lỗi      : {}".format(len(errors)))
    print("Thời gian     : {} giây".format(elapsed))
    print("=" * 72)

    return {
        "model_id": model_id,
        "model_version": spec.version,
        "run_id": run_id,
        "out_dir": str(out_dir),
        "predictions": str(predictions_path),
        "errors": None if errors_file is None else str(errors_file),
        "run_meta": str(run_meta_path),
        "metrics_json": str(metrics_path),
        "metrics_csv": str(out_dir / "metrics.csv"),
        "files": files,
        "accuracy": accuracy,
        "scores": scores,
        "n_rows": int(len(frame)),
        "n_errors": len(errors),
        "seconds": elapsed,
    }


__all__ = ["ASPECTS", "LABELS", "TASK", "run_experiment"]