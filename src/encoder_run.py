# -*- coding: utf-8 -*-
"""Chạy MỘT thí nghiệm dùng model ENCODER: huấn luyện LoRA rồi chấm trên split của vai `eval`.

VÌ SAO LÀ MODULE RIÊNG
Đường chạy model sinh (prompt + CoT, `src/evaluation/runner.py`) và đường chạy encoder khác nhau ở
đúng hai chỗ: encoder KHÔNG có prompt (nên phần prompt trong dấu vân tay là chuỗi rỗng), và nó phải
HỌC trước khi trả lời. Phần còn lại dùng chung: cùng dữ liệu của một phiên bản, cùng không gian
nhãn, cùng bộ chấm điểm, cùng cách ghi kết quả và ghi nhận - nhờ vậy hai đường cho ra bảng điểm so
được với nhau.

HAI BƯỚC, CỐ Ý TÁCH RỜI (giống `experiment_run`)
    plan(...)   đọc dữ liệu và cấu hình, quyết định chạy mới hay chạy tiếp. KHÔNG cần GPU.
    run(plan)   huấn luyện, suy luận, chấm điểm, ghi file, ghi nhận. Cần GPU.

CHẠY TIẾP
    Huấn luyện: ở mức CHECKPOINT (`model/last` + `trainer_state.json`, vân tay ba giá trị).
    Suy luận: ở mức MẪU, dùng chung `predictions/part_*.jsonl` với đường prompt (`src/resume.py`),
    nên đứt phiên giữa lúc chấm vẫn không phải chạy lại từ đầu.
"""

import json
import random

from src import config, experiments, labels, paths, resume, runlog, runtime, tracking, training, utils
from src import experiment_run
from src.evaluation import records, scorers
from src.preprocessing import loader
from src.training import lora
from src.tracking import run_meta

# Vai bắt buộc của một thí nghiệm encoder: học từ train, chọn `model/best` theo val, chấm trên eval.
REQUIRED_ROLES = ("train", "val", "eval")

APPROACH = "encoder"


class EncoderRunError(Exception):
    """Không chạy được: thiếu vai, thiếu dữ liệu, hoặc cấu hình không phải đường chạy encoder."""


def roles_of(config_data):
    """Vai của thí nghiệm, đã kiểm đủ cho đường huấn luyện."""
    roles = dict((config_data.get("data") or {}).get("roles") or {})
    missing = [role for role in REQUIRED_ROLES if not roles.get(role)]
    if missing:
        raise EncoderRunError(
            "Thí nghiệm dùng model encoder phải khai đủ vai {} trong `data.roles` (thiếu: {}). "
            "`train` để học, `val` để chọn model/best, `eval` để chấm - thiếu `val` thì không có cơ "
            "sở chọn model tốt nhất.".format(
                ", ".join(REQUIRED_ROLES), ", ".join(missing)))
    return roles


def log_config(plan_data, log):
    """Bảng GHI ĐÈ và giá trị hiệu lực của lượt huấn luyện, ghi vào `run.log` nhãn `[CONFIG]`."""
    config_data = plan_data["config"]
    merged = plan_data.get("merged") or {}
    found = plan_data["training"]
    log.config("thí nghiệm: {}/{}/{} | dữ liệu: {} | split chấm: {} | n: {}".format(
        plan_data["model_id"] or "-", plan_data["method"] or "-", plan_data["exp_id"] or "-",
        plan_data["version_id"], plan_data["split"], plan_data["limit"] or "cả split"))
    for name, before, after, _layer in merged.get("overrides") or []:
        log.config("đè {}: {} <- {}".format(name, before, after))
    if not merged.get("overrides"):
        log.config("không có khoá nào bị lớp sau đè")
    log.config("bài toán: label_space={} neutral_policy={} not_mentioned={} | nhãn: {}".format(
        config_data.get("label_space"), config_data.get("neutral_policy"),
        config_data.get("not_mentioned"), ", ".join(str(code) for code in plan_data["codes"])))
    log.config("huấn luyện: trainer={} lora r={} alpha={} dropout={} | module={} | lr={} "
               "batch={} grad_accum={} epochs={} weight_decay={}".format(
                   found["trainer"], found["lora_r"], found["lora_alpha"], found["lora_dropout"],
                   ", ".join(found["target_modules"]), found["lr"], found["batch"],
                   found["grad_accum"], found["epochs"], found["weight_decay"]))
    log.config("checkpoint: mỗi {} bước, giữ {} | lưu last={} best={} xoá trung gian={}".format(
        found["every_n_steps"], found["keep_last_k"], found["save_last"], found["save_best"],
        found["delete_intermediate"]))
    log.config("chạy: max_length={} | batch chấm={} | device={} | dtype={}".format(
        plan_data["max_length"], plan_data["batch_size"], plan_data["device"], found["dtype"]))


def run_record(plan_data):
    """Các giá trị CHỈ CÓ KHI CHẠY, ghi vào khối `run` của `run_meta.json`."""
    found = plan_data["training"]
    return {
        "approach": APPROACH,
        "split": plan_data["split"],
        "limit": plan_data["limit"],
        "n_samples": plan_data["info"]["n_samples"],
        "subset_seed": plan_data["seed"],
        "quant": found["quantization"],
        "max_length": plan_data["max_length"],
        "batch_size": plan_data["batch_size"],
        "training": {"trainer": found["trainer"], "epochs": found["epochs"],
                     "batch": found["batch"], "grad_accum": found["grad_accum"],
                     "lr": found["lr"], "lora_r": found["lora_r"],
                     "lora_alpha": found["lora_alpha"],
                     "target_modules": list(found["target_modules"])},
        # Không có prompt và không có cách sinh: hai khoá này để TRỐNG thay vì bịa, vì bản ghi là
        # chỗ tra cứu của một phép đo.
        "prompt": None,
        "prompt_sha": None,
        "examples_sha": None,
        "system_sha": None,
    }


def device_info(report):
    """Thông tin thiết bị để `run_meta.device_info` đọc, lấy từ số liệu THẬT của lượt huấn luyện."""
    import torch

    on_gpu = report["device"] == "cuda"
    return {
        "thiết bị": report["device"],
        "gpu": torch.cuda.get_device_name(0) if on_gpu else None,
        "vram_gb": (round(torch.cuda.get_device_properties(0).total_memory / 1024 ** 3, 1)
                    if on_gpu else None),
        "quant": report["quantization"],
        "dtype": report["dtype"],
        "torch": getattr(torch, "__version__", ""),
        "transformers": _version("transformers"),
        "trainable_params": report.get("trainable_params"),
        "total_params": report.get("total_params"),
    }


def _version(name):
    """Phiên bản một thư viện, hoặc chuỗi rỗng nếu máy không có."""
    import importlib.util

    if importlib.util.find_spec(name) is None:
        return ""
    return str(getattr(__import__(name), "__version__", ""))


def split_data(frame, aspects):
    """Dữ liệu của một vai: văn bản, mã nhãn THÔ (N×A), và chỉ số dòng gốc."""
    texts = frame[config.TEXT_COLUMN].astype(str).tolist()
    codes = frame[aspects].astype(int).to_numpy().tolist()
    return texts, codes, list(range(len(texts)))


def fit_data(config_data, version_id, ds, roles):
    """Dữ liệu cho ba vai, nhãn đã CHIẾU sang không gian nhãn của thí nghiệm.

    Trả về `(dữ liệu, codes, projection)`:
        dữ liệu["train"|"val"]  `{"texts", "labels", "mask"}` để huấn luyện
        dữ liệu["eval"]         thêm `golds` (mã THÔ) để chấm đúng như đường prompt
    """
    frames = {}
    for role in REQUIRED_ROLES:
        name = str(roles[role])
        frames[role] = loader.load_processed(name, version_id=version_id, dataset=ds["name"])

    # Bộ khía cạnh và bảng mã nhãn đọc từ ĐÚNG phiên bản đang chạy, rồi lọc theo không gian nhãn.
    label_map = labels.filter_label_map(
        loader.load_label_map(version_id, dataset=ds["name"]),
        config_data["label_space"], config_data["neutral_policy"])
    aspects = labels.task_aspects(config_data, label_map["aspects"])

    raw = {role: split_data(frame, aspects)[1] for role, frame in frames.items()}
    # `projection` chỉ dùng để lấy ĐÚNG bộ mã và chính sách neutral; việc chiếu từng ô do
    # `project_multi_head` làm, vì nó trả về cả MASK (ô bị loại không vào loss, nhưng không mất
    # các khía cạnh khác của cùng review).
    projection = labels.project(raw["eval"], raw["eval"], config_data["label_space"],
                                config_data["neutral_policy"], config_data["not_mentioned"])
    codes = [int(code) for code in projection["codes"]]

    data = {}
    for role in REQUIRED_ROLES:
        texts, matrix, row_index = split_data(frames[role], aspects)
        projected, mask = loader.project_multi_head(matrix, projection)
        golds = [dict(zip(aspects, row)) for row in matrix]
        data[role] = {"texts": texts, "labels": projected, "mask": mask, "golds": golds,
                      "row_index": row_index, "rows": len(texts)}
    return data, codes, projection, aspects, label_map



def identity(config_data, version_id, model_id=None, method=None, exp_id=None, max_length=None):
    """Dấu vân tay + thư mục kết quả của một lượt chạy encoder: chỗ DUY NHẤT quyết định.

    Tách khỏi `plan()` vì preflight cần ĐÚNG phép tính này mà không cần đọc dữ liệu (đọc cả ba
    split chỉ để biết thư mục kết quả là việc nặng vô ích). Hai chỗ gọi cùng một hàm, nên "kiểm
    trước" và lượt chạy thật không thể nói hai chuyện khác nhau.

    Model encoder KHÔNG có prompt, nên phần prompt của dấu vân tay là chuỗi RỖNG (không phải chuỗi
    bịa); ngưỡng cắt và mã commit vào `extra` vì chúng đổi phép đo mà không nằm trong config.
    """
    found = lora.settings(config_data, model_id)
    value = int(max_length or found["max_length"])
    repo = run_meta.repo_info(url=config_data.get("url"), branch=config_data.get("branch"))
    config_sha = experiments.config_sha256(
        {"config": config_data}, prompt_text="",
        extra={"version_id": version_id, "repo_sha": repo["sha"], "approach": APPROACH,
               "max_length": value})
    hash8 = experiment_run.run_hash(config_sha)
    return {"config_sha256": config_sha,
            "fingerprint": resume.fingerprint(config_sha, version_id, repo["sha"]),
            "hash": hash8, "repo": repo, "max_length": value,
            "out_dir": experiment_run.out_dir_of(hash8, model_id, method, exp_id)}


def plan(config_data, merged, ds, version_id, split=None, limit=None, model=None, seed=42,
         batch_size=None, max_length=None, quant="auto", new=False, quiet=False):
    """Đọc dữ liệu và quyết định chạy mới hay chạy tiếp. KHÔNG cần GPU.

    Tham số truyền vào chỉ để ĐÈ khi chạy nhanh trên dòng lệnh; giá trị đang dùng lấy từ config của
    thí nghiệm, nên notebook và dòng lệnh cho ra cùng một cấu hình.
    """
    model_id = merged.get("model_id")
    method = merged.get("method")
    exp_id = merged.get("exp_id")
    if not (model_id and method and exp_id):
        raise EncoderRunError(
            "Chưa biết thí nghiệm (thiếu model/method/exp_id). Mở notebook của thí nghiệm rồi chạy.")
    roles = roles_of(config_data)
    split = str(split or roles["eval"])
    found = lora.settings(config_data, model_id)
    found["device"] = lora.device_of()
    names = scorers.check(config_data.get("scores"))
    data, codes, _projection, aspects, label_map = fit_data(config_data, version_id, ds, roles)

    eval_data = data["eval"]
    texts, golds, row_index = list(eval_data["texts"]), list(eval_data["golds"]), \
        list(eval_data["row_index"])
    if limit and limit < len(texts):
        # Tập con chọn bằng random CÓ SEED để tái lập được, và giữ chỉ số dòng GỐC - không có nó
        # thì không tra ngược được kết quả về review nào trong file dữ liệu.
        keep = sorted(random.Random(seed).sample(list(range(len(texts))), int(limit)))
        texts = [texts[position] for position in keep]
        golds = [golds[position] for position in keep]
        row_index = [row_index[position] for position in keep]

    max_length_value = int(max_length or found["max_length"])
    identity_data = identity(config_data, version_id, model_id=model_id, method=method,
                             exp_id=exp_id, max_length=max_length_value)
    repo = identity_data["repo"]
    config_sha = identity_data["config_sha256"]
    fingerprint = identity_data["fingerprint"]
    hash8 = identity_data["hash"]
    out_dir = identity_data["out_dir"]
    others = experiment_run.sibling_runs(out_dir)
    if others:
        print("LƯU Ý: thí nghiệm này đã có {} lượt chạy KHÁC:".format(len(others)))
        for row in others:
            print("  {}".format(row))
        print("Lượt này ghi vào thư mục MỚI '{}' (bản code/cấu hình khác). Kết quả cũ không bị "
              "đụng tới.\n".format(hash8))
    if split == "test":
        print("LƯU Ý: đang chạy trên TEST. Tập này chỉ dùng cho con số CUỐI CÙNG, sau khi đã chốt "
              "cấu hình trên val - chọn theo test là tự lừa mình.\n")

    parts = resume.Parts(out_dir)
    mode, reason = resume.decide(run_meta.read(out_dir), fingerprint, parts.count(),
                                 force_new=new)
    skip = parts.keys() if mode == resume.MODE_RESUME else set()
    if skip:
        keep = [position for position, index in enumerate(row_index) if str(index) not in skip]
        texts = [texts[position] for position in keep]
        golds = [golds[position] for position in keep]
        row_index = [row_index[position] for position in keep]

    log.config("mã hạt giống: {}".format(plan_data["seed"]))


    info = {
        "dataset": ds["name"], "version_id": version_id, "split": split, "approach": APPROACH,
        "prompt": None, "prompt_sha": None, "model": model or found["checkpoint"],
        "quant": found["quantization"], "max_length": max_length_value,
        "batch_size": int(batch_size or found["eval_batch"]),
        "subset": {"limit": limit, "seed": seed}, "n_samples": len(texts),
        "experiment": {"model": model_id, "method": method, "exp_id": exp_id},
        "label_space": config_data.get("label_space"),
        "neutral_policy": config_data.get("neutral_policy"),
        "not_mentioned": config_data.get("not_mentioned"),
        "training": {key: found[key] for key in (
            "trainer", "epochs", "batch", "grad_accum", "lr", "weight_decay", "lora_r",
            "lora_alpha", "lora_dropout", "target_modules", "every_n_steps", "keep_last_k",
            "quantization", "dtype")},
    }

    # Số bản ghi của TỪNG vai và dấu vân tay tập đánh giá: hai thứ người đọc bản ghi cần biết.
    # Nhập muộn để cấp module của file này không phụ thuộc preflight.
    from src import preflight

    rows_by_role = {}
    for role, name in sorted(roles.items()):
        path = paths.processed(version_id) / "{}.csv".format(name)
        if path.is_file():
            rows_by_role[role] = preflight.count_rows(path)
    lock = dict(ds.get("eval_lock") or {})
    eval_lock = {"enforce": bool(lock.get("enforce", False)),
                 "declared": (lock.get("test") or {}).get("sha256")}

    return {
        "approach": APPROACH, "config": config_data, "merged": merged, "model_id": model_id,
        "method": method, "exp_id": exp_id, "exp_dir": merged.get("dir"), "dataset": ds,
        "version_id": version_id, "split": split, "limit": limit, "seed": seed,
        "total": len(eval_data["texts"]), "label_map": label_map,
        "labels": experiment_run.label_names(label_map), "aspects": aspects, "codes": codes,
        "texts": texts, "golds": golds, "row_index": row_index, "data": data,
        "names": names, "columns": records.columns(with_prompt=False),
        "batch_size": int(batch_size or found["eval_batch"]), "train_batch": found["batch"],
        "quiet": quiet, "hash": hash8, "out_dir": out_dir, "info": info, "repo": repo,
        "config_sha256": config_sha, "fingerprint": fingerprint, "mode": mode, "reason": reason,
        "parts": parts, "skip": skip, "roles": roles, "rows_by_role": rows_by_role,
        "eval_lock": eval_lock, "training": found, "model": model or found["checkpoint"],
        "files": experiment_run.input_files(ds, None, model_id, None, None),
        # Không dùng cho model encoder, nhưng phần ghi kết quả dùng chung với đường prompt đọc
        # chúng; để None thay vì bỏ khoá, nhờ vậy hai đường không cần hai bản ghi kết quả.
        "examples": None, "system": None, "generation": {}, "sampled": False,
        "max_length": max_length_value, "quant": quant, "device": found["device"],
    }


def print_config(plan_data):
    """In cấu hình ĐANG DÙNG ra màn hình, để bảng điểm sau này biết nó thuộc cấu hình nào."""
    found = plan_data["training"]
    print("Thí nghiệm : {}/{}/{}".format(plan_data["model_id"], plan_data["method"],
                                        plan_data["exp_id"]))
    print("Dataset    : {} {} -> {}".format(plan_data["dataset"]["name"],
                                           plan_data["dataset"].get("version"),
                                           plan_data["version_id"]))
    print("Vai        : {}".format(plan_data["roles"]))
    print("Bài toán   : label_space={}, neutral_policy={}, not_mentioned={} | nhãn {}".format(
        plan_data["config"].get("label_space"), plan_data["config"].get("neutral_policy"),
        plan_data["config"].get("not_mentioned"),
        ", ".join(str(code) for code in plan_data["codes"])))
    print("Huấn luyện : LoRA r={} alpha={} trên {} | {} epoch, batch {} (tích luỹ {})".format(
        found["lora_r"], found["lora_alpha"], ", ".join(found["target_modules"]),
        found["epochs"], found["batch"], found["grad_accum"]))
    print("Chấm điểm  : {} mẫu (n={}), chỉ số {}".format(
        plan_data["info"]["n_samples"], plan_data["limit"] or "cả split", plan_data["names"]))
    print("Model      : {} | ngưỡng cắt {} token | device {}".format(
        plan_data["model"], plan_data["max_length"], plan_data["device"]))


def prediction_rows(plan_data, answers, seconds_per_sample=0.0):
    """Bảng dự đoán của model encoder: cùng cột với đường prompt, THIẾU cột prompt.

    Model encoder học từ chuỗi thô nên không có prompt nào để ghi (xem `records.columns`). Mọi ô
    đều `đọc được = có`: model luôn trả về một mã cho mỗi khía cạnh, còn đúng hay sai thì phần
    chấm điểm nói.
    """
    columns = plan_data["columns"]
    aspects = plan_data["aspects"]
    rows = []
    for position, answer in enumerate(answers):
        row = dict.fromkeys(columns, "")
        row["chỉ số"] = str(plan_data["row_index"][position])
        row["split"] = plan_data["split"]
        row["kiểu đọc"] = "số"
        row["đọc được"] = records.MENTIONED
        row[records.REASON_COLUMN] = "ok"
        row["text"] = plan_data["texts"][position]
        row["nhãn đúng"] = json.dumps(plan_data["golds"][position], ensure_ascii=False)
        row["nhãn đoán"] = json.dumps(
            {name: int(code) for name, code in zip(aspects, answer)}, ensure_ascii=False)
        row["token sinh"] = 0
        row["giây"] = round(float(seconds_per_sample), 4)
        row["có suy luận"] = "không"
        row["có <think>"] = "không"
        row["câu trả lời"] = json.dumps([int(code) for code in answer])
        rows.append([row[column] for column in columns])
    return rows



def run(plan_data, log=None):
    """Huấn luyện, suy luận, chấm điểm, ghi kết quả và ghi nhận. CẦN GPU.

    Trả về cùng dạng dict với `experiment_run.run`, để notebook dùng tiếp mà không phải biết lượt
    này đi đường nào.
    """
    out_dir = plan_data["out_dir"]
    mode = plan_data["mode"]
    if mode == resume.MODE_STOP:
        print("DỪNG: {}".format(plan_data["reason"]))
        print("      Đây là lượt chạy đã XONG của đúng bản code + cấu hình + dữ liệu này.")
        print("      Muốn chạy lại từ đầu thì XOÁ thư mục kết quả rồi chạy lại:\n"
              "        {}".format(utils.rel(out_dir)))
        return {"out_dir": out_dir, "mode": mode, "reason": plan_data["reason"], "stopped": True}

    runtime.load_env()

    with runlog.start(out_dir, mode=mode, info=plan_data["info"]) as active:
        log = log or active
        record = run_meta.build(
            out_dir, hash8=plan_data["hash"],
            experiment={"model": plan_data["model_id"], "method": plan_data["method"],
                        "exp_id": plan_data["exp_id"]},
            data={"dataset": plan_data["dataset"]["name"],
                  "version": plan_data["dataset"].get("version"),
                  "ma": plan_data["version_id"], "roles": dict(plan_data["roles"]),
                  "rows": dict(plan_data["rows_by_role"]),
                  "eval_lock": dict(plan_data["eval_lock"])},
            repo=plan_data["repo"],
            config={"sha256": plan_data["config_sha256"],
                    "layers": plan_data["merged"]["layers"],
                    "sources": plan_data["merged"]["sources"]},
            task=experiment_run.merged_task(plan_data["config"]),
            overrides=plan_data["merged"]["overrides"], files=plan_data["files"],
            env=run_meta.env_info(kind=runtime.env_name()), run_extra=run_record(plan_data),
            note="chạy tiếp" if mode == resume.MODE_RESUME else None)
        run_meta.write(out_dir, record)
        log.on_close(run_meta.closer(record, out_dir, log=log))
        session = tracking.begin(plan_data["config"], out_dir, info=plan_data["info"], log=log)
        log.on_close(tracking.closer(session, log=log))

        log_config(plan_data, log)
        print_config(plan_data)

        found = plan_data["training"]
        trainer = training.get(found["trainer"])
        log.step("huấn luyện: {} epoch, batch {} (tích luỹ {}), {} mẫu train, {} mẫu val".format(
            found["epochs"], found["batch"], found["grad_accum"],
            plan_data["data"]["train"]["rows"], plan_data["data"]["val"]["rows"]))
        report = trainer.fit(plan_data["config"], plan_data["model_id"], out_dir,
                             train=plan_data["data"]["train"], val=plan_data["data"]["val"],
                             aspects=plan_data["aspects"], codes=plan_data["codes"],
                             fingerprint=plan_data["fingerprint"], seed=plan_data["seed"],
                             source=plan_data["model"], log=log)
        log.step("huấn luyện xong: {} bước trong {} giây ({} tham số học / {} tổng)".format(
            report["steps"], report["seconds"], report["trainable_params"],
            report["total_params"]), seconds=report["seconds"])
        # Máy, kiểu số và số tham số chỉ biết được SAU khi huấn luyện, nên bổ sung vào bản ghi.
        record["env"].update(run_meta.device_info(
            device_info(report), quant=found["quantization"]))
        run_meta.write(out_dir, record)

        adapter = report["best_dir"] or report["last_dir"]
        log.step("suy luận bằng {}".format(utils.rel(adapter)))
        answers, head_config = trainer.predict(
            plan_data["config"], plan_data["model_id"], adapter, plan_data["texts"],
            source=plan_data["model"])
        log.step("suy luận xong {} mẫu; checkpoint huấn luyện với {} khía cạnh, nhãn {}".format(
            len(answers), head_config["n_aspects"],
            ", ".join(str(code) for code in head_config["codes"])))
        seconds_per_sample = report["seconds"] / max(len(answers), 1)
        rows = prediction_rows(plan_data, answers, seconds_per_sample)
        plan_data["parts"].append(rows, plan_data["columns"])
        cost = {"giây": report["seconds"], "token sinh TB": None, "token sinh/giây": None,
                "huấn luyện giây": report["seconds"], "số bước": report["steps"]}
        return experiment_run.finish(plan_data, rows, cost, device_info(report),
                                     plan_data["info"], session, log)
