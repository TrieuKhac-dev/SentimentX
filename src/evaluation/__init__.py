# -*- coding: utf-8 -*-
"""Đánh giá kết quả model sinh (đánh giá model): bộ đọc kết quả, chỉ số, và vòng chạy.

Chỉ `runner.py` cần `torch`; `parse.py` và `metrics.py` là hàm thuần (không model, không
I/O) nên kiểm được bằng test mà không cần GPU:

    python -m unittest discover -s tests
"""
