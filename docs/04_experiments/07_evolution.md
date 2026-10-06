# 07. Cây phát triển thí nghiệm

> Đọc file này khi: muốn biết một thí nghiệm SINH RA từ đâu, hoặc vì sao dự án đi bước tiếp theo là bước đó.
> Liên quan: `docs/04_experiments/04_backlog.md` (việc chưa làm), `docs/06_plan/P7_rerun.md` (đợt chạy lại)

File này là bản NGƯỜI ĐỌC của dòng phát triển thí nghiệm: **thí nghiệm nào sinh ra thí nghiệm nào, và
VÌ SAO**. Bảng máy đọc nằm ở `data/reports/experiment_registry/` (mỗi lượt chạy một dòng); ở đây ghi
phần một dòng CSV không chứa được - **lý do** và **quan hệ cha - con** giữa các bước.

Quy ước ghi một nút:

```
<expNNN hoặc mã lượt chạy>  <-  <nút cha>            (vì sao đi bước này)
    Kết quả: <số nhanh>       Kết luận: <giữ / bỏ / đổi hướng>
```

File này ĐỂ TRỐNG nội dung cây lúc tạo và được ghi DẦN: mỗi khi chốt một bước phát triển mới (thêm
thí nghiệm, đổi loss, hoãn một kỹ thuật, ...) thì thêm một nút kèm lý do và mốc ngày.

---

## Chốt kỹ thuật của đợt "đo lường + MLflow" (mốc 02/10/2026)

Các mục dưới đây là QUYẾT ĐỊNH đã chốt; việc CHƯA làm nằm ở `docs/04_experiments/04_backlog.md`.

### Chọn `model/best` và dừng sớm

- Chọn best theo `checkpoints.best_metric` (mặc định `sentiment_f1` = macro-F1 sắc thái). Vì sao KHÔNG
  dùng `accuracy_cell`: dữ liệu mất cân bằng (ví dụ `price` 3.238 dương / 21 âm) nên accuracy bị lớp
  trội chi phối, còn macro-F1 cho mỗi khía cạnh một phiếu.
- `val` đo bằng ĐÚNG engine của `test` (`src/evaluation/scorers`), nên `val` có đủ P/R/F1 và detection
  F1 - không có định nghĩa metric thứ hai.
- `early_stop.enabled: true` thì dừng khi chỉ số val không tăng quá `min_delta` trong `patience` lần đo
  liên tiếp. CHỈ đường huấn luyện encoder; model prompt không train nên không đụng tới.

### Hai mục đích, HAI cơ sở đo (đừng lẫn)

| Mục đích | Cơ sở đo | Tập | Nguồn số |
| --- | --- | --- | --- |
| SO VỚI CÔNG BỐ | `paper` | `test` | `metrics.json::scores_paper`, `metrics.csv` (basis=`paper`) |
| CHỌN `model/best` / dừng sớm / vẽ curve | `all` | `val` | `training_history.csv`, khối `training` của `metrics.json` |

KHÔNG đem số `all` đi so công bố, và KHÔNG đưa chỉ số chọn-best (val) vào bảng `metrics_matrix`.

### Rescore là CHẤM THÊM, không ghi đè

`scripts/rescore.py --dir <results/<hash8>>` đọc `predictions.csv` rồi ghi `metrics_rescored.json` /
`metrics_rescored.csv`; `metrics.json`/`metrics.csv` của lượt chạy KHÔNG bị chạm tới. Bảng
`metrics_matrix` hiển thị HAI họ cột `(gốc)` / `(rescored)` khi lượt đó có rescore - không trộn hai
nguồn trong cùng một ô.

### Một phép đo = MỘT run MLflow

`run_meta.json` giữ `tracking.run_id` (dòng log cũng ghi mã run đó); phiên chạy tiếp (RESUME) NỐI vào đúng run đó thay vì mở run
mới. Tham số phẳng gửi ngay khi biết; phần SỐ của cấu trúc lớn (`read_rate`, `cost`, `resume`) đi qua
metric (không bị giới hạn 500 ký tự như param). Số cơ sở `paper` lên MLflow với tiền tố `paper.`; run
tham chiếu công bố do `scripts/log_reference_run.py` ghi (chạy tay khi có mạng).

### Ma trận nhầm ở artifact, không lên MLflow

`confusion` chỉ nằm trong `metrics.json` (khoá `tables.confusion`) và `plots/accuracy.html`; đưa lên
MLflow thì `numeric()` làm phẳng thành hàng trăm metric rời và mất dạng ma trận.

### Chống mất cân bằng

`loss.type: weighted_ce` + `loss.class_weight: inverse` (nghịch đảo tần suất, chuẩn hoá trung bình 1)
là TUỲ CHỌN trong config. Đổi loss đổi `config_sha256` nên ra **thư mục kết quả mới** - kết quả cũ
không bị ghi đè.

### Hoãn có chủ ý

**Optuna** (tìm siêu tham số) hoãn một nhịp: objective/loss vừa đổi, tối ưu sớm là tối ưu nhầm.
**focal loss / trọng số theo khía cạnh** làm sau khi curve cho thấy lớp hiếm bị bỏ. Chi tiết ở backlog.

---

## Cây tính tới 04/10/2026 - mười bảy lượt có kết quả

Sáu nhánh: hai encoder học LoRA (nhóm A, 4 lượt), Qwen3-4B hỏi bằng prompt ở ba mức ví dụ với ba cấu
hình (nhóm B: `exp002-004` 4-bit lô 8; `exp005-007` fp16 lô 4; `exp008-010` 4-bit lô 4), ba biến thể
prompt 1 ví dụ (nhánh E: `exp011-013`), một biến về CÁCH HỎI (nhánh F: một lượt, bỏ suy luận), và một
biến về QUY MÔ model (nhánh G: 0.6B, CHƯA có kết quả). Số dưới đây là cơ sở `paper` trên split `test`,
đọc từ `data/reports/metrics_matrix/`; câu hỏi và điểm riêng của từng lượt ở
`docs/04_experiments/08_experiment_rationale.md`.

**Cập nhật 05/10/2026:** cây này là bản chụp **17 lượt CÓ kết quả**. Ngoài ra đã tạo **6 lượt ablation đầu
phân loại** (CHƯA chạy - xem §2b của `08_experiment_rationale.md`) và registry nay có **sáu** encoder chứ
không phải hai; nhóm mới chưa có số nên không nằm dưới đây.

```
qwen3-4b-instruct-2507/prompt-cot/exp002   <- (gốc nhóm prompt)      đúng mức COT+0-shot của công bố
    Kết quả: acc TB khía cạnh 97,16 · F1 sắc thái macro 0,895 · 2.415 ô
    Kết luận: GIỮ - mốc gốc của nhóm

qwen3-4b-instruct-2507/prompt-cot/exp003   <- (gốc nhóm prompt)      mức COT+1-shot của công bố
    Kết quả: 97,72 · 0,926 · 2.315 ô
    Kết luận: GIỮ - mốc 1 ví dụ, hơn công bố 0,02 điểm

qwen3-4b-instruct-2507/prompt-cot/exp004   <- (gốc nhóm prompt)      mức COT+5-shot của công bố
    Kết quả: 97,11 · 0,902 · 2.378 ô   (đọc được 99,88%; chạy TIẾP, dùng lại 1.304 mẫu)
    Kết luận: GIỮ - nhưng thêm ví dụ KHÔNG tăng điểm so với exp003

qwen3-4b-instruct-2507/prompt-cot/exp005   <- exp002                 fp16 + lô 4 - mức 0 ví dụ
    Kết quả: 96,62 · 0,896 · 2.580 ô
    Kết luận: GIỮ - đối chứng lượng hoá cho exp008

qwen3-4b-instruct-2507/prompt-cot/exp006   <- exp003                 fp16 + lô 4 - mức 1 ví dụ
    Kết quả: 96,60 · 0,909 · 2.461 ô
    Kết luận: GIỮ - đối chứng lượng hoá cho exp009

qwen3-4b-instruct-2507/prompt-cot/exp007   <- exp004                 fp16 + lô 4 - mức 5 ví dụ
    Kết quả: 96,48 · 0,899 · 2.520 ô   (lâu nhất trong 17 lượt: 13.833 giây)
    Kết luận: GIỮ - đối chứng lượng hoá cho exp010

qwen3-4b-instruct-2507/prompt-cot/exp008   <- exp002                 4-bit + lô 4 - mức 0 ví dụ
    Kết quả: 97,26 · 0,894 · 2.414 ô   (hơn exp005 0,64 điểm, nhưng bớt 166 ô)
    Kết luận: GIỮ - nửa đầu của phép so lượng hoá SẠCH MỘT BIẾN

qwen3-4b-instruct-2507/prompt-cot/exp009   <- exp003                 4-bit + lô 4 - mức 1 ví dụ
    Kết quả: 97,77 · 0,928 · 2.324 ô   (hơn exp006 1,17 điểm, nhưng bớt 137 ô)
    Kết luận: GIỮ - ĐỈNH của 17 lượt, hơn công bố 0,07 điểm (nằm trong nhiễu một lần chạy greedy)

qwen3-4b-instruct-2507/prompt-cot/exp010   <- exp004                 4-bit + lô 4 - mức 5 ví dụ
    Kết quả: 97,19 · 0,907 · 2.375 ô   (hơn exp007 0,71 điểm; chạy TIẾP, 411,3 giây)
    Kết luận: GIỮ - cùng chiều với hai lượt trên

qwen3-4b-instruct-2507/prompt-cot/exp011   <- exp003                 ví dụ 1 có NHÃN ÂM (texture/stayingpower/packing)
    Kết quả: 97,63 (kém exp003 0,09) · 0,902 · 2.359 ô · F1 `price` âm 0,308 (exp003: 0,600)
    Kết luận: BỎ - sửa VÍ DỤ không giúp, còn làm `price` âm tệ đi

qwen3-4b-instruct-2507/prompt-cot/exp012   <- exp003                 thêm bước 0 "quét mọi lời phàn nàn"
    Kết quả: 96,52 (kém 1,20) · 0,908 · 2.305 ô · F1 `price` âm 0,600
    Kết luận: BỎ - thêm quy trình dài vào CÂU CHỮ prompt không giúp

qwen3-4b-instruct-2507/prompt-cot/exp013   <- exp003                 thêm "lưu ý dữ liệu lệch nhãn"
    Kết quả: 92,66 (kém 5,06) · 0,842 · 1.972 ô   (mất 343 ô) · F1 `price` âm 0,167
    Kết luận: BỎ - lời nhắc lệch nhãn làm model kiêng trả lời, hại cả điểm lẫn số ô

qwen3-4b-instruct-2507/prompt-one-turn/exp001  <- (gốc)               bỏ suy luận từng bước thì mất bao nhiêu
    Kết quả: 95,33 · 0,871 · 2.663 ô   (kém CoT 0 ví dụ 1,83 điểm)
    Kết luận: GIỮ - bằng chứng CoT có tác dụng thật, không chỉ tốn token

phobert-base-v2/lora/exp001                <- (gốc)                  encoder + tách từ vncorenlp, học LoRA gốc
    Kết quả: 88,40 · 0,540 · 2.665 ô   (stayingpower 64,71 - thấp nhất bảng)
    Kết luận: GIỮ làm mốc ĐỐI CHỨNG

phobert-base-v2/lora/exp002                <- exp001                 chỉ thêm `weighted_ce` + `inverse`
    Kết quả: 96,62 (+8,22 điểm) · F1 macro 0,876 (+0,336) · 2.736 ô · `price` âm vẫn 0,00
    Kết luận: GIỮ - SỬA BẰNG HỌC là hướng hiệu quả nhất của dự án

visobert/lora/exp001                       <- (gốc)                  encoder đọc nguyên bản, không tách từ
    Kết quả: 94,86 · 0,765 · 2.688 ô   (phát hiện khía cạnh tốt nhất: F1 macro 0,966)
    Kết luận: GIỮ - mất điểm ở lớp TIÊU CỰC: colour 0,50 · price 0 · packing 0

visobert/lora/exp002                       <- exp001                 chỉ thêm `weighted_ce` + `inverse`
    Kết quả: 95,61 (+0,75 điểm) · F1 macro 0,836 (+0,071) · 2.701 ô
    Kết luận: GIỮ - cùng cơ chế nhưng lợi ít hơn hẳn; ĐẢO THỨ HẠNG hai encoder

qwen3-0.6b/prompt-cot/exp001..003          <- (gốc)                  model nhỏ hơn ~7 lần thì kém bao nhiêu
    Kết quả: KHÔNG DÙNG - đã chạy HAI lần, hỏng HAI kiểu khác nhau:
              (1) `8db40559`/`db6efb02`/`30c9e674` nạp NHẦM trọng số 4B (metrics.model =
                  Qwen/Qwen3-4B-Instruct-2507; số ô 2.580/2.461/2.520 trùng khít exp005/006/007);
              (2) `bc32904d`/`edc0797a`/`d5b8e7fc` đúng 0.6B nhưng BẬT SUY NGHĨ ăn hết trần 400 token
                  (đọc được 3,33/1,36/1,73%; `<think>` 999/714/788 lần). Cả sáu xoá 04/10/2026.
    Kết luận: ĐỔI HƯỚNG - chạy lại với `preprocess.enable_thinking: false`; lượt bật suy nghĩ thành
              nhánh RIÊNG, có bước DÒ (`exp004`) chốt trần token trước khi chạy đầy đủ
```

Đọc cây này kèm `04_backlog.md` (việc chưa làm) và `08_experiment_rationale.md` (câu hỏi của từng lượt).
Nhánh G (0.6B) có nút kết quả ở bản chụp 05/10 bên dưới; sáu thư mục của ba lượt đầu đã xoá
(04/10/2026) vì không dùng được; xem `08_experiment_rationale.md` §5.

## Cây tính tới 05/10/2026 - 23 lượt của đợt 7 (bản chụp thứ hai, nối tiếp bản trên)

Số ở cơ sở `paper` trên `test`, trừ lượt nào ghi rõ `VAL` (số `val` để CHỐT LUẬT, không so công bố). Lượt
nào KHÔNG dùng được thì nói thẳng là không dùng được - không suy diễn thay cho lượt hỏng.

```
BỐN ENCODER MỚI (nhóm C; parent null; cùng công thức LoRA + `weighted_ce` của nhóm A):
cafebert/lora/exp001                 <- (gốc)  kho tiếng Việt, kiến trúc DeBERTa, không tách từ
    Kết quả: 97,67 · F1 macro 0,886 · F1 âm macro 0,788 · 2.745 ô   <-- TỐT NHẤT trong sáu encoder
    Kết luận: GIỮ - "PhoBERT không phải lựa chọn duy nhất"
phobert-large/lora/exp001            <- (gốc)  cùng họ PhoBERT nhưng 1.024 ẩn
    Kết quả: 96,54 · 0,875 · 0,775 · 2.718 ô
    Kết luận: GIỮ - to hơn KHÔNG hơn bản base (96,62)
xlm-roberta-base/lora/exp001         <- (gốc)  ĐỐI CHỨNG đa ngữ (tiếng Việt chỉ là phần nhỏ của kho)
    Kết quả: 95,20 · 0,853 · 0,740 · 2.715 ô
    Kết luận: GIỮ - thua cafebert 2,47 điểm ⇒ kho tiền huấn luyện tiếng Việt CÓ giá
vibert-base-cased/lora/exp001        <- (gốc)  kho tiếng Việt, chữ phân biệt hoa/thường
    Kết quả: 94,99 · 0,828 · 0,692 · 2.721 ô
    Kết luận: GIỮ - yếu nhất nhóm encoder

HAI LƯỢT VAL CỦA ENCODER (nhóm D) - điều kiện để CHỐT ngưỡng và trọng số ensemble:
phobert-base-v2/lora/exp003          <- exp002   (VAL)
    Kết quả: 96,78 · 0,942 · F1 âm macro 0,9005 · 2.755 ô
    Kết luận: GIỮ - vế CHỐT của ngưỡng + trọng số
visobert/lora/exp003                 <- exp002   (VAL)
    Kết quả: 94,24 · 0,875 · 0,7768 · 2.727 ô   (thua PhoBERT 2,54 điểm, cùng chiều như trên test)
    Kết luận: GIỮ - vế thứ hai của ensemble

HAI LƯỢT TEST ĐỂ ÁP NGƯỠNG (nhóm D):
phobert-base-v2/lora/exp004          <- exp002   cùng cấu hình, chạy lại trên bản mã ĐÃ SỬA hai lỗi
    Kết quả: 96,62 · 0,876 · 2.736 ô - TRÙNG KHÍT exp002 (từng dòng `metrics.csv`)
    Kết luận: GIỮ - bằng chứng hai lỗi đã sửa KHÔNG đổi số; cũng là lượt nhận ngưỡng
visobert/lora/exp004                 <- exp002
    Kết quả: 95,61 · 0,836 · 2.701 ô - cũng trùng khít exp002
    Kết luận: GIỮ - như trên
```
```
BA LƯỢT VỀ `price` (nhóm E) - chi tiết ở §7 của `08_experiment_rationale.md`:
qwen3-4b/prompt-cot/exp014           <- exp003   sửa câu chữ prompt (định nghĩa lời chê giá gián tiếp)
    Kết quả: 97,01 (−0,71) · 0,906 · 2.228 ô · bắt 4/6 ô `price` âm nhưng gán mã 2 cho 22 ô (cha: 7)
    Kết luận: BỎ - F1 `price` âm 0,600 -> 0,320 (bắt thêm 1 ô đổi lấy 15 báo động giả)
qwen3-4b/prompt-cot/exp015           <- exp003   thêm ví dụ có ô giá mã 2
    Kết quả: 97,39 (−0,33) · 0,915 · 2.436 ô · bắt 3/6 ô, gán mã 2 cho 10 ô
    Kết luận: BỎ - 0,500, vẫn dưới cha
qwen3-4b/prompt-cot/exp016           <- exp003   chẩn đoán: chỉ hỏi ĐÚNG một khía cạnh
    Kết quả: 95,93 · 0,690 · **295 ô** · bắt 4/6 ô   (khác tập ô nên KHÔNG trộn vào bảng chính)
    Kết luận: BỎ khỏi bảng chính, GIỮ làm chẩn đoán

LƯỢT VAL PHÍA LLM (nhóm F):
qwen3-4b/prompt-cot/exp017           <- exp009   (VAL)
    Kết quả: 96,73 · 0,856 · 2.295 ô · `price` âm: val có 0 ô nhưng model vẫn gán mã 2 cho 6 ô
    Kết luận: GIỮ - điều kiện chốt bảng LUẬT LAI

SÁU LƯỢT ĐẦU PHÂN LOẠI (nhóm H; mỗi lượt khác cha ĐÚNG một khoá `head.trainable: true`):
    phobert-large exp001->exp002     : 96,54 -> 97,69   (+1,15) · F1 âm macro 0,775 -> 0,781
    xlm-roberta-base exp001->exp002  : 95,20 -> 96,36   (+1,16) · 0,740 -> 0,740
    phobert-base-v2 exp002->exp005   : 96,62 -> 97,59   (+0,97) · 0,776 -> 0,784
    visobert exp002->exp005          : 95,61 -> 96,28   (+0,67) · 0,700 -> 0,723
    vibert-base-cased exp001->exp002 : 94,99 -> 94,84   (−0,15) · 0,692 -> 0,679
    cafebert exp001->exp002          : 97,67 -> 97,88   (+0,21) · F1 âm macro 0,788 -> 0,847
    Kết luận: GIỮ làm PHÉP ĐO CƠ CHẾ, không thay cha: 5/6 cặp hơn 0,21-1,16 điểm, lớp âm gần như đứng
              yên, chỗ đổi rõ nhất là DỊCH CHUYỂN giữa các khía cạnh (`packing` rơi ở 4/6 cặp).
              ĐỢT 10: chạy lại ba nhánh với `decoding.seed: 7` để ĐO biên nhiễu cho đường encoder.

HAI MODEL NHỎ:
qwen2.5-0.5b-instruct/prompt-cot/exp001..003  <- (gốc)  mốc "nhỏ" ở họ KHÁC
    Kết quả: đọc được 95,81 / 97,29 / 100,0 nhưng chỉ chịu trả lời 464 / 256 / 239 ô
              (73,4-82,1% review bị gán "không nhắc tới" cho MỌI khía cạnh); F1 âm macro
              0,257 / 0,056 / 0,000
    Kết luận: GIỮ làm mốc "nhỏ thì kém" - nhưng KHÔNG so điểm trực tiếp được (khác cỡ mẫu)
qwen3-0.6b/prompt-cot/exp001..003    <- (gốc)  mốc "nhỏ" cùng họ
    Kết quả: KHÔNG DÙNG - dưới cửa đọc được (42,02 / 21,63 / 84,41%) và KHÔNG phải vì trần token
    Kết luận: ĐỔI HƯỚNG - nhánh BẬT suy nghĩ (`exp005`, trần 1985) + nhánh MỘT LƯỢT
              (`prompt-one-turn/exp001`)
qwen3-0.6b/prompt-cot/exp004         <- exp002   lượt DÒ (bật suy nghĩ, trần 8.192, 60 mẫu)
    Kết quả: p50 642 / p95 1.072 / p99 1.323 / max 1.434 token sinh; đọc được 98,33%
    Kết luận: GIỮ - đã CHỐT trần 1985 cho nhánh bật suy nghĩ (luật 23a)
qwen3-0.6b/prompt-one-turn/exp001    <- (gốc)  bỏ suy luận, bắt trả JSON ngay
    Kết quả: ĐỌC ĐƯỢC 99,94% (VƯỢT cửa 95%) nhưng acc TB 87,04 · F1 macro 0,610 · F1 âm macro
              0,211 · chỉ 877 ô paper (cũng KIÊNG TRẢ LỜI, khác 0,5B ở chỗ không hỏng định dạng)
    Kết luận: GIỮ - ĐỊNH DẠNG là cơ chế hỏng của ba lượt exp001..003, KHÔNG phải trần token;
              nhưng điểm vẫn thấp ⇒ 0,6B vẫn quá nhỏ để so điểm
qwen3-0.6b/prompt-cot/exp005        <- exp002   BẬT suy nghĩ (1 ví dụ), trần 1985
    Kết quả: đọc được 96,98% (QUA cửa) nhưng acc TB 90,92 · **detection F1 0,479** · F1 âm macro 0,356
    Kết luận: **BỎ nhánh 0.6B bật suy nghĩ** - suy nghĩ làm HỎNG phát hiện khía cạnh (det 0,479 so
              ~0,86-0,91 của nhánh tắt suy nghĩ); 0.6B quá nhỏ, không so điểm được với công bố
qwen3-0.6b/prompt-cot/exp006        <- exp001   BẬT suy nghĩ (0 ví dụ), cùng trần 1985
qwen3-0.6b/prompt-cot/exp007        <- exp003   BẬT suy nghĩ (5 ví dụ), cùng trần 1985
    Kết quả: **HUỶ - KHÔNG chạy** (người dùng chốt 06/10/2026 sau kết quả `exp005`)
```



SÁU BƯỚC KẾT HỢP (không chạy model; đọc lại các lượt đã có; tệp trong `data/reports/fusion/`). Luật chốt trên
`val` rồi mới áp lên `test`:

| Bước | Kết quả | Kết luận |
| --- | --- | --- |
| **Ngưỡng theo khía cạnh** - dò trên `val` (`phobert-base-v2/lora/exp003`) ra 0,95/0,95/0,95/**0,30**/0,95/**0,45**; `price` để nguyên; áp lên `test` (`lora/exp004`) | chỉ khía cạnh `smell` đổi: F1 âm 0,887 → **0,862**; F1 âm macro 0,7757 → **0,7721** (−0,0036); số ô KHÔNG đổi (2.736) | **KHÔNG có tác dụng** (chênh dưới mức nhiễu) - nói "không có tác dụng", KHÔNG nói "có hại" |
| **Ensemble hai encoder** - trọng số chốt trên `val` (PhoBERT 0,5369 · ViSoBERT 0,4631), áp lên `test` | acc TB **96,61** so với PhoBERT một mình 96,62; F1 âm macro **0,7591** so với 0,7757; 2.721 ô so với 2.736 | **KHÔNG có tác dụng** - trộn một encoder kém hơn vào không cải thiện gì |
| **Lai encoder + LLM theo khía cạnh** - luật chốt trên `val` bằng `exp017`; kết quả: chỉ `packing` lấy từ encoder | LLM `exp009` một mình: 97,77 · F1 âm `packing` 0,769 ⇒ lai: **98,02** · micro 98,28 · **F1 âm `packing` 0,952** · 2.324 ô (1.623 ô lấy từ encoder, 4 ô thiếu) | **GIỮ** - +0,25 điểm và F1 âm của khía cạnh đó tăng 0,183; chỉ ĐÚNG MỘT khía cạnh đổi |
| **Biểu quyết 3 mẫu** | **CHƯA chạy** - cần `exp018`/`exp019`/`exp020` (đợt 8) | chưa có gì để đọc |
| **Router theo khía cạnh** (mới, `scripts/ensemble_aspect.py`) - chốt trên `val` với **2 ứng viên đang có ở máy** (`phobert-base-v2/lora/exp003`, `visobert/lora/exp003`) | cả 7 khía cạnh đều chọn PhoBERT-base-v2 ⇒ bản router **trùng** lượt `phobert-base-v2/lora/exp004` (acc macro 93,28; F1 âm macro 0,7757; 2.736 ô). ViSoBERT **cao accuracy hơn** (95,97) nhưng **F1 âm thấp hơn** (0,7004), nên luật `--criterion f1_âm` KHÔNG chọn nó | **chưa đọc được gì** - cần ≥ 4-5 ứng viên `val` mới thấy tác dụng của việc chọn-theo-khía-cạnh. Đây là lần chạy ĐẦU để thử đường ống, không phải một thành tích |
| **Gộp HAI TẦNG** (mới, `scripts/fuse_aspect.py`) - luật ĐÃ CHỐT (`fusion.TWO_TIER_LAW`: khung ô từ encoder, sắc thái từng khía cạnh từ lượt một-khía-cạnh, lệch về "không nhắc tới" thì giữ encoder) | **CHƯA chạy** - cần bảy lượt một-khía-cạnh (`absa_aspect_<khía cạnh>_v1`, mục 14.11) | chưa có gì để đọc; đã có mã + test + luật đóng băng TRƯỚC khi chạy (đúng mục 14.10) |
