# 05.06. Cấu hình riêng của thí nghiệm

> Đọc file này khi: tạo thí nghiệm mới hoặc sửa cấu hình của một thí nghiệm.
> Liên quan: `docs/05_config/05_experiments_shared.md`, `docs/06_plan/P5_notebook_pin.md`

File: `experiments/<model_id>/<method>/<expNNN>/config.yaml`.

## Ví dụ

```yaml
exp_id: exp002
parent: null
model: qwen3-4b-instruct-2507
method: prompt-cot
notes: "CoT 1 shot, chấm trên val"
data:
  dataset: cosmetics
  version: v0.1.0
  roles: { train: train, val: val, eval: test }
prompt: prompt.txt
examples: examples.txt
system_prompt: configs/prompts/system/absa_cot.txt
requires_extra: []
```

## Giải thích

| Khoá             | Ý nghĩa                                                                                      |
| ---------------- | -------------------------------------------------------------------------------------------- |
| `exp_id`         | định danh thí nghiệm, trùng tên thư mục                                                      |
| `parent`         | thí nghiệm gốc, ghi bằng đường dẫn đầy đủ `<model>/<method>/<expNNN>`; `null` nếu là bản gốc |
| `model`          | `model_id`, trỏ tới `configs/models/<model_id>.yaml`                                         |
| `method`         | tên phương pháp, cũng là tên thư mục cha                                                     |
| `notes`          | một dòng mô tả thí nghiệm khác gì các thí nghiệm khác; `--title` của `new_experiment.py` điền vào đây |
| `data.dataset`   | **một** dataset duy nhất. Không được khai danh sách                                          |
| `data.version`   | phiên bản dataset, trỏ tới `configs/datasets/<name>/<version>.yaml`                          |
| `data.roles`     | **bắt buộc khai**, không kế thừa: mỗi vai dùng split nào của chính dataset đó                |
| `prompt`         | đường dẫn file prompt: tính từ thư mục THÍ NGHIỆM trước, rồi tới gốc repo (từ đây lên gốc là bốn cấp) |
| `examples`       | đường dẫn file ví dụ few-shot, bắt buộc khi prompt dùng ô nhớ `{examples}`                   |
| `system_prompt`  | đường dẫn khối chỉ dẫn hệ thống dùng chung, bắt buộc khi prompt dùng ô nhớ `{system_prompt}`. File nhận cả hai cách viết: chỉ có câu hệ thống, hoặc có mục `[SYSTEM]` |
| `requires_extra` | danh sách đường dẫn bổ sung mà notebook phải kiểm, cho thứ máy không suy ra được. Mục **bắt đầu bằng `data/`** tính từ GỐC DỮ LIỆU (`SENTIMENTX_DATA_ROOT`) - trên Colab là thư mục Drive; mục khác tính từ gốc repo |

## Ghi đè lớp dùng chung: được, kể cả ngưỡng cắt input

Lớp thí nghiệm là lớp **CUỐI** khi hợp nhất, nên khoá nào đã có ở lớp trước đều khai lại được ở đây,
và giá trị khai lại là giá trị chạy. Ví dụ với ngưỡng cắt input:

```yaml
preprocess:
  max_length: 2304          # ghi đè `preprocess.max_length` của configs/models/<model_id>.yaml
```

Dùng khi một thí nghiệm cần ngưỡng khác hẳn ngưỡng của model: prompt nhiều ví dụ thì dài hơn, ngưỡng
của model có thể không đủ, và phần bị cắt là phần ĐUÔI - đúng chỗ chứa dòng dạy định dạng đầu ra.
Hai điều cần nhớ:

- Ngưỡng KHÔNG làm đổi phép đo độ dài input; nó chỉ quyết định **ai bị cắt**
  (`docs/04_experiments/02_model_input.md` mục 4.2).
- `run_token_stats.py` đo theo ngưỡng trong file cấu hình model, nên muốn đo theo ngưỡng của thí
  nghiệm thì truyền `--max-length` đúng giá trị đó.

Ngưỡng đang dùng được in ra khi chạy và ghi vào `run.log` (`[RUN] max_length=...`), nên không phải
đoán xem lượt chạy đó dùng số nào. (Trước 25/09/2026, ghi đè ở lớp thí nghiệm bị bỏ qua trong im
lặng: bước lập kế hoạch đọc thẳng file cấu hình model.)

`prompt`, `examples`, `system_prompt` đều nhận TÊN TRẦN (không dấu `/`, không `.txt`) để lấy file
trong thư viện dùng chung: `configs/prompts/<tên>.txt`, `configs/prompts/examples/<tên>.txt`,
`configs/prompts/system/<tên>.txt`. Muốn dùng chung một khối hệ thống cho nhiều prompt thì viết câu
hệ thống một lần ở `configs/prompts/system/<tên>.txt` rồi cho các prompt cùng trỏ vào đó.

## Quy tắc vai

| Vai     | Bắt buộc                     | Ghi chú                                                   |
| ------- | ---------------------------- | --------------------------------------------------------- |
| `eval`  | luôn                         | thí nghiệm chỉ prompt cũng cần, để biết chấm trên tập nào |
| `train` | khi `training.enabled: true` |                                                           |
| `val`   | khi `training.enabled: true` | là cơ sở chọn `model/best`                                |

Ngoài ra: giá trị của mỗi vai phải là khoá có thật trong `splits` của file dataset version.
Chấm trên `train` bị chặn, vì đó là rò rỉ dữ liệu.

## Thí nghiệm dùng model encoder thì khác gì

Model encoder (`approach: encoder`) học từ dữ liệu gán nhãn, nên config của nó:

- KHÔNG khai `prompt`, `examples`, `system_prompt` - không có câu chỉ dẫn nào để gửi cho model.
- Bắt buộc `enabled: true` và đủ ba vai `train`, `val`, `eval`: học từ `train`, chọn `model/best`
  theo `val`, chấm trên `eval`. Thiếu `val` thì không có cơ sở chọn model tốt nhất.
- Tham số huấn luyện lấy từ `configs/experiments/training.yaml`; phần riêng của kiến trúc (ví dụ
  `lora.target_modules`) lấy từ `configs/models/<model_id>.yaml`.

```yaml
exp_id: exp001
model: visobert
method: lora
notes: "LoRA cơ bản trên ViSoBERT, chấm trên test"
data:
  dataset: cosmetics
  version: v0.1.0
  roles: {train: train, val: val, eval: test}
enabled: true
```

Chi tiết đường chạy (checkpoint, chạy tiếp, thiết bị cần gì):
`docs/04_experiments/06_lora_encoder.md`.

## Thứ tự hợp nhất

```
configs/models/<model_id>.yaml
configs/experiments/repo.yaml
configs/experiments/task.yaml
configs/experiments/evaluation.yaml
configs/experiments/training.yaml
configs/experiments/tracking.yaml
experiments/<model_id>/<method>/<expNNN>/config.yaml     đè lên tất cả
```

Không hợp nhất: `configs/paths.yaml`, `configs/dagshub.yaml`, `configs/pipeline/<v>.yaml`,
`configs/datasets/<name>/<v>.yaml`, và các file prompt. Chúng được ghi vào `run_meta.files[]` kèm `role`.

## Cách ghi đè một giá trị dùng chung

Năm file trong `configs/experiments/` khai khoá ở mức cao nhất, nên muốn đè thì thí nghiệm ghi
**đúng đường dẫn khoá đó** ở mức cao nhất của `config.yaml`:

```yaml
# configs/experiments/evaluation.yaml khai "n: null"
n: 200                      # <= đè đúng khoá đó
preprocess:
  max_length: 1024          # <= đè khoá lồng của lớp model
```

Ghi `evaluation: {n: 200}` là **sai**: nó tạo ra một khoá `evaluation` mới mà không chỗ nào đọc,
trong khi `n` vẫn giữ giá trị cũ. Vì đây là lỗi im lặng, phần kiểm tra sẽ báo lỗi khi gặp khoá
lạ trong cấu hình đã hợp nhất.

## Tạo thí nghiệm mới

Dùng `python scripts/new_experiment.py --model ... --method ... --title "mô tả ngắn"`. Công cụ này tự
chọn số `expNNN` kế tiếp từ trạng thái đã hợp nhất, nên không thể trùng số với thí nghiệm trước;
`--title` điền vào `notes` của `config.yaml`. Đổi tiêu đề sau khi đã tạo cũng được - sửa thẳng dòng
`notes` trong file config.
