# Thêm một mục EDA mới

> Đọc file này khi: thêm một mục EDA mới.
> Liên quan: `docs/02_eda/03_modules.md`, `src/registry.py`

## 1. Ba bước

1. Tạo file mới trong `src/eda/`, ví dụ `emoji_deep.py`.

2. Viết hàm `run(context)` trả về **một dict mô tả một mục báo cáo**:

```python
def run(context):
    splits = context["splits"]        # {"train": DataFrame, "val": ..., "test": ...}
    out_dir = context["out_dir"]      # thư mục của phiên bản hiện tại
    aspects = context["dataset"]["aspects"]   # schema đọc từ configs/datasets/*.yaml

    return {
        "id": "emoji_deep",                      # dùng làm mục lục + neo liên kết
        "title": "EDA 06 - Phân tích emoji sâu",
        "cards": [{"label": "Số emoji", "value": 1234}],
        # biểu đồ: chỉ MÔ TẢ dữ liệu, không cần biết Plotly
        "charts": [{
            "title": "Emoji phổ biến nhất",
            "kind": "bar",          # xem bảng "loại biểu đồ" bên dưới
            "x": ["😍", "❤️"],
            "y": [120, 90],
            "orientation": "h",                  # tuỳ chọn: cột ngang (tự sắp giảm dần)
            "tickangle": -30,                    # tuỳ chọn: xoay nhãn trục ngang
        }],
        "tables": [{
            "title": "Bảng ví dụ",
            "columns": ["cột A", "cột B"],
            "rows": [["a", 1], ["b", 2]],
            "num_columns": [1],                  # các cột căn phải
        }],
        "files": [utils.rel(utils.write_csv(
            rows, columns, out_dir / "06_emoji.csv"))],
    }
```

3. Mở `src/registry.py`, import và thêm vào `EDA_MODULES`:

```python
from src.eda import emoji_deep
EDA_MODULES = [overview, label_aspect, quality_noise, text_analysis,
               split_leakage, emoji_deep]
```

Xong. Không cần sửa `run_eda.py`, `build_report.py` hay `src/reporting/`.
Vị trí trong danh sách **chính là** vị trí mục trên báo cáo.

## 2. Quy ước của một mục báo cáo

Xem thêm `src/reporting/result.py`:

| Khoá          | Ý nghĩa                                                                                                                                                                                                                                                                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `id`, `title` | định danh và tiêu đề mục                                                                                                                                                                                                                                                                                                                                     |
| `cards`       | vài con số lớn, dễ nhìn                                                                                                                                                                                                                                                                                                                                      |
| `charts`      | mô tả biểu đồ - `src/reporting/charts.py` mới là nơi quyết định cách vẽ                                                                                                                                                                                                                                                                                      |
| `tables`      | bảng số liệu; đặt `"first": True` để bảng hiện ngay dưới phần thẻ số liệu, trước biểu đồ; `"num_columns"` = các cột căn phải; `"narrow_columns"` = các cột cho co hết mức (aspect, split, mã nhãn) để nhường chỗ cho cột văn bản dài; `"pre_wrap_columns"` = các cột văn bản, giữ nguyên xuống dòng như trong CSV để copy một ô dán đi tìm trong CSV là thấy |
| `files`       | đường dẫn file số liệu chi tiết (ghi ra đĩa; báo cáo **không** liệt kê từng file nữa - chỉ ghi một thư mục ở đầu báo cáo)                                                                                                                                                                                                                                    |

> **Không có khoá `summary` hay `note`.** Báo cáo chỉ chứa số liệu và biểu đồ.
>
> Khi thêm số liệu mới, tuân theo quy ước ở
> [04_report_rules.md mục 2](04_report_rules.md): mỗi số liệu chỉ hiện một lần.

## 3. Các loại biểu đồ đang có

Khai báo bằng khoá `"kind"`:

| `kind`         | Dùng khi                                                                                                                         |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `bar`          | một chuỗi số liệu; `"orientation": "h"` để vẽ cột ngang (tự đảo trục cho giảm dần)                                               |
| `grouped_bar`  | vài chuỗi cạnh nhau trên cùng trục nhãn (so sánh 3 split)                                                                        |
| `stacked_bar`  | các phần của một tổng; `"barnorm": "percent"` để chuẩn hoá 100%, `"label_mode": "count_and_percent"` để in cả số lượng lẫn tỉ lệ |
| `stacked_grid` | cần đọc cả trong-từng-split lẫn giữa-các-split: mỗi facet là một split, chung trục tung, chung chú thích                         |
| `heatmap`      | ma trận (ví dụ mức xuất hiện cùng nhau giữa các khía cạnh)                                                                       |
| `pie`          | tỉ lệ phần trăm khi chỉ có 2-3 nhóm                                                                                              |

Muốn thêm **loại biểu đồ mới**: viết hàm dựng hình trong `src/reporting/charts.py`
rồi đăng ký vào `_BUILDERS` - module EDA chỉ cần khai báo `"kind"` tương ứng.

---

Xem thêm: [04_report_rules.md](04_report_rules.md) - quy ước trình bày;
[01_flow.md](01_flow.md) - luồng EDA tổng quát.
