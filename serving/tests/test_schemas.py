# -*- coding: utf-8 -*-
"""Unit tests for serving.schemas (Pydantic v2)."""

import unittest

from pydantic import ValidationError

from serving.schemas import (
    AspectPrediction,
    PredictionItem,
    PredictRequest,
    PredictResponse,
)


class PredictRequestTests(unittest.TestCase):
    def test_text_ok(self):
        req = PredictRequest(text="x")
        self.assertEqual(req.text, "x")
        self.assertIsNone(req.texts)

    def test_texts_ok(self):
        req = PredictRequest(texts=["a", "b"])
        self.assertEqual(req.texts, ["a", "b"])

    def test_text_and_texts_rejected(self):
        with self.assertRaises(ValidationError):
            PredictRequest(text="x", texts=["a"])

    def test_neither_rejected(self):
        with self.assertRaises(ValidationError):
            PredictRequest()

    def test_empty_text_rejected(self):
        with self.assertRaises(ValidationError):
            PredictRequest(text="")

    def test_too_many_texts_rejected(self):
        with self.assertRaises(ValidationError):
            PredictRequest(texts=["a"] * 17)

    def test_extra_field_rejected(self):
        with self.assertRaises(ValidationError):
            PredictRequest(text="x", bogus=1)


class PredictResponseTests(unittest.TestCase):
    def test_round_trip(self):
        resp = PredictResponse(
            request_id="req-1",
            model="cafebert_exp027",
            model_version="v1",
            model_hash="hash",
            device="fake",
            latency_ms=1.5,
            batch_size=1,
            results=[
                PredictionItem(
                    text="x",
                    aspects={
                        "colour": AspectPrediction(
                            label="positive", label_vi="Tích cực", code=1
                        )
                    },
                )
            ],
        )
        data = resp.model_dump()
        again = PredictResponse.model_validate(data)
        self.assertEqual(again.model, "cafebert_exp027")
        self.assertEqual(again.results[0].aspects["colour"].label, "positive")


if __name__ == "__main__":
    unittest.main()