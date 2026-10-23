# -*- coding: utf-8 -*-
"""Regression tests for tests.support.patch_modules."""

import sys
import types
import unittest

from tests.support import patch_modules


class PatchModulesTest(unittest.TestCase):
    def test_restores_replaced_keys(self):
        name = "_sentimentx_test_replaced"
        original = types.ModuleType(name)
        replacement = types.ModuleType(name)
        sys.modules[name] = original
        try:
            with patch_modules({name: replacement}):
                self.assertIs(sys.modules[name], replacement)
            self.assertIs(sys.modules[name], original)
        finally:
            sys.modules.pop(name, None)

    def test_modules_added_inside_context_remain(self):
        name = "_sentimentx_test_inside"
        inside = types.ModuleType(name)
        try:
            with patch_modules({}):
                sys.modules[name] = inside
            self.assertIs(sys.modules.get(name), inside)
        finally:
            sys.modules.pop(name, None)

    def test_keys_absent_before_are_removed(self):
        name = "_sentimentx_test_absent"
        sys.modules.pop(name, None)
        with patch_modules({name: types.ModuleType(name)}):
            self.assertIn(name, sys.modules)
        self.assertNotIn(name, sys.modules)


if __name__ == "__main__":
    unittest.main()
