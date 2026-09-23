# -*- coding: utf-8 -*-
"""Đo tokenizer THẬT của từng model trên dữ liệu đã xử lý (pha 3).

VÌ SAO PHẢI ĐO Ở ĐÂY, KHÔNG PHẢI Ở EDA
--------------------------------------
EDA đếm TỪ (`utils.tokenize`) để khảo sát dữ liệu, còn model đọc SUBWORD của tokenizer
riêng. Cùng một review có thể thành 20 token với model này và 60 token với model khác,
và con số quyết định là bao nhiêu review vượt `max_length` (tức bị cắt mất phần đuôi).
Chỉ tokenizer của chính model mới đo đúng được điều đó, nên phép đo nằm ở pha 3 — EDA
không được phụ thuộc vào một model cụ thể.

Chỉ cần thư viện `transformers` (KHÔNG cần torch), nên đo được trước khi huấn luyện.
Model nào chưa đo được (ví dụ PhoBERT thiếu Java để chạy bộ tách từ chính chủ) sẽ được
BỎ QUA kèm lí do rõ ràng, không ghi số liệu sai.

MỖI DÒNG SỐ LIỆU GHI RÕ CÁI GÌ ĐÃ SINH RA NÓ
--------------------------------------------
Bốn cột `tokenizer`, `segmenter`, `vocab`, `max_length` là phần TRUY VẾT. Cùng một
review, đổi bộ tách từ hoặc đổi prompt là số token đổi, nên một bảng chỉ có model/split
là không đủ để so sánh về sau. Riêng Qwen còn phụ thuộc prompt nào — tên prompt nằm
trong `info()` và trong tên file CSV khi chạy với `--prompt`/`--segmenter`.

Bộ ví dụ few-shot là biến thí nghiệm THỨ HAI của Qwen và cũng phải truy vết được: cùng
một prompt đi với 0/1/2 ví dụ cho ra ba số liệu khác nhau mà `prompt_sha` lại giống nhau,
nên `info()` của Qwen trả thêm `examples_sha` (mã của file ví dụ, xem
`src/prompts.examples_info`) và tên file CSV có thêm `ex-<sha4>` khi prompt dùng ví dụ.
"""

import inspect

from src import config, prompts, utils, versioning
from src.preprocessing import loader, phobert, qwen, segmenters, visobert

def _word_count(texts, **kwargs):
    """Đếm "từ" cho model KHÔNG có bước tách từ riêng (ViSoBERT, Qwen).

    Dùng utils.tokenize — cùng định nghĩa "từ" mà EDA dùng — để chỉ số "subword / từ"
    của các model so sánh được với nhau. Nhận thêm `**kwargs` (ví dụ `segmenter`) rồi bỏ
    qua, vì model này không tách từ.
    """
    return sum(len(utils.tokenize(text)) for text in texts)


# Tokenizer thật của từng model. Ngưỡng cắt KHÔNG ghi số ở đây mà trỏ tới `limit()` của
# module model, và `limit()` đọc theo thứ tự: configs/models/<model>.yaml > hằng số
# MAX_LENGTH. `--max-length` khi chạy đứng trên cả hai (xem `effective_limit`). Nhờ vậy
# con số dùng để ĐO và con số dùng để CẮT lúc huấn luyện (`build_inputs`) luôn là một.
MODELS = (
    {
        "key": "phobert",
        "model_name": phobert.MODEL_NAME,
        "limit": phobert.limit,
        "default_max_length": phobert.MAX_LENGTH,
        "encode": phobert.encode,
        "words": phobert.words,
        "tokenizer": phobert.tokenizer,
        "info": phobert.info,
    },
    {
        "key": "visobert",
        "model_name": visobert.MODEL_NAME,
        "limit": visobert.limit,
        "default_max_length": visobert.MAX_LENGTH,
        "encode": visobert.encode,
        "words": _word_count,
        "tokenizer": visobert.tokenizer,
        "info": visobert.info,
    },
    {
        "key": "qwen",
        "model_name": qwen.MODEL_NAME,
        "limit": qwen.limit,
        "default_max_length": qwen.MAX_LENGTH,
        "encode": qwen.encode,
        "words": _word_count,
        "tokenizer": qwen.tokenizer,
        "info": qwen.info,
    },
)


def effective_limit(spec, overrides=None):
    """Ngưỡng cắt ĐANG DÙNG cho một model: (giá trị, nguồn hiển thị được).

    Thứ tự áp dụng, trên xuống:

        1. `--max-length` khi chạy            -> thử nhanh, không phải sửa file
        2. `max_length` trong configs/models/<model>.yaml -> cấu hình thí nghiệm
        3. hằng số MAX_LENGTH trong module model          -> giá trị mặc định

    Cả ba đường đều đi qua ĐÂY, nên con số dùng để đo (`token_stats`) và con số dùng để
    cắt lúc huấn luyện/chạy model (`build_inputs`) không thể lệch nhau. Nguồn được giữ
    lại để IN RA và GHI VÀO số liệu: một ngưỡng cắt không rõ từ đâu ra thì đọc bảng số
    liệu xong vẫn không biết nó thuộc thí nghiệm nào.
    """
    override = (overrides or {}).get(spec["key"])
    if override:
        return int(override), "--max-length khi chạy", True
    value, source = spec["limit"]()
    return int(value), source, False


def limits(overrides=None):
    """Danh sách (model, ngưỡng cắt, nguồn, KHÁC mặc định?, TỪ DÒNG LỆNH?) cho mọi model.

    Hai cờ cuối phục vụ hai việc khác nhau:

    - "khác mặc định": ngưỡng đang dùng không bằng hằng số trong module model → in ra để
      người đọc biết con số này không phải mặc định của code.
    - "từ dòng lệnh": ngưỡng đến từ `--max-length`. CHỈ cờ dòng lệnh mới làm tên file kết
      quả có thêm `maxlen-...` (xem run_token_stats.build_tag), vì cờ dòng lệnh nghĩa là
      "chạy khác đi MỘT LẦN", còn sửa `configs/models/<model>.yaml` là CẤU HÌNH CỦA DỰ ÁN
      nên vẫn ghi vào file mặc định — nếu không, chỉ đổi một dòng YAML là tên file mặc
      định biến mất, khó tra cứu.
    """
    result = []
    for spec in MODELS:
        value, source, from_cli = effective_limit(spec, overrides)
        differs = int(value) != int(spec["default_max_length"])
        result.append((spec["key"], value, source, differs, from_cli))
    return result

SPLITS = ("train", "val", "test")

# Cột của bảng kết quả (cũng là cột file CSV)
COLUMNS = [
    "model", "split",
    "tokenizer", "segmenter", "vocab", "max_length",
    "số review", "token/review TB", "p50", "p95", "p99", "max",
    "% review > max_length", "% token <unk>", "subword / từ",
]

# Số cột đầu là phần TRUY VẾT (model + cái gì sinh ra số liệu), phần còn lại là số đo
TRACE_COLUMNS = ("tokenizer", "segmenter", "vocab")
# 6 cột đầu = model, split, 3 cột truy vết ở trên, và max_length; phần còn lại là số đo
METRIC_COLUMNS = tuple(COLUMNS[6:])

# Giá trị hiển thị khi một chỉ số KHÔNG TÍNH ĐƯỢC. Ví dụ tokenizer của Qwen khai báo
# `unk_token = null`, tức model không có token <unk> nào; in "0.00%" ở đây là nói dối
# kiểu khác (0% ngụ ý "có đo và bằng 0"), nên ghi rõ là không áp dụng.
NOT_APPLICABLE = "—"




def _matching_kwargs(func, context, extra=None):
    """Lọc `context` để lấy ĐÚNG những tham số mà `func` thật sự nhận.

    Mỗi model có bộ tham số khác nhau (PhoBERT cần `segmenter`, Qwen cần `prompt_name`,
    ViSoBERT không cần gì), còn nơi gọi thì dùng chung một ngữ cảnh. Lọc theo chữ ký hàm
    giữ lời gọi ở một dòng mà vẫn tường minh, và thêm tham số mới cho một model không
    làm hỏng các model khác.
    """
    values = dict(context)
    if extra:
        values.update(extra)
    parameters = inspect.signature(func).parameters
    return {key: value for key, value in values.items() if key in parameters}


def _encode(spec, texts, context):
    """Gọi hàm encode của model và kiểm tra kết quả TRƯỚC KHI tin nó.

    Hai điều kiện tối thiểu, vì cả hai lỗi dưới đây đều cho ra một bảng số liệu nhìn
    rất hợp lí nhưng sai hết:
      1. Phải là list[list[int]], KHÔNG được là tensor đã pad (đo độ dài trên tensor đã
         pad thì mọi dòng đều "dài" bằng nhau).
      2. Không được là trường hợp MỌI dòng đều dài ĐÚNG BẰNG `max_length` — dấu hiệu
         encode đang cắt sẵn dữ liệu.
    """
    rows = spec["encode"](texts, **_matching_kwargs(spec["encode"], context))

    if len(rows) == 0 or not isinstance(rows[0], (list, tuple)):
        raise TypeError(
            "encode() của {} phải trả về list[list[int]] (không pad, không tensor) để "
            "đo được độ dài thật.".format(spec["key"])
        )
    lengths = [len(row) for row in rows]
    limit = spec["max_length"]
    if len(lengths) > 1 and all(length == limit for length in lengths):
        raise ValueError(
            "encode() của {} trả về MỌI dòng đều đúng {} token — gần như chắc chắn hàm "
            "encode đang bật truncation/padding sẵn (không đo được độ dài thật).".format(
                spec["key"], limit)
        )
    return rows


def _meta(spec, context):
    """Thông tin truy vết của model: tokenizer, bộ tách từ, từ vựng, ngưỡng cắt."""
    return dict(spec["info"](**_matching_kwargs(spec["info"], context)))


# Giới hạn vị trí thật của từng model, đọc từ config của model (nhớ lại sau lần đầu).
_POSITION_LIMITS = None

# `tokenizer.model_max_length` của vài tokenizer trả về một số sentinel khổng lồ
# (1e30) với nghĩa "tokenizer này không khai báo giới hạn". Số lớn hơn ngưỡng này
# KHÔNG phải giới hạn thật, phải bỏ qua.
_SENTINEL_LIMIT = 10 ** 12


def position_limits():
    """Giới hạn vị trí (max_position_embeddings) của từng model, tra theo `model_name`.

    PHẢI đọc từ config của model vì `tokenizer.model_max_length` không đáng tin: với
    PhoBERT và ViSoBERT (tokenizer chậm của dòng RoBERTa/XLM-R), transformers trả về số
    sentinel 1e30, tức "không khai báo giới hạn" — chỉ dựa vào đó thì phép kiểm
    `_check_max_length` bên dưới KHÔNG kiểm được gì cho 2 model này.

    Chỉ tải `config.json` (vài KB, đã có trong cache), KHÔNG tải trọng số.
    """
    global _POSITION_LIMITS
    if _POSITION_LIMITS is None:
        limits = {}
        try:
            from transformers import AutoConfig
        except ImportError:  # pragma: no cover - phụ thuộc môi trường
            AutoConfig = None
        for spec in MODELS:
            limits[spec["key"]] = None
            if AutoConfig is None:
                continue
            try:
                config = AutoConfig.from_pretrained(spec["model_name"])
                value = getattr(config, "max_position_embeddings", None)
                limits[spec["key"]] = int(value) if value else None
            except Exception:  # noqa: BLE001
                # Không đọc được config (mạng, cache thiếu, config đổi khoá) thì bỏ qua:
                # mất một phép kiểm còn hơn làm hỏng cả phép đo.
                limits[spec["key"]] = None
        _POSITION_LIMITS = limits
    return _POSITION_LIMITS


def _check_max_length(spec, tokenizer):
    """Kiểm tra ngưỡng cắt của dự án có vượt giới hạn THẬT của model hay không.

    Thứ tự lấy giới hạn: `tokenizer.model_max_length` nếu là số cụ thể (Qwen khai báo
    1.010.000), nếu không thì `max_position_embeddings` trong config của model
    (PhoBERT 258, ViSoBERT 514). Nếu vượt, phần đuôi bị model cắt hoặc sai vị trí mà
    bảng số liệu vẫn báo "0% bị cắt" — đúng loại lỗi im lặng cần chặn.
    """
    supplied = getattr(tokenizer, "model_max_length", None)
    concrete = isinstance(supplied, int) and 0 < supplied < _SENTINEL_LIMIT
    limit = supplied if concrete else position_limits().get(spec["key"])
    if limit and spec["max_length"] > limit:
        raise ValueError(
            "MAX_LENGTH của {} ({}) lớn hơn giới hạn của model ({}). Phần vượt sẽ bị "
            "model cắt hoặc sai vị trí mà bảng số liệu vẫn báo 0% bị cắt — sửa hằng số "
            "MAX_LENGTH trong module model, hoặc rút ngắn prompt.".format(
                spec["key"], spec["max_length"], limit)
        )
    return limit


def measure(spec, texts, context=None):
    """Đo MỘT model trên MỘT dãy văn bản. Trả về (metrics, meta).

    Lỗi thiếu thư viện / thiếu Java / thiếu model để nguyên cho nơi gọi xử lý, không
    nuốt lỗi: bỏ qua một model phải là quyết định có ghi lại lí do.
    """
    context = dict(context or {})
    meta = _meta(spec, context)

    tokenizer = spec["tokenizer"]()
    _check_max_length(spec, tokenizer)

    id_rows = _encode(spec, texts, context)
    lengths = [len(ids) for ids in id_rows]
    stats = utils.length_stats(lengths, "token")

    unk_id = meta.get("unk_id")
    n_tokens = sum(lengths)
    n_rows = len(lengths)
    n_unk = None if unk_id is None else sum(ids.count(unk_id) for ids in id_rows)
    n_words = spec["words"](texts, **_matching_kwargs(spec["words"], context))

    metrics = {
        "số review": n_rows,
        "token/review TB": stats["trung bình"],
        "p50": stats["p50"],
        "p95": stats["p95"],
        "p99": stats["p99"],
        # `max` là con số THẬT SỰ quyết định `max_length` (không phải p99): muốn 0% bị cắt
        # thì ngưỡng phải >= max của MỌI split. Thiếu nó thì mỗi lần chọn ngưỡng lại phải
        # viết script riêng — đã phải làm vậy một lần cho prompt CoT, và chính vì thế mà
        # số liệu đó không được lưu lại cùng bảng.
        "max": stats["lớn nhất"],
        "% review > max_length":
            round(100 * sum(1 for length in lengths
                            if length > spec["max_length"]) / n_rows, 2)
            if n_rows else 0.0,
        "% token <unk>": NOT_APPLICABLE if n_unk is None else (
            round(100 * n_unk / n_tokens, 2) if n_tokens else 0.0),
        "subword / từ": round(n_tokens / n_words, 2) if n_words else 0.0,
    }
    meta["tokens"] = n_tokens
    return metrics, meta


def _reason(exc):
    """Một dòng mô tả lí do bỏ qua một model (đủ để biết phải cài gì)."""
    lines = [line for line in str(exc).strip().splitlines() if line.strip()]
    return "{}: {}".format(type(exc).__name__, lines[0] if lines else "")



def run(dataset=None, version_id=None, prompt_name=None, segmenter=None, max_length=None):
    """Đo mọi model trên cả 3 split.

    Trả về (rows, skipped, context):
        rows    : danh sách dòng theo đúng thứ tự COLUMNS
        skipped : danh sách (model, lí do) cho model không đo được
        context : cấu hình đã dùng (phiên bản dữ liệu, prompt, bộ tách từ, ngưỡng cắt,
                  thông tin từng model) để entrypoint ghi vào mục lục — đo mà không ghi
                  lại cấu hình thì lần sau đọc số liệu không biết nó thuộc về cái gì.

    `prompt_name` / `segmenter`: chỉ truyền khi muốn đo một cấu hình KHÁC mặc định
    (`--prompt`, `--segmenter`). Truyền None nghĩa là "dùng mặc định của chính model",
    nên giá trị được chuyển tiếp xuống model thay vì tự quyết ở đây.

    `max_length`: dict {tên model: số token} để ghi đè NGƯỠNG CẮT cho một lần chạy
    (`--max-length`). Ngưỡng hiệu lực = CLI > configs/models/<model>.yaml > hằng số của
    module model, xem `effective_limit`.
    """
    # Ngưỡng cắt được chốt MỘT LẦN cho cả lần chạy, rồi truyền xuống `measure` qua spec.
    # Nhờ vậy trong cùng một lần chạy, con số đem đi đo luôn đúng bằng con số đã ghi vào
    # cột `max_length` của CSV và vào mục lục.
    specs = []
    for spec in MODELS:
        value, source, _from_cli = effective_limit(spec, max_length)
        specs.append(dict(spec, max_length=value, max_length_source=source))

    frames = {
        name: loader.load_processed(name, version_id=version_id, dataset=dataset)
        for name in SPLITS
    }
    # Bộ khía cạnh và bảng nhãn đọc từ ĐÚNG phiên bản đang đo, không lấy bản mới nhất:
    # prompt của Qwen mô tả bộ khía cạnh, nên dùng nhầm phiên bản là prompt mô tả sai
    # bài toán mà nhìn vào thì vẫn thấy hợp lí.
    label_map = loader.load_label_map(version_id, dataset=dataset)
    prompt_name = prompt_name or qwen.prompt_name()

    measure_context = {
        "dataset": dataset,
        "version_id": version_id,
        "aspects": list(label_map["aspects"]),
        "label_map": label_map,
        "segmenter": segmenter,
        "prompt_name": prompt_name,
    }

    rows, skipped, models = [], [], {}
    for spec in specs:
        for name in SPLITS:
            texts = frames[name][config.TEXT_COLUMN].astype(str).tolist()
            try:
                metrics, meta = measure(spec, texts, measure_context)
            except (ImportError, OSError, segmenters.SegmenterError) as exc:
                # Thiếu thư viện (transformers / bộ tách từ), thiếu Java, thiếu model
                # VnCoreNLP, hoặc không tải được tokenizer: bỏ qua model này kèm lí do,
                # không ghi số liệu sai.
                skipped.append((spec["key"], _reason(exc)))
                break
            models[spec["key"]] = meta
            rows.append(_row(spec, name, metrics, meta))

    return rows, skipped, {
        "prompt": prompt_name,
        "prompt_sha": qwen.load_prompt(prompt_name).sha,
        # Bộ ví dụ few-shot: sha riêng (xem prompts.examples_info) — prompt không dùng
        # {examples} thì None.
        "examples": prompts.examples_info(prompt_name),
        "segmenter": _resolved_segmenter(segmenter),
        "limits": {spec["key"]: {"value": spec["max_length"],
                                 "source": spec["max_length_source"]}
                   for spec in specs},
        "models": models,
    }


def _row(spec, split, metrics, meta):
    """Một dòng của bảng, theo ĐÚNG thứ tự COLUMNS."""
    return ([spec["key"], split]
            + [meta.get(column, NOT_APPLICABLE) for column in TRACE_COLUMNS]
            + [spec["max_length"]]
            + [metrics[column] for column in METRIC_COLUMNS])


def _resolved_segmenter(spec):
    """Tên bộ tách từ thật sự dùng được, hoặc None nếu máy chưa cài được bộ nào."""
    try:
        return segmenters.resolve(spec)[0]
    except segmenters.SegmenterError:
        return None


def file_name(tag=None):
    """Tên file CSV của một lần đo.

    Có `tag` khi chạy với prompt hoặc bộ tách từ KHÁC mặc định: mỗi cấu hình một file
    riêng để hai thí nghiệm không ghi đè lên nhau. Không có tag thì giữ tên cũ
    (`token_stats.csv`), nhờ vậy các bản chạy trước vẫn tra cứu được.
    """
    return "token_stats.csv" if not tag else "token_stats__{}.csv".format(tag)


def write(rows, version_id, tag=None):
    """Ghi bảng số liệu ra CSV theo phiên bản. Trả về đường dẫn file."""
    out_dir = versioning.version_dir(config.MODEL_INPUT_REPORT_DIR, version_id)
    return utils.write_csv(rows, COLUMNS, out_dir / file_name(tag))

