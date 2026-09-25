# -*- coding: utf-8 -*-
"""Test chạy tiếp sau khi bị ngắt (src/resume.py) và bảng dự đoán (src/evaluation/records.py).

Bốn điều được khoá ở đây, vì đều chỉ phát hiện được khi đã hỏng thật:
    - Chỉ RESUME khi ba giá trị (`config_sha256`, mã phiên bản, `repo.sha`) trùng khít; lệch một
      giá trị là phải chạy lại từ đầu, và kết quả cũ KHÔNG bị xoá.
    - Lần chạy trước đã XONG với đúng bộ ba thì DỪNG, không chạy lại vô ích.
    - Dòng viết dở trong khối bị bỏ qua và ĐẾM LẠI, để mẫu đó được chạy lại.
    - Điểm số khi chạy tiếp là điểm của CẢ split, không phải của phần còn lại.

Chạy: python -m unittest discover -s tests
"""

import json
import tempfile
import unittest
from pathlib import Path

from src import resume
from src.evaluation import records
from src.tracking import run_meta


def row(index, gold, guess, valid=True, extra=None):
    """Một dòng bảng dự đoán, đúng thứ tự cột của `records.COLUMNS`."""
    values = {
        "chỉ số": index, "split": "val", "prompt": "absa_cot_v1", "kiểu đọc": "json",
        "đọc được": "có" if valid else "KHÔNG",
        "lí do": "" if valid else "JSON không hợp lệ",
        "text": "review {}".format(index),
        "nhãn đúng": json.dumps(gold, ensure_ascii=False),
        "nhãn đoán": json.dumps(guess or {}, ensure_ascii=False),
        "token sinh": 100, "giây": 1.5, "có suy luận": "có", "có <think>": "không",
        "câu trả lời": "...",
    }
    values.update(extra or {})
    return [values[column] for column in records.COLUMNS]


class TestDecide(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "run"
        self.out_dir.mkdir(parents=True)
        self.want = resume.fingerprint("b" * 64, "cosmetics-ds0.1.0", "a" * 40)

    def tearDown(self):
        self._tmp.cleanup()

    def record(self, status=None, sha="a" * 40, config_sha="b" * 64, ma="cosmetics-ds0.1.0"):
        payload = run_meta.build(
            self.out_dir, repo={"sha": sha}, config={"sha256": config_sha},
            data={"ma": ma}, env={})
        if status:
            run_meta.finish_attempt(run_meta.attempt_of(payload), status)
        return payload

    def test_no_previous_run_is_new(self):
        mode, _reason = resume.decide(None, self.want, 0)
        self.assertEqual(mode, resume.MODE_NEW)

    def test_finished_with_same_fingerprint_stops(self):
        mode, reason = resume.decide(
            self.record(run_meta.STATUS_FINISHED), self.want, parts=10)
        self.assertEqual(mode, resume.MODE_STOP)
        self.assertIn("đã XONG", reason)

    def test_interrupted_with_same_fingerprint_resumes(self):
        mode, reason = resume.decide(
            self.record(run_meta.STATUS_FAILED), self.want, parts=10)
        self.assertEqual(mode, resume.MODE_RESUME)
        self.assertIn("10 mẫu", reason)

    def test_interrupted_without_parts_is_new(self):
        mode, _reason = resume.decide(
            self.record(run_meta.STATUS_FAILED), self.want, parts=0)
        self.assertEqual(mode, resume.MODE_NEW)

    def test_changed_code_is_new_not_resume(self):
        """Code đổi thì kết quả cũ không còn so được: chạy lại từ đầu (rules.md mục 14)."""
        mode, reason = resume.decide(
            self.record(run_meta.STATUS_FAILED, sha="c" * 40), self.want, parts=10)
        self.assertEqual(mode, resume.MODE_NEW)
        self.assertIn("KHÁC", reason)

    def test_changed_config_or_data_is_new(self):
        for kwargs in ({"config_sha": "d" * 64}, {"ma": "cosmetics-ds0.2.0"}):
            mode, _reason = resume.decide(self.record(run_meta.STATUS_FAILED, **kwargs),
                                          self.want, parts=5)
            self.assertEqual(mode, resume.MODE_NEW, kwargs)

    def test_force_new_wins(self):
        mode, reason = resume.decide(
            self.record(run_meta.STATUS_FAILED), self.want, parts=10, force_new=True)
        self.assertEqual(mode, resume.MODE_NEW)
        self.assertIn("--new", reason)


class TestParts(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out_dir = Path(self._tmp.name) / "run"
        self.out_dir.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_append_writes_part_file_and_reads_back(self):
        parts = resume.Parts(self.out_dir)
        path = parts.append([row(0, {"colour": 1}, {"colour": 1})])

        self.assertEqual(path.name, "part_0001.jsonl")
        self.assertEqual(path.parent.name, "predictions")
        self.assertEqual(parts.count(), 1)
        self.assertEqual(parts.keys(), {"0"})
        record = parts.records()[0]
        self.assertEqual(record["text"], "review 0")
        self.assertEqual(json.loads(record["nhãn đoán"]), {"colour": 1})

    def test_new_part_after_max_records(self):
        parts = resume.Parts(self.out_dir, max_records=2)
        parts.append([row(0, {"a": 1}, {"a": 1}), row(1, {"a": 1}, {"a": 1})])
        parts.append([row(2, {"a": 1}, {"a": 1})])

        self.assertEqual([path.name for path in parts.paths()],
                         ["part_0001.jsonl", "part_0002.jsonl"])
        self.assertEqual(parts.count(), 3)

    def test_torn_line_is_skipped_and_counted(self):
        """Mất điện giữa chừng để lại một dòng viết dở; mẫu đó phải được chạy lại."""
        parts = resume.Parts(self.out_dir)
        parts.append([row(0, {"a": 1}, {"a": 1})])
        with open(parts.paths()[0], "a", encoding="utf-8") as handle:
            handle.write('{"chỉ số": 1, "text": "viết d')

        fresh = resume.Parts(self.out_dir)
        self.assertEqual(fresh.count(), 1)
        self.assertEqual(fresh.torn, 1)
        self.assertEqual(fresh.keys(), {"0"})

    def test_rows_are_ready_for_csv(self):
        parts = resume.Parts(self.out_dir)
        parts.append([row(7, {"colour": 2}, {"colour": 2})])
        rows = parts.rows()
        self.assertEqual(rows[0][0], 7)
        self.assertEqual(len(rows[0]), len(records.COLUMNS))

    def test_stash_moves_parts_without_deleting(self):
        parts = resume.Parts(self.out_dir)
        parts.append([row(0, {"a": 1}, {"a": 1})])
        moved = parts.stash()

        self.assertTrue(moved.is_dir())
        self.assertIn("_bo-qua-", moved.name)
        self.assertEqual(len(list(moved.glob("part_*.jsonl"))), 1)
        self.assertEqual(resume.Parts(self.out_dir).count(), 0)

    def test_stash_without_parts_is_nothing(self):
        self.assertIsNone(resume.Parts(self.out_dir).stash())


class TestRecords(unittest.TestCase):
    def test_merge_sorts_and_lets_new_win(self):
        stored = [{"chỉ số": 5, "text": "cũ"}, {"chỉ số": 9, "text": "giữ"}]
        new = [row(1, {"a": 1}, {"a": 1}), row(5, {"a": 2}, {"a": 2}, extra={"text": "mới"})]
        merged = records.merge(stored, new)

        self.assertEqual([item[records.KEY_INDEX] for item in merged], [1, 5, 9])
        self.assertEqual(merged[1][records.COLUMNS.index("text")], "mới")

    def test_to_arrays_keeps_unreadable_as_none(self):
        rows = [row(0, {"colour": 1}, {"colour": 1}),
                row(1, {"colour": 2}, {}, valid=False)]
        golds, preds, infos = records.to_arrays(rows, ["colour"])

        self.assertEqual(golds[0], {"colour": 1})
        self.assertEqual(preds[0], {"colour": 1})
        self.assertIsNone(preds[1])
        self.assertFalse(infos[1]["valid"])
        self.assertIn("JSON", infos[1]["reason"])

    def test_to_arrays_marks_missing_aspects(self):
        rows = [row(0, {"colour": 1, "price": 2}, {"colour": 1})]
        _golds, preds, infos = records.to_arrays(rows, ["colour", "price"])

        self.assertEqual(preds[0], {"colour": 1})
        self.assertEqual(infos[0]["thiếu"], ["price"])

    def test_to_arrays_survives_broken_labels(self):
        """Ô nhãn hỏng trong file cũ thì coi như không đọc được, không được ném."""
        rows = [row(0, {}, {}, extra={"nhãn đoán": "{hỏng"})]
        golds, preds, infos = records.to_arrays(rows, ["colour"])

        self.assertEqual(golds[0], {"colour": 0})
        self.assertEqual(preds[0], {})
        self.assertEqual(infos[0]["thiếu"], ["colour"])


class PromptColumnTest(unittest.TestCase):
    """Cột `prompt gửi model`: có ở đường chạy LLM, KHÔNG có ở bảng của model encoder.

    Vì sao khoá: bảng dự đoán là chỗ duy nhất trả lời được "mẫu này thành prompt nào rồi model trả
    lời ra sao". Thiếu cột đó thì phải chạy lại model mới biết. Nhưng model encoder (PhoBERT,
    ViSoBERT) học từ chuỗi thô - chúng không có prompt nào để ghi, nên bảng của chúng phải giữ
    nguyên 14 cột; thêm cột rỗng vào đó là nói dối về dữ liệu.
    """

    def test_llm_table_has_the_prompt_right_before_the_answer(self):
        columns = records.columns(with_prompt=True)
        self.assertEqual(len(columns), len(records.COLUMNS) + 1)
        self.assertEqual(columns[columns.index(records.ANSWER_COLUMN) - 1],
                         records.PROMPT_COLUMN)
        self.assertNotIn(records.PROMPT_COLUMN, records.COLUMNS)

    def test_encoder_table_is_unchanged(self):
        self.assertEqual(records.columns(with_prompt=False), records.COLUMNS)
        self.assertEqual(records.columns(), records.COLUMNS)

    def test_merging_keeps_the_prompt_of_rows_already_on_disk(self):
        """Chạy tiếp: dòng đã lưu (dict) phải giữ được prompt khi gộp vào bảng."""
        columns = records.columns(with_prompt=True)
        stored = [dict(zip(columns, [0, "val", "p", "khối", "có", "ok", "review", "{}", "{}",
                                     10, 1.0, "có", "không", "PROMPT CŨ", "trả lời cũ"]))]
        merged = records.merge(stored, [], columns)
        self.assertEqual(merged[0][columns.index(records.PROMPT_COLUMN)], "PROMPT CŨ")

    def test_prompt_column_is_named_in_vietnamese_like_the_others(self):
        self.assertIn(" ", records.PROMPT_COLUMN)


if __name__ == "__main__":
    unittest.main()

