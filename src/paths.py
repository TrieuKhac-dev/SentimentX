# -*- coding: utf-8 -*-
"""Đường dẫn của dự án, lấy từ MỘT nguồn duy nhất là `configs/paths.yaml`.

VÌ SAO CHỈ MỘT NGUỒN
Đổi cấu trúc thư mục thì chỉ sửa `configs/paths.yaml`, không phải đi tìm từng chỗ
viết cứng đường dẫn trong code.

GHI ĐÈ KHI CHẠY TRÊN COLAB
Hai biến môi trường đổi gốc đường dẫn, không cần symlink:

    SENTIMENTX_DATA_ROOT      gốc thay cho `<repo>/data`
    SENTIMENTX_RESULTS_ROOT   gốc thay cho `<repo>/experiments`

GIỚI HẠN ĐÃ BIẾT
`.gitignore` và `.gitattributes` không đọc được YAML, nên khi đổi cây thư mục vẫn phải
sửa tay hai file đó. Trong code chỉ còn `ROOT_DIR` suy từ `__file__`, vì cần nó để tìm
ra chính file cấu hình này.
"""

import os
from functools import lru_cache
from pathlib import Path

import yaml

ENV_DATA_ROOT = "SENTIMENTX_DATA_ROOT"
ENV_RESULTS_ROOT = "SENTIMENTX_RESULTS_ROOT"

ROOT_DIR = Path(__file__).resolve().parent.parent
PATHS_CONFIG_PATH = ROOT_DIR / "configs" / "paths.yaml"


@lru_cache(maxsize=1)
def config():
    """Nội dung `configs/paths.yaml`, đã trao đổi chỗ các tham chiếu `{...}`.

    Nạp một lần cho cả tiến trình. Báo lỗi rõ nếu file thiếu hoặc sai định dạng.
    """
    if not PATHS_CONFIG_PATH.exists():
        raise FileNotFoundError(
            "Thiếu file cấu hình đường dẫn: {}. Xem docs/05_config/01_paths.md.".format(
                PATHS_CONFIG_PATH)
        )
    with PATHS_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    resolved = {"roots": {}, "data": {}, "reports": {}, "configs": {},
                "patterns": dict(raw.get("patterns") or {}),
                "colab": dict(raw.get("colab") or {}),
                "canonical": dict(raw.get("canonical") or {})}
    resolved["version"] = raw.get("version", 1)

    # Giá trị của `roots` được các nhóm khác tham chiếu bằng tên, ví dụ "{data}/raw".
    for group in ("roots", "data", "reports", "configs"):
        for key, value in (raw.get(group) or {}).items():
            text = str(value)
            for name, target in resolved["roots"].items():
                text = text.replace("{" + name + "}", target)
            if group == "roots":
                resolved["roots"][key] = text
            else:
                resolved[group][key] = text
    return resolved


def cfg():
    """Lối tắt cho `config()`."""
    return config()


def root():
    """Thư mục gốc của repo."""
    return ROOT_DIR


def data_root():
    """Gốc dữ liệu. Trên Colab đổi được bằng biến môi trường."""
    override = os.environ.get(ENV_DATA_ROOT, "").strip()
    return Path(override) if override else root() / cfg()["roots"]["data"]


def results_root():
    """Gốc ghi kết quả thí nghiệm. Trên Colab đổi được bằng biến môi trường."""
    override = os.environ.get(ENV_RESULTS_ROOT, "").strip()
    return Path(override) if override else root() / cfg()["roots"]["experiments"]


def experiments_dir():
    """Thư mục định nghĩa thí nghiệm (config, notebook, prompt). Luôn nằm trong repo."""
    return root() / cfg()["roots"]["experiments"]


def templates_dir():
    return root() / cfg()["roots"]["templates"]


def docs_dir():
    return root() / cfg()["roots"]["docs"]


def configs_dir():
    return root() / cfg()["roots"]["configs"]


def data(*parts):
    """Đường dẫn trong `data/`, ví dụ `data("raw")`."""
    return data_root().joinpath(*parts)


def reports_dir(name=None):
    """Thư mục report sinh tự động, hoặc một nhóm report cụ thể."""
    if name is None:
        return data("reports")
    if name not in cfg()["reports"]:
        raise KeyError(
            "Không có nhóm report '{}'. Các nhóm hiện có: {}.".format(
                name, ", ".join(sorted(cfg()["reports"])))
        )
    return data_root() / cfg()["reports"][name]


def report(name=None):
    """Nhóm report sinh tự động, ví dụ `report("experiment_registry")`."""
    return reports_dir(name)


def assets_dir():
    return data("assets")


def reference_publication_dir():
    return data("reference_publication")


def raw_dir(name, raw_version):
    """Thư mục dữ liệu gốc của một phiên bản: `data/raw/<name>/<raw_version>/`."""
    return data("raw") / str(name) / str(raw_version)


def processed(ma):
    """Thư mục dataset của một mã phiên bản: `data/processed/<mã>/`."""
    return data("processed") / str(ma)


def config_path(*parts):
    """Đường dẫn trong `configs/`."""
    return configs_dir().joinpath(*parts)


def experiment_dir(model_id, method, exp_id):
    """Thư mục một thí nghiệm: `experiments/<model_id>/<method>/<expNNN>/`."""
    return experiments_dir() / str(model_id) / str(method) / str(exp_id)


def results_dir(model_id, method, exp_id):
    """Thư mục kết quả của một thí nghiệm: `<gốc kết quả>/<model>/<method>/<exp>/results/`.

    Mỗi LƯỢT CHẠY là một thư mục con tên là **mã băm danh tính** (xem
    `experiment_run.run_identity`), nên không còn tầng "mã phiên bản dữ liệu" ở giữa: mã phiên bản
    dữ liệu đã nằm trong chính mã băm, và nhờ vậy đường dẫn ngắn, đọc được, và giống nhau trên mọi
    máy (`experiments/<model_id>/<method>/<expNNN>/results/<hash8>/`).
    """
    return (results_root() / str(model_id) / str(method) / str(exp_id)
            / cfg()["patterns"].get("run_meta_dir", "results"))


def pattern(key, **values):
    """Tên file hoặc tên thư mục theo mẫu trong `configs/paths.yaml`.

    Ví dụ: `pattern("run_log")` -> `run.log`;
           `pattern("pred_parts", n=3)` -> `predictions/part_0003.jsonl`.
    """
    patterns = cfg()["patterns"]
    if key not in patterns:
        raise KeyError(
            "Không có mẫu tên '{}'. Các mẫu hiện có: {}.".format(
                key, ", ".join(sorted(patterns)))
        )
    return str(patterns[key]).format(**values)


def ordered_lists():
    """Tên các khoá mà danh sách của chúng có thứ tự có nghĩa khi băm cấu hình."""
    return list(cfg()["canonical"].get("ordered_lists") or [])


def describe():
    """Vài dòng mô tả gốc đường dẫn đang dùng, để ghi vào log."""
    return {
        "root": str(root()),
        "data_root": str(data_root()),
        "results_root": str(results_root()),
        "data_root_override": os.environ.get(ENV_DATA_ROOT, ""),
        "results_root_override": os.environ.get(ENV_RESULTS_ROOT, ""),
    }
