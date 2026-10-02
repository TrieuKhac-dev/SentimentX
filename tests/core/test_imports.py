# -*- coding: utf-8 -*-
"""Luật CI: `src/` KHÔNG được kéo `plotly`/`jinja2` (và các thư viện nặng) ở CẤP MODULE.

VÌ SAO
`requirements-ci.txt` chỉ cài `pandas`, `numpy`, `PyYAML` (và `jinja2`, `plotly` chỉ trong
`src/reporting/` để vẽ HTML). Một import cấp module ở chỗ khác làm CI đỏ ngay ở bước chạy test.

Đã gặp thật: `src/experiments/encoder_run.py` import `src.reporting.curves` ở cấp module, mà `curves`
import `render`, `render` cần `jinja2` -> `ModuleNotFoundError: No module named 'jinja2'` trên CI.
Test này khoá lại: import các module mà `src.api` kéo theo, trong TIẾN TRÌNH CON, rồi kiểm `sys.modules`.

Chạy: python -m unittest discover -s tests
"""

import subprocess
import sys
import unittest

from src.core import paths

# Thư viện KHÔNG được có mặt sau khi import các module dưới (CI không cài chúng).
# KHÔNG đưa `pyarrow` vào đây: `pandas` tự kéo nó khi máy có cài (tuỳ chọn), không phải code của ta.
HEAVY = ("torch", "transformers", "mlflow", "plotly", "jinja2", "peft")

# Module mà CI/`src.api` import - phải nhẹ.
MODULES = ("src.experiments.encoder_run", "src.experiments.experiment_run",
           "src.reporting.reports", "src.api")


class NoHeavyImportsTest(unittest.TestCase):
    def probe(self, module):
        """Import `module` trong tiến trình CON, trả về tên các thư viện nặng đã bị kéo vào."""
        code = ("import sys; import {module}; "
                "print(','.join(name for name in {heavy!r} if name in sys.modules))").format(
                    module=module, heavy=HEAVY)
        done = subprocess.run([sys.executable, "-c", code], cwd=str(paths.root()),
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(done.returncode, 0, "{} -> {}".format(module, done.stderr))
        return done.stdout.strip()

    def test_no_heavy_library_is_pulled_in_at_module_level(self):
        for module in MODULES:
            with self.subTest(module=module):
                self.assertEqual(
                    self.probe(module), "",
                    "{} kéo thư viện nặng vào CẤP MODULE (phải import trong hàm)".format(module))


if __name__ == "__main__":
    unittest.main()
