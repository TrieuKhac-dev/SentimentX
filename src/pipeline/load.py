# -*- coding: utf-8 -*-
"""Pipeline bước 1 - LOAD.

Nạp dữ liệu gốc của dataset (theo khai báo trong configs/datasets/<tên>.yaml)
và đưa về DẠNG CHUẨN NỘI BỘ:
    cột "text"  +  một cột cho mỗi aspect

Các cột thừa (ví dụ "others") bị bỏ ngay khi đọc.
Cột aspect thiếu trong file gốc được thêm vào với giá trị rỗng và được
báo lại ở bước Validate.

Bước này KHÔNG sửa nội dung ô: chỉ đọc, đổi tên cột và chọn cột.
"""

from src import config, dataset


def run(context):
    cfg = context["dataset"]
    splits, missing = dataset.load_splits(cfg)
    context["splits"] = splits
    context["original_counts"] = {name: len(df) for name, df in splits.items()}
    # Cột aspect thiếu trong file gốc -> bước Validate sẽ báo lại
    context["missing_columns"] = missing

    # Giữ lại VĂN BẢN GỐC của từng dòng (đúng thứ tự). Bước Final Validate dùng
    # nó để chứng minh mọi bước sau chỉ ĐỔI HÌNH THỨC (khoảng trắng, Unicode...)
    # chứ không làm mất dấu tiếng Việt: xem `final_validate.py`.
    context["raw_texts"] = {
        name: df[config.TEXT_COLUMN].astype(str).tolist()
        for name, df in splits.items()
    }

    aspects = cfg["aspects"]
    rows = [
        [name, (cfg.get("splits") or {}).get(name, "-"), len(df),
         len(df.columns), len(aspects)]
        for name, df in splits.items()
    ]
    total = sum(len(df) for df in splits.values())
    missing_rows = [
        ["{} ({})".format(name, (cfg.get("splits") or {}).get(name, "?")),
         ", ".join(columns)]
        for name, columns in missing.items()
    ]

    tables = [
        {
            # Số dòng mỗi file chỉ hiện MỘT lần trong báo cáo: ở bảng này, không
            # vẽ thêm biểu đồ cột cho đúng những con số đó.
            "title": "Số dòng đọc được",
            "columns": ["split", "tệp gốc", "số dòng", "số cột",
                        "số cột khía cạnh"],
            "rows": rows,
            "num_columns": [2, 3, 4],
            "first": True,
        },
    ]
    if missing_rows:
        tables.append({
            "title": "Số cột khía cạnh bị thiếu trong file gốc",
            "columns": ["split (tệp gốc)", "cột bị thiếu"],
            "rows": missing_rows,
        })

    return {
        "id": "pipeline_load",
        "title": "Step 1 - Load (đọc dữ liệu gốc)",
        "cards": [
            {"label": "Số dòng vào pipeline", "value": "{}".format(total)},
            {"label": "Số khía cạnh dùng trong config", "value": len(aspects)},
            {"label": "Cột bị bỏ khi nạp (drop_columns)",
             "value": ", ".join(cfg["drop_columns"]) or "-"},
            {"label": "Số cột khía cạnh bị thiếu (đã tự thêm ô trống)",
             "value": sum(len(columns) for columns in missing.values())},
        ],
        "charts": [],
        "tables": tables,
        "files": [],
    }
