# -*- coding: utf-8 -*-
"""Hợp đồng của một WRITER: cách ghi trọng số của MỘT cách huấn luyện.

Writer chỉ lo ĐÚNG một việc: biến các đối tượng model thành file trên đĩa (và đọc lại). Mọi thứ khác
- chính sách lưu, đường dẫn, ``trainer_state.json``, dọn ảnh chụp cũ - nằm ở ``src/training/checkpoints.py``,
nên thêm một cách huấn luyện mới KHÔNG phải chép lại phần đó.

    NAME        tên trong registry ``SAVERS``
    DESCRIPTION một dòng, để ``available()`` in ra
    save(directory, weights_only=False, **payload)   ghi trọng số vào thư mục
    read_metadata(directory)                          đọc mô tả bài toán đã huấn luyện
    check()                                           thư viện cần có (rỗng là chạy được)

``payload`` là đối tượng của trainer: writer ``adapter`` cần ``model`` (đã bọc LoRA) và ``head``; writer
cho full fine-tune sẽ cần ``model`` khác hẳn - trainer tự biết nó có gì nên nó đưa đúng thứ writer cần.
"""
