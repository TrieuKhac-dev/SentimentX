# -*- coding: utf-8 -*-
"""Ghi và đọc FILE KẾT QUẢ (JSON) - cầu nối giữa "tính toán" và "trình bày".

Dự án tách thành 3 tầng độc lập:

    1. TÍNH TOÁN   run_eda.py / run_pipeline.py
                   -> chỉ đo lường, ghi số liệu ra file kết quả JSON + CSV
    2. LƯU TRỮ     data/reports/**, data/processed/**
    3. TRÌNH BÀY   build_report.py
                   -> đọc lại file kết quả rồi vẽ Plotly + Jinja2 ra HTML

Vì sao tách như vậy:
    - Chạy lại pipeline tốn thời gian; sửa giao diện báo cáo thì không cần chạy lại.
    - Dữ liệu kết quả nằm trong file JSON nên soi được bằng mắt, so sánh được
      giữa hai phiên bản, và không phụ thuộc vào thư viện vẽ.

CẤU TRÚC MỘT FILE KẾT QUẢ
---
{
  "schema": 1,                     # phiên bản định dạng file kết quả
  "phase": "eda",                  # eda | pipeline
  "dataset": "cosmetics",
  "version_id": "cosmetics-v0.1.0-1a2b3c4d",
  "generated_at": "17/09/2026 10:30",
  "meta": ["câu mô tả ngắn", ...],  # chỉ là THÔNG TIN, không phải nhận xét
  "sections": [
    {
      "id":     "overview",
      "title":  "EDA 01 - Tổng quan dữ liệu",
      "cards":  [{"label": ..., "value": ...}],
      "charts": [{"title": ..., "kind": "bar", "x": [...], "y": [...]}],
      "tables": [{"title": ..., "columns": [...], "rows": [[...]],
                  "num_columns": [chỉ số các cột cần canh phải]}],
      "files":  ["<đường dẫn file CSV chi tiết>"]
    }
  ]
}

Quy ước quan trọng: section chỉ chứa SỐ LIỆU và BIỂU ĐỒ.
Mọi câu giải thích, diễn giải, khuyến nghị nằm trong docs/.
"""

import json
from datetime import datetime
from pathlib import Path

from src import config

# Phiên bản định dạng file kết quả. Tăng khi cấu trúc thay đổi
# để build_report.py biết file cũ có đọc được hay không.
RESULT_SCHEMA = 1

# Các khoá hợp lệ của một section. Khoá lạ sẽ bị cảnh báo lúc đọc.
SECTION_KEYS = ("id", "title", "cards", "charts", "tables", "files")

# Một bảng trong "tables" là dict: title, columns, rows, num_columns (chỉ số các
# cột căn phải) và tuỳ chọn "first": True - bảng đó được hiện ngay dưới phần thẻ
# số liệu, TRƯỚC mọi biểu đồ (dùng cho bảng cấu trúc file ở EDA 01).


def result_filename(phase):
    """Tên file kết quả của một nhóm: eda -> 'eda_result.json'."""
    return "{}_result.json".format(phase)


def result_path(out_dir, phase):
    """Đường dẫn đầy đủ tới file kết quả."""
    return Path(out_dir) / result_filename(phase)


def section_filename(index, section_id):
    """Tên file kết quả của MỘT phần: (1, 'overview') -> '01_overview.json'."""
    return "{:02d}_{}.json".format(index, section_id)


def write_sections(payload, out_dir):
    """Ghi mỗi phần ra một file JSON riêng. Trả về danh sách đường dẫn.

    File tổng (eda_result.json) vẫn là thứ build_report.py đọc, vì báo cáo
    cần đủ mọi phần mới dựng được mục lục và biểu đồ. Các file riêng này để
    soi / so sánh một phần giữa hai phiên bản mà không phải mở file tổng.
    """
    out_dir = Path(out_dir)
    header = {
        key: payload.get(key)
        for key in ("schema", "phase", "dataset", "version_id", "generated_at")
    }
    written = []
    for index, section in enumerate(payload.get("sections") or [], start=1):
        content = dict(header)
        content["section"] = section
        written.append(
            write_result(content, out_dir / section_filename(index, section["id"]))
        )
    return written


def make_payload(phase, dataset, version_id, meta, sections,
                 title="", subtitle=""):
    """Đóng gói kết quả của một lần chạy thành dict để ghi ra JSON."""
    return {
        "schema": RESULT_SCHEMA,
        "phase": phase,
        "dataset": dataset,
        "version_id": version_id,
        "title": title,
        "subtitle": subtitle,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "meta": list(meta),
        "sections": [_clean_section(s) for s in sections],
    }


def _clean_section(section):
    """Chuẩn hoá một section: đủ khoá, đúng kiểu, JSON-serializable."""
    clean = {}
    for key in SECTION_KEYS:
        value = section.get(key)
        if key in ("cards", "charts", "tables", "files"):
            clean[key] = list(value) if value else []
        elif key == "id":
            # id được dùng làm mục lục và neo liên kết trong HTML
            clean[key] = str(value or "section")
        else:
            clean[key] = "" if value is None else str(value)
    return clean


def write_result(payload, path):
    """Ghi file kết quả ra đĩa (JSON, giữ nguyên tiếng Việt)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def read_result(path):
    """Đọc file kết quả. Báo lỗi rõ ràng nếu file thiếu hoặc sai định dạng."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            "Chưa có file kết quả: {}. Hãy chạy run_eda.py hoặc "
            "run_pipeline.py trước.".format(
                _display(path)
            )
        )
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict) or "sections" not in payload:
        raise ValueError(
            "File kết quả không đúng định dạng: {}".format(_display(path))
        )

    schema = payload.get("schema")
    if schema != RESULT_SCHEMA:
        raise ValueError(
            "File kết quả dùng định dạng schema={} nhưng code đang cần "
            "schema={}. Hãy chạy lại run_eda.py / run_pipeline.py.".format(
                schema, RESULT_SCHEMA
            )
        )
    return payload


def _display(path):
    """Hiển thị đường dẫn tương đối cho dễ đọc, lỗi vẫn rõ ràng."""
    try:
        return Path(path).relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)
