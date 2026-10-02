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

from src.core import config, paths
from src.reporting import charts

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
TRAINING_TEMPLATE = "training.html"

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
    try:
        relative = os.path.relpath(str(target), str(out_dir)).replace("\\", "/")
    except ValueError:
        # Windows: `out_dir` và thư mục assets nằm khác Ổ ĐĨA nên không có đường TƯƠNG ĐỐI. Dùng đường
        # tuyệt đối dạng `file://` để trang vẫn mở được, thay vì chết cả trang vì một thẻ <script>.
        return '<script charset="utf-8" src="{}"></script>'.format(target.as_uri())
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


# ---
# Curve train/val (`plots/training.html`)
# ---


def build_training_html(data, out_dir, plotlyjs="local", assets_dir=None):
    """Ghép curve train/val với template (Jinja2) thành nội dung HTML hoàn chỉnh.

    `data` gồm `specs` (mô tả biểu đồ đường), `columns`/`rows` (bảng dữ liệu để đối chiếu) và
    `title`/`subtitle`/`meta`. Cùng plotly + jinja2 như báo cáo EDA/pipeline.
    """
    blocks = []
    for index, spec in enumerate(data.get("specs") or []):
        chart_id = "training-chart-{}".format(index)
        try:
            blocks.append({"title": spec.get("title", ""),
                           "html": charts.to_html(charts.build(spec), chart_id), "error": ""})
        except Exception as exc:  # noqa: BLE001 - một biểu đồ lỗi không được làm mất cả trang
            blocks.append({"title": spec.get("title", ""), "html": "",
                           "error": "{}: {}".format(type(exc).__name__, exc)})
    template = _environment().get_template(TRAINING_TEMPLATE)
    return template.render(
        title=data.get("title") or "Curve train/val",
        subtitle=data.get("subtitle", ""),
        meta=data.get("meta", []),
        charts=blocks,
        columns=data.get("columns") or [],
        rows=data.get("rows") or [],
        plotlyjs_tag=_plotlyjs_tag(plotlyjs, Path(out_dir), assets_dir),
    )


def write_training_html(data, out_dir, plotlyjs="local", assets_dir=None):
    """Ghi `<out_dir>/plots/training.html`. Trả về đường dẫn file HTML."""
    out_dir = Path(out_dir)
    folder = out_dir / paths.pattern("plots")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "training.html"
    path.write_text(
        build_training_html(data, folder, plotlyjs=plotlyjs, assets_dir=assets_dir),
        encoding="utf-8")
    return path
