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
trong đợt này (`src/experiments/encoder_run.py`, `src/training/lora.py`) và đã chạy trọn vẹn một lượt thu nhỏ trên
máy cá nhân trước khi ghim; ô cấu hình của notebook và phép kiểm dữ liệu gốc trong preflight cũng đã
được sửa sau lượt chạy thử đầu tiên trên Colab. Năm con số của tập `test` vẫn đang chờ máy GPU của
Colab.

*Cập nhật 26/09/2026 - lượt chạy thật đầu tiên trên Colab (giữ lại làm mốc trước khi dọn):* cả ba
đường chạy đã chạy trọn vẹn trên T4 và ghi kết quả vào Drive. Bảng dưới là số của tập `test` (1.518
review, `label_space: binary`, `neutral_policy: drop`, 199 ô neutral bị loại ở cả ba lượt):

| Thí nghiệm | Thư mục kết quả | commit ghim | accuracy macro/micro | when-mentioned | detection F1 (micro) | sentiment F1 macro/micro | exact match | giây |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `visobert/lora/exp001` | `0c458fe4` | `0e9473b` | 97,00 / 97,02 | 92,45 | 0,966 | 0,758 / 0,921 | 82,61 % | 2095 |
| `phobert-base-v2/lora/exp001` | `5b5f429c` | `0e9473b` | 95,64 / 95,67 | 86,25 | 0,964 | 0,539 / 0,872 | 75,69 % | 2348 |
| `qwen3-4b-instruct-2507/prompt-cot/exp002` | `6e186300` | `0e9473b` | 93,79 / 93,82 | 82,90 | 0,875 | 0,765 / 0,868 | 66,47 % | 3129 |

Ba ghi chú đọc số:

1. **PhoBERT lặp lại y hệt lần trước**: `6b14bfb8` (commit `b14dc1f`) và `5b5f429c` (commit `0e9473b`) có
   `metrics.json` khác nhau ĐÚNG hai dòng `giây` (2198,1 so với 2301,0) - mọi chỉ số, từng khía cạnh và
   confusion matrix giống tuyệt đối. Đường encoder vì vậy là **tái lập được** với seed cố định; lượt
   `6b14bfb8` là bản lặp, không phải kết quả thứ hai.
2. **Mặt TIÊU CỰC là chỗ yếu của hai encoder**: `texture` (82 ô âm), `smell` (48), `colour` (54),
   `price` (6), `packing` (10) đều F1 = 0 ở lượt PhoBERT (model không đoán âm lần nào), trong khi
   ViSoBERT đoán được: `texture` 0,771, `smell` 0,778, `colour` 0,506, `shipping` 0,939. Đây là chỗ đối
   chiếu trực tiếp với bảng của công bố.
3. **Lượt Qwen exp002 chạy hai phiên** (hết quota Colab giữa chừng): `run.log` ghi hai dòng
   `=== lần chạy … mode=NEW` rồi `mode=RESUME`, `metrics.json` ghi `resume: reused 784, new 734`
   (784 + 734 = 1.518). Bản ghi `run_meta.json` khi đó chỉ giữ được MỘT attempt vì lỗi ghi đè đã sửa
   ở P4 (thiếu `previous=`).

Ba lỗi chặn đường của các lượt hỏng (đã xử lý, ghi lại để P7 T5 khỏi vấp lại):

| Thư mục | commit | Lỗi | Đã xử lý bằng |
| --- | --- | --- | --- |
| `06517238` | `ab7f53e` | `ImportError: Found an incompatible version of torchao … 0.10.0 … above 0.16.0` | ô bootstrap hỏi chính `peft` rồi **gỡ** `torchao` (từ `63def29`) |
| `efcdb205` | `ce40cfc` | cùng lỗi torchao | như trên |
| `c95ca35a` | `63def29` | `RuntimeError: Sizes of tensors must match except in dimension 0. Expected size 107 but got size 164` | `lora.encode` pad mọi lô về cùng độ rộng (từ `b14dc1f`) |

Cả ba lượt hỏng còn có cảnh báo `không dùng được MLflow: chưa cài thư viện mlflow` - tức **không lượt
nào lên DagsHub**, xem mục "Cổng MLflow" ở `P4_logging_mlflow.md`. Toàn bộ bảy thư mục kết quả cũ đã
được XOÁ theo yêu cầu (26/09/2026) để chạy lại từ đầu; bảng và bảng lỗi trên là bản ghi duy nhất còn
lại của đợt đó.

*Cập nhật 29/09/2026 - đợt thí nghiệm thứ ba (lưới MƯỜI HAI lượt):* T3 nay gồm **mười hai** thí nghiệm,
vẫn ghim CÙNG một bản code: năm lượt của đợt hai, thêm một lượt Qwen3 `prompt-one-turn/exp001` (prompt MỘT
LƯỢT, 0 ví dụ - mốc so với ba mức CoT), ba lượt Qwen3-0.6B (`qwen3-0.6b/prompt-cot/exp001` đến `exp003`,
đúng ba mức ví dụ, nên câu hỏi "model nhỏ hơn 10 lần mất bao nhiêu điểm" trả lời được mà không đổi thứ gì
khác - bản 0.6B có `tokenizer.json` giống từng byte), và ba lượt **đối chứng KHÔNG lượng hoá** cho model
4B (`qwen3-4b-instruct-2507/prompt-cot/exp005` đến `exp007`, `parent` trỏ đúng lượt 4-bit của cùng mức ví
dụ, khai thêm `inference.quantization: null`, `dtype: float16`, `batch_size: 4`). Nhóm fp16 trả lời câu
"lượng hoá 4-bit làm mất bao nhiêu điểm" - lượt 4-bit vốn bị ép bởi 6 GB VRAM của máy cá nhân chứ không
phải một lựa chọn phương pháp. Lưu ý khi đọc số của nhóm này: `batch_size` cũng nằm trong mã băm danh
tính (`05_predictions.md` mục 2), nên phải so từng dòng `predictions.csv` với lượt 4-bit tương ứng, đừng
gán hết chênh lệch cho lượng hoá.

Đợt này cũng sửa hai lỗi hạ tầng lộ ra khi dựng lượt chạy 0.6B: trọng số Qwen3-0.6B trên máy cá nhân bị
cắt cụt (838.852.608 byte trong khi header safetensors đòi 1.503.300.328, tức thiếu 44%) và đã tải lại
trọn vẹn, và `scripts/setup/setup_qwen_model.ps1` phải thêm BOM UTF-8 mới parse được bằng `powershell.exe`
(xem `docs/00_workflow/06_conventions.md`).

*Cập nhật 30/09/2026 - gói bàn giao nay gửi TĂNG DẦN (Batch 5b):* vòng bàn giao không còn là "nén cả
cây rồi gửi lại". `scripts/build_package.py` dựng gói `NNN` chỉ chứa file MỚI hoặc ĐÃ ĐỔI, kèm sổ
trong git: `handover/files.csv` (ứng viên hiện tại), `handover/ledger.csv` (đã gửi file nào, băm nào,
ở gói nào), `handover/packages/<NNN>/manifest.csv` (nội dung từng gói, bốn lớp
`new`/`changed`/`kept`/`deleted`; `deleted` là danh sách người nhận phải xoá). Ứng viên suy từ cấu
hình thí nghiệm chứ không chép tay, và gói zip nằm ở `handover/out/` (không vào git). Một luật an
toàn mới: đổi nội dung một file TRONG phiên bản dữ liệu đã gửi thì công cụ DỪNG (mã thoát 3) và chỉ
đường tạo phiên bản dữ liệu mới - vì kết quả người nhận đã chạy không còn so được với lần chạy mới.

*Đã xong trong Batch 5b (30/09/2026):* 12 notebook thí nghiệm đã được dựng lại theo bản mẫu mới (ô
bootstrap mỏng, có khối bảo vệ ngắt phiên, sửa đường dẫn cũ) rồi ghim lại vào commit code mới
`a7ba8fc`; gói `001` là gói GỐC của sổ bàn giao, và gói zip `a7ac72a` cũ cùng thư mục `_ban_giao/` bên
ngoài repo đã bị xoá.

*Cập nhật 01/10/2026 - dữ liệu nay là `v0.2.0`, test nguyên bản:* bản cũ (`...-e0ccc484`, `test.csv`
1.518 dòng) đã được thay bằng `cosmetics-ds0.2.0-pl0.2.0-srccosmetics@0.1.0-e616c1e3`: pipeline
v0.2.0 không sửa `test` (`steps.clean.apply_to`/`steps.normalize.apply_to` = `[train, val]`), nên
`test.csv` bằng ĐÚNG dữ liệu gốc (1.623 dòng, 0 dòng lệch văn bản, 0 ô lệch nhãn) và so được với công
bố; rò rỉ dữ liệu chuyển sang xử lý ở phía tập HỌC (`leakage.keep_priority: [test, val, train]`, còn
0 cặp trùng giữa ba tập). Cả 12 `experiments/**/config.yaml` đã trỏ `data.version: v0.2.0`, 12 notebook
đã ghim lại commit `8df7830`, và 8 bảng số đo + EDA của phiên bản mới đã sinh xong. Gói bàn giao kế
tiếp là **gói 003** (chở dữ liệu v0.2.0 và 12 notebook ghim lại) và phải gửi **TRƯỚC** khi Batch 6 chạy:
notebook đọc config từ đúng commit nó ghim. Mọi số ở mục 2 (1.518 dòng, mã `e0ccc484`) là số của **bản
cũ** - giữ làm mốc lịch sử, không dùng để so với công bố nữa.

Gói **003** đã dựng ngày 01/10/2026: `handover/packages/003` + zip trong `handover/out/`, 48 ứng viên
gồm 6 `new` (dữ liệu đã xử lý của `…-e616c1e3`), 12 `changed` (12 notebook ghim lại), 30 `kept` và
**0 `deleted`** - dữ liệu của bộ `v0.1.0` nằm ở lớp `kept`, tức người nhận GIỮ nguyên trên Drive chứ
không phải xoá (`scripts/build_package.py::declared_dataset_versions`).

*Cập nhật 01/10/2026 - tệp thứ sáu của lượt chạy (`mispredictions_paper.csv`):* mỗi lượt chạy nay ghi
thêm danh sách ô đoán sai theo CƠ SỞ ĐO của công bố (tập con của `mispredictions.csv`, xem
`docs/04_experiments/metrics.md`), và tệp nhẹ của cơ sở `paper` cũng lên DagsHub
(`configs/experiments/tracking.yaml`). Vì tệp chỉ ra đời khi bản code ĐÃ GHIM có phần ghi nó, 12
notebook được **ghim lại** lần nữa vào commit `1dec8a9` (chỉ ô GHIM đổi; `EXP_DIR` và mọi ô khác giữ
nguyên, nên mỗi lượt chạy rơi vào thư mục `<hash8>` mới). Việc ghim lại này hợp lệ theo
`docs/00_workflow/10_template_notebook.md`: cách đo KHÔNG đổi và 12 thí nghiệm đó chưa chạy ở đâu.
Cùng đợt: sửa một lỗi ánh xạ chỉ số review khi lọc hai chiều (`dbe3d7b`) - lỗi nằm im cho tới khi tệp
mới gọi `kept()` trên bộ `paper`, và ở `neutral_policy: as_negative`/`as_positive` nó làm CẢ lượt chạy
chết ở bước ghi kết quả (xem `docs/04_experiments/04_backlog.md` §8.3).

Gói **004** đã dựng ngày 01/10/2026: `handover/packages/004` + zip trong `handover/out/`, 13 file
`changed` (12 notebook ghim lại + `README.md` của gói, nay nói "Sáu file nhẹ"), 35 `kept`, **0 `new`**,
**0 `deleted`**; zip tên `SentimentX-goi-004-1dec8a9-261001.zip`. Gói này **phụ thuộc gói 003**: người
nhận giải nén 003 trước, rồi 004 đè lên. Nhánh `experiment` đã đẩy tới `1dec8a9` - notebook kéo bản
ghim từ GitHub, nên gửi gói trước khi đẩy là notebook chết.

**Việc còn lại của P7, đặt tên là đợt tiếp theo:**

- **Batch 6 - chạy lưới để lấy KẾT QUẢ THẬT:** chạy lần lượt 12 notebook trên Colab, copy **6 tệp nhẹ**
  (`run.log`, `metrics.json`, `metrics.csv`, `run_meta.json`, `mispredictions.csv`,
  `mispredictions_paper.csv`) từ Drive về repo,
  chạy `python scripts/collect_reports.py`, rồi cập nhật số vào `docs/04_experiments/03_training_eval.md`
  §6.3 và đối chiếu với `docs/04_experiments/reference_publication.md`. Đây cũng là **phép kiểm cuối**
  cho đường Colab mà Batch 5b không chạy được ở máy cá nhân (điểm tiêm + câu in giữ nguyên chỉ thay
  được một lượt chạy thật).
- Sau Batch 6, thay cột "thời gian ước tính" bằng số giây thật (xem `docs/04_experiments/04_backlog.md`
  §8.3).

## 3. Task nhỏ (mỗi task một commit)

- [x] T1. Chạy lại pipeline để sinh phiên bản dataset đầu tiên theo cấu trúc mới.
      -> `chore(data): rebuild the dataset under the corrected version id`
      Điều kiện để chạy được trên Colab (đã gặp thật, ghi lại để P7 T5 khỏi vấp lại): dữ liệu GỐC
      KHÔNG nằm trong git (luật 20), nên bản clone sạch không có `data/raw/**/*.csv`. Muốn chạy
      pipeline trên Colab thì phải đưa dữ liệu lên trước (mount Drive, hoặc tải thư mục lên), rồi
      `python run_pipeline.py --name cosmetics --version v0.1.0`. Model `4bit` cần thêm
      `pip install bitsandbytes`. Preflight nay báo đúng việc này ở dòng ĐẦU của danh sách.
- [x] T2. Chạy lại EDA trên raw và trên dataset; sinh report tương ứng.
      -> `feat(data): regenerate eda and pipeline reports`
      Chạy thật (25/09/2026): `run_eda.py --on raw --name cosmetics --version v0.1.0` và
      `run_eda.py --on dataset --hash <hash8>` đều thoát 0, rồi `build_report.py` cho từng đích (ba
      lần) và `--all` sinh ba file HTML.
      Phép so quan trọng: diff của kết quả EDA trên dữ liệu gốc CHỈ có `version_id` (mã cũ -> mã mới)
      và `generated_at` - mọi con số giữ nguyên, tức bộ dữ liệu không đổi khi mã phiên bản đổi.
- [ ] T3. Chạy baseline prompt 0-shot, 1-shot, 5-shot trên tập `test` đúng như công bố.
      -> `feat(experiments): run baseline prompt experiments`
      **Phạm vi đã chốt lại (25/09/2026): NĂM thí nghiệm, không phải ba lượt của một thí nghiệm.**
      Ba mức 0/1/5 ví dụ của công bố là `prompt-cot/exp002`, `exp003`, `exp004`, mỗi mức chấm trên cả
      tập `test` (`n: null`, **1.623** review ở bộ `v0.2.0` đang dùng; bộ cũ `v0.1.0` là 1.518); hai lượt
      LoRA cho encoder là `visobert/lora/exp001` và
      `phobert-base-v2/lora/exp001`. Thí nghiệm `prompt-cot/exp001` (CoT 2 ví dụ, mức nội bộ của
      nhóm) đã được XOÁ theo yêu cầu: nó không phải một mức của công bố, giữ lại chỉ làm loãng bảng so
      sánh. Các thư mục kết quả của giai đoạn kiểm đường chạy (chấm trên `val`, `n` nhỏ) cũng đã được
      xoá khỏi repo vì cùng lý do. Hai công cụ phục vụ việc chạy và kiểm:
      `scripts/run_notebook.py` (chạy notebook trên máy cá nhân, kéo commit ghim vào thư mục tạm nên
      repo không bị đụng) và `scripts/show_prompt.py` (in prompt thật gửi cho model). Muốn tra từng
      mẫu thì đọc cột `prompt gửi model` trong `predictions.csv`
      (`docs/04_experiments/05_predictions.md`).
      *Cập nhật 29/09/2026:* phạm vi nay là **MƯỜI HAI** thí nghiệm (thêm một lượt `prompt-one-turn`, ba
      lượt `qwen3-0.6b/prompt-cot/exp001..003`, và ba lượt đối chứng fp16 `prompt-cot/exp005..007`) -
      xem mục 2 và `docs/00_workflow/07_colab.md` mục 3.
- [ ] T4. Sinh bảng so sánh với cột `reference`; ghi lại kết quả và khoảng cách.
      -> `docs(experiments): record baseline results against reference`
- [ ] T5. Giao notebook cho giảng viên: đẩy dữ liệu, notebook và `.env.colab` lên Drive, gửi hướng dẫn.
      (không tạo commit)
      Gói bàn giao đã dựng lại (lần cuối 29/09/2026, ghim `a7ac72a`): **mười hai** notebook (hai lượt LoRA,
      một lượt prompt một lượt, ba mức ví dụ của công bố trên bản 4B, ba lượt 0.6B, ba lượt đối chứng fp16)
      cộng README của từng thí nghiệm, cây đúng như `docs/00_workflow/07_colab.md` mục 2:

      ```
      .sentimentx_root                      README.md  (hướng dẫn người chạy)
      env/.env.colab  env/.env.colab.example
      notebooks/<model_id>/<method>/expNNN.ipynb          (mười hai notebook)
      experiments/<model_id>/<method>/expNNN/README.md    (mười hai thí nghiệm)
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
- Tập `test` không đổi: `records_sha256` khớp khoá tập đánh giá trong `data/processed/<mã>/eval_lock.json`
  (`sha256` là dấu vết của bản đã công bố: lệch byte mà vân tay dữ liệu khớp chỉ là ghi chú, không phải lỗi).
- Một thí nghiệm chạy trọn vẹn trên Colab của giảng viên, kết quả nằm trên Drive và trên DagsHub.

## 5. Rủi ro / lưu ý

- Nếu giảng viên chỉ có TPU, QLoRA không chạy: giữ Qwen3 ở dạng prompt và huấn luyện encoder.
- Kết quả sinh trên Colab nằm trên Drive; muốn vào git thì phải copy phần nhẹ về.

## 6. Phụ thuộc

P6 xong (đã có report và CI).

---

## 7. Cập nhật 02/10/2026 - sửa 3 lỗi đường LoRA

Hai notebook LoRA hỏng trên Colab ở lượt chạy đầu; nguyên nhân và cách sửa (đã ghim lại ở bước sau):

- **ViSoBERT**: `KeyError: 'every_n_steps'` - `plan()` trả về `training` thiếu khoá chính sách
  checkpoint, còn `log_config` đọc khoá đó. Đã gộp `checkpoints.settings` vào `training`.
- **PhoBERT**: báo "thiếu model VnCoreNLP" DÙ file có trên Drive - `config.py` đóng băng đường dẫn NGAY
  LÚC IMPORT, trước khi ô bootstrap đặt `SENTIMENTX_DATA_ROOT`, nên `vncorenlp` tìm sai chỗ (repo thay
  vì Drive). Đã chuyển hằng đường dẫn sang tính LÚC GỌI, và `vncorenlp.model_dir()` tính tại chỗ.
- **Không ngắt phiên khi lượt chạy encoder lỗi**: `experiment_run.run` bọc `end_session_on_error` nhưng
  với encoder nó thoát sang `encoder_run.run` TRƯỚC khối đó. Đã bọc trong chính `encoder_run.run`.

Kết quả cũ `91f50523` (visobert) và `6aaa0f2f` (phobert) KHÔNG dùng nữa: sau khi ghim lại, mỗi lượt
rơi vào thư mục mới (commit nằm trong mã băm danh tính).
