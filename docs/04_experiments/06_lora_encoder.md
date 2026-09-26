# 04.06. Chạy model encoder bằng LoRA

> Đọc file này khi: chạy thí nghiệm PhoBERT hoặc ViSoBERT, hoặc sửa cách huấn luyện.
> Liên quan: `docs/04_experiments/03_training_eval.md`, `docs/05_config/04_models.md`,
> `docs/05_config/05_experiments_shared.md`

## Hai đường chạy, chọn bằng `approach`

`configs/models/<model_id>.yaml` khai `approach`. Giá trị đó quyết định đường chạy, và không có giá
trị mặc định trong code:

| `approach` | Model | Đường chạy | Cần gì |
| --- | --- | --- | --- |
| `prompt` | `qwen3-4b-instruct-2507`, `qwen3-0.6b` | `src/evaluation/runner.py`: gửi prompt rồi đọc câu trả lời | GPU, prompt của thí nghiệm |
| `encoder` | `visobert`, `phobert-base-v2` | `src/encoder_run.py`: huấn luyện LoRA rồi suy luận | GPU, `peft`, ba vai |

Model encoder KHÔNG có prompt để tự trả lời, nên thí nghiệm dùng nó bắt buộc khai
`training.enabled: true` (guard ở `src/experiments.py::check`).

## Một lượt chạy encoder gồm gì

1. **Đọc dữ liệu ba vai**: `train` để học, `val` để chọn `model/best`, `eval` (split `test`) để chấm.
2. **Chiếu nhãn** sang không gian nhãn của thí nghiệm
   (`src/preprocessing/loader.project_multi_head`): ô neutral bị loại mang `mask = 0` - không vào
   loss và không được chấm, nhưng KHÔNG làm mất các khía cạnh khác của cùng review.
3. **Huấn luyện LoRA**: encoder gốc đóng băng, chỉ học adapter hạng thấp cộng một đầu phân loại
   riêng cho mỗi khía cạnh (`khía cạnh × mã nhãn`).
4. **Chọn `model/best` theo `val`** (độ chính xác theo Ô), rồi **suy luận trên split `eval`**.
5. **Chấm điểm và ghi kết quả** bằng đúng bộ chấm của đường prompt (`src/evaluation/scorers/`), nên
   hai đường cho ra bảng điểm so được với nhau và với công bố.

## Checkpoint

| Thư mục | Trong đó có gì | Dùng để |
| --- | --- | --- |
| `model/last` | adapter + `head.pt` + `optimizer.pt` + `scheduler.pt` + `trainer_state.json` | chạy tiếp sau khi bị ngắt |
| `model/best` | adapter + `head.pt` + `head_config.json` | suy luận, chấm điểm |
| `model/checkpoint-<bước>` | như `model/last`, giữ `keep_last_k` cái gần nhất | ảnh chụp trung gian để chạy tiếp |

`trainer_state.json` giữ vân tay ba giá trị (`config_sha256`, mã phiên bản dữ liệu, commit đã ghim).
Chạy tiếp chỉ hợp lệ khi cả ba y nguyên; khác thì báo lỗi và yêu cầu xoá thư mục kết quả, vì trộn
hai phép đo vào cùng một bảng là lỗi không nhìn thấy được.

Một chi tiết của đường này: văn bản được mã hoá theo TỪNG LÔ (để không dựng cả tập train trong bộ
nhớ), rồi các lô được nối lại - nên `lora.encode` pad mọi lô về **cùng một độ rộng**. Không pad như
vậy thì `torch.cat` ném `RuntimeError: Sizes of tensors must match except in dimension 0` ngay khi
tập train có nhiều lô (đã gặp thật với ~4.000 review; phép chạy thử ở máy chỉ có 40 review nên chỉ
một lô và không lộ ra).

## Chạy trên Colab

Hai notebook LoRA chạy được trên T4 (4-bit không bắt buộc: LoRA cơ bản vẫn vừa 6 GB VRAM). Ô bootstrap
tự cài `peft`, và với PhoBERT (`preprocess.segmenter: vncorenlp`) thì tự cài thêm `default-jdk` +
`py-vncorenlp`, đặt `JAVA_HOME` cho tiến trình, rồi tự tải model VnCoreNLP (27 MB) về gốc dữ liệu nếu
thiếu - người chạy không phải chép thư mục nào bằng tay.
`inference.dtype: auto` nghĩa là mã chọn bf16 khi máy hỗ trợ, fp16 khi không (T4 là Turing), fp32 trên
CPU - kiểu số đã dùng được ghi vào `run.log` và `run_meta.json`.

## Mở rộng

- Thêm cách huấn luyện khác (full fine-tune, QLoRA cho LLM): một module trong `src/training/` + một
  dòng trong `TRAINERS`, rồi khai `training.trainer` ở config.
- Thêm encoder: một module trong `src/preprocessing/` + một dòng trong `src/training/encoders.py` +
  file `configs/models/<model_id>.yaml` có `approach: encoder`.
