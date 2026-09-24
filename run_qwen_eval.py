# -*- coding: utf-8 -*-
"""Cửa vào DÒNG LỆNH để chạy một thí nghiệm khi không mở notebook.

ĐƯỜNG CHẠY CHÍNH LÀ NOTEBOOK (docs/00_workflow/01_flow.md): mỗi thí nghiệm được giao cho người
nhận dưới dạng notebook, bấm Run all. File này chỉ là CỬA VÀO MỎNG cho lúc muốn chạy nhanh trên
dòng lệnh - đo thử prompt trên vài chục mẫu, hay kiểm model có nạp được không.

VÌ SAO NÓ KHÔNG CHỨA LOGIC
Nếu notebook gọi một script dòng lệnh thì hợp đồng giữa hai bên là TÊN CỜ DÒNG LỆNH: đổi tên cờ
là hỏng notebook đã ghim (ghim rồi thì không được sửa), notebook chỉ nhận lại được mã thoát chứ
không nhận được số liệu, và cả hai bên đều tự đọc config. Ở đây ngược lại: mọi bước nằm trong
`src/experiment_run.py` (`plan` rồi `run`), notebook gọi thẳng hai hàm đó, còn file này chỉ đọc
tham số dòng lệnh rồi gọi đúng hai hàm ấy. Một đường chạy, hai cửa vào.

MỘT LẦN CHẠY GHI VÀO MỘT THƯ MỤC RIÊNG
`<kết quả của thí nghiệm>/<mã phiên bản dữ liệu>/<hậu tố cấu hình>/`, trong đó hậu tố ghi rõ
prompt, split, số mẫu, greedy hay lấy mẫu - nên hai lần chạy khác cấu hình không ghi đè nhau.
Chạy KHÔNG nêu thí nghiệm thì kết quả đi vào `data/reports/model_eval/` và có dòng nhắc rằng nó
không thuộc thí nghiệm nào.


VÌ SAO MẶC ĐỊNH LÀ `val`
`val` là tập để LỰA CHỌN (prompt nào, bao nhiêu ví dụ, ngưỡng nào). Chạy test từ đầu rồi chọn theo
test là tự lừa mình: mọi con số trên test sau đó mất ý nghĩa so sánh. Vì vậy split do config của
thí nghiệm quyết định (`data.roles.eval`), không phải do tham số dòng lệnh.

CÁCH DÙNG
    python run_qwen_eval.py --list-scorers
    python run_qwen_eval.py --experiment qwen3-4b-instruct-2507/prompt-cot/exp001
    python run_qwen_eval.py --prompt absa_cot_v1 --limit 200 --model Qwen/Qwen3-0.6B
"""

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Trên Windows, console mặc định có thể không phải UTF-8 (ví dụ cp1252),
# khiến việc in tiếng Việt bị lỗi. Ép stdout/stderr sang UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src import dataset, experiment_run, experiments, prompts, runtime, tracking, utils
from src.evaluation import scorers
from src.preprocessing import qwen


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Chạy một thí nghiệm Qwen3 bằng chỉ dẫn (prompt/CoT) rồi chấm điểm. "
                    "Đường chạy chính là notebook của thí nghiệm; đây là cửa vào dòng lệnh.")
    parser.add_argument("--experiment", default=None,
                        help="Thí nghiệm dạng <model>/<method>/<expNNN> - dùng config của nó.")
    parser.add_argument("--model-id", dest="model_id", default=None,
                        help="Phần <model> khi không dùng --experiment.")
    parser.add_argument("--method", default=None,
                        help="Phần <method> khi không dùng --experiment.")
    parser.add_argument("--exp-id", dest="exp_id", default=None,
                        help="Phần <expNNN> khi không dùng --experiment.")
    parser.add_argument("--dataset", default=None,
                        help="Tên dataset (mặc định: dataset khai trong config).")
    parser.add_argument("--version", default=None,
                        help="Mã phiên bản dữ liệu đã xử lý (mặc định: bản mới nhất).")
    parser.add_argument("--split", default=None, choices=["val", "test", "train"],
                        help="Ghi đè split để chấm (mặc định: `data.roles.eval` của thí nghiệm).")
    parser.add_argument("--prompt", default=None,
                        help="Tên prompt trong thư viện dùng chung, hoặc đường dẫn tới file "
                             "prompt cạnh notebook. Mặc định: khoá `prompt` của thí nghiệm.")
    parser.add_argument("--examples", default=None,
                        help="Ghi đè file ví dụ few-shot (tên trong thư viện, hoặc đường dẫn).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Chỉ chạy N mẫu của tập con ngẫu nhiên (tái lập theo --seed).")
    parser.add_argument("--model", default=None,
                        help="Ghi đè model HF (dùng để chạy thử với model nhỏ đã có sẵn).")
    parser.add_argument("--quant", default="auto", choices=["auto", "4bit", "8bit", "none"],
                        help="Cách nạp model. Mặc định 'auto' (4-bit khi có bitsandbytes).")
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=4,
                        help="Số review mỗi lượt sinh. Mặc định 4 (vừa VRAM 6 GB).")
    parser.add_argument("--max-new-tokens", dest="max_new_tokens", type=int, default=None,
                        help="Trần số token sinh mỗi review (mặc định: 400).")
    parser.add_argument("--max-length", dest="max_length", type=int, default=None,
                        help="Trần số token đầu vào (mặc định: max_length của Qwen).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed cho tập con và cho việc lấy mẫu. Mặc định 42.")
    parser.add_argument("--sample", action="store_true",
                        help="Lấy mẫu thay vì greedy (ghi đè `evaluation.decoding.mode`).")
    parser.add_argument("--new", action="store_true",
                        help="Chạy lại từ đầu dù đã có kết quả (kết quả cũ được chuyển sang "
                             "thư mục con, không bị xoá).")
    parser.add_argument("--quiet", action="store_true",
                        help="Không in tiến độ từng lượt sinh.")
    parser.add_argument("--list-scorers", dest="list_scorers", action="store_true",
                        help="In các bộ chấm điểm đang có rồi thoát.")
    parser.add_argument("--list-trackers", dest="list_trackers", action="store_true",
                        help="In các trình ghi nhận đang có rồi thoát.")
    return parser.parse_args(argv)


def identity(args):
    """Ba phần định danh thí nghiệm: (model, method, exp_id). Thiếu cả ba thì chạy NGOÀI thí nghiệm.

    Chạy ngoài vẫn hợp lệ (đo thử prompt), nhưng kết quả không thuộc thí nghiệm nào nên đi vào thư
    mục đánh giá dùng chung - và `plan` sẽ nói rõ điều đó.
    """
    if args.experiment:
        parts = [part for part in str(args.experiment).split("/") if part]
        if len(parts) != 3:
            raise ValueError("--experiment phải có dạng <model>/<method>/<expNNN>, ví dụ "
                             "qwen3-4b-instruct-2507/prompt-cot/exp001")
        return parts
    values = [args.model_id, args.method, args.exp_id]
    if any(values) and not all(values):
        raise ValueError("Cần đủ cả ba phần định danh thí nghiệm: --model-id, --method, --exp-id "
                         "(hoặc dùng --experiment).")
    return values


def main(argv=None):
    args = parse_args(argv)

    if args.list_scorers:
        print("Các bộ chấm điểm đang có (khai trong evaluation.scores):")
        for line in scorers.describe():
            print("  " + line)
        return 0
    if args.list_trackers:
        print("Các trình ghi nhận đang có (khai trong tracking.tracker):")
        for line in tracking.describe():
            print("  " + line)
        return 0

    try:
        model_id, method, exp_id = identity(args)
    except ValueError as exc:
        print("LỖI: {}".format(exc))
        return 2

    in_experiment = all([model_id, method, exp_id])
    if not in_experiment and not args.prompt:
        print("LỖI: chưa rõ prompt. Prompt là biến của thí nghiệm, không lấy từ config model. "
              "Nêu --prompt (xem `python run_token_stats.py --list-prompts`) hoặc chỉ định "
              "--experiment <model>/<method>/<expNNN>.")
        return 2

    print("=" * 70)
    print("QWEN3 BẰNG CHỈ DẪN - chạy model rồi chấm điểm (đánh giá model)")
    print("=" * 70)

    try:
        merged = (experiments.load(model_id, method, exp_id) if in_experiment
                  else experiments.load_shared(qwen.CONFIG_NAME))
        # Lập kế hoạch trước, chạy sau: bước này không cần GPU nên thiếu file hay sai tên split
        # đều lộ ra trong vài giây, không phải sau khi đã nạp model.
        plan = experiment_run.plan(
            merged, dataset_name=args.dataset, model_id=model_id, method=method,
            exp_id=exp_id, prompt=args.prompt, examples=args.examples, split=args.split,
            limit=args.limit, version_id=args.version, quant=args.quant, new=args.new,
            seed=args.seed, max_new_tokens=args.max_new_tokens, max_length=args.max_length,
            batch_size=args.batch_size, model=args.model, sample=args.sample or None,
            quiet=args.quiet)
        result = experiment_run.run(plan)
    except (dataset.DatasetError, experiments.ExperimentError, prompts.PromptError,
            scorers.ScorerError, experiment_run.RunError, FileNotFoundError, ValueError) as exc:
        print("LỖI: {}".format(exc))
        return 2

    if result.get("stopped"):
        return 2
    print("\nXong. Kết quả ở {} (chế độ {}).".format(utils.rel(result["out_dir"]),
                                                     result["mode"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

