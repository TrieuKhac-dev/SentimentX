# -*- coding: utf-8 -*-
"""Các bước của Data Pipeline (thực sự biến đổi dữ liệu).

MỘT BƯỚC ĐƯỢC SỬA SPLIT NÀO: khoá `apply_to` của chính bước đó, đọc qua `editable_splits`.
Từ phiên bản pipeline v0.2.0, `test` KHÔNG nằm trong `apply_to` của Clean và Normalize: nó phải
giữ nguyên bản dữ liệu gốc thì kết quả mới so được với công bố tham chiếu (xem
docs/04_experiments/reference_publication.md). Bước nào cũng phải hỏi `editable_splits` thay vì tự
quyết, để không có hai nơi hiểu luật khác nhau.
"""


class PipelineConfigError(Exception):
    """Cấu hình bước không dùng được: tên split lạ, hoặc quy tắc mâu thuẫn với tập bảo vệ."""


def editable_splits(step_name, step_cfg, splits):
    """Các split mà một bước được PHÉP SỬA (khoá `apply_to` của bước đó).

    Không khai `apply_to` thì bước được sửa MỌI split - đúng hành vi của pipeline v0.1.0, nên file
    cấu hình cũ không phải sửa. Tên lạ trong `apply_to` là LỖI chứ không bỏ qua: một tên viết sai
    làm bước không chạy ở đâu cả mà lần chạy vẫn báo "xong".

    Thứ tự trả về theo thứ tự của `splits`, để phần dựng lại DataFrame không phụ thuộc thứ tự khai
    trong `apply_to`.
    """
    names = list(splits)
    wanted = step_cfg.get("apply_to")
    if wanted is None:
        return names
    if not isinstance(wanted, (list, tuple)) or not wanted:
        raise PipelineConfigError(
            "steps.{}.apply_to phải là danh sách tên split, đang là {!r}.".format(step_name, wanted))
    unknown = [name for name in wanted if name not in names]
    if unknown:
        raise PipelineConfigError(
            "steps.{}.apply_to có tên split không tồn tại: {} (đang có: {}).".format(
                step_name, ", ".join(str(name) for name in unknown), ", ".join(names)))
    chosen = set(wanted)
    return [name for name in names if name in chosen]
