# -*- coding: utf-8 -*-
"""Biến SỐ LIỆU trong file kết quả thành BIỂU ĐỒ Plotly.

Đây là NƠI DUY NHẤT trong dự án quyết định "dữ liệu nào vẽ bằng loại biểu đồ
nào". Các module EDA và pipeline chỉ mô tả dữ liệu (dict có khoá `kind`),
hoàn toàn không import plotly. Nhờ vậy:

    - Đổi kiểu biểu đồ  -> sửa mỗi file này.
    - Đổi dữ liệu đo    -> sửa module EDA, không lo phần vẽ.
    - Máy chưa cài plotly vẫn chạy được EDA/pipeline (báo cáo chỉ có bảng).

MỘT ĐẶC TẢ BIỂU ĐỒ CÓ DẠNG
---
    {"title": "Số dòng theo split", "kind": "bar",
     "x": ["train", "val", "test"], "y": [100, 20, 20]}

    {"kind": "grouped_bar", "x": [...], "series": {"positive": [...],
                                                   "negative": [...]}}

    {"kind": "stacked_bar", "x": [...], "series": {...},
     "barnorm": "percent"}          # cột xếp chồng, chuẩn hoá 100%

    {"kind": "heatmap", "x": [...], "y": [...], "z": [[...], [...]]}

    {"kind": "pie", "x": [...], "y": [...]}

HAI QUY ƯỚC HIỂN THỊ (áp dụng cho MỌI biểu đồ)
---
1. Số phải hiện ĐỦ CHỮ SỐ, không dùng hậu tố SI của Plotly.
   Plotly mặc định rút gọn số lớn thành "16.227k" - vừa khó đọc vừa dễ hiểu sai
   (16.227k = 16 nghìn, còn "16.227" = mười sáu nghìn hai trăm hai mươi bảy).
   Vì vậy nhãn số luôn được truyền dưới dạng CHUỖI đã định dạng sẵn, và các
   trục số được đặt tickformat / hoverformat = "d" khi giá trị đủ lớn.
2. Chú thích màu (legend) nằm DƯỚI biểu đồ, không nằm trên đỉnh - đặt ở đỉnh
   thì nó dính sát tiêu đề và trông như một phần của tiêu đề.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Phiên bản plotly.js dùng khi không đọc được phiên bản của thư viện đang cài.
PLOTLY_CDN_FALLBACK_VERSION = "2.35.2"

# Bảng màu dùng chung cho mọi biểu đồ để báo cáo nhìn đồng nhất.
PALETTE = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed",
           "#0891b2", "#be123c", "#4d7c0f"]

# Các loại biểu đồ được hỗ trợ (khoá dùng trong file kết quả)
CHART_KINDS = {
    "bar": "Biểu đồ cột",
    "grouped_bar": "Biểu đồ cột nhóm",
    "stacked_bar": "Biểu đồ cột xếp chồng",
    "stacked_grid": "Biểu đồ cột xếp chồng, mỗi split một khung",
    "heatmap": "Bản đồ nhiệt",
    "pie": "Biểu đồ tròn",
}

# Ngưỡng giá trị mà từ đó Plotly bắt đầu rút gọn số thành dạng "16.2k".
SI_THRESHOLD = 1000

_BASE_LAYOUT = dict(
    template="plotly_white",
    margin=dict(l=10, r=10, t=48, b=10),
    title_font=dict(size=14),
    font=dict(family="Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif",
              size=12),
    colorway=PALETTE,
)


def number_text(value):
    """Chuỗi hiển thị một con số: đủ chữ số, gọn, không hậu tố SI.

        16227      -> "16227"
        21.05      -> "21.05"
        0.0        -> "0"

    Nhãn số của biểu đồ luôn đi qua hàm này. Nếu truyền thẳng số cho Plotly,
    nó tự rút gọn thành "16.227k" - đúng kiểu hiển thị mà dự án không dùng.
    """
    if isinstance(value, bool):
        return str(value)
    number = float(value)
    if number == int(number):
        return str(int(number))
    return "{:g}".format(round(number, 2))


def is_available():
    """Thư viện vẽ đã sẵn sàng chưa (plotly đã được cài trong môi trường)."""
    try:
        import plotly  # noqa: F401
    except ImportError:
        return False
    return True


def _height(spec, default=360):
    """Chiều cao biểu đồ, tự tăng khi có nhiều nhóm nhãn."""
    if spec.get("height"):
        return int(spec["height"])
    values = spec.get("x") if spec.get("orientation", "v") == "v" else spec.get("y")
    n = len(values or [])
    return min(max(default, 22 * n), 900)


def _titles(fig, spec):
    """Gắn tên trục (+ góc xoay nhãn nếu có) cho biểu đồ."""
    if spec.get("x_label"):
        fig.update_xaxes(title_text=spec["x_label"])
    if spec.get("y_label"):
        fig.update_yaxes(title_text=spec["y_label"])
    # Nhãn dài (tên chỉ số nhiễu, tên cột) cần xoay để không đè lên nhau.
    if spec.get("tickangle") is not None:
        fig.update_xaxes(tickangle=spec["tickangle"])
    return fig


def _number_axis(fig, values, axis="y"):
    """Buộc trục số hiện ĐỦ CHỮ SỐ khi giá trị đủ lớn.

    Không đặt tickformat thì Plotly hiện "16.2k" cho 16227. Chỉ đặt khi mọi
    giá trị đều là số nguyên - với tỉ lệ phần trăm (21.05) thì để mặc định.
    """
    numbers = [float(v) for v in values if isinstance(v, (int, float))]
    if not numbers:
        return
    if max(abs(v) for v in numbers) < SI_THRESHOLD:
        return
    if any(v != int(v) for v in numbers):
        return
    settings = {"tickformat": "d", "hoverformat": "d"}
    if axis == "y":
        fig.update_yaxes(**settings)
    else:
        fig.update_xaxes(**settings)


def _bar(spec):
    """Một chuỗi số liệu duy nhất, cột đứng hoặc cột ngang."""
    horizontal = spec.get("orientation", "v") == "h"
    if horizontal:
        x_values, y_values = spec["y"], spec["x"]
    else:
        x_values, y_values = spec["x"], spec["y"]

    fig = go.Figure(go.Bar(
        x=x_values,
        y=y_values,
        orientation="h" if horizontal else "v",
        text=[number_text(value) for value in spec["y"]],
        textposition="outside",
        cliponaxis=False,
        marker_color=spec.get("color", PALETTE[0]),
    ))
    # Với cột NGANG, Plotly đặt nhóm đầu tiên ở ĐÁY, nên dữ liệu đã sắp giảm
    # dần vẫn hiện như đang tăng dần khi đọc từ trên xuống. Đảo trục tung để
    # giá trị lớn nhất nằm trên cùng - đúng thứ tự người đọc mong đợi.
    if horizontal:
        fig.update_yaxes(autorange="reversed")
    _number_axis(fig, spec["y"], axis="x" if horizontal else "y")
    return _titles(fig, spec)


def _grouped_bar(spec):
    """Nhiều chuỗi số liệu đặt cạnh nhau trên cùng một trục nhãn."""
    fig = go.Figure()
    for index, (name, values) in enumerate(spec["series"].items()):
        fig.add_trace(go.Bar(
            x=spec["x"],
            y=values,
            name=str(name),
            text=[number_text(value) for value in values],
            textposition="outside",
            cliponaxis=False,
            marker_color=PALETTE[index % len(PALETTE)],
        ))
    fig.update_layout(barmode=spec.get("barmode", "group"))
    for values in spec["series"].values():
        _number_axis(fig, values, axis="y")
    return _titles(fig, spec)


def _stacked_bar(spec):
    """Các chuỗi số liệu xếp chồng lên nhau trên cùng một cột.

    Với "barnorm": "percent", mỗi cột được chuẩn hoá thành 100% và nhãn hiện
    theo phần trăm - dùng để so sánh THÀNH PHẦN giữa các split có số dòng
    khác nhau (train 12981 dòng so với val 1623 dòng).
    """
    series = spec["series"]
    percent = str(spec.get("barnorm", "")) == "percent"
    totals = [sum(values) for values in zip(*series.values())] if series else []

    fig = go.Figure()
    for index, (name, values) in enumerate(series.items()):
        if percent:
            if str(spec.get("label_mode")) == "count_and_percent":
                # Hiện CẢ số lượng và tỉ lệ: tỉ lệ để so giữa các split có số
                # dòng rất khác nhau, số lượng để biết con số thật là bao nhiêu.
                text = [
                    "{} ({:.1f}%)".format(number_text(value), 100 * value / total)
                    if total else ""
                    for value, total in zip(values, totals)
                ]
            else:
                text = [
                    "{:.1f}%".format(100 * value / total) if total else ""
                    for value, total in zip(values, totals)
                ]
        else:
            text = [number_text(value) for value in values]
        fig.add_trace(go.Bar(
            x=spec["x"],
            y=values,
            name=str(name),
            text=text,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=11),
            marker_color=PALETTE[index % len(PALETTE)],
        ))

    fig.update_layout(barmode="stack")
    if percent:
        fig.update_layout(barnorm="percent")
        fig.update_yaxes(range=[0, 100])
    else:
        _number_axis(fig, [sum(values) for values in zip(*series.values())], "y")
    # Nhãn nhỏ không đủ chỗ sẽ tự ẩn, tránh chữ chồng lên nhau.
    fig.update_layout(uniformtext=dict(minsize=9, mode="hide"))
    return _titles(fig, spec)


def _stacked_grid(spec):
    """Nhiều cột xếp chồng cạnh nhau, MỖI SPLIT MỘT KHUNG.

    Nhãn dạng "aspect, split" trên một biểu đồ duy nhất khiến người đọc phải tự
    tách lại: vừa muốn so các aspect trong cùng một split, vừa muốn so cùng một
    aspect giữa các split - hai việc khác nhau trên cùng một hình.

    Cách vẽ ở đây: mỗi split là một khung riêng, chung trục tung và chung chú
    thích màu, nên:
        - nhìn một khung  -> phân bố các nhãn giữa các aspect của split đó;
        - nhìn ngang      -> cùng một aspect được gán nhãn giống nhau ở 3 split
                             hay không.

    Mô tả:
        {"kind": "stacked_grid", "x": [...], "barnorm": "percent",
         "facets": [{"title": "train", "series": {"positive": [...], ...}}]}
    """
    facets = spec["facets"]
    percent = str(spec.get("barnorm", "")) == "percent"
    order = list(spec.get("series_order") or facets[0]["series"]) if facets else []

    fig = make_subplots(
        rows=1, cols=len(facets),
        shared_yaxes=True,
        subplot_titles=[str(facet.get("title", "")) for facet in facets],
        horizontal_spacing=0.04,
    )
    for column, facet in enumerate(facets, start=1):
        series = facet["series"]
        totals = [sum(values) for values in zip(*series.values())] if series else []
        for index, label in enumerate(order):
            values = series.get(label, [])
            text = []
            for value, total in zip(values, totals):
                if not total:
                    text.append("")
                elif percent:
                    text.append("{:.0f}%".format(100 * value / total))
                else:
                    text.append(number_text(value))
            fig.add_trace(go.Bar(
                x=spec["x"],
                y=values,
                name=str(label),
                legendgroup=str(label),
                showlegend=column == 1,
                text=text,
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=10),
                marker_color=PALETTE[index % len(PALETTE)],
            ), row=1, col=column)

    fig.update_layout(barmode="stack")
    if percent:
        fig.update_layout(barnorm="percent")
        fig.update_yaxes(range=[0, 100])
    if spec.get("y_label"):
        fig.update_yaxes(title_text=spec["y_label"])
    fig.update_layout(uniformtext=dict(minsize=8, mode="hide"))
    return fig


def _heatmap(spec):
    """Bản đồ nhiệt có ghi số trong từng ô (số đủ chữ số, không "16.2k")."""
    z_values = spec["z"]
    fig = go.Figure(go.Heatmap(
        x=spec["x"],
        y=spec["y"],
        z=z_values,
        text=[[number_text(value) for value in row] for row in z_values],
        texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale="Blues",
        showscale=False,
        hovertemplate="%{y} - %{x}<br>%{text}<extra></extra>",
    ))
    # Hàng trên cùng là aspect đầu tiên, giống cách đọc một bảng.
    fig.update_yaxes(autorange="reversed")
    return _titles(fig, spec)


def _pie(spec):
    fig = go.Figure(go.Pie(
        labels=spec["x"],
        values=spec["y"],
        hole=0.45,
        sort=False,
        textinfo="percent+label",
        customdata=[number_text(value) for value in spec["y"]],
        hovertemplate="%{label}: %{customdata} (%{percent})<extra></extra>",
    ))
    return fig


_BUILDERS = {
    "bar": _bar,
    "grouped_bar": _grouped_bar,
    "stacked_bar": _stacked_bar,
    "stacked_grid": _stacked_grid,
    "heatmap": _heatmap,
    "pie": _pie,
}

# Chiều cao phần đáy dành cho chú thích màu khi phải hiện chú thích
LEGEND_BOTTOM_MARGIN = 68


def build(spec):
    """Tạo đối tượng hình vẽ Plotly từ mô tả biểu đồ trong file kết quả."""
    kind = str(spec.get("kind", "bar"))
    if kind not in _BUILDERS:
        raise ValueError(
            "Loại biểu đồ không hỗ trợ: '{}'. Các loại hợp lệ: {}.".format(
                kind, ", ".join(sorted(_BUILDERS))
            )
        )
    if not spec.get("x"):
        raise ValueError(
            "Biểu đồ '{}' không có dữ liệu trục ngang (x).".format(
                spec.get("title", kind)
            )
        )

    fig = _BUILDERS[kind](spec)
    fig.update_layout(**_BASE_LAYOUT)

    # Chú thích màu nằm DƯỚI biểu đồ (đặt trên đỉnh thì dính vào tiêu đề).
    show_legend = (bool(spec.get("series")) or bool(spec.get("facets"))
                   or kind in ("grouped_bar", "pie"))
    layout = dict(
        title_text=spec.get("title", ""),
        height=_height(spec),
        showlegend=show_legend,
        bargap=spec.get("bargap", 0.25),
    )
    if show_legend:
        layout["legend"] = dict(orientation="h", yanchor="top", y=-0.16, x=0)
        layout["margin"] = dict(l=10, r=10, t=48, b=LEGEND_BOTTOM_MARGIN)
    fig.update_layout(**layout)
    return fig


def to_html(fig, chart_id):
    """Chuyển hình vẽ thành đoạn HTML (KHÔNG kèm thư viện plotly.js).

    Thư viện plotly.js được nhúng MỘT LẦN ở đầu trang báo cáo,
    nên mỗi biểu đồ chỉ cần phần thân.
    """
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=chart_id,
        config={"displaylogo": False, "responsive": True},
    )


def script_source():
    """Nội dung thư viện plotly.js để nhúng vào báo cáo (chạy offline)."""
    import plotly.offline

    return plotly.offline.get_plotlyjs()


def script_version():
    """Phiên bản plotly.js của thư viện đang cài (dùng cho chế độ CDN)."""
    try:
        import plotly.offline

        return plotly.offline.get_plotlyjs_version()
    except Exception:  # pragma: no cover - chỉ là nhãn hiển thị
        return PLOTLY_CDN_FALLBACK_VERSION
