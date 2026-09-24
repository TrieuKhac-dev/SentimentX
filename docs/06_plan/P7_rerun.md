# P7 - Chạy lại từ đầu và so với công bố

> Đọc file này khi: bắt đầu sinh kết quả chính thức cho báo cáo.
> Liên quan: `docs/04_experiments/metrics.md`, `docs/04_experiments/reference_publication.md`

## 1. Mục tiêu giai đoạn

Sinh lại toàn bộ dữ liệu và kết quả từ đầu theo cấu trúc mới, so được trực tiếp với công bố tham chiếu,
và có một vòng bàn giao hoàn chỉnh cho giảng viên.

## 2. Trạng thái

bắt đầu. T1 (dựng lại dataset) và T2 (EDA + report) đã xong - T1 xong sớm hơn dự kiến vì lỗi băm ở P2
buộc phải dựng lại ngay: `data/processed/...-bf68b1c5` bị xoá và thay bằng `...-e0ccc484`. Số đo của
tập đánh giá lần này: `test.csv` 1518 bản ghi, `sha256` `e2558137...`.
Còn T3..T5: chạy baseline 0/1/5-shot, sinh bảng so với công bố, và vòng bàn giao. Ba việc này cần
GPU: trên máy cá nhân (RTX 3050 6GB) một lượt Qwen3-4B 4-bit tốn khoảng 10 giây/mẫu, mà tập `test` có
1518 mẫu - nên chúng thuộc lượt chạy trên Colab, cùng lượt bàn giao ở T5.

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Chạy lại pipeline để sinh phiên bản dataset đầu tiên theo cấu trúc mới.
      -> `chore(data): rebuild the dataset under the corrected version id`
      Điều kiện để chạy được trên Colab (đã gặp thật, ghi lại để P7 T5 khỏi vấp lại): dữ liệu GỐC
      KHÔNG nằm trong git (luật 20), nên bản clone sạch không có `data/raw/**/*.csv`. Muốn chạy
      pipeline trên Colab thì phải đưa dữ liệu lên trước (mount Drive, hoặc tải thư mục lên), rồi
      `python run_pipeline.py --dataset cosmetics --version v0.1.0`. Model `4bit` cần thêm
      `pip install bitsandbytes`. Preflight nay báo đúng việc này ở dòng ĐẦU của danh sách.
- [x] T2. Chạy lại EDA trên raw và trên dataset; sinh report tương ứng.
      -> `feat(data): regenerate eda and pipeline reports`
      Chạy thật (25/09/2026): `run_eda.py --raw-version v0.1.0` và `run_eda.py --version <mã>` đều
      thoát 0, rồi `build_report.py --phase eda` (2 lần) và `--phase pipeline` sinh ba file HTML.
      Phép so quan trọng: diff của kết quả EDA trên dữ liệu gốc CHỈ có `version_id` (mã cũ -> mã mới)
      và `generated_at` - mọi con số giữ nguyên, tức bộ dữ liệu không đổi khi mã phiên bản đổi.
- [ ] T3. Chạy baseline prompt 0-shot, 1-shot, 5-shot trên tập `test` đúng như công bố.
      -> `feat(experiments): run baseline prompt experiments`
- [ ] T4. Sinh bảng so sánh với cột `reference`; ghi lại kết quả và khoảng cách.
      -> `docs(experiments): record baseline results against reference`
- [ ] T5. Giao notebook cho giảng viên: đẩy dữ liệu, notebook và `.env.colab` lên Drive, gửi hướng dẫn.
      (không tạo commit)
      Gói bàn giao đã dựng sẵn (25/09/2026), chỉ chờ gửi: `sentimentx-exp001-ban-giao.zip` (2,03 MB)
      với 13 file, giữ đúng cấu trúc mà notebook mong đợi khi giải nén vào Drive:
      `.sentimentx_root` (file đánh dấu), `notebook-exp001.ipynb`, `HUONG_DAN.md`,
      `env/.env.colab.example`, `data/raw/cosmetics/v0.1.0/` (4 CSV + `raw_meta.yaml`),
      `data/processed/<mã>/` (train, val, test, label_map).
      Kiểm trước khi gửi, bằng cách coi chính gói là thư mục Drive: mã phiên bản tính từ dữ liệu
      TRONG GÓI khớp tên thư mục; `test.csv` trong gói có sha256 `e2558137...` và 1518 bản ghi, khớp
      số đã đo; notebook trong gói ghim `67819b8` và sạch output; `preflight` từ gói báo 0 việc phải
      sửa, chế độ NEW. Phần chỉ Colab kiểm được: mount Drive, bấm Allow, và GPU T4.

## 4. Điều kiện hoàn thành (DoD)

- `data/reports/metrics_matrix/accuracy_by_aspect.csv` có cột `reference` và cột cho từng `expNNN`.
- Tập `test` không đổi: `sha256` khớp `eval_lock` trong file dataset version.
- Một thí nghiệm chạy trọn vẹn trên Colab của giảng viên, kết quả nằm trên Drive và trên DagsHub.

## 5. Rủi ro / lưu ý

- Nếu giảng viên chỉ có TPU, QLoRA không chạy: giữ Qwen3 ở dạng prompt và huấn luyện encoder.
- Kết quả sinh trên Colab nằm trên Drive; muốn vào git thì phải copy phần nhẹ về.

## 6. Phụ thuộc

P6 xong (đã có report và CI).
