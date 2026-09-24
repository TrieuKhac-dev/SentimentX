# Thí nghiệm - huấn luyện và đánh giá

## 1. Định dạng nhãn khi huấn luyện

Dữ liệu đã ở dạng **multi_head**: một vector 7 phần tử, mỗi phần tử là mã nhãn
`0/1/2/3`. Cách huấn luyện phổ biến:

- Mỗi aspect có **một đầu ra riêng** (multi-head), hoặc
- Coi đây là bài toán **phân loại nhiều nhãn song song** (multi-label).

Với 7 aspect, model sẽ có 7 đầu ra, mỗi đầu ra dự đoán 4 lớp. **Không** dùng
softmax chung cho cả 7 aspect, vì chúng độc lập nhau.

Bảng mã nhãn và ví dụ dữ liệu: [03_pipeline/05_output.md](../03_pipeline/05_output.md).

## 2. Chỉ số đánh giá

Vì mỗi aspect là một bài toán phân loại 4 lớp riêng, ta báo cáo:

| Chỉ số                       | Ý nghĩa                                                                            |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| **Precision** (độ chính xác) | trong số mẫu model đoán là lớp X, bao nhiêu phần trăm đúng                         |
| **Recall** (độ phủ)          | trong số mẫu thực sự thuộc lớp X, model tìm được bao nhiêu phần trăm               |
| **F1**                       | trung bình điều hoà của Precision và Recall - chỉ số gộp, dùng để so sánh tổng thể |
| **F1 macro**                 | lấy F1 trung bình của các lớp với **trọng số bằng nhau** - phản ánh lớp hiếm       |
| **F1 micro**                 | tính gộp toàn bộ dự đoán - phản ánh tổng thể, bị chi phối bởi lớp nhiều mẫu        |

Nên báo cáo **cả macro và micro** cho từng aspect, vì dữ liệu mất cân bằng
(xem EDA 02: `colour` được nhắc tới nhiều nhất, `stayingpower` ít nhất).

### 2.1. Với model SINH (Qwen3), tách thành HAI câu hỏi

Model sinh trả về văn bản nên bảng điểm phải trả lời hai câu khác nhau, và trộn chúng lại
sẽ che mất kiểu lỗi thật:

| Câu hỏi                                           | Chỉ số                                               | Vì sao tách riêng                                                                                            |
| ------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Model có **nhận ra** khía cạnh nào được nhắc tới? | `P nhắc`, `R nhắc`, `F1 nhắc` (nhị phân 0 vs khác 0) | Model 4B hay "thấy" khía cạnh không có, hoặc bỏ sót khía cạnh có - đây là lỗi khác hẳn với chọn sai sắc thái |
| Khi đã nhận ra, có chọn **đúng mã** cảm xúc?      | `acc`, `acc khi có nhắc`                             | Chọn sai 1 (tích cực) thành 2 (tiêu cực) không làm giảm `F1 nhắc`                                            |

Quy ước đếm (khoá bằng test trong `tests/test_metrics.py`):

```
TP: nhãn đúng != 0 và model đoán != 0     -> tìm đúng khía cạnh có được nhắc
FP: nhãn đúng == 0 nhưng model đoán != 0  -> model "thấy" khía cạnh không có
FN: nhãn đúng != 0 nhưng model đoán == 0  -> model bỏ sót khía cạnh có
```

**Lỗi đã gặp và đã sửa (ghi lại vì nó rất dễ tái diễn):** hai nhánh FP và FN từng bị **hoán
vị**. F1 không đổi (đối xứng) nên bảng điểm vẫn "trông hợp lí" - nhưng Precision và Recall
bị **đổi chỗ cho nhau**, và điều đó chỉ lộ ra khi đối chiếu với số đếm thô: prompt một lượt
được báo precision cao nhất (0,953) trong khi nó lại là cấu hình **nêu thừa khía cạnh nhiều
nhất** (219 ô đoán "có nhắc" so với 192 ô thật) - vô lí. Sau khi sửa: precision 0,836 /
recall 0,953, khớp đúng với số đếm. Kết quả đã ghi được **chấm lại** từ chính file dự đoán
(không phải chạy lại model, vì nhãn đã parse nằm sẵn trong file) và mục lục ghi rõ
`rescored`. Vì vậy mọi thay đổi hàm chấm điểm phải đi kèm một ca test **bất đối xứng**.

## 3. Các câu hỏi thực nghiệm nên trả lời

Đây là phần quan trọng nhất của một khóa luận: chứng minh được **preprocessing nào
thực sự có tác động**.

| Câu hỏi                                          | Cách làm                                                                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| Chuẩn hoá ký tự lặp có giúp không?               | `repeated_chars: false` vs `true`                                                                                  |
| Có nên loại review gibberish?                    | `remove_gibberish: false` vs `true`                                                                                |
| Xử lý trùng lặp toàn cục có công bằng hơn không? | `scope: within_split` vs `global`                                                                                  |
| Model nào tốt nhất cho ABSA tiếng Việt?          | so 3 model (PhoBERT / ViSoBERT / Qwen3) trên **cùng một** dataset; ViTASA gác lại ([04_backlog.md](04_backlog.md)) |
| Tách từ có giúp không, giúp bao nhiêu?           | `run_token_stats.py --segmenter vncorenlp` vs `pyvi` vs `underthesea` vs `none` - rồi so ở bước huấn luyện         |
| Prompt nào tốt hơn?                              | `run_token_stats.py --prompt <tên>` để đo, rồi huấn luyện/đánh giá với từng prompt trong `configs/prompts/`        |
| Loại bỏ `others` có ảnh hưởng gì?                | so với bản giữ `others` (đối chứng)                                                                                |

Với mỗi lần chạy, `processing_log.json` lưu lại cấu hình kèm phiên bản, và mỗi
cấu hình cho ra **một thư mục phiên bản riêng** trong `data/processed/`,
nên ta luôn chỉ ra được khác biệt đến từ phép biến đổi nào:

```bash
python run_pipeline.py --dataset cosmetics --version v0.1.0    # -> phiên bản A
# sửa một tham số trong configs/pipeline/v0.1.0.yaml
python run_pipeline.py --dataset cosmetics --version v0.1.0    # -> phiên bản B (phiên bản A vẫn còn nguyên)

python build_report.py --list # danh sách mọi phiên bản để đối chiếu
```

Danh sách khoá có thể đổi và ý nghĩa từng khoá:
[03_pipeline/03_config.md](../03_pipeline/03_config.md).

## 4. Thứ tự thực hiện đề xuất

1. **Chốt dataset nền** - chạy pipeline với cấu hình mặc định, ghi lại mã phiên bản
   (hoặc tăng `version` trong config để tên dễ đọc).
2. **Chạy baseline** - huấn luyện 3 model (PhoBERT / ViSoBERT / Qwen3) trên dataset nền,
   ghi lại kết quả. ViTASA gác lại ([04_backlog.md](04_backlog.md) mục 1).
3. **Thực nghiệm preprocessing** - đổi từng config một (mỗi lần chỉ đổi **một**
   thứ), chạy lại, so với baseline. Mỗi lần đổi cho ra một phiên bản mới.
4. **Phân tích lỗi** - dùng EDA 02 (ma trận cùng xuất hiện) để hiểu model hay sai
   ở cặp aspect nào.
5. **Tổng hợp** - bảng so sánh cuối cùng: model × cấu hình preprocessing × F1.
   Cột "cấu hình" chính là **mã phiên bản**, nên truy vết được về đúng file config.

## 5. Lưu ý

- Mỗi lần chỉ thay **một** tham số, để biết chắc nguyên nhân thay đổi kết quả.
- Luôn dùng **cùng một tập test** khi so sánh các cấu hình.
- Ghi lại **số dòng** của mỗi phiên bản dataset: nếu preprocessing làm mất quá
  nhiều dữ liệu, kết quả tốt hơn có thể chỉ vì bài toán trở nên dễ hơn, chứ không
  phải vì model giỏi hơn.
- Khi so sánh các cấu hình, con số đáng dùng là **số bản ghi ABSA** (card ở Step 5
  của báo cáo pipeline), không phải số dòng dữ liệu: một phần dữ liệu không có nhãn
  khía cạnh nào nên không đóng góp mẫu huấn luyện nào
  ([02_eda/02_metrics.md mục 11](../02_eda/02_metrics.md)).
- Trước khi huấn luyện, chạy `python run_token_stats.py` để biết input thật của
  từng model ([02_model_input.md mục 2](02_model_input.md)): nếu một model bị cắt quá
  nhiều input thì mọi so sánh sau đó đều không công bằng.

## 6. Kết quả đã có - Qwen3 chạy bằng CHỈ DẪN (prompt một lượt vs CoT)

Đây là phần đầu tiên của nhóm thí nghiệm có số liệu CHẤT LƯỢNG thật. Ba model encoder (PhoBERT,
ViSoBERT) chưa có script huấn luyện, nên bảng dưới đây so **bốn cách hỏi cùng một model
Qwen3-4B**, chưa phải so model với model.

### 6.1. Cách chạy (tái lập được)

```bash
python scripts/new_experiment.py --model qwen3-4b-instruct-2507 --method prompt-cot --title "CoT 1 shot"
# rồi mở notebook của thí nghiệm và chạy toàn bộ
```

| Tham số    | Giá trị                                                                                    | Vì sao                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Tập chạy   | `val`, **tập con 100 review** (`random.Random(42).sample`)                                 | `val` là tập LỰA CHỌN; test để dành cho con số cuối. Chạy tập con vì GPU chỉ 6 GB        |
| Sinh       | **greedy** (`do_sample=False`)                                                             | Tái lập: chạy lại phải ra đúng kết quả đó                                                |
| Nạp model  | 4-bit nf4, batch 4                                                                         | 4B ở bf16 là 8 GB, GPU có 6 GB                                                           |
| Ngưỡng cắt | 1280 token                                                                                 | prompt CoT cần tới 1.195 token (tiền xử lý cho model, mục 4.2)                              |
| Đầu ra     | `predictions__*.csv` (từng review) + `metrics__*.csv` (từng khía cạnh) + `summary__*.json` | mục lục ghi thêm prompt, sha, sha BỘ VÍ DỤ, cấu hình sinh, và `rescored` nếu có chấm lại |

### 6.2. Kết quả (cùng một tập 100 review)

| Prompt                      | ví dụ | acc macro | khớp hoàn toàn | P nhắc | R nhắc    | F1 nhắc micro | F1 nhắc macro | token sinh/review | thời gian |
| --------------------------- | ----- | --------- | -------------- | ------ | --------- | ------------- | ------------- | ----------------- | --------- |
| `qwen_absa_v1` (một lượt)   | 0     | 90,86     | **55%**        | 0,836  | **0,953** | **0,891**     | **0,884**     | **46**            | **104 s** |
| `qwen_absa_cot_zeroshot_v1` | 0     | **91,43** | 53%            | 0,916  | 0,854     | 0,884         | 0,869         | 233               | 564 s     |
| `qwen_absa_cot_1shot_v1`    | 1     | 89,29     | 47%            | 0,901  | 0,760     | 0,825         | 0,825         | 217               | 676 s     |
| `qwen_absa_cot_v1`          | 2     | 91,14     | 51%            | 0,909  | 0,833     | 0,870         | 0,868         | 217               | 739 s     |

Chi phí **input** đã đo ở tiền xử lý cho model (mục 4.2): 228,61 / 375,61 / 680,61 / 949,61 token/review - nên
tổng chi phí của CoT là input dài hơn **và** output dài hơn cùng lúc.

Bốn điều đọc ra từ bảng này:

1. **CoT KHÔNG thắng rõ.** Bốn cấu hình nằm trong khoảng 89,29-91,43 điểm acc macro. Với
   100 review × 7 khía cạnh = 700 ô, mỗi ô đúng/sai làm acc macro đổi ~0,14 điểm, nên chênh
   lệch lớn nhất (2,14 điểm khoảng 15 ô) là **quá nhỏ để kết luận**. Nói "CoT tốt hơn" từ bảng
   này là nói quá.
2. **Chi phí thì khác hẳn.** CoT sinh 217-233 token/review so với **46** của prompt một lượt
   (gấp 4,7-5,1 lần), cộng thêm input gấp 1,6-4,2 lần, và tốn 5,4-7,1 lần thời gian (104 s
   -> 564-739 s cho 100 review). Đổi lại **không có chỉ số nào tăng có ý nghĩa** -> với bài
   toán này và model 4B, prompt một lượt là lựa chọn đúng; CoT để dành cho câu hỏi khó hơn.
3. **CoT đổi KIỂU LỖI, không chỉ đổi điểm.** Prompt một lượt **nêu thừa** khía cạnh: 219 ô
   đoán "có nhắc" so với 192 ô thật, nên nó thiên về recall (0,953) và kém precision
   (0,836). CoT **thận trọng hơn**: precision 0,833-0,916 nhưng recall tụt còn 0,760-0,909,
   và càng nhiều ví dụ thì recall càng thấp. Đây là thông tin dùng được: muốn tăng recall
   thì phải chỉnh bộ ví dụ - ví dụ hiện tại gán "có nhắc" cho 5/7 khía cạnh, có thể đang dạy
   model rằng "nêu nhiều mới đúng", trong khi xu hướng đo được lại ngược lại.
4. **Khía cạnh khó nhất là `colour` và `texture`** ở cả bốn cấu hình (acc 80-88%), đúng hai
   khía cạnh được nhắc nhiều nhất (49 và 31 ô trên 100 review). Lưu ý về phép đo: tập con
   này chỉ có **20 ô mã 2 (tiêu cực)** và **15 ô mã 3 (trung tính)**, nên phần lớn khác biệt
   điểm số đến từ việc "có nhận ra khía cạnh hay không", chưa phải "phân biệt sắc thái".

### 6.3. Hạn chế của kết quả này

- **Tập con 100 review** (seed 42): đủ để thấy xu hướng, chưa đủ để chốt con số.
- **Một lần chạy greedy** cho mỗi cấu hình: chưa đo dao động giữa các lần chạy.
- **Lượng hóa 4-bit** để vừa VRAM; chưa đối chiếu bf16 (GPU 6 GB không chạy nổi bf16).
- **Chưa so với PhoBERT / ViSoBERT** - hai model này chưa có script huấn luyện, nên bảng
  trên chưa có dòng nào để so model với model.
- **Chưa chạy trên test**: đúng nguyên tắc - test chỉ dùng cho con số cuối sau khi chốt.

## 7. Việc còn thiếu của nhóm thí nghiệm

| Việc                                              | Bắt đầu từ đâu                                                                               |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Huấn luyện PhoBERT (× 4 bộ tách từ) và ViSoBERT   | chưa có script; dùng `loader.to_multi_head_arrays()` với `max_length` của từng module model  |
| Tăng `--limit` lên 300-500 cho hai cấu hình chính | `python run_qwen_eval.py --split val --limit 300 ...` (khoảng 5-35 phút tuỳ prompt)          |
| Đo dao động                                       | `--sample --seed <n>` vài lần; cấu hình lấy đúng khuyến nghị của model card (0.7 / 0.8 / 20) |
| Self-consistency (lấy mẫu nhiều lần rồi bỏ phiếu) | hạ tầng đã có: chạy `--sample` nhiều seed rồi bỏ phiếu theo từng ô                           |
| Đối chiếu bf16 với 4-bit                          | cần GPU >= 24 GB, hoặc chạy trên Colab/Kaggle                                                 |
| Chạy trên `test` sau khi chốt                     | `--split test` (script in cảnh báo về việc dùng test)                                        |
| Chấm lại khi đổi cách chấm | chấm lại từ file dự đoán trong thư mục kết quả, không cần GPU |

---

Xem thêm: [01_models.md](01_models.md) - bốn model;
[02_model_input.md](02_model_input.md) - chuẩn bị input cho model.
