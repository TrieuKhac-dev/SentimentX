# 01. Luồng làm việc

> Đọc file này khi: mới vào nhóm, hoặc không nhớ bước tiếp theo là gì.
> Liên quan: `docs/00_workflow/02_rules.md`, `docs/06_plan/README.md`

## Vai trò các thành phần

| Thành phần                  | Vai trò                                                      |
| --------------------------- | ------------------------------------------------------------ |
| GitHub                      | nơi chứa code và config, là nguồn duy nhất                   |
| Nhánh `experiment`          | nhánh duy nhất notebook kéo code                             |
| Nhánh `experiment/<name>`   | nhánh làm việc riêng, tạo từ `experiment`, xoá sau khi merge |
| Colab của giảng viên        | nơi chạy notebook                                            |
| Google Drive của giảng viên | nơi chứa dữ liệu vào và kết quả ra                           |
| DagsHub                     | nơi xem lại thí nghiệm qua MLflow                            |

## Tạo thí nghiệm mới

```bash
python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot --title "CoT 1 shot"
```

Lệnh này làm 6 việc:

1. Kiểm cây làm việc sạch. Còn thay đổi chưa commit thì dừng.
2. Chạy `git fetch origin experiment`.
3. Kiểm nhánh hiện tại đã chứa `origin/experiment`. Chưa chứa thì dừng và yêu cầu merge trước.
4. Quét `experiments/<model>/<method>/exp*` trong cây làm việc và trong `origin/experiment`,
   lấy số `expNNN` kế tiếp.
5. Copy `templates/experiment/` thành `experiments/<model>/<method>/expNNN/`.
6. Điền `exp_id`, `model`, `method`, `parent`, `notes` và in ra các bước tiếp theo.

Vì sao không trùng số: số kế tiếp luôn được tính từ trạng thái đã hợp nhất trên `origin/experiment`,
nên hai người không thể cùng nhận một số.

Nếu không muốn dùng lệnh: vẫn có thể copy tay `templates/experiment/`, đặt đúng đường dẫn rồi điền tay.

## Luồng một thí nghiệm

1. Tạo thí nghiệm mới bằng lệnh ở trên.
2. Viết config và các file của thí nghiệm:
   - `config.yaml`: bắt buộc cho mọi thí nghiệm.
   - `prompt.txt` và `examples.txt`: chỉ dùng cho model dạng LLM, ví dụ Qwen3.
     Model encoder như PhoBERT, ViSoBERT không dùng prompt.
3. Chạy thử trên máy cá nhân: mở `notebook.ipynb` và chạy toàn bộ.
4. Merge nhánh riêng vào nhánh `experiment` và giải quyết mọi xung đột ở bước này.
5. Ghim bản code: `python scripts/pin.py <model>/<method>/<expNNN>`.
6. `git push` và gửi file notebook cho giảng viên.
7. Giảng viên: mount Drive, mở notebook, bấm Run all.
8. Xem kết quả:
   - Trên DagsHub: xem ngay, không cần copy gì.
   - Trên máy cá nhân: phải copy thư mục kết quả từ Drive về repo trước,
     vì kết quả chạy trên Colab nằm trên Drive.
9. Sinh lại bảng tổng hợp: `python scripts/collect_reports.py`.

## Ba điều quan trọng nhất

- Notebook luôn kéo đúng bản code đã ghim, không kéo bản khác, để tránh sai lệch phiên bản code.
- Tập test và metric không đổi, vì phải so được với công bố tham chiếu.
- Kết quả chỉ được dùng khi commit đã ghim nằm trên nhánh `experiment`,
  và khi merge vào nhánh `experiment` không phải sửa bất kỳ file nào.

## Nhật ký một lần chạy

Mỗi lần chạy có một thư mục kết quả riêng. Trong đó:

| File            | Khi nào có     | Nội dung                                                                 |
| --------------- | -------------- | ------------------------------------------------------------------------ |
| `run.log`       | luôn có        | từng bước đã chạy, kèm số giây của bước tốn thời gian                     |
| `errors.json`   | chỉ khi có lỗi | kiểu lỗi, vết gọi, thứ còn thiếu (`requires`), máy đã chạy               |
| `metrics.json`  | khi chấm xong  | chỉ số, kèm `label_space`, `neutral_policy`, số ô neutral bị loại         |
| `run_meta.json` | khi chấm xong  | bản ghi lần chạy để tra cứu, và để MLflow gắn nhãn cho run               |

Trong `run.log`, mỗi dòng bắt đầu bằng một mục, nên tìm bằng `grep`:

| Mục       | Nội dung                                                           |
| --------- | ------------------------------------------------------------------ |
| `[RUN]`   | bắt đầu/kết thúc lần chạy, `mode=NEW` hay `mode=RESUME`, cấu hình   |
| `[STEP]`  | bước đang chạy                                                     |
| `[WARN]`  | việc không làm chết run nhưng người đọc phải biết                   |
| `[ERROR]` | lỗi - đồng thời được ghi vào `errors.json`                          |
| `[TRACK]` | ghi kết quả lên MLflow: thành công hay thất bại                     |

Hai quy tắc không được vi phạm:

- Mỗi dòng log được ghi xuống đĩa NGAY, không đệm. Tiến trình bị dừng đột ngột vẫn còn log tới
  dòng cuối cùng đã chạy, nên biết được đã đi tới đâu.
- `errors.json` KHÔNG được tạo khi không có lỗi. File rỗng làm người đọc tưởng đã từng có lỗi,
  còn thiếu file thì rõ ràng là không lỗi.

Xem `src/runlog.py` để biết cách gọi, và `docs/04_experiments/metrics.md` cho phần chỉ số.

## Khi có lỗi

| Hiện tượng                      | Xem ở đâu                               |
| ------------------------------- | --------------------------------------- |
| Notebook dừng giữa chừng        | `results/<mã>/errors.json` và `run.log` |
| Không thấy kết quả trên DagsHub | `run.log`, mục `[TRACK]`                |
| Thiếu file dữ liệu trên Drive   | `errors.json`, mục `requires`           |
| CI báo đỏ                       | `docs/00_workflow/03_ci.md`             |
