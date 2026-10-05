# 05.05. Cấu hình dùng chung cho thí nghiệm

> Đọc file này khi: đổi cách chấm điểm, cách huấn luyện, hoặc cách ghi nhận kết quả.
> Liên quan: `docs/05_config/06_experiment.md`, `docs/04_experiments/metrics.md`

Năm file trong `configs/experiments/`. Chúng hợp nhất với nhau và với cấu hình riêng của thí nghiệm.

## repo.yaml

| Khoá               | Ý nghĩa                                                |
| ------------------ | ------------------------------------------------------ |
| `url`              | địa chỉ repo GitHub                                    |
| `branch`           | nhánh duy nhất notebook kéo code, hiện là `experiment` |
| `allowed_branches` | danh sách nhánh được phép; để trống thì tắt kiểm       |

## task.yaml - định nghĩa bài toán

| Khoá             | Giá trị                                                 | Ý nghĩa                                                                                                                                                               |
| ---------------- | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `label_space`    | `binary` (mặc định) hoặc `full`                         | `binary`: chỉ positive và negative, cộng một quyết định nhị phân riêng là "có nhắc tới hay không". `full`: bốn trạng thái gồm không nhắc, positive, negative, neutral. Không gian nhãn là registry ở `src/labels/` |
| `neutral_policy` | `drop` (mặc định), `as_negative`, `as_positive`, `keep` | cách xử lý ô có nhãn `neutral` khi ở `binary`. Số ô bị loại được ghi vào `metrics.json`                                                                               |
| `not_mentioned`  | `separate` (mặc định), `as_class`                       | `separate`: "có nhắc tới hay không" là quyết định nhị phân riêng, đúng như công bố. `as_class`: coi đó là một lớp                                                     |
| `aspects`        | `all` hoặc danh sách                                    | giới hạn khía cạnh dùng cho thí nghiệm                                                                                                                                |

Việc chiếu nhãn theo `label_space` là một bước của **tiền xử lý cho model**, không phải của pipeline.
Pipeline giữ nguyên bốn trạng thái.

## evaluation.yaml - cách chấm điểm

| Khoá               | Ý nghĩa                                                                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------- |
| `n`                | số mẫu dùng để chấm; `null` nghĩa là toàn bộ split                                                          |
| `decoding`         | cách sinh văn bản: `greedy` chọn token xác suất cao nhất nên tất định; `sample` lấy `temperature`/`top_p`, và để `null` nghĩa là dùng khuyến nghị trong model card (`CARD_SETTINGS` của `src/experiments/experiment_run.py`) |
| `decoding.max_new_tokens` | trần token sinh cho MỘT review; **không khai thì là 400** (`runner.DEFAULT_MAX_NEW_TOKENS`). Khai khi cần câu trả lời DÀI hơn, nhất là lượt **bật suy nghĩ** (model viết hết trần trong khối ` thinking` rồi không in ra JSON - đã gặp với `Qwen/Qwen3-0.6B`; xem `docs/04_experiments/metrics.md` luật 3). Thứ tự ưu tiên: tham số `max_new_tokens` truyền vào lúc chạy > khoá này > 400. **Tên cũ:** kế hoạch đợt 7 và một số ghi chú trước đây gọi khoá này là `generation.max_new_tokens` - đó là **TÊN CŨ**, không phải một khoá thứ hai; chỉ `decoding.max_new_tokens` được `KNOWN_KEYS` nhận và có tác dụng |
| `decoding.seed`    | hạt giống của chế độ **lấy mẫu**; cặp khoá với `mode: sample` (luật 23 của `docs/00_workflow/02_rules.md`). Không khai thì dùng `SEED_DEFAULT` = 42, **đúng bằng giá trị trước đây nằm cứng trong mã**, nên các lượt cũ không đổi dấu vân tay. Phải khai được trong config vì ba lượt lấy mẫu cho bước **biểu quyết** cần ba hạt giống khác nhau - hạt giống đi vào dấu vân tay lượt chạy, nên cùng hạt giống là cùng thư mục kết quả. Chế độ `greedy` bỏ qua khoá này (hạt giống để `null` trong bản ghi). Thứ tự ưu tiên: tham số `seed` truyền vào lúc chạy > khoá này > 42 |
| `scores`           | danh sách tên chỉ số cần tính; tên phải có trong registry `SCORERS`, thiếu tên thì báo lỗi                  |
| `scores_paper`     | danh sách chỉ số chấm thêm trên CƠ SỞ ĐO CỦA CÔNG BỐ (`scores_paper` trong `metrics.json`); mặc định bỏ `aspect_detection` vì trên cơ sở này mọi ô giữ lại đều "có nhắc tới". Bỏ hẳn khoá này thì suy ra từ `scores`. Xem `docs/04_experiments/metrics.md` mục "Hai cơ sở đo" |
| `group_by`         | chiều phân rã bảng chỉ số, ví dụ theo `aspect` và `sentiment`                                               |
| `save.predictions` | ghi `predictions.csv` hay không                                                                             |
| `save.plots`       | giữ chỗ cho biểu đồ sinh kèm lượt chạy; hiện biểu đồ do bước sinh báo cáo vẽ từ `metrics.json`, nên khoá này chưa có tác dụng và không nên bật với hy vọng có thêm hình               |
| `save.confusion`   | ghi ma trận nhầm theo khía cạnh hay không                                                                   |

## training.yaml - huấn luyện

| Khoá                                                          | Ý nghĩa                                                                                 |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `enabled`                                                     | `true` với thí nghiệm huấn luyện. Khi `true`, `roles` bắt buộc có `train` và `val`       |
| `trainer`                                                     | cách huấn luyện, phải có tên trong registry `TRAINERS` (`src/training/`); hiện có `lora` |
| `lora.r`, `lora.alpha`, `lora.dropout`                        | hệ số LoRA (thứ RIÊNG của từng kiến trúc như `lora.target_modules` khai ở config model)   |
| `lr`, `batch`, `epochs`, `grad_accum`, `weight_decay`         | tham số huấn luyện. `weight_decay` là weight decay thật                                 |
| `head.trainable`                                              | cơ chế học của ĐẦU PHÂN LOẠI (chỉ đường encoder): `false` (**mặc định**) = **ĐÓNG BĂNG** - `peft` đóng băng mọi tham số không phải adapter nên chỉ adapter học, còn đầu phân loại là một phép chiếu NGẪU NHIÊN CỐ ĐỊNH (`head.pt` của bốn lượt LoRA đầu tiên giống nhau TỪNG BYTE giữa các checkpoint - đó là số đo, không phải suy đoán); `true` = đầu phân loại HỌC cùng adapter, dùng CHUNG `lr` (cố ý **không** có `lr` riêng: một biến mỗi thí nghiệm). Giá trị KHÔNG phải `true`/`false` là LỖI, không đoán hộ (`bool("flase")` là `True`, nên đoán hộ ở đây là BẬT một cơ chế học khác mà không ai biết). Đổi giá trị đổi `config_sha256` nên ra THƯ MỤC KẾT QUẢ MỚI. Xem `docs/04_experiments/06_lora_encoder.md` |
| `checkpoints.every_n_steps`                                   | lưu checkpoint mỗi bao nhiêu bước                                                       |
| `checkpoints.keep_last_k`                                     | giữ bao nhiêu checkpoint gần nhất để resume; cũ hơn thì xoá                             |
| `checkpoints.save_last`                                       | lưu `model/last` đủ để chạy tiếp                                                        |
| `checkpoints.save_best`                                       | lưu `model/best` theo chỉ số trên `val`                                                 |
| `checkpoints.delete_intermediate`                             | xoá ngay các `checkpoint-*` trung gian sau mỗi lần lưu, để tiết kiệm Drive              |
| `checkpoints.best_metric`                                     | chỉ số để chọn `model/best` và để dừng sớm; phải là một khoá trong kết quả đo val của trainer (`accuracy_cell`, `sentiment_f1`, `sentiment_precision`, `sentiment_recall`, `detection_f1`, `loss`, ...). Mặc định dự án dùng `sentiment_f1` (macro-F1 sắc thái) vì dữ liệu MẤT CÂN BẰNG |
| `early_stop.enabled`                                          | `true` thì dừng sớm khi chỉ số `checkpoints.best_metric` không còn cải thiện. CHỈ đường huấn luyện encoder |
| `early_stop.patience`                                         | số lần đo val LIÊN TIẾP không cải thiện thì dừng (>= 1)                                  |
| `early_stop.min_delta`                                        | mức cải thiện tối thiểu để tính là "có cải thiện"                                        |
| `loss.type`                                                   | `ce` (cross-entropy) hoặc `weighted_ce` (nhân trọng số lớp). Đổi giá trị này đổi `config_sha256` nên ra THƯ MỤC KẾT QUẢ MỚI |
| `loss.class_weight`                                           | `none` hoặc `inverse`; `inverse` = trọng số nghịch đảo tần suất (chuẩn hoá trung bình 1) tính trên ô ĐƯỢC TÍNH của tập train. `weighted_ce` bắt buộc đi kèm `inverse` |

Ai đọc những khoá này: `src/training/checkpoints.py` (chính sách + `Store`) - KHÔNG phải trainer, nên
mọi cách huấn luyện dùng chung. Cách ghi trọng số do writer ở `src/training/savers/` quyết định
(hiện có `adapter` cho LoRA).
Chi tiết checkpoint và cách chạy tiếp: `docs/04_experiments/06_lora_encoder.md`.

Tên nhóm là `checkpoints` (số nhiều) vì `checkpoint` (số ít) đã là tên model trên Hugging Face
ở lớp `configs/models/<model_id>.yaml`; trùng tên thì lớp sau đè mất lớp trước mà không báo gì.

## tracking.yaml - ghi nhận kết quả

| Khoá          | Ý nghĩa                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| `tracker`     | `mlflow`, `local_json` hoặc `none`; tên phải có trong registry `TRACKERS`                            |
| `experiment`  | tên experiment trên máy chủ MLflow                                                                   |
| `mlflow_tags` | nhãn của run trên DagsHub, không phải git tag. Giá trị `auto` nghĩa là notebook tự lấy từ `info` của lượt chạy - tra ở cả khối `experiment` lồng trong đó (`model`, `method`, `exp_id` ghi theo khối, xem `src/tracking/base.py::resolve_tags`). Nhãn nào thiếu giá trị thì BỎ, không gắn chuỗi `auto` |
| `artifacts`   | danh sách file nhỏ được tải lên; không tải checkpoint. CẢ HAI cơ sở đo đều lên: số của cơ sở `paper` nằm trong `metrics.json` (khoá `scores_paper`), và danh sách ô đoán sai của cơ sở đó là `mispredictions_paper.csv`. Nay thêm `run.log` (nhật ký đầy đủ của lượt chạy) và `training_history.csv` (curve train/val) |

Ba trình ghi nhận đang có (registry `TRACKERS` ở `src/tracking/`):

| Tên          | Làm gì                                                                |
| ------------ | --------------------------------------------------------------------- |
| `mlflow`     | ghi lên máy chủ MLflow của DagsHub (địa chỉ ở `configs/dagshub.yaml`) |
| `local_json` | ghi bản ghi JSON trong nhóm report `experiment_registry`              |
| `none`       | không ghi đi đâu cả - lựa chọn hợp lệ khi chạy thử trên máy cá nhân   |

Ghi nhận là việc PHỤ. Máy chủ hỏng, token hết hạn hay mạng đứt đều chỉ thành dòng
`[WARN]`/`[TRACK]` trong `run.log`, còn `metrics.json` vẫn nằm nguyên trong thư mục kết quả: file
được ghi xuống đĩa TRƯỚC khi gọi máy chủ. Thiếu thư viện `mlflow` cũng vậy - lần chạy vẫn xong.
Muốn biết trước thì gọi `tracking.check()` (preflight của notebook dùng hàm này).
