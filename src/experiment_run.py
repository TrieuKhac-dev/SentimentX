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

import json
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


def batch_size_of(model_id, config_data):
    """Số review mỗi lượt sinh, lấy từ `inference.batch_size` của model.

    KHÔNG đặt mặc định trong code: mặc định nằm ở `configs/models/<model_id>.yaml`, và một mặc định
    ngầm trong code là thứ khiến notebook (không truyền gì) chạy khác dòng lệnh (truyền 4) mà không
    ai biết. Đúng lỗi đã xảy ra: lượt chạy trong notebook chết ở `range(0, len(texts), None)`.
    """
    value = (config_data.get("inference") or {}).get("batch_size")
    if not value:
        raise RunError(
            "Thiếu `inference.batch_size` cho model '{}': xem {}. Khoá này quyết định số review mỗi "
            "lượt sinh nên không có giá trị mặc định trong code.".format(
                model_id, model_config.config_path(model_id)))
    return int(value)


def effective_max_length(config_data, passed=None):
    """Ngưỡng cắt ĐANG dùng cho lượt chạy này, theo thứ tự ưu tiên.

    `passed` (tham số dòng lệnh) > `preprocess.max_length` của cấu hình ĐÃ HỢP NHẤT > ngưỡng khai
    trong file cấu hình model.

    Vì sao đọc từ cấu hình đã hợp nhất: lớp THÍ NGHIỆM là lớp cuối khi hợp nhất, nên khai
    `preprocess.max_length` trong `experiments/<model>/<method>/expNNN/config.yaml` là ghi đè được
    ngưỡng của model - cách duy nhất để chạy một cấu hình với ngưỡng khác mà không sửa file dùng
    chung. Bản trước đọc thẳng file cấu hình model, nên ghi đè kiểu đó bị bỏ qua trong im lặng.
    """
    if passed:
        return int(passed)
    value = ((config_data or {}).get("preprocess") or {}).get("max_length")
    if value:
        return int(value)
    return qwen.limit()[0]


def run_hash(config_sha256):
    """Tên thư mục kết quả của một lượt chạy: **tám ký tự đầu của mã băm danh tính**.

    Tên thư mục CỐ Ý không mô tả gì. Đường dẫn đã nói thí nghiệm nào
    (`experiments/<model_id>/<method>/<expNNN>/`), còn cấu hình đầy đủ nằm trong mã băm và trong
    `run_meta.json` của chính thư mục đó. Nhờ vậy cùng một phép đo chạy trên Colab và trên máy cá
    nhân ra **cùng một tên thư mục** - điều kiện để copy kết quả từ Drive về repo, và để hai bên
    không sinh ra hai thư mục "trông khác nhau mà là một".
    """
    return str(config_sha256)[:8]


def out_dir_of(hash8, model_id=None, method=None, exp_id=None):
    """Thư mục kết quả của lượt chạy: `experiments/<model>/<method>/<exp>/results/<hash8>/`.

    KHÔNG còn đường ghi nào NGOÀI thí nghiệm: mọi kết quả đều thuộc một thí nghiệm, nên con số luôn
    truy được về một cấu hình đã ghim. Thiếu định danh thí nghiệm là LỖI, không phải chuyện tự chọn
    chỗ ghi khác - kết quả nằm ngoài thí nghiệm thì không ai biết nó thuộc bản code nào.
    """
    missing = [name for name, value in (("model_id", model_id), ("method", method),
                                        ("exp_id", exp_id)) if not value]
    if missing:
        raise RunError(
            "Chưa biết kết quả thuộc thí nghiệm nào (thiếu {}).\n"
            "      Mở notebook của thí nghiệm rồi bấm Run all, hoặc tạo thí nghiệm mới bằng\n"
            "      `python scripts/new_experiment.py <model_id>/<method>/<expNNN>`.".format(
                ", ".join(missing)))
    return paths.results_dir(model_id, method, exp_id) / str(hash8)


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


def input_files(ds, prompt_path, model_id, examples_path=None, system_path=None):
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
    entries.append((system_path, run_meta.ROLE_SYSTEM))
    return run_meta.input_files(entries)


def merged_task(config_data):
    """Ba khoá định nghĩa BÀI TOÁN đang giải, để ghi vào bản ghi lần chạy.

    Tách ra thành hàm vì `run_meta.json` và `metrics.json` phải nói cùng một chuyện: đổi không
    gian nhãn là đổi bài toán, không phải đổi cách trình bày, nên bản ghi phải nói rõ.
    """
    return {name: config_data.get(name)
            for name in ("label_space", "neutral_policy", "not_mentioned")}


def run_record(plan_data):
    """Các giá trị CHỈ CÓ KHI CHẠY, để ghi vào khối `run` của `run_meta.json`.

    Vì sao cần: `metrics.json` chỉ ra đời khi lượt chạy XONG, nên một lượt bị ngắt giữa chừng không
    cho biết nó đã đo bằng gì. Khối này ghi ngay từ lúc bắt đầu (cùng lúc với `run.log`), nên tra
    được cả với lượt chạy hỏng. Máy/GPU/kiểu số không nằm ở đây mà ở khối `env` - chúng chỉ biết
    được SAU khi nạp model.
    """
    return {
        "split": plan_data["split"],
        "limit": plan_data["limit"],
        "n_samples": plan_data["info"]["n_samples"],
        "subset_seed": plan_data["seed"],
        "quant": effective_quant(plan_data.get("quant"), plan_data["config"]),
        "max_length": plan_data["max_length"],
        "batch_size": plan_data["batch_size"],
        "generation": dict(plan_data.get("generation") or {}),
        "prompt": plan_data["prompt"].name,
        "prompt_sha": plan_data["prompt"].sha,
        "examples_sha": (plan_data["examples"] or {}).get("sha"),
        "system_sha": (plan_data["system"] or {}).get("sha"),
    }


def log_config(plan_data, log):
    """Ghi bảng GHI ĐÈ và giá trị hiệu lực vào `run.log` với nhãn `[CONFIG]`.

    Vì sao phải nằm trong FILE: bảng này cũng được in ra màn hình, nhưng notebook gửi cho người
    nhận không giữ output (CI bắt buộc sạch output), nên mất bản in là mất dấu vết "khoá này do
    lớp cấu hình nào đặt".
    """
    config_data = plan_data["config"]
    merged = plan_data.get("merged") or {}
    log.config("thí nghiệm: {}/{}/{} | dữ liệu: {} | split chấm: {} | n: {}".format(
        plan_data["model_id"] or "-", plan_data["method"] or "-", plan_data["exp_id"] or "-",
        plan_data["version_id"], plan_data["split"], plan_data["limit"] or "cả split"))
    for name, before, after, layer in merged.get("overrides") or []:
        log.config("đè {}: {} <- {}".format(name, before, after))
    if not merged.get("overrides"):
        log.config("không có khoá nào bị lớp sau đè")
    task = merged_task(config_data)
    log.config("bài toán: label_space={} neutral_policy={} not_mentioned={}".format(
        task["label_space"], task["neutral_policy"], task["not_mentioned"]))
    log.config("prompt: {} (sha {}) | ví dụ: {} | sinh: {}".format(
        plan_data["prompt"].name, plan_data["prompt"].sha,
        (plan_data["examples"] or {}).get("sha") or "không dùng",
        "greedy" if not plan_data["sampled"] else "lấy mẫu"))
    generation = dict(plan_data.get("generation") or {})
    log.config("chạy: max_length={} | max_new_tokens={} | batch={} | do_sample={} "
               "temperature={} top_p={} top_k={} seed={}".format(
                   plan_data["max_length"], generation.get("max_new_tokens"),
                   plan_data["batch_size"], generation.get("do_sample"),
                   generation.get("temperature"), generation.get("top_p"),
                   generation.get("top_k"), generation.get("seed")))


def sibling_runs(out_dir):
    """Các lượt chạy KHÁC đã có của cùng thí nghiệm: một dòng mô tả mỗi thư mục.

    In ra trước khi bắt đầu, vì mã băm danh tính có cả commit: ghim lại bản code (kể cả chỉ sửa tài
    liệu) là ra thư mục MỚI, và người chạy cần thấy mình đang tạo lượt mới vì bản code/cấu hình khác
    - chứ không phải mất một lượt chạy dài trong im lặng.
    """
    found = []
    parent = Path(out_dir).parent
    if not parent.is_dir():
        return found
    for path in sorted(parent.glob("*")):
        if not path.is_dir() or path.resolve() == Path(out_dir).resolve():
            continue
        record = run_meta.read(path)
        if not record:
            continue
        run = dict(record.get("run") or {})
        scores = ((_read_json(path / paths.pattern("metrics_json")).get("scores") or {})
                  .get("accuracy") or {})
        found.append("{}  commit {}  {:<9}  accuracy macro {}".format(
            path.name, str((record.get("repo") or {}).get("sha", ""))[:7],
            run.get("status", ""), scores.get("macro", "-")))
    return found


def _read_json(path):
    """Đọc JSON, trả {} nếu thiếu file hoặc file hỏng (việc in cảnh báo không được làm chết lượt chạy)."""
    path = Path(path)
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


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


def system_label(prompt_obj, system_info):
    """Khối chỉ dẫn hệ thống của lượt chạy, nói rõ nó ĐẾN TỪ ĐÂU.

    Hai nguồn: file khối hệ thống dùng chung (khoá `system_prompt` của config), hoặc ngay trong file
    prompt (mục `[SYSTEM]`). In "không dùng" khi prompt có mục `[SYSTEM]` là nói SAI: model vẫn nhận
    một khối hệ thống, chỉ là nó nằm trong chính file prompt - người đọc log dễ tưởng model không có
    chỉ dẫn nào.
    """
    if system_info:
        return "{} (sha {})".format(system_info["file"], system_info["sha"])
    sections = prompt_obj.sections or []
    if any(name == "system" for name, _text in sections):
        return "trong chính file prompt (mục [SYSTEM])"
    return "không dùng"


def print_config(plan_data, model_info):
    """In cấu hình của lần chạy TRƯỚC khi sinh, để nhìn là biết đang đo cái gì."""
    prompt = plan_data["prompt"]
    examples = plan_data["examples"]
    system = plan_data.get("system")
    print("Cấu hình chạy:")
    print("  thí nghiệm  : {}/{}/{}".format(
        plan_data["model_id"], plan_data["method"], plan_data["exp_id"]))
    print("  thư mục kết quả: {} (mã băm danh tính của lượt chạy)".format(
        utils.rel(plan_data["out_dir"])))
    print("  prompt      : {} ({}), sha {}".format(prompt.name, prompt.where, prompt.sha))
    print("  ví dụ       : {}".format(
        "{} - {} ví dụ, sha {}".format(examples["file"], examples["examples"],
                                       examples["sha"]) if examples else "không dùng"))
    print("  hệ thống    : {}".format(system_label(prompt, system)))
    print("  tập dữ liệu : {} - {}{}".format(
        plan_data["split"], plan_data["limit"] or plan_data["total"],
        " (TẬP CON ngẫu nhiên, seed {})".format(plan_data["seed"])
        if plan_data["limit"] and plan_data["limit"] < plan_data["total"] else ""))
    print("  ngưỡng cắt  : {} token (preprocess.max_length đang dùng)".format(
        plan_data["max_length"]))
    print("  sinh        : {}".format(
        "greedy (tái lập)" if not plan_data["sampled"] else
        "lấy mẫu: temperature={}, top_p={}, top_k={}, seed={}".format(
            plan_data["generation"]["temperature"], plan_data["generation"]["top_p"],
            plan_data["generation"]["top_k"], plan_data["generation"]["seed"])))
    print("  tối đa sinh : {} token/review".format(plan_data["generation"]["max_new_tokens"]))
    print("  mỗi lô      : {} review (inference.batch_size)".format(plan_data["batch_size"]))
    print("  model       : {} - {}, {}, {}".format(
        plan_data["model"], model_info.get("quant"), model_info.get("cách nạp"),
        model_info.get("thiết bị")))
    print()


def run_model(config_data, model=None):
    """Model của lượt chạy: tham số truyền vào > `hf_model` của config > model mặc định của module.

    Một chỗ duy nhất, vì tên thư mục kết quả có phần model khi nó KHÁC `checkpoint` của config:
    `plan()` và `preflight` phải chọn cùng một giá trị, nếu không thì hai bên nhìn hai thư mục khác
    nhau (đã từng xảy ra với `SENTIMENTX_MODEL` trên máy cá nhân).
    """
    return model or config_data.get("hf_model") or qwen.MODEL_NAME


def run_prompt(config_data, model_id=None, method=None, exp_id=None, prompt=None, examples=None,
               base_dir=None):
    """Nạp prompt của một lượt chạy (và đăng ký vào `qwen` cho các bước sau dùng theo tên).

    Một chỗ duy nhất, vì `plan()` và `preflight` đều cần CÙNG prompt đó - nạp ở hai nơi là hai nơi
    có thể lệch nhau (một nơi dùng tên trong thư viện, nơi kia dùng đường dẫn).

    `base_dir`: thư mục thí nghiệm để giải đường dẫn tương đối trong config. `plan()` truyền thư mục
    nó đang làm việc (kết quả đã nạp có khoá `dir`), còn khi chỉ có tên thí nghiệm thì suy ra.
    """
    if base_dir is None and model_id and method and exp_id:
        base_dir = paths.experiment_dir(model_id, method, exp_id)
    return qwen.load_prompt(
        prompt or config_data.get("prompt"), base_dir=base_dir,
        examples=examples if examples is not None else config_data.get("examples"),
        system=config_data.get("system_prompt"))


def side_shas(prompt_obj):
    """`{nhãn: (đường dẫn, sha)}` của các file đi kèm prompt, để đưa vào dấu vân tay.

    Bộ ví dụ few-shot và khối hệ thống KHÔNG nằm trong file prompt, nên nếu không băm chúng thì đổi
    bộ ví dụ mà dấu vân tay không đổi - lượt chạy bị ngắt sẽ RESUME trên bộ ví dụ cũ.
    """
    found = {}
    for name, info in (("examples", prompt_obj.examples_info()),
                       ("system", prompt_obj.system_info())):
        if info:
            found[name] = (info.get("file"), info.get("sha"))
    return found


def effective_quant(quant, config_data):
    """Cách biểu diễn model của lượt chạy: tham số truyền vào > `inference.quantization` của config.

    `auto` nghĩa là "theo config", nên giá trị hiệu lực lấy từ config. Trả về None khi model không
    lượng hoá - lúc đó tên thư mục không có phần này.
    """
    if quant and quant != "auto":
        return str(quant)
    value = (config_data.get("inference") or {}).get("quantization")
    return str(value) if value else None


def run_generation(config_data, quant, sampled, max_new_tokens=None, seed=42):
    """Cấu hình sinh HIỆU LỰC của một lượt chạy: `plan()` và `preflight` dùng chung hàm này.

    Nhiệt độ/top_p/top_k lấy theo model card (hoặc giá trị config khai đè), seed chỉ có nghĩa khi
    lấy mẫu. Cấu hình sinh được băm vào dấu vân tay lượt chạy, nên hai bên tính khác nhau là hai
    dấu vân tay khác nhau - và lượt chạy bị ngắt sẽ RESUME trên cách sinh khác.
    """
    card, _sampled = settings_of(config_data, do_sample=sampled)
    return runner.settings(quant=quant, max_new_tokens=max_new_tokens, do_sample=sampled,
                           temperature=card.get("temperature"), top_p=card.get("top_p"),
                           top_k=card.get("top_k"), seed=seed if sampled else None)


def run_identity(config_data, version_id, prompt_obj, model_id=None, method=None, exp_id=None,
                 generation=None, max_length=None):
    """Thư mục kết quả + mã băm danh tính + dấu vân tay của MỘT lượt chạy: chỗ DUY NHẤT quyết định.

    `plan()` (lượt chạy thật) và `preflight` (kiểm trước) đều gọi hàm này, nên không thể nói hai
    chuyện khác nhau. Đã từng lệch thật (25/09/2026): preflight báo `NEW - chưa có lần chạy nào
    trong thư mục này` trong khi lượt chạy cùng lúc báo `RESUME - chạy tiếp từ 16 mẫu đã xong`, vì
    preflight nhìn thư mục PHIÊN BẢN còn lượt chạy nhìn thư mục LƯỢT CHẠY.

    MÃ BĂM DANH TÍNH - và vì sao đúng những thứ này:

    | Có trong mã băm | Không có |
    | --- | --- |
    | Nội dung cấu hình đã hợp nhất (bài toán, prompt nào, split, n, cách sinh, lượng hoá, ngưỡng cắt) | Máy, GPU, kiểu số (fp16/bf16) |
    | Nội dung file prompt + file ví dụ + khối hệ thống | Nguồn trọng số (id HF hay thư mục trên đĩa) |
    | Mã phiên bản dữ liệu | Thời điểm chạy, số lần chạy |
    | **Commit đã ghim** (`repo.sha`) | |
    | `generation` và `max_length` hiệu lực (kể cả khi truyền vào lúc chạy) | |

    Nhờ vậy cùng một phép đo trên Colab và trên máy cá nhân ra CÙNG thư mục (copy qua lại được),
    còn đổi commit - kể cả chỉ sửa tài liệu - là thư mục KHÁC, nên lượt chạy mới không bao giờ trộn
    vào kết quả cũ.

    Trả về dict gồm `config_sha256`, `fingerprint`, `hash`, `out_dir`, `repo`.
    """
    repo = run_meta.repo_info(url=config_data.get("url"), branch=config_data.get("branch"))
    config_sha = experiments.config_sha256(
        {"config": config_data}, prompt_text=prompt_obj.text, side_files=side_shas(prompt_obj),
        extra={"generation": generation or {}, "max_length": max_length,
               "version_id": version_id, "repo_sha": repo["sha"]})
    fingerprint = resume.fingerprint(config_sha, version_id, repo["sha"])
    hash8 = run_hash(config_sha)
    return {"config_sha256": config_sha, "fingerprint": fingerprint, "hash": hash8,
            "out_dir": out_dir_of(hash8, model_id, method, exp_id), "repo": repo}


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
    # Giữ lại tham số ĐÈ của người gọi (dòng lệnh hoặc `SENTIMENTX_MODEL`): đường encoder dùng nó
    # làm nguồn trọng số, còn đường prompt để `run_model` suy tiếp từ config.
    model_override = model
    model = run_model(config_data, model)
    # Số review mỗi lượt sinh: tham số truyền vào (dòng lệnh) -> `inference.batch_size` của model.
    if not batch_size:
        batch_size = batch_size_of(model_id, config_data)

    # Model encoder đi đường khác: nó phải HỌC trước khi trả lời, và không có prompt nào để ghim.
    # Phần chấm điểm và ghi kết quả thì dùng chung, nên ở đây chỉ rẽ nhánh phần LẬP KẾ HOẠCH.
    if model_config.approach_of(config_data, model_id) == "encoder":
        from src import encoder_run

        return encoder_run.plan(config_data, merged, ds=ds, version_id=version_id, split=split,
                                limit=limit, model=model_override, seed=seed, batch_size=batch_size,
                                max_length=max_length, quant=quant, new=new, quiet=quiet)

    # Prompt: tên trong thư viện dùng chung, hoặc đường dẫn tới file cạnh notebook. Nạp xong thì
    # đăng ký luôn (`qwen.load_prompt`), vì các bước sau chỉ truyền được một cái TÊN.
    prompt_value = prompt or config_data.get("prompt")
    examples_value = examples if examples is not None else config_data.get("examples")
    prompt_obj = run_prompt(config_data, model_id, method, exp_id,
                            prompt=prompt_value, examples=examples_value, base_dir=exp_dir)
    # Thông tin truy vết đọc từ CHÍNH prompt đã nạp (đường dẫn đã giải xong), không giải lại từ
    # config: hai chỗ giải đường dẫn là hai chỗ có thể lệch nhau.
    examples_info = prompt_obj.examples_info()
    system_info = prompt_obj.system_info()

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
    _card, sampled = settings_of(config_data, do_sample=sample)
    # Cách biểu diễn model tính MỘT LẦN: cấu hình sinh ghi vào bản ghi và dấu vân tay đều dùng giá
    # trị hiệu lực, không dùng chữ "auto" - hai chỗ ghi hai giá trị khác nhau là hai dấu vân tay.
    quant_effective = effective_quant(quant, config_data)
    generation = run_generation(config_data, quant_effective, sampled, max_new_tokens, seed)
    max_length = effective_max_length(config_data, max_length)

    identity = run_identity(config_data, version_id, prompt_obj,
                            model_id=model_id, method=method, exp_id=exp_id,
                            generation=generation, max_length=max_length)
    hash8 = identity["hash"]
    out_dir = identity["out_dir"]
    others = sibling_runs(out_dir)
    if others:
        print("LƯU Ý: thí nghiệm này đã có {} lượt chạy KHÁC:".format(len(others)))
        for row in others:
            print("  {}".format(row))
        print("Lượt này ghi vào thư mục MỚI '{}' (bản code/cấu hình khác). Kết quả cũ không bị "
              "đụng tới.\n".format(hash8))
    if split == "test":
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
    # docs/00_workflow/02_rules.md mục 13 yêu cầu giống nhau (cấu hình, dữ liệu, mã repo). Ba giá
    # trị đó lấy từ `run_identity` - cùng hàm mà preflight gọi, nên hai bên không thể lệch nhau.
    repo = identity["repo"]
    config_sha256 = identity["config_sha256"]
    parts = resume.Parts(out_dir)
    # Cột của bảng dự đoán: đường chạy này LUÔN gửi prompt cho model, nên bảng ghi luôn chuỗi đã gửi
    # (xem `records.columns`). Đường chạy model encoder sẽ khai bảng KHÔNG có cột này.
    columns = records.columns(with_prompt=True)
    done_count = parts.count()
    mode, reason = resume.decide(
        run_meta.read(out_dir), resume.fingerprint(config_sha256, version_id, repo["sha"]),
        done_count, force_new=new)
    if mode == resume.MODE_NEW and done_count:
        # Không xảy ra được với mã băm danh tính nằm trong tên thư mục: trong một thư mục thì mọi
        # attempt đều cùng code + cấu hình + dữ liệu. Nếu vẫn thấy, tức là thư mục bị trộn bằng tay
        # (sửa run_meta.json, hoặc đổi tên thư mục cũ) - DỪNG, vì chạy tiếp sẽ trộn hai phép đo.
        raise RunError(
            "Thư mục {} có {} khối kết quả nhưng bản ghi không khớp lượt chạy hiện tại.\n"
            "      Không dùng lại được. Xoá thư mục đó rồi chạy lại.".format(
                utils.rel(out_dir), done_count))

    # Mẫu đã chạy xong thì bỏ qua (chỉ khi chạy tiếp).
    skip = parts.keys() if mode == resume.MODE_RESUME else set()
    if skip:
        keep = [position for position, index in enumerate(row_index) if str(index) not in skip]
        texts = [texts[position] for position in keep]
        golds = [golds[position] for position in keep]
        row_index = [row_index[position] for position in keep]
        info["n_samples"] = len(texts)

    # Số bản ghi của TỪNG vai, và dấu vân tay tập đánh giá: hai thứ người đọc bản ghi cần biết để
    # hiểu con số trước mặt. Đếm bằng `preflight.count_rows` (đếm BẢN GHI, không đếm dòng - review
    # trong dữ liệu này có xuống dòng bên trong ô được trích dẫn), nhập muộn để cấp module của file
    # này không phụ thuộc preflight.
    from src import preflight
    roles = dict((config_data.get("data") or {}).get("roles") or {})
    rows_by_role = {}
    for role, name in sorted(roles.items()):
        path = paths.processed(version_id) / "{}.csv".format(name)
        if path.is_file():
            rows_by_role[role] = preflight.count_rows(path)
    lock = dict(ds.get("eval_lock") or {})
    eval_lock = {"enforce": bool(lock.get("enforce", False)),
                 "declared": (lock.get("test") or {}).get("sha256")}

    return {
        "config": config_data, "merged": merged, "model_id": model_id, "method": method,
        "exp_id": exp_id, "exp_dir": exp_dir, "dataset": ds,
        "version_id": version_id, "split": split, "limit": limit, "seed": seed,
        "total": len(frame), "prompt": prompt_obj, "examples": examples_info,
        "system": system_info,
        "label_map": label_map, "labels": label_names(label_map), "aspects": aspects,
        "texts": texts, "golds": golds, "row_index": row_index, "generation": generation,
        "sampled": sampled, "max_length": max_length, "model": model, "quant": quant,
        "names": names,
        "columns": columns,
        "batch_size": batch_size, "quiet": quiet, "hash": hash8, "out_dir": out_dir,
        "info": info,
        "repo": repo, "config_sha256": config_sha256, "mode": mode, "reason": reason,
        "parts": parts, "skip": skip, "roles": roles, "rows_by_role": rows_by_role,
        "eval_lock": eval_lock,
        "files": input_files(
            ds, prompt_obj.path, model_id,
            prompt_obj.examples_path if prompt_obj.examples_value else None,
            prompt_obj.system_path if prompt_obj.system_value else None),
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
        print("      Đây là lượt chạy đã XONG của đúng bản code + cấu hình + dữ liệu này.")
        print("      Muốn chạy lại từ đầu thì XOÁ thư mục kết quả rồi chạy lại:\n"
              "        {}".format(utils.rel(out_dir)))
        return {"out_dir": out_dir, "mode": mode, "reason": plan_data["reason"], "stopped": True}

    # Đường chạy encoder có vòng đời riêng (huấn luyện rồi mới suy luận): nó tự mở nhật ký và bản
    # ghi, rồi quay lại `finish` của file này để chấm điểm và ghi kết quả - một bản chấm, hai đường.
    if plan_data.get("approach") == "encoder":
        from src import encoder_run

        return encoder_run.run(plan_data, log=log)

    # Nạp biến môi trường TRƯỚC khi mở phiên ghi nhận: `DAGSHUB_TOKEN` nằm ở Colab Secrets hoặc
    # file `.env` (cả hai đều không được commit). Không nạp thì token có trong máy mà phần ghi
    # nhận vẫn báo "thiếu token" - một lỗi im lặng rất khó đoán.
    runtime.load_env()

    with runlog.start(out_dir, mode=mode, info=info) as active:
        log = log or active
        # Bản ghi lần chạy: ghi NGAY từ đầu, để lần chạy hỏng vẫn còn dấu vết (đang ở attempt nào,
        # với code và config nào). Chốt lại lúc đóng log; việc chốt chạy TRƯỚC phần ghi nhận nên
        # bản được tải lên máy chủ là bản đã chốt.
        record = run_meta.build(
            out_dir, hash8=plan_data["hash"],
            experiment={"model": plan_data["model_id"], "method": plan_data["method"],
                        "exp_id": plan_data["exp_id"]},
            data={"dataset": plan_data["dataset"]["name"],
                  "version": plan_data["dataset"].get("version"),
                  "ma": plan_data["version_id"],
                  "roles": dict(plan_data["roles"]),
                  "rows": dict(plan_data["rows_by_role"]),
                  "eval_lock": dict(plan_data["eval_lock"])},
            repo=plan_data["repo"],
            config={"sha256": plan_data["config_sha256"],
                    "layers": plan_data["merged"]["layers"],
                    "sources": plan_data["merged"]["sources"]},
            task=merged_task(config_data),
            overrides=plan_data["merged"]["overrides"],
            files=plan_data["files"],
            env=run_meta.env_info(kind=runtime.env_name()),
            run_extra=run_record(plan_data),
            note="chạy tiếp" if mode == resume.MODE_RESUME else None)
        run_meta.write(out_dir, record)
        log.on_close(run_meta.closer(record, out_dir, log=log))

        # Mở phiên ghi nhận ngay từ đầu: lần chạy hỏng giữa chừng vẫn phải KẾT THÚC run trên máy
        # chủ, nếu không thì trên DagsHub còn lại những run mãi ở trạng thái đang chạy và người
        # xem không biết run nào thật sự xong. `on_close` bảo đảm việc đó.
        session = tracking.begin(config_data, out_dir, info=info, log=log)
        log.on_close(tracking.closer(session, log=log))

        # Cấu hình ĐANG dùng vào log TRƯỚC khi nạp model: đây là thứ người đọc cần khi lần chạy
        # hỏng giữa chừng, mà bảng in ra màn hình thì notebook không giữ lại.
        log_config(plan_data, log)

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

        # Máy và lượng hoá chỉ biết được SAU khi nạp model, nên bổ sung vào bản ghi rồi ghi lại.
        # Không có hai thứ này thì không tra được vì sao cùng một cấu hình mà hai máy cho số khác
        # nhau (4-bit so với bf16 là hai phép đo khác nhau).
        record["env"].update(run_meta.device_info(model_info, quant=plan_data["quant"]))
        run_meta.write(out_dir, record)

        print_config(plan_data, model_info)
        print("Đang sinh...")
        log.step("bắt đầu sinh {} mẫu của split {} (batch {})".format(
            len(plan_data["texts"]), plan_data["split"], plan_data["batch_size"]))
        rows, _infos, _preds, cost = runner.run(
            plan_data["split"], plan_data["texts"], plan_data["golds"], plan_data["aspects"],
            plan_data["label_map"], plan_data["prompt"].name, model, tokenizer,
            batch_size=plan_data["batch_size"], max_length=plan_data["max_length"],
            generation=plan_data["generation"], row_index=plan_data["row_index"],
            quiet=plan_data["quiet"], store=plan_data["parts"],
            columns=plan_data["columns"])
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
    rows_all = records.merge(parts.records(), rows, plan_data["columns"])
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
    if plan_data.get("approach") == "encoder":
        # Model encoder không sinh token, nên "token sinh" và "token/giây" vô nghĩa ở đây; con số
        # có nghĩa là thời gian huấn luyện + suy luận của cả lượt.
        print("\nChi phí lượt này: {} giây cho {} mẫu (gồm {} bước huấn luyện)".format(
            cost["giây"], len(rows_all), cost.get("số bước", "-")))
    else:
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
        shown[paths.pattern("predictions")] = runner.write(rows, plan_data["columns"],
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
    print("  (thư mục '{}' là mã băm danh tính của lượt chạy này - mở run_meta.json để đọc cấu hình)"
          .format(plan_data["hash"]))
    return shown




