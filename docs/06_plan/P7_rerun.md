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

*Cập nhật 25/09/2026 - đợt thí nghiệm thứ hai:* T3 nay gồm NĂM thí nghiệm thay vì ba lượt của một
thí nghiệm (thí nghiệm CoT 2 ví dụ `prompt-cot/exp001` đã được xoá), tất cả ghim CÙNG một bản code đã
đẩy lên nhánh `experiment` và nằm trong gói bàn giao: hai lượt LoRA cho encoder
(`visobert/lora/exp001`, `phobert-base-v2/lora/exp001`) và ba mức ví dụ của công bố trên Qwen3
(`prompt-cot/exp002` 0 ví dụ, `exp003` 1 ví dụ, `exp004` 5 ví dụ). Đường huấn luyện encoder được thêm
trong đợt này (`src/encoder_run.py`, `src/training/lora.py`) và đã chạy trọn vẹn một lượt thu nhỏ trên
máy cá nhân trước khi ghim; ô cấu hình của notebook và phép kiểm dữ liệu gốc trong preflight cũng đã
được sửa sau lượt chạy thử đầu tiên trên Colab. Năm con số của tập `test` vẫn đang chờ máy GPU của
Colab.

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
      **Phạm vi đã chốt lại (25/09/2026): NĂM thí nghiệm, không phải ba lượt của một thí nghiệm.**
      Ba mức 0/1/5 ví dụ của công bố là `prompt-cot/exp002`, `exp003`, `exp004`, mỗi mức chấm trên cả
      tập `test` (`n: null`, 1.518 review); hai lượt LoRA cho encoder là `visobert/lora/exp001` và
      `phobert-base-v2/lora/exp001`. Thí nghiệm `prompt-cot/exp001` (CoT 2 ví dụ, mức nội bộ của
      nhóm) đã được XOÁ theo yêu cầu: nó không phải một mức của công bố, giữ lại chỉ làm loãng bảng so
      sánh. Các thư mục kết quả của giai đoạn kiểm đường chạy (chấm trên `val`, `n` nhỏ) cũng đã được
      xoá khỏi repo vì cùng lý do. Hai công cụ phục vụ việc chạy và kiểm:
      `scripts/run_notebook.py` (chạy notebook trên máy cá nhân, kéo commit ghim vào thư mục tạm nên
      repo không bị đụng) và `scripts/show_prompt.py` (in prompt thật gửi cho model). Muốn tra từng
      mẫu thì đọc cột `prompt gửi model` trong `predictions.csv`
      (`docs/04_experiments/05_predictions.md`).
- [ ] T4. Sinh bảng so sánh với cột `reference`; ghi lại kết quả và khoảng cách.
      -> `docs(experiments): record baseline results against reference`
- [ ] T5. Giao notebook cho giảng viên: đẩy dữ liệu, notebook và `.env.colab` lên Drive, gửi hướng dẫn.
      (không tạo commit)
      Gói bàn giao đã dựng lại (25/09/2026): **năm** notebook (hai lượt LoRA và ba mức ví dụ của công
      bố) cộng README của từng thí nghiệm, cây đúng như `docs/00_workflow/07_colab.md` mục 2:

      ```
      .sentimentx_root                      README.md  (hướng dẫn người chạy)
      env/.env.colab  env/.env.colab.example
      notebooks/<model_id>/<method>/expNNN.ipynb          (năm notebook)
      experiments/<model_id>/<method>/expNNN/README.md    (năm thí nghiệm)
      data/raw/cosmetics/v0.1.0/            4 CSV + raw_meta.yaml
      data/processed/<mã>/                  train, val, test, label_map.json, processing_log.json,
                                            eval_lock.json
      ```

      Gói được nén lại từ thư mục `_ban_giao/goi/` mỗi lần nội dung thay đổi, nên thứ đối chiếu được là
      CÂY trong gói chứ không phải tên file zip.

      `env/.env.colab` có token DagsHub thật (gói gửi qua kênh riêng, đổi token sau đồ án). Hai khoá
      gốc đường dẫn trong file đó để nguyên dạng CHÚ THÍCH: `runtime._apply_file` dùng
      `os.environ.setdefault` và ô bootstrap nạp file này TRƯỚC khi tự dò thư mục, nên khoá nào có
      trong file sẽ thắng giá trị tự dò - khai sai tên thư mục là mất dữ liệu và kết quả vào máy ảo.

      Notebook trong gói ghim bản code đã rà soát: đọc bốn hằng số ở ô đầu notebook, và
      `python scripts/ci_checks.py` kiểm sha đó tồn tại trong repo cùng nằm trên nhánh `experiment`;
      `preflight` chạy với hai gốc trỏ vào CHÍNH GÓI báo 0 việc phải sửa, chế độ NEW; `test.csv`
      trong gói vẫn là `e2558137...` với 1518 bản ghi, khớp số đã đo ở P2. Phần chỉ Colab kiểm được:
      mount Drive, bấm Allow, và GPU T4.

      Hai lỗi lộ ra ở lượt chạy đầu trên Colab (notebook PhoBERT) đã sửa trước khi dựng lại gói:
      ô CẤU HÌNH ĐANG DÙNG đọc thẳng `config["prompt"]` nên chết ngay với model encoder (nay rẽ nhánh
      theo `approach`, mọi khoá đọc qua `.get`, và in luôn gốc dữ liệu cùng mã phiên bản đang dùng),
      và preflight chưa đối chiếu dữ liệu gốc với dấu vân tay đã ghi (nay so từng file và in ra đúng
      tên file lệch, kèm danh sách mã đang có trong `data/processed/`).

      Vì sao đã ghim lại hai lần: bản ghim đầu (`67819b8`) KHÔNG chạy được thí nghiệm khi đó (`exp001`,
      CoT 2 ví dụ, nay đã xoá) - prompt và file ví
      dụ của thí nghiệm này khai bằng ĐƯỜNG DẪN, mà bộ dựng prompt khi đó giải đường dẫn theo thư mục
      repo nên không thấy file ví dụ và dừng ở lô sinh đầu tiên, tức là SAU khi đã nạp model. Lần thứ
      hai là để gói bàn giao chạy đúng bản code đã rà soát sau cùng (kể cả phần báo thiếu thư viện
      của preflight). Lỗi đường dẫn là loại chỉ lộ ra ở lượt chạy đầu tiên của một thí nghiệm dùng
      prompt theo đường dẫn, nên đường chạy bằng TÊN prompt (`--prompt absa_cot_v1`) không gặp.

## 4. Điều kiện hoàn thành (DoD)

- `data/reports/metrics_matrix/accuracy_by_aspect.csv` có cột `reference` và cột cho từng `expNNN`.
- Tập `test` không đổi: `sha256` khớp `eval_lock` trong file dataset version.
- Một thí nghiệm chạy trọn vẹn trên Colab của giảng viên, kết quả nằm trên Drive và trên DagsHub.

## 5. Rủi ro / lưu ý

- Nếu giảng viên chỉ có TPU, QLoRA không chạy: giữ Qwen3 ở dạng prompt và huấn luyện encoder.
- Kết quả sinh trên Colab nằm trên Drive; muốn vào git thì phải copy phần nhẹ về.

## 6. Phụ thuộc

P6 xong (đã có report và CI).
