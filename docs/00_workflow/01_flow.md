# 01. Luồng làm việc

> Đọc file này khi: mới vào nhóm, hoặc không nhớ bước tiếp theo là gì.
> Liên quan: `docs/00_workflow/02_rules.md` · `docs/06_plan/README.md`

## Vai trò

| Thành phần | Vai trò |
|---|---|
| GitHub | nơi chứa code và cấu hình, là nguồn duy nhất |
| Nhánh `experiment` | nhánh duy nhất notebook kéo code |
| Nhánh `experiment/<tên>` | nhánh làm việc riêng, tạo từ `experiment`, xoá sau khi merge |
| Colab của giảng viên | nơi chạy notebook |
| Google Drive của giảng viên | nơi chứa dữ liệu vào và kết quả ra |
| DagsHub | nơi xem lại thí nghiệm qua MLflow |

## Luồng một thí nghiệm

1. Tạo thí nghiệm mới bằng `python scripts/new_experiment.py --model ... --method ...`.
2. Viết `prompt.txt`, `examples.txt` và `config.yaml` của thí nghiệm.
3. Chạy thử trên máy cá nhân: mở `notebook.ipynb` và chạy toàn bộ.
4. Merge nhánh riêng vào `experiment` và giải mọi xung đột ở bước này.
5. Ghim bản code: `python scripts/pin.py <model>/<method>/<expNNN>`.
6. `git push` và gửi tệp notebook cho giảng viên.
7. Giảng viên: mount Drive, mở notebook, bấm Run all.
8. Nhóm xem kết quả trên DagsHub, và trên Drive trong `experiments/.../results/<mã>/`.
9. Sinh lại bảng tổng hợp: `python scripts/collect_reports.py`.

## Điều quan trọng nhất

- Notebook luôn kéo **đúng bản code đã ghim**, không kéo bản mới nhất.
- Tập `test` và bộ chỉ số **không đổi**, vì phải so được với công bố tham chiếu.
- Kết quả chỉ được dùng khi đã merge vào `experiment` và merge không phải sửa tệp nào.

## Khi có lỗi

| Hiện tượng | Xem ở đâu |
|---|---|
| Notebook dừng giữa chừng | `results/<mã>/errors.json` và `run.log` |
| Không thấy kết quả trên DagsHub | `run.log`, mục `[TRACK]` |
| Thiếu tệp dữ liệu trên Drive | `errors.json`, mục `requires` |
| CI báo đỏ | `docs/00_workflow/03_ci.md` |
