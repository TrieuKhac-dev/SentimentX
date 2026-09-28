# -*- coding: utf-8 -*-
"""Mã phiên bản dữ liệu và đường dẫn kết quả của một phiên bản.

MÃ PHIÊN BẢN
    <name>-ds<version>-pl<pipeline_version>-src<nguồn>@<phiên bản>-<hash8>

Ví dụ: cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-3f9a1c2d

    ds<version>             phiên bản dataset, lấy từ file cấu hình dataset
    pl<pipeline_version>    phiên bản pipeline dùng để tạo dataset
    src<nguồn>@<phiên bản>  từng nguồn; nhiều nguồn thì nối bằng dấu +
    <hash8>                 8 ký tự đầu của băm: nội dung hai file cấu hình và nội dung mọi
                            file dữ liệu của các nguồn

VÌ SAO BĂM CẢ NỘI DUNG FILE
Cùng đường dẫn nhưng khác nội dung là hai bộ dữ liệu khác nhau, nên phải ra hai mã khác nhau.
Nhờ vậy chạy lại cùng cấu hình và cùng dữ liệu cho ra đúng kết quả cũ, còn đổi cấu hình hoặc đổi
dữ liệu thì kết quả cũ vẫn còn nguyên để so sánh.

CÂY KẾT QUẢ CỦA MỘT PHIÊN BẢN
    data/processed/<mã>/train.csv, val.csv, test.csv, label_map.json, processing_log.json
    data/processed/<mã>/eval_lock.json   khoá tập đánh giá: vân tay TẬP BẢN GHI + vân tay BYTE
    data/processed/<mã>/pipeline/   báo cáo của lần chạy pipeline
    data/raw/<name>/<raw_version>/eda/ hoặc data/processed/<mã>/eda/   kết quả EDA
"""

import hashlib
import json
import re
from pathlib import Path

from src import paths, utils

# Số ký tự hash dùng trong mã phiên bản (đủ để không trùng trên thực tế)
HASH_LENGTH = 8

# Dạng viết tắt của mã phiên bản: đúng `HASH_LENGTH` ký tự hex (xem `find_version`).
VERSION_HASH_PATTERN = re.compile("^[0-9a-f]{{{}}}$".format(HASH_LENGTH))

# Công thức tính `records_sha256` (dấu vân tay của TẬP BẢN GHI). Số này đi vào `eval_lock.json`, nên
# đổi công thức là đổi khoá tập đánh giá: bump số ở đây và ghi vào docs/01_dataset/changelog.md.
RECORDS_LOCK_SCHEMA = 1

# Ký tự ngăn cách khi băm bản ghi: ký tự điều khiển, không thể có trong review nên không nhập nhằng.
RECORD_FIELD_SEPARATOR = "\x1f"
RECORD_LINE_SEPARATOR = "\x1e"

# Tên ba file dữ liệu của một dataset đã xử lý. Dùng khi một nguồn là dataset khác.
DATASET_FILES = ("train.csv", "val.csv", "test.csv")


# ---
# Tính mã phiên bản
# ---


class VersionError(Exception):
    """Lỗi liên quan tới phiên bản dữ liệu (file phiên bản bị sửa, thiếu phiên bản...)."""


def declared_files(dataset_cfg, source):
    """Mọi file dữ liệu mà một nguồn KHAI, kể cả file chưa có trên đĩa.

    Nguồn `raw` chỉ lấy đúng file khai trong `splits` và `full`, không lấy cả thư mục: trong thư mục
    còn `raw_meta.yaml` và kết quả EDA, không phải dữ liệu.
    """
    if source.get("kind") == "dataset":
        names = list(DATASET_FILES)
    else:
        names = list((dataset_cfg.get("splits") or {}).values())
        if dataset_cfg.get("full"):
            names.append(dataset_cfg["full"])
    return [Path(source["dir"]) / str(name) for name in names]


def source_files(dataset_cfg, source):
    """Các file dữ liệu CÓ trên đĩa của một nguồn, theo thứ tự tên.

    Dùng cho việc băm nội dung và cho nhật ký nguồn. Việc THIẾU file là lỗi riêng, do
    `missing_sources()` báo - không lặng lẽ bỏ qua ở đây.
    """
    return [path for path in declared_files(dataset_cfg, source) if path.exists()]


def missing_sources(dataset_cfg):
    """File dữ liệu đã KHAI của các nguồn mà KHÔNG có trên đĩa.

    Vì sao cần phép kiểm này: mã phiên bản băm NỘI DUNG các file nguồn, nên nếu chỗ băm bỏ qua file
    thiếu thì một gốc dữ liệu RỖNG vẫn cho ra một mã trông hợp lệ - mã đó được in ra ở ô cấu hình,
    được dùng làm tên thư mục kết quả, rồi preflight báo "chưa có dataset đã xử lý". Người đọc đi tìm
    lỗi ở phiên bản dữ liệu, trong khi nguyên nhân thật là chưa đưa dữ liệu gốc lên máy.
    """
    missing = []
    for source in dataset_cfg.get("_sources") or []:
        missing.extend(path for path in declared_files(dataset_cfg, source) if not path.exists())
    return missing


def compute_id(dataset_cfg, pipeline_cfg=None):
    """Tính mã phiên bản từ cấu hình và nội dung dữ liệu của các nguồn.

    Không truyền `pipeline_cfg` thì nạp file pipeline ghi ở `pipeline_version` của dataset.

    Thiếu file dữ liệu gốc là LỖI: băm một bộ nguồn rỗng cho ra một mã hợp lệ nhưng vô nghĩa, và mọi
    thứ đi sau đó (tên thư mục kết quả, khoá resume, bảng tổng hợp) đều dựa vào mã ấy.
    """
    missing = missing_sources(dataset_cfg)
    if missing:
        raise VersionError(
            "Thiếu {} file dữ liệu gốc của dataset {!r} trong gốc dữ liệu {} nên KHÔNG tính được mã "
            "phiên bản:\n  - {}\n"
            "Đưa đủ dữ liệu gốc vào thư mục của nguồn rồi chạy lại. Dữ liệu gốc KHÔNG nằm trong git "
            "(luật 20 của docs/00_workflow/02_rules.md), nên bản clone sạch không có chúng.".format(
                len(missing), dataset_cfg.get("name"), paths.data_root(),
                "\n  - ".join(utils.rel(path) for path in missing)))

    if pipeline_cfg is None:
        pipeline_cfg = utils.load_pipeline_config(dataset_cfg.get("pipeline_version"))

    digest = hashlib.sha1()
    digest.update(b"dataset:")
    digest.update(_file_bytes(dataset_cfg.get("_path")))
    digest.update(b"pipeline:")
    digest.update(_file_bytes(_config_path(pipeline_cfg)))
    digest.update(b"sources:")
    for source in dataset_cfg.get("_sources") or []:
        for path in source_files(dataset_cfg, source):
            name = path.relative_to(source["dir"]).as_posix()
            digest.update(name.encode("utf-8"))
            digest.update(utils.digest_bytes(path))

    sources = "+".join(
        "{}@{}".format(source.get("name"), _label(source.get("version")))
        for source in dataset_cfg.get("_sources") or []
    )
    return "{}-ds{}-pl{}-src{}-{}".format(
        dataset_cfg.get("name", "dataset"),
        _label(dataset_cfg.get("version")),
        _label(dataset_cfg.get("pipeline_version")),
        sources or "khong_nguon",
        digest.hexdigest()[:HASH_LENGTH],
    )


def _label(value):
    """Bỏ chữ 'v' ở đầu nhãn phiên bản cho gọn trong mã."""
    text = str(value or "")
    return text[1:] if text.startswith("v") else text


def source_files(dataset_cfg, source):
    """Các file dữ liệu của một nguồn, theo thứ tự tên.

    Nguồn `raw` chỉ lấy đúng file khai trong `splits` và `full`, không lấy cả thư mục: trong
    thư mục còn `raw_meta.yaml` và kết quả EDA, không phải dữ liệu.
    """
    if source.get("kind") == "dataset":
        names = list(DATASET_FILES)
    else:
        names = list((dataset_cfg.get("splits") or {}).values())
        if dataset_cfg.get("full"):
            names.append(dataset_cfg["full"])
    files = []
    for name in names:
        path = Path(source["dir"]) / str(name)
        if path.exists():
            files.append(path)
    return files


def _config_path(value):
    """Chấp nhận cả dict cấu hình (có khoá _path) và đường dẫn trực tiếp."""
    if value is None:
        return None
    if isinstance(value, (str, Path)):
        return Path(value)
    return value.get("_path")


def _file_bytes(path):
    """Nội dung file cấu hình để băm; file thiếu được coi là rỗng.

    Đi qua `utils.digest_bytes` để hai máy khác hệ điều hành ra cùng một mã (xem hàm đó).
    """
    if not path:
        return b""
    path = Path(path)
    return utils.digest_bytes(path) if path.exists() else b""


# ---
# Đường dẫn theo phiên bản
# ---


def processed_dir(version_id):
    """Thư mục dataset của một phiên bản: `data/processed/<mã>/`."""
    if not version_id:
        raise ValueError("Thiếu mã phiên bản dữ liệu.")
    return paths.processed(version_id)


def pipeline_report_dir(version_id):
    """Thư mục báo cáo pipeline, nằm trong thư mục dataset."""
    return processed_dir(version_id) / paths.pattern("pipeline_dir")


def processing_log_path(version_id):
    return processed_dir(version_id) / paths.pattern("processing_log")


def read_processing_log(version_id):
    """Đọc `processing_log.json` của một phiên bản; trả về dict rỗng nếu chưa có."""
    path = processing_log_path(version_id)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle) or {}


def dataset_dirs():
    """Các phiên bản dataset đang có trên đĩa, mới nhất trước theo thời gian sửa."""
    root = paths.data("processed")
    if not root.is_dir():
        return []
    found = [
        path for path in root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]
    return sorted(found, key=lambda path: path.stat().st_mtime, reverse=True)


def latest_dataset(dataset=None):
    """Mã phiên bản dataset mới nhất trên đĩa; lọc theo tên dataset nếu có."""
    for path in dataset_dirs():
        if dataset is None or path.name.startswith(str(dataset) + "-ds"):
            return path.name
    return None


def version_parts(version_id):
    """Tách mã phiên bản thành `(tên dataset, hash8)` để in cho người đọc."""
    text = str(version_id or "")
    return text.split("-ds", 1)[0], text.rsplit("-", 1)[-1]


def known_versions_text():
    """Danh sách phiên bản đã xử lý đang có trên đĩa, để ghép vào thông báo lỗi."""
    known = sorted(directory.name for directory in dataset_dirs())
    return "\n  - ".join(known) if known else "(chưa có phiên bản nào trong data/processed/)"


def find_version(hash_or_id):
    """Tìm mã phiên bản dữ liệu ĐÃ XỬ LÝ từ hash8 hoặc mã đầy đủ.

    VÌ SAO BẮT BUỘC PHẢI GHI RÕ
    Mọi tool chạy sau pipeline đều đo / kiểm / ghi số liệu gắn với MỘT phiên bản dữ liệu. Để tool
    tự chọn "bản mới nhất" là đoán: khi có phiên bản thứ hai, kết quả rơi vào thư mục của một bản
    khác mà nhìn vào vẫn hợp lý. Nên tham số là bắt buộc, và hàm này chỉ nhận đúng hai cách viết:

        e0ccc484                                              8 ký tự hex cuối mã
        cosmetics-ds0.1.0-pl0.1.0-srccosmetics@0.1.0-e0ccc484  mã đầy đủ

    Không khớp gì - hoặc hash8 khớp NHIỀU phiên bản - đều là LỖI kèm danh sách đang có, không đoán.
    """
    text = str(hash_or_id or "").strip()
    if not text:
        raise VersionError(
            "Thiếu `--hash`: phải ghi rõ phiên bản dữ liệu, ví dụ `--hash e0ccc484` hoặc "
            "`--hash <mã đầy đủ>`. Đang có:\n  - {}".format(known_versions_text()))

    known = [directory.name for directory in dataset_dirs()]
    if "-ds" in text:
        if text in known:
            return text
        raise VersionError(
            "Không có phiên bản dữ liệu {!r} trong {}. Đang có:\n  - {}".format(
                text, utils.rel(paths.data("processed")), known_versions_text()))

    if not VERSION_HASH_PATTERN.match(text.lower()):
        raise VersionError(
            "`--hash` phải là {} ký tự hex (ví dụ `e0ccc484`) hoặc mã phiên bản đầy đủ "
            "(chứa `-ds`); đang nhận {!r}. Đang có:\n  - {}".format(
                HASH_LENGTH, text, known_versions_text()))

    matches = [name for name in known if name.lower().endswith(text.lower())]
    if not matches:
        raise VersionError(
            "Không phiên bản dữ liệu nào kết thúc bằng {!r}. Đang có:\n  - {}".format(
                text, known_versions_text()))
    if len(matches) > 1:
        raise VersionError(
            "hash8 {!r} khớp NHIỀU phiên bản nên không đoán được bản nào:\n  - {}".format(
                text, "\n  - ".join(sorted(matches))))
    return matches[0]


def file_sha256(path):
    """sha256 của một file, dùng cho guard bất biến và cho `eval_lock`.

    Băm qua `utils.digest_bytes`, tức file văn bản được chuẩn hoá kiểu xuống dòng trước khi băm. Cần
    như vậy vì `eval_lock.test.sha256` được ghi vào file config dataset ở một máy rồi ĐEM SO ở máy
    khác (máy cá nhân Windows ghi, Colab Linux đối chiếu): băm thẳng byte thì hai máy luôn lệch nhau
    và tập test bị coi là đã bị đổi.
    """
    digest = hashlib.sha256()
    digest.update(utils.digest_bytes(path))
    return digest.hexdigest()


def records_sha256(path, aspects, text_column="text"):
    """Dấu vân tay của TẬP BẢN GHI trong một file dataset - KHÔNG phụ thuộc cách ghi file.

    VÌ SAO CÓ HÀM NÀY
    `file_sha256` băm byte của file, nên đổi cách ghi (trích dẫn, CRLF/LF, BOM, phiên bản pandas) là
    đổi khoá dù dữ liệu y nguyên - đã xảy ra thật 25/09/2026: `test.csv` giữ nguyên 1.518 bản ghi
    nhưng `sha256` đổi từ `e2558137…` thành `9ac701de…`, và pipeline dừng ở bước ghi khoá. Khoá tập
    đánh giá phải neo vào thứ thật sự quyết định quyền so với công bố: **các bản ghi**.

    CÔNG THỨC (bất biến; đổi là đổi khoá, xem `RECORDS_LOCK_SCHEMA`)
        `sha256` của: tiền tố `records:<schema>:` rồi, theo ĐÚNG THỨ TỰ trong file, mỗi bản ghi là
        văn bản (đã chuẩn hoá: bỏ BOM, CRLF/CR -> `\\n`) + mã nhãn của từng aspect nối bằng `\\x1f`;
        giữa hai bản ghi là `\\x1e`.

    Thứ tự aspect lấy theo ĐỐI SỐ `aspects` (nguồn là `label_map.json` của phiên bản), không lấy theo
    thứ tự cột trong file: đổi thứ tự cột là chuyện của cách ghi, không phải của dữ liệu.

    `aspects` truyền vào chứ không tự đọc `label_map.json`: `src/preprocessing/loader.py` đã import
    module này, tự đọc ở đây là tạo vòng import.
    """
    columns = [text_column] + [str(aspect) for aspect in aspects]
    frame = utils.read_csv(path)
    missing = [name for name in columns if name not in frame.columns]
    if missing:
        raise VersionError(
            "{} thiếu cột {} nên KHÔNG tính được dấu vân tay tập bản ghi. Cột đang có: {}.".format(
                utils.rel(path), ", ".join(missing), ", ".join(map(str, frame.columns))))

    digest = hashlib.sha256()
    digest.update("records:{}:".format(RECORDS_LOCK_SCHEMA).encode("utf-8"))
    for index, row in enumerate(frame[columns].itertuples(index=False, name=None)):
        if index:
            digest.update(RECORD_LINE_SEPARATOR.encode("utf-8"))
        digest.update(utils.normalize_text(str(row[0])).encode("utf-8"))
        for value in row[1:]:
            digest.update(RECORD_FIELD_SEPARATOR.encode("utf-8"))
            digest.update(str(value).encode("utf-8"))
    return digest.hexdigest()


def eval_lock_path(version_id):
    """Đường dẫn `data/processed/<mã>/eval_lock.json`: khoá tập đánh giá của một phiên bản."""
    return processing_log_path(version_id).parent / paths.pattern("eval_lock")


def read_eval_lock(version_id):
    """Nội dung `eval_lock.json`: `{tên split: {file, sha256, rows}}`; chưa có thì trả về {}.

    KHOA NÀY CÓ TỪ BẢN ĐẦU TIÊN, không phải từ phiên bản sau: nó được ghi trong cùng lần chạy
    pipeline đã tạo ra `test.csv`, và nằm cạnh dữ liệu (`data/processed/<mã>/`). File cấu hình
    dataset chỉ khai *chính sách* (`eval_lock.enforce`, tên file) và - khi cần - giá trị MONG ĐỢI để
    đối chiếu với một tập test bên ngoài. Nhờ vậy bản v0 cũng có khoá, và không phải chờ phiên bản
    kế tiếp mới biết tập đánh giá là tập nào.

    Khoá theo TÊN SPLIT để sau này khoá thêm split khác cũng được, và để bảng tổng hợp đọc thẳng ra
    được split nào đang được khoá (xem `src/reports.py`).
    """
    path = eval_lock_path(version_id or "")
    if not path.is_file():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle) or {}


def split_lock(version_id, split="test"):
    """Khoá của MỘT split, hoặc {} nếu chưa có."""
    return dict(read_eval_lock(version_id).get(str(split)) or {})


def _lock_conflict(previous, payload, split, version_id):
    """Khoá đã ghi có KHÁC lần này không? Trả về câu giải thích, hoặc `None` nếu không có gì để chặn.

    So theo `records_sha256` khi CẢ HAI bên đều có: đó là tập bản ghi - thứ quyết định quyền so với
    công bố. Khoá ghi TRƯỚC khi trường đó ra đời thì rơi về so `sha256` (bảo thủ như trước): một khoá
    đã phát ra không được im lặng nới lỏng, vì khi đó không còn cách nào phân biệt "dữ liệu đổi" với
    "chỉ cách ghi đổi".
    """
    previous_records = previous.get("records_sha256")
    current_records = payload.get("records_sha256")
    if previous_records and current_records:
        if previous_records == current_records:
            return None
        return (
            "Tập BẢN GHI của khoá tập đánh giá ({}) của {} đã có và KHÁC lần này: đã ghi {} "
            "({} dòng), đo được {} ({} dòng). Tập đánh giá đã thay đổi, nên tạo phiên bản dataset "
            "mới thay vì ghi đè khoá cũ.".format(
                split, version_id, previous_records, previous.get("rows"),
                current_records, payload.get("rows")))
    if previous.get("sha256") != payload.get("sha256"):
        return (
            "Khoá tập đánh giá ({}) của {} đã có và KHÁC lần này: đã ghi {} ({} dòng), đo được {} "
            "({} dòng). Tập đánh giá đã thay đổi, nên tạo phiên bản dataset mới thay vì ghi đè "
            "khoá cũ.".format(
                split, version_id, previous.get("sha256"), previous.get("rows"),
                payload["sha256"], payload.get("rows")))
    return None


def write_eval_lock(version_id, measured):
    """Ghi khoá tập đánh giá cho một phiên bản. Trả về đường dẫn file.

    Ghi lần thứ hai với TẬP BẢN GHI khác là lỗi: cùng một mã phiên bản nghĩa là cùng một bộ dữ liệu,
    mà tập đánh giá đã khác thì kết quả cũ không còn so được. Cách sửa đúng là tạo phiên bản dataset
    mới (raw khác, hoặc pipeline khác), chứ không phải ghi đè khoá.

    Ghi lần thứ hai với tập bản ghi GIỐNG nhưng khác `sha256` thì KHÔNG lỗi: dữ liệu y nguyên, chỉ
    cách ghi file đổi - khoá được cập nhật lại dấu vân tay byte, và `export` in một dòng ghi chú.

    Khoá cũ CHƯA có `records_sha256` (ghi trước khi trường này ra đời, ví dụ `…-e0ccc484`): lần chạy
    đầu tiên so `sha256` như cũ, khớp thì BỔ SUNG trường mới - không đổi giá trị nào đã ghi.
    """
    path = eval_lock_path(version_id)
    payload = dict(measured or {})
    payload["sha256"] = payload.get("sha256") or ""
    payload["records_sha256"] = payload.get("records_sha256") or ""
    payload["schema"] = payload.get("schema") or RECORDS_LOCK_SCHEMA
    split = Path(str(payload.get("file") or "test.csv")).stem
    previous = split_lock(version_id, split)
    if previous:
        conflict = _lock_conflict(previous, payload, split, version_id)
        if conflict:
            raise VersionError(conflict)
        if (previous.get("sha256") == payload["sha256"]
                and previous.get("records_sha256") == payload["records_sha256"]
                and previous.get("rows") == payload.get("rows")):
            return path
    stored = read_eval_lock(version_id)
    stored[split] = payload
    return Path(utils.write_json(stored, path))


def guard_versions(dataset_cfg=None, pipeline_cfg=None):
    """Chặn việc sửa file phiên bản đã dùng.

    Mọi `processing_log.json` đã ghi đều giữ sha256 của hai file cấu hình tại thời điểm chạy.
    Nếu file trên đĩa hiện khác giá trị đó thì file đã bị sửa SAU khi dùng, và kết quả cũ
    không còn dựng lại được từ chính file đó nữa. Đây là lỗi im lặng nguy hiểm nhất của cách
    đánh phiên bản theo nội dung, nên phải chặn chứ không chỉ cảnh báo.
    """
    watched = []
    for kind, cfg in (("dataset", dataset_cfg), ("pipeline", pipeline_cfg)):
        path = (cfg or {}).get("_path")
        if path:
            watched.append((kind, Path(path)))
    if not watched:
        return []

    problems = []
    for directory in dataset_dirs():
        log = read_processing_log(directory.name)
        if not log:
            continue
        for kind, path in watched:
            stored_block = log.get(kind) or {}
            stored = stored_block.get("config_sha256")
            # Chỉ so với log của ĐÚNG file đó, không so với file khác cùng loại.
            if not stored or stored_block.get("config") != utils.rel(path):
                continue
            current = file_sha256(path)
            if current != stored:
                problems.append(
                    "{}: {} đã bị sửa sau khi dùng (sha256 hiện tại {}, lúc chạy {}).".format(
                        directory.name, utils.rel(path), current[:8], stored[:8]))

    if problems:
        raise VersionError(
            "File phiên bản đã dùng thì không được sửa:\n  - {}\n"
            "Hãy tạo file phiên bản mới (copy rồi sửa, và đổi cả tên file), rồi chạy lại: "
            "kết quả cũ phải tra được từ đúng file đã tạo ra nó. Nếu lần chạy trước chỉ là chạy "
            "thử thì xoá thư mục kết quả cũ của mã đó rồi chạy lại.".format(
                "\n  - ".join(problems))
        )
    return problems



