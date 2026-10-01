# -*- coding: utf-8 -*-
"""Khoá: bộ dữ liệu thô của ta = bộ dữ liệu CÔNG KHAI của bài nguồn (khác đúng BOM).

VÌ SAO CÓ FILE NÀY
"Split test của ta chính là tập test của công bố" là ĐIỀU KIỆN để mọi so sánh có nghĩa. Nếu ai đó
ghi lại / chia lại `data/raw/.../data_test.csv` thì tập đánh giá đổi mà không có gì báo, và mọi bảng
so với công bố thành vô nghĩa - lỗi im lặng. Cách khoá là git BLOB SHA (tên theo NỘI DUNG):

    blob_sha = SHA1(b"blob " + str(len(bytes)).encode() + b"\\x00" + bytes)

Cùng blob sha <=> cùng nội dung TỪNG BYTE. Bốn giá trị dưới đây là blob sha mà repo GitHub của bài
nguồn báo cho `data/` (xem `docs/04_experiments/reference_publication.md`).

GIỚI HẠN
`data/raw` KHÔNG nằm trong git (luật 20), nên ở bản clone sạch (CI) file này tự bỏ qua; chỉ chạy ở
máy có dữ liệu. Ba file train/val/test của ta có BOM UTF-8 (3 byte) còn bản công khai thì không, nên
phải bỏ BOM trước khi băm; `full_data.csv` không có BOM.
"""

import hashlib
import unittest

from src.core import paths

RAW_NAME = "cosmetics"
RAW_VERSION = "v0.1.0"
BOM = b"\xef\xbb\xbf"

# blob sha (KHÔNG BOM) của bốn file thô, đúng như repo của bài nguồn báo.
EXPECTED = {
    "data_test.csv": "52371d86d849fed58af60b3c9a64c73634310c47",
    "data_train.csv": "85d42dc2b0b6bd3ac6cc280be09c07e3f44011ed",
    "data_val.csv": "d7d987abd4f4e0924af79bf85fea9ef46cebe93e",
    "full_data.csv": "86cb19bdea314403c877f8112081b9e2b07a0794",
}


def blob_sha(body):
    """Blob sha của git cho một nội dung byte."""
    return hashlib.sha1(b"blob " + str(len(body)).encode() + b"\x00" + body).hexdigest()


def body_of(path):
    """Nội dung file, đã BỎ BOM UTF-8 nếu có."""
    raw = path.read_bytes()
    return raw[3:] if raw[:3] == BOM else raw


class RawDatasetTest(unittest.TestCase):
    """Bốn file thô phải trùng từng byte với bộ công khai của bài nguồn."""

    def setUp(self):
        self.directory = paths.raw_dir(RAW_NAME, RAW_VERSION)
        missing = [name for name in EXPECTED if not (self.directory / name).is_file()]
        if missing:
            raise unittest.SkipTest(
                "chưa có dữ liệu gốc trên máy này: {}".format(", ".join(missing)))

    def test_file_tho_trung_blob_sha_cua_bai_nguon(self):
        for name, want in EXPECTED.items():
            with self.subTest(file=name):
                self.assertEqual(
                    blob_sha(body_of(self.directory / name)), want,
                    "{} đã đổi so với bộ công khai của bài nguồn - tập đánh giá không còn "
                    "so được với công bố".format(name))


if __name__ == "__main__":
    unittest.main()
