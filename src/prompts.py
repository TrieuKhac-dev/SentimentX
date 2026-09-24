# -*- coding: utf-8 -*-
"""Kho prompt nằm ở FILE VĂN BẢN: configs/prompts/<tên>.txt.

VÌ SAO PROMPT NẰM Ở FILE, KHÔNG NẰM TRONG CODE
---
Prompt là một BIẾN THỰC NGHIỆM: đổi câu chỉ dẫn có thể đổi kết quả, nên phải đổi
được mà không phải sửa code. Mỗi prompt một file .txt để:
    - đọc / sửa / so sánh (diff) như văn bản, không phải lồng chuỗi trong Python;
    - giữ NGUYÊN VĂN cả dấu ba nháy, xuống dòng, dấu ngoặc nhọn;
    - truy vết được đã dùng prompt nào (tên file + mã sha in vào báo cáo).

Ngoài phần văn bản, file .txt KHÔNG chứa siêu dữ liệu: "thí nghiệm nào dùng prompt nào" do
config của thí nghiệm quyết định (khoá `prompt`, xem docs/05_config/06_experiment.md).

HỢP ĐỒNG CỦA MỘT FILE PROMPT
---
1. Văn bản thuần UTF-8, dùng các "ô nhớ" (placeholder) dạng {tên}:

       {text}        nội dung review - BẮT BUỘC phải có
       {aspects}     danh sách khía cạnh, cách nhau ", "
       {label_guide} bảng mã nhãn, sinh từ label_map.json của đúng phiên bản dữ liệu
       {example}     một object JSON mẫu (sinh tự động theo danh sách khía cạnh)
       {examples}    khối ví dụ few-shot, đọc từ configs/prompts/examples/<tên>.txt

   Cần in dấu ngoặc nhọn thật thì viết {{ và }} (chuẩn của str.format).

   File ví dụ ĐƯỢC PHÉP mở đầu bằng khối CHÚ THÍCH: các dòng bắt đầu bằng "#", dùng để
   ghi NGUỒN GỐC của ví dụ. Khối này bị CẮT trước khi chèn vào prompt, nên (a) model
   không bao giờ nhìn thấy nó, (b) sửa mỗi lời chú thích không làm đổi số token và không
   làm đổi mã `examples_sha`. Ví dụ lấy TỪ DỮ LIỆU chỉ được lấy từ split train (ví dụ nằm
   trong prompt nghĩa là model đã nhìn thấy nó) - kiểm bằng `python run_check_examples.py`.

2. KHÔNG có dòng đánh dấu => cả file là MỘT message của người dùng (prompt một
   lượt - dạng đang dùng của dự án).
3. CÓ dòng đánh dấu => tách thành hội thoại NHIỀU LƯỢT, theo đúng thứ tự trong file:

       [SYSTEM]      chỉ dẫn hệ thống
       [USER]        lượt người dùng
       [ASSISTANT]   lượt của model (dùng cho ví dụ few-shot / prompt CoT)

   Dòng trống quanh mỗi mục được bỏ; mục rỗng bị bỏ qua.
4. Sai ô nhớ, thiếu {text}, hoặc dòng đánh dấu lạ => báo LỖI ngay khi nạp, kèm
   đường dẫn file và gợi ý - không chạy tiếp với một prompt sai.

Thêm prompt mới: tạo `configs/prompts/<tên>.txt` rồi ghi tên đó vào config của thí nghiệm
(khoá `prompt`), hoặc chạy `python run_token_stats.py --prompt <tên>` để đo thử.
"""

import difflib
import hashlib
import re
import string
from pathlib import Path
from functools import lru_cache

from src import config, utils

# Ô nhớ được phép dùng trong file prompt
PLACEHOLDERS = ("text", "aspects", "label_guide", "example", "examples")

# Ô nhớ bắt buộc: thiếu {text} thì prompt không dùng được cho review nào
REQUIRED_PLACEHOLDERS = ("text",)

# Dòng đánh dấu mở một mục của hội thoại, ví dụ "[USER]"
SECTION_NAMES = ("system", "user", "assistant")
_SECTION_RE = re.compile(r"^\[\s*([A-Za-z_]+)\s*\]$")

# Dòng CHÚ THÍCH của dự án ở đầu file ví dụ few-shot (ghi nguồn gốc ví dụ). Những dòng
# này KHÔNG được gửi cho model - xem `_split_examples_note`.
_COMMENT_RE = re.compile(r"^\s*#")
_COMMENT_CLEAN_RE = re.compile(r"^\s*#\s?")

# Dòng mở đầu một ví dụ trong file ví dụ, ví dụ "--- Ví dụ 1 ---"
_EXAMPLE_BLOCK_RE = re.compile(r"^\s*---.*---\s*$")

# Chữ dùng trong bảng mã nhãn. Nhãn của dataset khác không có ở đây thì lấy
# nguyên tên nhãn, nên bảng vẫn đúng mà không phải sửa code.
LABEL_WORDS = {
    "": "không nhắc tới khía cạnh này",
    "positive": "positive (tích cực)",
    "negative": "negative (tiêu cực)",
    "neutral": "neutral (trung tính)",
    "mixed": "mixed (vừa tích cực vừa tiêu cực)",
}

PROMPT_HINT = (
    "Một file prompt cần có ô nhớ {{text}} và có thể dùng thêm: {}.".format(
        ", ".join("{" + name + "}" for name in PLACEHOLDERS))
)


class PromptError(Exception):
    """Lỗi file prompt: thiếu file, sai ô nhớ, sai dòng đánh dấu, thiếu giá trị."""


# ---
# Danh sách và đường dẫn
# ---


def available():
    """Tên các prompt đã có file trong configs/prompts/."""
    directory = config.PROMPT_DIR
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.txt"))


def default_name():
    """Prompt mặc định khi chưa cấu hình gì: prompt đầu tiên theo thứ tự chữ cái."""
    names = available()
    if not names:
        raise PromptError(
            "Chưa có file prompt nào trong {}. Tạo một file configs/prompts/"
            "<tên>.txt trước. {}".format(config.PROMPT_DIR, PROMPT_HINT)
        )
    return names[0]


def prompt_path(name):
    """Đường dẫn file prompt của một tên prompt."""
    return config.PROMPT_DIR / "{}.txt".format(name)


def examples_path(name):
    """Đường dẫn file ví dụ few-shot của một prompt (tuỳ chọn, có thể không có)."""
    return config.PROMPT_DIR / "examples" / "{}.txt".format(name)


def resolve(value, base_dir=None, examples=False):
    """Đổi giá trị khai trong config thành (TÊN, ĐƯỜNG DẪN) của file prompt hoặc file ví dụ.

    Tên TRẦN - không có dấu `/` và không có `.txt` - là tên trong thư viện dùng chung
    (`configs/prompts/`). Còn lại là ĐƯỜNG DẪN: tính từ thư mục thí nghiệm trước, rồi tới gốc
    repo, đúng như docs/05_config/06_experiment.md quy định.

    Có hai dạng để một thí nghiệm dùng prompt: prompt riêng nằm cạnh notebook (`prompt.txt`) khi
    nó chỉ dùng cho thí nghiệm đó, hoặc prompt trong thư viện chung khi nhiều thí nghiệm dùng
    chung. Cả hai đi qua cùng một hàm này, nên không có hai cách nạp khác nhau.
    """
    text = str(value or "").strip()
    if not text:
        raise PromptError(
            "Thiếu giá trị khai cho {}của prompt: nêu tên trong thư viện dùng chung, hoặc đường "
            "dẫn tới file. Prompt cần ô nhớ {{examples}} thì phải khai khoá `examples` trong "
            "config của thí nghiệm (xem docs/05_config/06_experiment.md).".format(
                "FILE VÍ DỤ few-shot" if examples else "prompt"))
    bare = "/" not in text and "\\" not in text and not text.endswith(".txt")
    if bare:
        return text, (examples_path(text) if examples else prompt_path(text))
    path = Path(text)
    if not path.is_absolute():
        candidate = (Path(base_dir) / text) if base_dir else None
        path = candidate if candidate is not None and candidate.exists() else \
            (config.ROOT_DIR / text)
    return path.stem, path



def suggest(name):
    """Câu gợi ý tên prompt gần đúng khi người dùng gõ sai tên."""
    similar = difflib.get_close_matches(str(name), available(), n=3, cutoff=0.6)
    if not similar:
        return ""
    return "Có phải bạn muốn: {}?".format(" hoặc ".join(similar))


def _display(path):
    """Đường dẫn tương đối so với gốc dự án, cho dễ đọc trong thông báo lỗi."""
    try:
        return path.relative_to(config.ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


# ---
# Nạp và kiểm tra một file prompt
# ---


def _read_text(path):
    """Đọc file prompt: bỏ BOM, đưa về LF, bỏ ĐÚNG một xuống dòng ở cuối file.

    Hai bước chuẩn hoá cuối là bắt buộc để prompt nằm ở file cho ra CHUỖI Y HỆT
    prompt cũ nằm trong code: trên Windows file dễ bị lưu bằng CRLF và dễ có thêm
    một xuống dòng ở cuối - cả hai đều làm đổi số token đo được.
    """
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    text = text.lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.endswith("\n"):
        text = text[:-1]
    return text


def _placeholders(text, where):
    """Danh sách ô nhớ trong prompt, theo thứ tự xuất hiện. Báo lỗi nếu sai cú pháp."""
    found = []
    try:
        for _literal, field, _spec, _conv in string.Formatter().parse(text):
            if field is None:
                continue
            name = field.split(".")[0].split("[")[0]
            if not name:
                raise PromptError(
                    "{}: có ô nhớ không có tên ({{}} hoặc {{0}}) - phải ghi rõ "
                    "tên, ví dụ {{text}}. {}".format(where, PROMPT_HINT)
                )
            if name not in found:
                found.append(name)
    except PromptError:
        raise
    except ValueError as exc:
        raise PromptError(
            "{}: sai cú pháp ô nhớ ({}). Dấu ngoặc nhọn thật phải viết là "
            "{{{{ và }}}}. {}".format(where, exc, PROMPT_HINT)
        ) from exc
    return found


def _split_sections(text, where):
    """Tách prompt nhiều lượt thành [(tên mục, nội dung), ...].

    Trả về None khi file KHÔNG có dòng đánh dấu nào (prompt một lượt).
    """
    sections = []
    current = None
    buffer = []

    for line in text.split("\n"):
        match = _SECTION_RE.match(line.strip())
        if not match:
            buffer.append(line)
            continue
        name = match.group(1).lower()
        if name not in SECTION_NAMES:
            raise PromptError(
                "{}: dòng đánh dấu '[{}]' không hợp lệ. Chỉ dùng: {}. (Muốn in "
                "dấu ngoặc vuông bình thường thì đừng để nó đứng một mình trên "
                "một dòng.)".format(
                    where, match.group(1),
                    ", ".join("[{}]".format(item.upper()) for item in SECTION_NAMES))
            )
        if current is None and "".join(buffer).strip():
            raise PromptError(
                "{}: có nội dung nằm TRƯỚC dòng đánh dấu '[SYSTEM]' đầu tiên - "
                "nội dung không thuộc mục nào như vậy là mập mờ, hãy đưa nó vào "
                "một mục hoặc bỏ hết dòng đánh dấu để dùng prompt một "
                "lượt.".format(where)
            )
        if current is not None:
            sections.append((current, "\n".join(buffer).strip("\n")))
        current, buffer = name, []

    if current is None:
        return None
    sections.append((current, "\n".join(buffer).strip("\n")))
    return [(name, content) for name, content in sections if content.strip()]


class Prompt:
    """Một prompt đã nạp và đã kiểm tra."""

    def __init__(self, name, path, text, examples=None):
        self.name = name
        self.path = path
        self.text = text
        # Tên (hoặc đường dẫn) file VÍ DỤ few-shot đi cùng prompt này. Prompt nằm trong thư mục
        # thí nghiệm thì file ví dụ cũng ở đó, nên phải mang theo giá trị đã khai trong config
        # chứ không suy ra từ tên prompt (suy ra là nguồn sự thật thứ hai, lệch lúc nào không biết).
        # None nghĩa là CHƯA khai: prompt cần {examples} thì lỗi ngay, prompt không cần thì bỏ qua.
        self.examples_value = str(examples) if examples is not None else None
        self.sha = hashlib.sha1(utils.normalize_text(text).encode("utf-8")).hexdigest()[:8]
        self.where = _display(path)
        self.placeholders = _placeholders(text, self.where)
        self.sections = _split_sections(text, self.where)

        if not text.strip():
            raise PromptError("{}: file prompt rỗng.".format(self.where))

        missing = [item for item in REQUIRED_PLACEHOLDERS
                   if item not in self.placeholders]
        if missing:
            raise PromptError(
                "{}: thiếu ô nhớ bắt buộc {{{}}}. {}".format(
                    self.where, "}, {".join(missing), PROMPT_HINT)
            )

        unknown = [item for item in self.placeholders if item not in PLACEHOLDERS]
        if unknown:
            hint = difflib.get_close_matches(unknown[0], PLACEHOLDERS, n=1, cutoff=0.5)
            raise PromptError(
                "{}: ô nhớ {{{}}} không hợp lệ.{} Ô nhớ được phép dùng: {}.".format(
                    self.where, unknown[0],
                    " Có phải bạn muốn {{{}}}?".format(hint[0]) if hint else "",
                    ", ".join("{" + item + "}" for item in PLACEHOLDERS))
            )

    # -- dùng prompt ----------------------------------------------------

    @property
    def multiline(self):
        """True nếu prompt có dòng đánh dấu (hội thoại nhiều lượt)."""
        return self.sections is not None

    def render(self, values):
        """Điền giá trị vào prompt, trả về MỘT chuỗi."""
        missing = [item for item in self.placeholders if item not in values]
        if missing:
            raise PromptError(
                "{}: thiếu giá trị cho ô nhớ: {}. Nơi gọi prompt phải truyền đủ "
                "giá trị.".format(
                    self.where, ", ".join("{" + item + "}" for item in missing))
            )
        return self._fill(self.text, values)

    def transcript(self, values):
        """Bản ĐỌC ĐƯỢC của prompt đã điền giá trị (để xem/in, không phải để gửi model).

        Prompt một lượt: trả về đúng chuỗi sẽ gửi. Prompt nhiều lượt: mỗi mục thành một
        khối có nhãn vai, KHÔNG in các dòng đánh dấu `[SYSTEM]`/`[USER]` - đó là cú pháp
        của FILE, model không bao giờ thấy chúng, nên bản đọc được cũng không nên in ra
        (in ra sẽ khiến người đọc tưởng model nhận cả dòng `[USER]`).
        """
        if not self.multiline:
            return self.render(values)
        return "\n\n".join(
            "### {}\n{}".format(name.upper(), self._fill(section, values))
            for name, section in self.sections
        )

    def messages(self, values):
        """Hội thoại đã điền giá trị: [{"role": ..., "content": ...}, ...].

        Prompt một lượt trả về đúng MỘT message của người dùng - đây là dạng mọi
        model của dự án đang dùng; prompt nhiều lượt (có dòng đánh dấu) trả về
        đủ các lượt theo thứ tự trong file.
        """
        if not self.multiline:
            return [{"role": "user", "content": self.render(values)}]
        return [
            {"role": name, "content": self._fill(section, values)}
            for name, section in self.sections
        ]

    def _fill(self, template, values):
        """Điền giá trị vào một đoạn văn bản (cả prompt hoặc một mục hội thoại)."""
        try:
            return template.format(**values)
        except KeyError as exc:
            raise PromptError(
                "{}: thiếu giá trị cho ô nhớ {}.".format(self.where, exc)
            ) from exc
        except (IndexError, ValueError, AttributeError) as exc:
            raise PromptError(
                "{}: không điền được giá trị vào prompt ({}).".format(self.where, exc)
            ) from exc

    def describe(self):
        """Một dòng mô tả prompt, để in ra console (dùng cho --list-prompts)."""
        info = (examples_info(self.examples_value) if self.examples_value
                and "examples" in self.placeholders else None)
        if info is None:
            shot = "-"
        elif info["missing"]:
            shot = "THIẾU FILE ví dụ"
        else:
            shot = "{} ví dụ (sha {})".format(info["examples"], info["sha"])
        return {
            "name": self.name,
            "file": self.where,
            "sha": self.sha,
            "kiểu": "nhiều lượt ({})".format(
                " -> ".join(name.upper() for name, _ in self.sections))
            if self.multiline else "một lượt",
            "ô nhớ": ", ".join("{" + item + "}" for item in self.placeholders),
            "số ví dụ": shot,
        }


@lru_cache(maxsize=None)
def load(value, base_dir=None, examples=None):
    """Nạp + kiểm tra một prompt, có nhớ kết quả (prompt không đổi trong một lần chạy).

    `value` là TÊN trong thư viện dùng chung, hoặc ĐƯỜNG DẪN tới file prompt của thí nghiệm
    (xem `resolve`). `examples` là giá trị khai ở khoá `examples` của thí nghiệm; để trống thì
    lấy cùng tên với prompt, đúng như trước.
    """
    name, path = resolve(value, base_dir)
    if not path.exists():
        if "/" in str(value) or "\\" in str(value):
            raise PromptError(
                "Không thấy file prompt {} (khai trong config của thí nghiệm). Đường dẫn tính từ "
                "thư mục thí nghiệm trước, rồi tới gốc repo.".format(_display(path)))
        hint = suggest(name)
        raise PromptError(
            "Không tìm thấy prompt '{}' tại {}. Các prompt hiện có: {}. {}{}".format(
                name, _display(path), ", ".join(available()) or "(trống)",
                hint + " " if hint else "", PROMPT_HINT)
        )
    # File ví dụ mặc định chỉ suy ra được khi prompt gọi bằng TÊN (cùng tên trong thư viện dùng
    # chung). Prompt khai bằng ĐƯỜNG DẪN thì KHÔNG suy ra: lấy file prompt làm file ví dụ là lỗi
    # im lặng đúng loại nguy hiểm nhất - model nhận cả file prompt ở chỗ đáng lẽ là mấy ví dụ mẫu,
    # và kết quả vẫn ra số bình thường. Không khai `examples` thì báo lỗi rõ ràng lúc nạp.
    if examples is None:
        bare = ("/" not in str(value) and "\\" not in str(value)
                and not str(value).endswith(".txt"))
        examples = value if bare else None
    return Prompt(name, path, _read_text(path), examples=examples)


def render(name, values):
    """Tiện dụng: nạp prompt theo tên rồi điền giá trị."""
    return load(name).render(values)


# ---
# Giá trị cho các ô nhớ dùng chung
# ---


def label_guide(label_map=None):
    """Bảng mã nhãn dạng văn bản, ví dụ "  0 = không nhắc tới khía cạnh".

    Sinh từ `label_map.json` của ĐÚNG phiên bản dữ liệu đang xử lý (khoá
    `label_to_id`), nên dataset đổi bộ nhãn thì prompt đổi theo và không phải
    sửa code. Chữ hiển thị lấy ở LABEL_WORDS; nhãn lạ thì giữ nguyên tên nhãn.
    """
    label_to_id = (label_map or {}).get("label_to_id") or config.LABEL_TO_ID
    ordered = sorted(label_to_id.items(), key=lambda item: int(item[1]))
    return "\n".join(
        "  {} = {}".format(code, LABEL_WORDS.get(label, label or "(không nhãn)"))
        for label, code in ordered
    )


def _split_examples_note(text):
    """Tách file ví dụ thành (PHẦN CHÚ THÍCH, PHẦN HIỆU LỰC).

    Quy tắc: chú thích là các dòng bắt đầu bằng "#" nằm LIỀN NHAU ở đầu file (dòng trống
    xen giữa được coi là thuộc khối chú thích). Gặp dòng đầu tiên không phải chú thích thì
    phần còn lại là ví dụ - nhờ vậy dấu "#" xuất hiện trong NỘI DUNG ví dụ vẫn được giữ
    nguyên, không bị cắt oan.
    """
    lines = text.split("\n")
    index = 0
    while index < len(lines) and (not lines[index].strip()
                                  or _COMMENT_RE.match(lines[index])):
        index += 1
    note = "\n".join(_COMMENT_CLEAN_RE.sub("", line).rstrip()
                     for line in lines[:index] if _COMMENT_RE.match(line))
    return note.strip(), "\n".join(lines[index:]).strip("\n")


def _count_examples(text):
    """Số ví dụ trong phần hiệu lực của file ví dụ (đếm dòng mở đầu '--- ... ---')."""
    return sum(1 for line in text.split("\n") if _EXAMPLE_BLOCK_RE.match(line))


def examples_info(value, base_dir=None):
    """Thông tin TRUY VẾT của file ví dụ few-shot, hoặc None nếu prompt không dùng.

    `value` là giá trị khai ở khoá `examples` của thí nghiệm (tên trong thư viện, hoặc đường dẫn
    tới file cạnh notebook).

    VÌ SAO CẦN `sha` RIÊNG CHO FILE VÍ DỤ: `Prompt.sha` chỉ tính nội dung file PROMPT,
    nên hai bộ ví dụ khác nhau (0/1/2 ví dụ) đi với cùng một prompt sẽ mang CÙNG một
    `prompt_sha` - hai thí nghiệm khác nhau mà dấu vết giống nhau, đúng loại lỗi im lặng
    cần chặn. Mã ở đây tính trên phần ĐÃ CẮT chú thích, nên chỉ sửa lời chú thích thì mã
    (và tên file số liệu) không đổi.
    """
    path = resolve(value, base_dir, examples=True)[1]
    if not path.exists():
        # Prompt cần ví dụ mà chưa có file: hiện rõ ở --list-prompts. Lỗi cứng sẽ được
        # báo khi thật sự dựng prompt (xem `examples`), để việc liệt kê không bị chặn.
        return {"file": _display(path), "sha": None, "examples": 0, "note": "",
                "missing": True}

    note, body = _split_examples_note(_read_text(path))
    return {
        "file": _display(path),
        "sha": hashlib.sha1(utils.normalize_text(body).encode("utf-8")).hexdigest()[:8],
        "examples": _count_examples(body),
        "note": note,
        "missing": False,
    }


def examples(value, base_dir=None):
    """Khối ví dụ few-shot của một prompt (mặc định configs/prompts/examples/<tên>.txt).

    `value` là giá trị khai ở khoá `examples` của thí nghiệm. Trả về phần HIỆU LỰC (đã cắt khối
    chú thích ở đầu file) - đây mới là phần đi vào prompt. Xem `_split_examples_note`.
    """
    path = resolve(value, base_dir, examples=True)[1]
    if not path.exists():
        raise PromptError(
            "Prompt cần ô nhớ {{examples}} nhưng chưa có file ví dụ {}. Tạo "
            "file đó (với prompt CoT, mỗi ví dụ nên gồm cả phần suy luận và JSON "
            "kết quả), hoặc bỏ ô nhớ {{examples}} khỏi prompt.".format(_display(path))
        )
    _note, body = _split_examples_note(_read_text(path))
    return body


def describe_all():
    """Thông tin mọi prompt đang có (dùng cho --list-prompts)."""
    return [load(name).describe() for name in available()]
