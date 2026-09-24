# -*- coding: utf-8 -*-
"""Sinh báo cáo cho NGƯỜI ĐỌC từ FILE KẾT QUẢ.

    file kết quả JSON  ->  Plotly (biểu đồ) + Jinja2 (giao diện)  ->  HTML

Nguyên tắc của dự án:
    - Số liệu chi tiết (CSV/JSON) do các module EDA/pipeline ghi ra.
    - Báo cáo cho người đọc do module NÀY sinh ra, và nó KHÔNG tự tính toán gì
      thêm - mọi con số đều đọc từ file kết quả.
    - Báo cáo chỉ trình bày SỐ LIỆU và BIỂU ĐỒ. Câu giải thích nằm trong docs/.
    - Chỉ có MỘT định dạng cho người đọc là HTML. Bản Markdown đã bỏ: nó lặp
      lại đúng bấy nhiêu số liệu mà không có biểu đồ, nên chỉ thêm một bản copy
      lệch nhau mỗi lần sửa báo cáo.

Nhờ tách như vậy, muốn vẽ lại báo cáo chỉ cần chạy build_report.py, không phải
chạy lại EDA hay pipeline.
"""

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src import config
from src.reporting import charts

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# Tên file thư viện vẽ được nhúng vào thư mục assets (để HTML mở offline)
PLOTLY_JS_FILENAME = "plotly.min.js"


# ---
# Chuẩn bị môi trường template
# ---


def _environment():
    """Môi trường Jinja2: template nằm trong templates/, tự escape HTML."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html",)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def default_assets_dir():
    """Thư mục chứa tài nguyên dùng chung của báo cáo (plotly.min.js)."""
    return config.ASSETS_DIR


def ensure_plotlyjs(assets_dir=None):
    """Bảo đảm đã có plotly.min.js trong thư mục assets.

    File được lấy từ chính thư viện plotly đang cài, không tải từ mạng,
    nên báo cáo HTML mở được khi không có Internet.
    """
    assets_dir = Path(assets_dir) if assets_dir else default_assets_dir()
    target = assets_dir / PLOTLY_JS_FILENAME
    if target.exists() and target.stat().st_size > 0:
        return target

    assets_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(charts.script_source(), encoding="utf-8")
    return target


def _plotlyjs_tag(mode, out_dir, assets_dir):
    """Thẻ <script> nạp thư viện vẽ: bản sao cục bộ hoặc từ CDN."""
    if str(mode).lower() == "cdn":
        url = "https://cdn.plot.ly/plotly-{}.min.js".format(charts.script_version())
        return '<script charset="utf-8" src="{}"></script>'.format(url)

    if not charts.is_available():
        return "<!-- Chưa cài plotly: báo cáo chỉ hiển thị bảng số liệu -->"

    target = ensure_plotlyjs(assets_dir)
    relative = os.path.relpath(str(target), str(out_dir)).replace("\\", "/")
    return '<script charset="utf-8" src="{}"></script>'.format(relative)


# ---
# HTML
# ---


def _chart_blocks(section):
    """Vẽ từng mô tả biểu đồ của một section thành HTML.

    Nếu một biểu đồ lỗi, phần còn lại của báo cáo vẫn được sinh bình thường
    và lỗi được ghi rõ ngay tại chỗ - không im lặng bỏ qua.
    """
    blocks = []
    for index, spec in enumerate(section.get("charts") or []):
        chart_id = "{}-chart-{}".format(section.get("id", "section"), index)
        try:
            blocks.append({
                "title": spec.get("title", ""),
                "html": charts.to_html(charts.build(spec), chart_id),
                "error": "",
            })
        except Exception as exc:
            blocks.append({
                "title": spec.get("title", ""),
                "html": "",
                "error": "{}: {}".format(type(exc).__name__, exc),
            })
    return blocks


def build_html(payload, out_dir, plotlyjs="local", assets_dir=None):
    """Ghép file kết quả với template để ra nội dung HTML hoàn chỉnh.

    Một bảng có thể đặt khoá `"first": True` để được hiện NGAY DƯỚI phần thẻ số
    liệu, trước mọi biểu đồ. Dùng cho bảng mô tả cấu trúc file: nó là thông tin
    người đọc cần thấy trước tiên, và cũng để một số liệu không bị lặp lại vừa
    ở bảng vừa ở biểu đồ.
    """
    sections = []
    for section in payload.get("sections", []):
        entry = dict(section)
        tables = []
        for table in (section.get("tables") or []):
            item = dict(table)
            # Hai khoá này là TUỲ CHỌN trong file kết quả; điền sẵn danh sách
            # rỗng để template không phải kiểm tra tồn tại.
            item.setdefault("num_columns", [])
            # narrow_columns: các cột "hẹp" (aspect, split, mã nhãn...) - trình
            # duyệt co lại hết mức để nhường chỗ cho cột văn bản dài.
            item.setdefault("narrow_columns", [])
            # pre_wrap_columns: các cột văn bản - giữ nguyên xuống dòng như trong
            # CSV, để copy một ô trong báo cáo dán đi tìm trong CSV là thấy.
            item.setdefault("pre_wrap_columns", [])
            tables.append(item)

        entry["chart_blocks"] = _chart_blocks(section)
        entry["lead_tables"] = [t for t in tables if t.get("first")]
        entry["tables"] = [t for t in tables if not t.get("first")]
        sections.append(entry)

    template = _environment().get_template("report.html")
    return template.render(
        title=payload.get("title") or "Báo cáo SentimentX",
        subtitle=payload.get("subtitle", ""),
        meta=payload.get("meta", []),
        sections=sections,
        generated_at=payload.get("generated_at", ""),
        plotlyjs_tag=_plotlyjs_tag(plotlyjs, Path(out_dir), assets_dir),
    )


# ---
# Ghi ra đĩa
# ---


def write_reports(payload, out_dir, plotlyjs="local", assets_dir=None):
    """Ghi report.html vào out_dir. Trả về đường dẫn file HTML."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / "report.html"
    html_path.write_text(
        build_html(payload, out_dir, plotlyjs=plotlyjs, assets_dir=assets_dir),
        encoding="utf-8",
    )
    return html_path
