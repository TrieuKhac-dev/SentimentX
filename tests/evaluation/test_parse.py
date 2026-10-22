# -*- coding: utf-8 -*-
"""Test bộ đọc kết quả của model sinh (src/evaluation/parse.py).

Chạy: python -m unittest discover -s tests

Vì sao cần: mọi chỉ số của hướng LLM đều đi qua bộ đọc này. Nếu nó đọc hụt một khía cạnh
mà không báo lỗi, khía cạnh đó bị tính là "không nhắc tới" và bảng điểm trông vẫn hợp lí -
đúng loại lỗi im lặng mà dự án đang cố tránh.
"""

import unittest

from src.evaluation import parse

ASPECTS = ["stayingpower", "texture", "smell", "price", "colour", "shipping", "packing"]
CODES = [0, 1, 2, 3]


def answer(**labels):
    """Sinh chuỗi JSON trả lời cho tiện viết test."""
    import json
    return json.dumps(labels, ensure_ascii=False)


class TestJsonObjects(unittest.TestCase):
    def test_finds_each_object(self):
        text = 'a {"x": 1} b {"y": {"z": 2}} c'
        self.assertEqual(parse.json_objects(text), ['{"x": 1}', '{"y": {"z": 2}}'])

    def test_braces_inside_string_do_not_break_counting(self):
        text = '{"texture": 1, "note": "son có { và } trong câu"}'
        found = parse.json_objects(text)
        self.assertEqual(found, [text])

    def test_escaped_quote_inside_string(self):
        text = '{"note": "anh ấy nói \\"ngon\\" luôn"}'
        self.assertEqual(parse.json_objects(text), [text])

    def test_unbalanced_object_is_ignored(self):
        self.assertEqual(parse.json_objects('{"a": 1'), [])


class TestTailAfterMarker(unittest.TestCase):
    def test_marker_with_diacritics(self):
        self.assertEqual(parse.tail_after_marker("SUY LUẬN: x\nKẾT QUẢ:\n{\"a\": 1}"),
                         "\n{\"a\": 1}")

    def test_marker_without_diacritics(self):
        self.assertEqual(
            parse.tail_after_marker('KET QUA: {"a": 1}').strip(), '{"a": 1}')

    def test_last_marker_wins(self):
        text = "KẾT QUẢ: {\"a\": 0}\nKẾT QUẢ: {\"a\": 1}"
        self.assertIn('{"a": 1}', parse.tail_after_marker(text))

    def test_no_marker(self):
        self.assertIsNone(parse.tail_after_marker("{\"a\": 1}"))


class TestParseLabels(unittest.TestCase):
    def test_plain_json_answer(self):
        labels, info = parse.parse_labels(answer(texture=1, price=0), ASPECTS, CODES)
        self.assertTrue(info["valid"])
        self.assertEqual(labels, {"texture": 1, "price": 0})
        self.assertEqual(info["kiểu đọc"], "đường lui: object JSON cuối cùng")
        self.assertEqual(sorted(info["thiếu"]), [
            "colour", "packing", "shipping", "smell", "stayingpower"])

    def test_cot_answer_reads_block_after_marker(self):
        text = (
            "SUY LUẬN:\n"
            "- texture: \"mịn\" | khen | mã 1\n"
            "KẾT QUẢ:\n"
            + answer(texture=1)
        )
        labels, info = parse.parse_labels(text, ASPECTS, CODES)
        self.assertTrue(info["valid"])
        self.assertEqual(labels, {"texture": 1})
        self.assertEqual(info["kiểu đọc"], "khối KẾT QUẢ")
        self.assertTrue(info["has_reasoning"])

    def test_json_inside_reasoning_is_not_taken_as_answer(self):
        text = (
            "Ví dụ định dạng: {\"texture\": 0}\n"
            "SUY LUẬN:\n- texture: \"mịn\" | khen | mã 2\n"
            "KẾT QUẢ: " + answer(texture=2)
        )
        labels, _info = parse.parse_labels(text, ASPECTS, CODES)
        self.assertEqual(labels, {"texture": 2})

    def test_marker_missing_falls_back_to_last_object(self):
        text = "Tôi nghĩ vậy {\"texture\": 3} và đây là kết quả {\"texture\": 1}"
        labels, info = parse.parse_labels(text, ASPECTS, CODES)
        self.assertEqual(labels, {"texture": 1})
        self.assertIn("đường lui", info["kiểu đọc"])

    def test_invalid_json_is_reported_not_silently_zero(self):
        labels, info = parse.parse_labels("KẾT QUẢ: {\"texture\": 1,}", ASPECTS, CODES)
        self.assertFalse(info["valid"])
        self.assertEqual(labels, {})
        self.assertIn("JSON không hợp lệ", info["reason"])

    def test_unknown_keys_are_reported(self):
        labels, info = parse.parse_labels(answer(khong_ton_tai=1), ASPECTS, CODES)
        self.assertFalse(info["valid"])
        self.assertEqual(info["lạ"], ["khong_ton_tai"])

    def test_bad_code_is_reported(self):
        labels, info = parse.parse_labels(answer(texture=9), ASPECTS, CODES)
        self.assertFalse(info["valid"])
        self.assertEqual(info["mã sai"], {"texture": 9})
        self.assertEqual(labels, {})

    def test_quoted_code_is_accepted(self):
        labels, info = parse.parse_labels('{"texture": "2"}', ASPECTS, CODES)
        self.assertTrue(info["valid"])
        self.assertEqual(labels, {"texture": 2})

    def test_thinking_block_is_stripped(self):
        text = "<think>đây là suy nghĩ {\"texture\": 0}</think>KẾT QUẢ: {\"texture\": 1}"
        labels, info = parse.parse_labels(text, ASPECTS, CODES)
        self.assertTrue(info["had_thinking"])
        self.assertEqual(labels, {"texture": 1})

    def test_empty_answer(self):
        labels, info = parse.parse_labels("   ", ASPECTS, CODES)
        self.assertFalse(info["valid"])
        self.assertEqual(info["reason"], "câu trả lời rỗng")
        self.assertEqual(labels, {})

    def test_text_without_json(self):
        labels, info = parse.parse_labels("Tôi không biết.", ASPECTS, CODES)
        self.assertFalse(info["valid"])
        self.assertEqual(info["reason"], "không thấy JSON nào")

    def test_require_all_marks_incomplete_as_invalid(self):
        labels, info = parse.parse_labels(answer(texture=1), ASPECTS, CODES,
                                          require_all=True)
        self.assertFalse(info["valid"])
        self.assertEqual(labels, {"texture": 1})


class TestParseEvidence(unittest.TestCase):
    """Quote/reason chỉ để hiển thị: đọc đúng chữ model sinh, không bịa, không chấm điểm."""

    def test_quoted_quote_reason_and_code(self):
        text = (
            "SUY LUẬN:\n"
            '- colour: "màu 102 rất bợt" | màu lệch và bợt so với kỳ vọng | mã 2\n'
            "KẾT QUẢ:\n{\"colour\": 2}"
        )
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["colour"]["quote"], "màu 102 rất bợt")
        self.assertEqual(evidence["colour"]["reason"], "màu lệch và bợt so với kỳ vọng")

    def test_unquoted_khong_nhac_toi_is_preserved(self):
        text = "- price: không nhắc tới | không có thông tin về giá | mã 0"
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["price"]["quote"], "không nhắc tới")
        self.assertEqual(evidence["price"]["reason"], "không có thông tin về giá")

    def test_multiple_aspects_separated_by_comma(self):
        text = '- colour, price: "bợt" | lệch màu | mã 2'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["colour"]["quote"], "bợt")
        self.assertEqual(evidence["colour"]["reason"], "lệch màu")
        self.assertEqual(evidence["price"]["quote"], "bợt")
        self.assertEqual(evidence["price"]["reason"], "lệch màu")

    def test_missing_aspect_is_not_fabricated(self):
        text = '- colour: "bợt" | lệch | mã 2'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["colour"]["quote"], "bợt")
        for aspect in ASPECTS:
            if aspect == "colour":
                continue
            self.assertEqual(evidence[aspect], {"quote": None, "reason": None})

    def test_empty_answer(self):
        empty = {"quote": None, "reason": None}
        for answer in ("", "   ", None):
            evidence = parse.parse_evidence(answer, ASPECTS)
            self.assertEqual(set(evidence), set(ASPECTS))
            self.assertTrue(all(value == empty for value in evidence.values()))

    def test_literal_backslash_n_is_a_newline(self):
        text = (
            '- colour: "bợt" | lệch | mã 2\\n'
            '- price: "không nhắc tới" | không có | mã 0'
        )
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["colour"]["quote"], "bợt")
        self.assertEqual(evidence["price"]["quote"], "không nhắc tới")

    def test_quote_with_internal_quotes(self):
        text = '- smell: ""thơm" nhẹ" | mùi "dễ chịu" | mã 1'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["smell"]["quote"], '"thơm" nhẹ')
        self.assertEqual(evidence["smell"]["reason"], 'mùi "dễ chịu"')

    def test_reason_containing_pipe(self):
        text = '- texture: "mịn" | mềm | mượt | mã 1'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["texture"]["quote"], "mịn")
        self.assertEqual(evidence["texture"]["reason"], "mềm | mượt")

    def test_two_segments_without_code(self):
        text = '- texture: "mịn" | khen'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["texture"]["quote"], "mịn")
        self.assertEqual(evidence["texture"]["reason"], "khen")

    def test_duplicate_keeps_first_non_empty(self):
        text = '- colour: "" | | mã 0\n- colour: "bợt" | lệch | mã 2'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["colour"]["quote"], "bợt")
        self.assertEqual(evidence["colour"]["reason"], "lệch")

    def test_packaging_is_mapped_to_packing(self):
        text = '- packaging: "hộp đẹp" | đóng gói tốt | mã 1'
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertEqual(evidence["packing"]["quote"], "hộp đẹp")
        self.assertEqual(evidence["packing"]["reason"], "đóng gói tốt")

    def test_empty_quoted_reason_becomes_none(self):
        evidence = parse.parse_evidence('- smell: "mùi thơm" | "" | mã 1', ["smell"])
        self.assertEqual(evidence["smell"]["quote"], "mùi thơm")
        self.assertIsNone(evidence["smell"]["reason"])

    def test_empty_quoted_quote_becomes_none(self):
        evidence = parse.parse_evidence('- smell: "" | lý do | mã 1', ["smell"])
        self.assertIsNone(evidence["smell"]["quote"])
        self.assertEqual(evidence["smell"]["reason"], "lý do")

    def test_quoted_reason_is_unwrapped_and_preserved(self):
        text = '- smell: "mùi thơm" | "mùi "dễ chịu", thoang thoảng" | mã 1'
        evidence = parse.parse_evidence(text, ["smell"])
        self.assertEqual(evidence["smell"]["reason"], 'mùi "dễ chịu", thoang thoảng')

    def test_quoted_khong_nhac_toi_quote_is_preserved(self):
        text = '- smell: "không nhắc tới" | không có | mã 0'
        evidence = parse.parse_evidence(text, ["smell"])
        self.assertEqual(evidence["smell"]["quote"], "không nhắc tới")
        self.assertEqual(evidence["smell"]["reason"], "không có")

    def test_lines_without_pipe_or_valid_aspect_are_skipped(self):
        text = (
            "- colour: bợt\n"
            "- không có khía cạnh này: \"x\" | y | mã 1\n"
            '{"colour": 2}\n'
        )
        evidence = parse.parse_evidence(text, ASPECTS)
        self.assertTrue(all("quote" in value for value in evidence.values()))
        self.assertTrue(all(value["quote"] is None for value in evidence.values()))
        self.assertTrue(all(value["reason"] is None for value in evidence.values()))


if __name__ == "__main__":
    unittest.main()
