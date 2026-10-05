# Bảng KẾT HỢP: ngưỡng theo khía cạnh, ensemble encoder, luật lai, biểu quyết

> Đọc file này khi: mở thư mục này và cần biết tệp nào là gì. Cách dùng chi tiết ở
> `docs/04_experiments/09_fusion.md`.

Bốn bước kết hợp KHÔNG chạy model: chúng đọc `predictions.csv` (nhãn cứng) và `probabilities.csv` (xác
suất từng ô, chỉ đường encoder có), chọn lại nhãn, rồi chấm bằng ĐÚNG engine của dự án
(`src/evaluation/scorers/`). Vì vậy số của chúng so được với số của từng lượt.

| Tệp | Do lệnh nào ghi | Nội dung |
| --- | --- | --- |
| `thresholds.json` | `scripts/fit_thresholds.py --run <val>` | ngưỡng theo từng khía cạnh + bảng quét làm bằng chứng; `price` ghi `null` kèm lí do |
| `thresholds_applied.json` | `scripts/fit_thresholds.py --apply-to <lượt cần áp>` | số khi ÁP bảng ngưỡng đã chốt lên một lượt khác (thường `test`): F1 âm trước/sau, số ô, macro ba cách |
| `rules.json` | `scripts/fuse.py --fit` | luật lai chốt trên `val`: mỗi khía cạnh lấy nguồn nào |
| `ensemble_val.json` | `scripts/ensemble.py --weights val` | số của bản gộp trên **`val`** - vế CHỐT của trọng số (không phải số báo cáo) |
| `weights_val.json` | `scripts/ensemble.py --write-weights` | trọng số đã chốt trên `val`, khoá theo **TÊN MODEL** (nhờ đó ráp được `.../exp003` với `.../exp004`) |
| `ensemble.json` | `scripts/ensemble.py` | số của bản gộp trung bình xác suất + trọng số từng lượt |
| `fuse.json` | `scripts/fuse.py --apply` | số của bản LAI khi áp luật đã chốt |
| `vote.json` | `scripts/vote.py` | số của bản bỏ phiếu + số của TỪNG mẫu + thống kê phiếu |
| `inputs/*.csv` | `scripts/ensemble.py`, `scripts/vote.py`, `dump_inputs` | **đầu vào rút gọn** của từng lượt: khung ô, nhãn đúng, nhãn đoán, `p(mã âm)`, `p(mã dương)` |

**Vì sao commit `inputs/`:** phần LƯỢT CHẠY THẬT của đường encoder (`predictions.csv`,
`probabilities.csv` - từng mẫu, vài trăm KB mỗi tệp) không vào git; repo chỉ giữ phần bằng chứng NHẸ
(`metrics.json`, `metrics.csv`, `run_meta.json`, `run.log`, `mispredictions*.csv`). Nếu chỉ ghi kết luận
thì không ai kiểm lại được con số kết hợp, nên `inputs/` là **bản rút gọn CÓ commit** của đúng dữ liệu
đó. Mỗi lượt vài trăm KB, KHÔNG chứa văn bản review.

**Hai luật bắt buộc** (chi tiết ở `docs/04_experiments/09_fusion.md`):
1. Luật/ngưỡng chốt trên **`val`**, rồi mới áp lên `test` - không xem `test` để chọn.
2. **`price` không có ngưỡng** (`val` có 0 ô âm): ghi `null` + lí do, và đọc `price` bằng số lần gán mã 2
   + danh sách ô âm, KHÔNG bằng F1.
