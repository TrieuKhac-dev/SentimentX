# -*- coding: utf-8 -*-
"""Chạy MỘT thí nghiệm: nạp cấu hình, kiểm trước, sinh, chấm điểm, ghi kết quả, ghi nhận.

VÌ SAO LÀ THƯ VIỆN, VÀ `run_qwen_eval.py` CHỈ LÀ CỬA VÀO MỎNG
Thí nghiệm được chạy từ NOTEBOOK (docs/00_workflow/01_flow.md): notebook là thứ được giao cho
người nhận, bấm Run all. Nếu notebook gọi một script dòng lệnh thì hợp đồng giữa hai bên là TÊN
CỜ DÒNG LỆNH - đổi tên cờ là hỏng notebook đã giao (mà sau khi ghim thì không được sửa thí
nghiệm), notebook không nhận lại được gì ngoài mã thoát, và cả hai bên đều tự đọc config.

Ở đây ngược lại: hàm trong file này trả về kết quả CÓ CẤU TRÚC (đường dẫn, chỉ số, chế độ chạy),
nên notebook dùng tiếp được (in bảng, vẽ, quyết định bước sau). `run_qwen_eval.py` chỉ là cửa vào
cho lúc muốn chạy nhanh trên dòng lệnh - nó gọi đúng hai hàm dưới đây. Một đường chạy, hai cửa.

HAI BƯỚC, CỐ Ý TÁCH RỜI
    plan(...)   đọc dữ liệu và cấu hình, quyết định chạy mới hay chạy tiếp. KHÔNG cần GPU.
    run(plan)   nạp model, sinh, chấm điểm, ghi file, ghi nhận. Cần GPU.

Tách như vậy vì bước `plan` là bước hay hỏng (thiếu file, sai tên split, mã phiên bản lệch) và
kiểm được trong vài giây; còn `run` mới là bước tốn hàng chục phút. Notebook gọi `plan` rồi
`preflight` trước, chỉ khi sạch mới tới `run`.
"""

import random
from pathlib import Path

from src import config, dataset, experiments, labels, model_config, paths, prompts, resume, runlog, runtime, tracking, utils, versioning
from src.evaluation import metrics, records, runner, scorers
from src.preprocessing import loader, qwen
from src.tracking import run_meta

# Cấu hình lấy mẫu theo khuyến nghị của model card Qwen3-4B-Instruct-2507
# (Temperature=0.7, TopP=0.8, TopK=20). Chỉ dùng khi chạy ở chế độ `sample`.
CARD_SETTINGS = {"temperature": 0.7, "top_p": 0.8, "top_k": 20}


class RunError(Exception):
    """Không chạy được: thiếu file, sai cấu hình, hoặc tên thí nghiệm không hợp lệ."""


def split_of(config_data):
    """Split để CHẤM: lấy từ vai `eval` của thí nghiệm, không phải từ tham số dòng lệnh.

    Chạy test từ đầu rồi chọn theo test là tự lừa mình, nên vai `eval` phải được khai trong config
    của thí nghiệm; `val` là tập để LỰA CHỌN, `test` chỉ dùng cho con số cuối cùng.
    """
    roles = dict((config_data.get("data") or {}).get("roles") or {})
    if not roles.get("eval"):
        raise RunError("Thiếu `data.roles.eval`: không biết chấm trên split nào. Xem "
                       "docs/05_config/06_experiment.md.")
    return str(roles["eval"])


def limit_of(config_data):
    """Số mẫu dùng để chấm: `evaluation.n`. None/rỗng nghĩa là CẢ split (cách so với công bố)."""
    value = config_data.get("n")
    return int(value) if value else 0


def settings_of(config_data, do_sample=None):
    """Cấu hình sinh, lấy từ config (`evaluation.decoding`), không phải từ tham số dòng lệnh.

    `greedy` là tất định nên kết quả tái lập được - đó là mặc định của dự án. `sample` mới lấy
    theo nhiệt độ/top_p/top_k của model card (hoặc giá trị config khai đè).
    """
    decoding = dict(config_data.get("decoding") or {})
    sampled = bool(do_sample) if do_sample is not None else \
        str(decoding.get("mode") or "greedy").lower() == "sample"
    settings = dict(CARD_SETTINGS) if sampled else {}
    for key in ("temperature", "top_p", "top_k"):
        if decoding.get(key):
            settings[key] = float(decoding[key])
    return settings, sampled


def build_tag(prompt_name, split, limit, sampled, quant, model=None):
    """Tên thư mục kết quả của MỘT cấu hình chạy.

    Cấu hình nằm ở TÊN THƯ MỤC nên tên file bên trong là tên cố định, và hai lần chạy khác cấu
    hình không bao giờ ghi đè nhau. `model` chỉ được ghi khi nó KHÁC checkpoint trong config (tức
    là khi có người truyền `--model <thứ khác>`, ví dụ chạy thử bằng model nhỏ): không ghi thì hai
    lần chạy khác model mà cùng cấu hình sẽ tranh nhau một thư mục, và lần thứ hai bị coi là "đã
    chạy xong" - một lỗi im lặng rất khó thấy.
    """
    parts = ["prompt-{}".format(prompt_name), str(split)]
    if limit:
        parts.append("n{}".format(limit))
    parts.append("sample" if sampled else "greedy")
    if quant:
        parts.append(str(quant))
    if model:
        parts.append(str(model))
    return "__".join(parts)


def model_tag(model, config_data):
    """Phần tên model để đưa vào tên thư mục: rỗng nếu trùng checkpoint của config.

    Model truyền vào có thể là id HF (`Qwen/Qwen3-0.6B`) hoặc thư mục cục bộ (`data/models/Qwen3-0.6B`),
    nên chỉ lấy đoạn cuối cho tên thư mục ngắn và đọc được.
    """
    if not model or str(model) == str(config_data.get("checkpoint") or ""):
        return None
    return str(model).replace("\\", "/").strip("/").split("/")[-1] or None


def inside_experiment(exp_dir, value):
    """Đường dẫn khai trong config thí nghiệm: tính từ thư mục thí nghiệm trước, rồi tới gốc repo."""
    path = Path(str(value))
    if path.is_absolute() or exp_dir is None:
        return path
    candidate = Path(exp_dir) / str(value)
    return candidate if candidate.exists() else paths.root() / str(value)


def shared_prompt_path(name):
    """Đường dẫn prompt trong thư viện dùng chung."""
    return paths.config_path(paths.cfg()["configs"]["prompts"], "{}.txt".format(name))


def label_names(label_map):
    """Bảng tên nhãn để in kết quả (mã -> tên). Khoá là số vì bảng đếm dùng mã bằng số."""
    return {int(code): name for code, name in (label_map.get("id_to_label") or {}).items()}


def input_files(ds, prompt_path, model_id, examples_path=None):
    """File ĐẦU VÀO của lần chạy, kèm vai, để `run_meta.json` tự mô tả được.

    Vì sao phải ghi cả file cấu hình dữ liệu: một con số chỉ so được khi biết nó sinh ra từ code
    nào, config nào và dữ liệu nào. Đường dẫn ở đây là đường dẫn TƯƠNG ĐỐI (xem `run_meta`).
    """
    shared = paths.cfg()["configs"]
    entries = [(paths.config_path(shared["paths"]), run_meta.ROLE_PATHS),
               (tracking.base.dagshub_path(), run_meta.ROLE_TRACKING)]
    entries += [(experiments.shared_path(name), run_meta.ROLE_CONFIG)
                for name in experiments.SHARED]
    entries.append((model_config.config_path(model_id), run_meta.ROLE_MODEL))
    entries.append((ds.get("_path"), run_meta.ROLE_DATASET))
    entries.append((paths.config_path(shared["pipeline"],
                                      "{}.yaml".format(ds.get("pipeline_version"))),
                    run_meta.ROLE_PIPELINE))
    entries.append((prompt_path, run_meta.ROLE_PROMPT))
    entries.append((examples_path, run_meta.ROLE_EXAMPLES))
    return run_meta.input_files(entries)


def out_dir_of(version_id, tag, model_id=None, method=None, exp_id=None):
    """Thư mục kết quả của lần chạy, và cho biết có nằm TRONG thí nghiệm không.

    Đủ ba phần định danh thí nghiệm thì dùng đúng chỗ của thí nghiệm
    (`experiments/<model>/<method>/<expNNN>/results/<mã>/<hậu tố>/`). Chạy tay trên dòng lệnh mà
    không nêu thí nghiệm thì dùng thư mục đánh giá cũ - và nói rõ là đang chạy NGOÀI thí nghiệm,
    để không ai tưởng kết quả đó thuộc một thí nghiệm đã ghim.
    """
    if model_id and method and exp_id:
        return paths.results_dir(model_id, method, exp_id, version_id) / str(tag), True
    return config.MODEL_EVAL_REPORT_DIR / str(version_id) / str(tag), False


def print_table(rows, columns):
    """In bảng canh cột. Dùng cho bảng chỉ số và bảng cấu hình."""
    widths = []
    for index, name in enumerate(columns):
        width = max([len(str(name))] + [len(str(row[index])) for row in rows] or [0])
        widths.append(min(width, 34))
    print("  " + "  ".join(str(name).ljust(widths[index])
                           for index, name in enumerate(columns)))
    print("  " + "  ".join("-" * widths[index] for index in range(len(columns))))
    for row in rows:
        print("  " + "  ".join(str(value)[:34].ljust(widths[index])
                               for index, value in enumerate(row)))


def print_scores(scores):
    """In các con số tổng hợp của từng bộ chấm. Bảng chi tiết in bằng `scorers.table`."""
    for name, values in scores.items():
        print("  {}".format(name))
        for key, value in values.items():
            if isinstance(value, dict):
                flat = "  ".join("{}={}".format(inner, item) for inner, item in value.items()
                                 if isinstance(item, (int, float, str)))
                if flat:
                    print("    {:<20} {}".format(key, flat))
            else:
                print("    {:<20} {}".format(key, value))


def print_config(plan_data, model_info):
    """In cấu hình của lần chạy TRƯỚC khi sinh, để nhìn là biết đang đo cái gì."""
    prompt = plan_data["prompt"]
    examples = plan_data["examples"]
    print("Cấu hình chạy:")
    print("  thí nghiệm  : {}".format(
        "{}/{}/{}".format(plan_data["model_id"], plan_data["method"], plan_data["exp_id"])
        if plan_data["inside"] else "chạy NGOÀI thí nghiệm (kết quả không thuộc thí nghiệm nào)"))
    print("  prompt      : {} ({}), sha {}".format(prompt.name, prompt.where, prompt.sha))
    print("  ví dụ       : {}".format(
        "{} - {} ví dụ, sha {}".format(examples["file"], examples["examples"],
                                       examples["sha"]) if examples else "không dùng"))
    print("  tập dữ liệu : {} - {}{}".format(
        plan_data["split"], plan_data["limit"] or plan_data["total"],
        " (TẬP CON ngẫu nhiên, seed {})".format(plan_data["seed"])
        if plan_data["limit"] and plan_data["limit"] < plan_data["total"] else ""))
    print("  ngưỡng cắt  : {} token (max_length của Qwen)".format(plan_data["max_length"]))
    print("  sinh        : {}".format(
        "greedy (tái lập)" if not plan_data["sampled"] else
        "lấy mẫu: temperature={}, top_p={}, top_k={}, seed={}".format(
            plan_data["generation"]["temperature"], plan_data["generation"]["top_p"],
            plan_data["generation"]["top_k"], plan_data["generation"]["seed"])))
    print("  tối đa sinh : {} token/review".format(plan_data["generation"]["max_new_tokens"]))
    print("  model       : {} - {}, {}, {}".format(
        plan_data["model"], model_info.get("quant"), model_info.get("cách nạp"),
        model_info.get("thiết bị")))
    print()


def plan(merged, dataset_name=None, model_id=None, method=None, exp_id=None, prompt=None,
         examples=None, split=None, limit=None, version_id=None, quant="auto", new=False,
         seed=42, max_new_tokens=None, max_length=None, batch_size=None, model=None,
         sample=None, quiet=False):
    """Đọc dữ liệu và quyết định chạy mới hay chạy tiếp. KHÔNG cần GPU.

    Trả về KẾ HOẠCH (dict) cho `run()`: dữ liệu đã lọc theo split/tập con, prompt đã nạp và đã
    đăng ký, thư mục kết quả, và chế độ chạy (NEW/RESUME/STOP).

    Giá trị lấy từ CONFIG trước; tham số truyền vào chỉ để đè khi chạy nhanh trên dòng lệnh. Nhờ
    vậy notebook (đọc config của thí nghiệm) và dòng lệnh cho ra cùng một cấu hình - không có hai
    nguồn sự thật cho cùng một lần chạy.
    """
    config_data = dict(merged.get("config") or {})
    model_id = model_id or merged.get("model_id") or qwen.CONFIG_NAME
    method = method or merged.get("method")
    exp_id = exp_id or merged.get("exp_id")
    exp_dir = merged.get("dir")

    ds = dataset.load_config(dataset_name or (config_data.get("data") or {}).get("dataset"))
    version_id = version_id or versioning.compute_id(ds)
    # Split do config của thí nghiệm quyết định (`data.roles.eval`). Chạy TAY mà lớp dùng chung chưa
    # khai vai `eval` thì dùng `val` - tập LỰA CHỌN, không phải test; còn chạy TRONG thí nghiệm mà
    # thiếu vai `eval` là lỗi, không đoán hộ.
    if split:
        split = str(split)
    else:
        try:
            split = split_of(config_data)
        except RunError:
            if method and exp_id:
                raise
            split = "val"
            print("LƯU Ý: config chưa khai `data.roles.eval`; chạy tay nên dùng split 'val' "
                  "(tập LỰA CHỌN, không phải test).")
    limit = limit if limit else limit_of(config_data)
    quant = quant or "auto"
    model = model or config_data.get("hf_model") or qwen.MODEL_NAME

    # Prompt: tên trong thư viện dùng chung, hoặc đường dẫn tới file cạnh notebook. Nạp xong thì
    # đăng ký luôn (`qwen.load_prompt`), vì các bước sau chỉ truyền được một cái TÊN.
    prompt_value = prompt or config_data.get("prompt")
    examples_value = examples if examples is not None else config_data.get("examples")
    prompt_obj = qwen.load_prompt(prompt_value, base_dir=exp_dir, examples=examples_value)
    examples_info = (prompts.examples_info(prompt_obj.examples_value, base_dir=exp_dir)
                     if "examples" in prompt_obj.placeholders else None)

    label_map = loader.load_label_map(version_id, dataset=ds["name"])
    frame = loader.load_processed(split, version_id=version_id, dataset=ds["name"])
    # Lọc bảng mã nhãn theo không gian nhãn TRƯỚC khi đưa cho model: đưa một nhãn mà bài toán
    # không dùng là mọi câu trả lời mang nhãn đó đều bị tính sai.
    label_map = labels.filter_label_map(label_map, config_data["label_space"],
                                        config_data["neutral_policy"])
    aspects = labels.task_aspects(config_data, label_map["aspects"])
    # Tên các bộ chấm điểm đang bật (khai trong `evaluation.scores`) - kiểm ngay ở bước lập kế
    # hoạch, vì gõ sai tên rồi chờ nạp model xong mới biết là mất cả chục phút.
    names = scorers.check(config_data.get("scores"))

    texts = frame[config.TEXT_COLUMN].astype(str).tolist()
    codes = frame[aspects].astype(int).to_numpy().tolist()
    golds = [dict(zip(aspects, row)) for row in codes]

    # Tập con (nếu có): chọn bằng random CÓ SEED để tái lập được, và giữ chỉ số dòng GỐC - không
    # có nó thì không tra ngược được kết quả về review nào trong file dữ liệu.
    row_index = list(range(len(texts)))
    if limit and limit < len(texts):
        row_index = sorted(random.Random(seed).sample(row_index, limit))
        texts = [texts[index] for index in row_index]
        golds = [golds[index] for index in row_index]

    # Cấu hình sinh: `evaluation.decoding` trong config quyết định greedy hay lấy mẫu; khi lấy mẫu
    # thì nhiệt độ/top_p/top_k theo model card (hoặc giá trị config khai đè).
    card, sampled = settings_of(config_data, do_sample=sample)
    generation = runner.settings(quant=quant, max_new_tokens=max_new_tokens, do_sample=sampled,
                                 temperature=card.get("temperature"), top_p=card.get("top_p"),
                                 top_k=card.get("top_k"), seed=seed if sampled else None)
    max_length = max_length or qwen.limit()[0]

    tag = build_tag(prompt_obj.name, split, limit, sampled,
                    quant if quant and quant != "auto" else None,
                    model_tag(model, config_data))
    out_dir, inside = out_dir_of(version_id, tag, model_id, method, exp_id)
    if not inside:
        print("LƯU Ý: chạy NGOÀI thí nghiệm nên kết quả đi vào {} (không thuộc thí nghiệm nào). "
              "Muốn kết quả nằm trong thí nghiệm thì chạy notebook của thí nghiệm.".format(
                  utils.rel(out_dir)))
    if split == "test" and inside:
        print("LƯU Ý: đang chạy trên TEST. Tập này chỉ dùng cho con số CUỐI CÙNG, sau khi đã")
        print("       chốt prompt và ngưỡng trên val - chọn theo test là tự lừa mình.\n")

    info = {
        "dataset": ds["name"], "version_id": version_id, "split": split,
        "prompt": prompt_obj.name, "prompt_sha": prompt_obj.sha,
        "model": model, "quant": quant, "max_length": max_length, "generation": generation,
        "subset": {"limit": limit, "seed": seed}, "n_samples": len(texts),
        "experiment": {"model": model_id, "method": method, "exp_id": exp_id},
    }

    # Chạy mới hay chạy tiếp: quyết định ở MỘT chỗ (`src/resume.py`), dựa trên ba giá trị mà
    # docs/00_workflow/02_rules.md mục 13 yêu cầu giống nhau (cấu hình, dữ liệu, mã repo).
    repo = run_meta.repo_info(url=config_data.get("url"), branch=config_data.get("branch"))
    config_sha256 = experiments.config_sha256(merged, prompt_text=prompt_obj.text)
    parts = resume.Parts(out_dir)
    done_count = parts.count()
    mode, reason = resume.decide(
        run_meta.read(out_dir), resume.fingerprint(config_sha256, version_id, repo["sha"]),
        done_count, force_new=new)
    if mode == resume.MODE_NEW and done_count:
        # KHÔNG chuyển kết quả cũ ở đây: `plan()` chỉ lập kế hoạch, người gọi có thể chỉ muốn XEM
        # trước (in ra cấu hình, kiểm tra) rồi quyết định không chạy. Việc chuyển khối cũ sang thư
        # mục con nằm trong `run()`, kèm số khối cần chuyển ở `stash_count`.
        info["stash_count"] = done_count

    # Mẫu đã chạy xong thì bỏ qua (chỉ khi chạy tiếp).
    skip = parts.keys() if mode == resume.MODE_RESUME else set()
    if skip:
        keep = [position for position, index in enumerate(row_index) if str(index) not in skip]
        texts = [texts[position] for position in keep]
        golds = [golds[position] for position in keep]
        row_index = [row_index[position] for position in keep]
        info["n_samples"] = len(texts)

    return {
        "config": config_data, "merged": merged, "model_id": model_id, "method": method,
        "exp_id": exp_id, "exp_dir": exp_dir, "inside": inside, "dataset": ds,
        "version_id": version_id, "split": split, "limit": limit, "seed": seed,
        "total": len(frame), "prompt": prompt_obj, "examples": examples_info,
        "label_map": label_map, "labels": label_names(label_map), "aspects": aspects,
        "texts": texts, "golds": golds, "row_index": row_index, "generation": generation,
        "sampled": sampled, "max_length": max_length, "model": model, "quant": quant,
        "names": names, "stash_count": info.get("stash_count", 0),
        "batch_size": batch_size, "quiet": quiet, "tag": tag, "out_dir": out_dir, "info": info,
        "repo": repo, "config_sha256": config_sha256, "mode": mode, "reason": reason,
        "parts": parts, "skip": skip,
        "files": input_files(
            ds, prompt_obj.path, model_id,
            prompts.resolve(prompt_obj.examples_value, exp_dir, examples=True)[1]
            if prompt_obj.examples_value else None),
    }


def run(plan_data, log=None):
    """Nạp model, sinh, chấm điểm, ghi kết quả, ghi nhận. CẦN GPU. TRẢ VỀ kết quả (dict).

    Trả về `{"out_dir", "mode", "scores", "metrics", "read_rate", "cost", "files", "stopped"}` để
    notebook dùng tiếp (in bảng, vẽ, quyết định bước sau). Cửa vào dòng lệnh chỉ in tóm tắt - nó
    không phải nơi chứa logic, nên đổi cách chạy cũng không đổi hợp đồng với notebook.
    """
    out_dir = plan_data["out_dir"]
    info = plan_data["info"]
    config_data = plan_data["config"]
    mode = plan_data["mode"]
    if mode == resume.MODE_STOP:
        print("DỪNG: {}".format(plan_data["reason"]))
        print("      Muốn chạy lại từ đầu thì dùng `--new` (kết quả cũ được chuyển sang thư mục "
              "con, không bị xoá).")
        return {"out_dir": out_dir, "mode": mode, "reason": plan_data["reason"], "stopped": True}

    # Nạp biến môi trường TRƯỚC khi mở phiên ghi nhận: `DAGSHUB_TOKEN` nằm ở Colab Secrets hoặc
    # file `.env` (cả hai đều không được commit). Không nạp thì token có trong máy mà phần ghi
    # nhận vẫn báo "thiếu token" - một lỗi im lặng rất khó đoán.
    runtime.load_env()

    with runlog.start(out_dir, mode=mode, info=info) as active:
        log = log or active
        if plan_data.get("stash_count"):
            # Kết quả cũ KHÔNG bị xoá: chuyển sang thư mục con, vì nó là dấu vết của một lần chạy
            # thật. Làm ở đây chứ không ở `plan()` để bước lập kế hoạch không đụng vào đĩa.
            stashed = plan_data["parts"].stash()
            info["stashed"] = utils.rel(stashed)
            print("Chạy lại từ đầu: {} khối cũ được chuyển sang {}".format(
                plan_data["stash_count"], utils.rel(stashed)))
        # Bản ghi lần chạy: ghi NGAY từ đầu, để lần chạy hỏng vẫn còn dấu vết (đang ở attempt nào,
        # với code và config nào). Chốt lại lúc đóng log; việc chốt chạy TRƯỚC phần ghi nhận nên
        # bản được tải lên máy chủ là bản đã chốt.
        record = run_meta.build(
            out_dir, tag=plan_data["tag"],
            experiment={"model": plan_data["model_id"], "method": plan_data["method"],
                        "exp_id": plan_data["exp_id"]},
            data={"dataset": plan_data["dataset"]["name"],
                  "version": plan_data["dataset"].get("version"),
                  "ma": plan_data["version_id"]},
            repo=plan_data["repo"],
            config={"sha256": plan_data["config_sha256"],
                    "layers": plan_data["merged"]["layers"],
                    "sources": plan_data["merged"]["sources"]},
            files=plan_data["files"],
            env=run_meta.env_info(kind=runtime.env_name()),
            note="chạy tiếp" if mode == resume.MODE_RESUME else None)
        run_meta.write(out_dir, record)
        log.on_close(run_meta.closer(record, out_dir, log=log))

        # Mở phiên ghi nhận ngay từ đầu: lần chạy hỏng giữa chừng vẫn phải KẾT THÚC run trên máy
        # chủ, nếu không thì trên DagsHub còn lại những run mãi ở trạng thái đang chạy và người
        # xem không biết run nào thật sự xong. `on_close` bảo đảm việc đó.
        session = tracking.begin(config_data, out_dir, info=info, log=log)
        log.on_close(tracking.closer(session, log=log))

        log.step("nạp model: {} (quant={})".format(info["model"], plan_data["quant"]))
        try:
            model, tokenizer, model_info = runner.load(plan_data["quant"],
                                                       model_name=plan_data["model"])
        except (ImportError, RuntimeError, OSError) as exc:
            # `requires` là thứ còn thiếu để chạy được, để lần sau không phải đoán.
            log.error("Không nạp được model: {}".format(exc), exc=exc,
                      context={"model": info["model"], "quant": plan_data["quant"]},
                      requires=["bitsandbytes + accelerate (lượng hóa 4-bit)",
                                "VRAM trống đủ cho model đang dùng"])
            raise RunError("Không nạp được model: {}".format(exc))
        log.step("đã nạp model: {}, {}".format(
            model_info.get("quant"), model_info.get("cách nạp")), seconds=log.elapsed())

        print_config(plan_data, model_info)
        print("Đang sinh...")
        log.step("bắt đầu sinh {} mẫu của split {} (batch {})".format(
            len(plan_data["texts"]), plan_data["split"], plan_data["batch_size"]))
        rows, _infos, _preds, cost = runner.run(
            plan_data["split"], plan_data["texts"], plan_data["golds"], plan_data["aspects"],
            plan_data["label_map"], plan_data["prompt"].name, model, tokenizer,
            batch_size=plan_data["batch_size"], max_length=plan_data["max_length"],
            generation=plan_data["generation"], row_index=plan_data["row_index"],
            quiet=plan_data["quiet"], store=plan_data["parts"])
        log.step("sinh xong {} mẫu mới".format(len(rows)), seconds=cost["giây"])
        return finish(plan_data, rows, cost, model_info, info, session, log)


def finish(plan_data, rows, cost, model_info, info, session, log):
    """Chấm điểm trên TOÀN BỘ mẫu của split rồi in + ghi kết quả. Trả về kết quả (dict).

    Vì sao chấm trên TOÀN BỘ mẫu: mẫu đã xong từ lần chạy trước lấy trong các khối, mẫu vừa chạy
    lấy từ bộ nhớ. Nhờ vậy một lượt chạy bị ngắt rồi chạy tiếp vẫn cho điểm của cả split, không
    phải điểm của phần còn lại - nếu không thì lần chạy tiếp nào cũng cho ra một con số khác nhau.
    """
    config_data = plan_data["config"]
    aspects = plan_data["aspects"]
    parts = plan_data["parts"]
    rows_all = records.merge(parts.records(), rows)
    golds_all, preds_all, infos_all = records.to_arrays(rows_all, aspects)
    read = metrics.read_rate(infos_all)
    log.step("tổng {} mẫu ({} mẫu mới), đọc được {}% kết quả".format(
        len(rows_all), len(rows), read["% đọc được"]))

    samples = scorers.Samples.build(
        aspects, golds_all, preds_all, task=config_data, labels=plan_data["labels"],
        sample_ids=[str(row[records.KEY_INDEX]) for row in rows_all],
        meta={"split": plan_data["split"], "dataset": plan_data["dataset"]["name"],
              "version_id": plan_data["version_id"]})
    result = scorers.run_all(samples, names=plan_data["names"])
    log.step("chấm xong {} chỉ số: {}".format(len(plan_data["names"]),
                                              ", ".join(plan_data["names"])))
    if samples.meta["dropped_neutral"]:
        log.step("loại {} ô neutral theo neutral_policy={}".format(
            samples.meta["dropped_neutral"], config_data["neutral_policy"]))

    print("\nĐọc kết quả:")
    for key, value in read.items():
        if key != "lí do lỗi":
            print("  {:<18}: {}".format(key, value))
    for reason, count in read["lí do lỗi"].items():
        print("      lỗi: {:<44} {}".format(reason, count))

    print("\nSố theo khía cạnh và sắc thái:")
    table_rows, table_columns = scorers.table(result["rows"])
    print_table(table_rows, table_columns)
    print("\nTổng hợp:")
    print_scores(result["scores"])
    print("\nChi phí lượt này: {} token sinh/review TB, {} giây, {} token sinh/giây".format(
        cost["token sinh TB"], cost["giây"], cost["token sinh/giây"]))
    if plan_data["skip"]:
        print("Dùng lại {} mẫu của lần chạy trước ({} mẫu chạy trong lượt này).".format(
            len(plan_data["skip"]), len(rows)))

    extra = dict(info)
    extra.update({
        "prompt_examples": plan_data["examples"],
        "model_info": model_info,
        "subset": {"limit": plan_data["limit"], "seed": plan_data["seed"],
                   "how": "random.Random(seed).sample trên split, giữ chỉ số dòng gốc"},
        "read_rate": read,
        "cost": cost,
        "scores_order": result["names"],
        # Lượt này là chạy mới hay chạy tiếp, và dùng lại bao nhiêu mẫu. Người đọc `metrics.json`
        # cần biết con số trước mặt có phải từ một lượt chạy liền mạch hay không.
        "resume": {"mode": plan_data["mode"], "reason": plan_data["reason"],
                   "reused": len(plan_data["skip"]), "new": len(rows)},
    })
    shown = write_all(plan_data, rows_all, samples, result, extra, session, log)
    return {"out_dir": plan_data["out_dir"], "mode": plan_data["mode"], "stopped": False,
            "scores": result["scores"], "metrics": result["rows"], "names": result["names"],
            "read_rate": read, "cost": cost, "files": shown, "samples": samples}


def write_all(plan_data, rows, samples, result, extra, session, log):
    """Ghi kết quả của lần chạy vào thư mục riêng của nó. Trả về {tên file: đường dẫn}.

    Thư mục riêng cho mỗi cấu hình nên tên file TRONG đó là tên cố định; cấu hình nằm ở tên thư
    mục. Nhờ vậy không bao giờ ghi đè số liệu của lần chạy khác, và cũng không phải ghép tên file
    từ cấu hình (ghép chuỗi là nguồn sự thật thứ hai, lệch lúc nào không biết).
    """
    out_dir = plan_data["out_dir"]
    save = dict(plan_data["config"].get("save") or {})
    shown = {}
    if save.get("predictions", True):
        shown[paths.pattern("predictions")] = runner.write(rows, runner.PREDICTION_COLUMNS,
                                                           out_dir)
        log.step("ghi {} dòng dự đoán".format(len(rows)))
    shown.update(scorers.write(out_dir, samples, names=result["names"],
                               save_confusion=bool(save.get("confusion", True)), extra=extra))
    log.step("đã ghi: {}".format(", ".join(sorted(shown))))

    # Ghi nhận SAU khi file đã nằm trên đĩa: máy chủ hỏng thì kết quả vẫn còn. Danh sách file tải
    # lên lấy từ `tracking.artifacts`, và chỉ lấy file đang có.
    session.log_params(extra)
    session.log_metrics(result["scores"])
    session.log_artifacts(tracking.base.artifact_paths(
        out_dir, plan_data["config"].get("artifacts")))
    log.step("ghi nhận: {} tham số, {} chỉ số, {} file".format(
        len(session.params), len(session.metrics), len(session.artifacts)))

    print("Hoàn tất. Đã ghi vào {}:".format(utils.rel(out_dir)))
    for name, path in shown.items():
        print("  - {:<18} {}".format(name, utils.rel(path)))
    print("  (tên thư mục '{}' ghi rõ cấu hình của lần chạy này)".format(plan_data["tag"]))
    return shown




