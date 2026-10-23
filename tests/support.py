# -*- coding: utf-8 -*-
"""Helpers for tests that temporarily replace entries in sys.modules."""
import sys
from contextlib import contextmanager

_MISSING = object()


@contextmanager
def patch_modules(mapping):
    """Replace only the named sys.modules keys, then restore them.

    Unlike mock.patch.dict(sys.modules, ...), this does NOT clear the whole
    module table, so NumPy/SciPy extensions imported inside the context stay
    loaded and are not re-initialised later in the same process.
    """
    previous = {name: sys.modules.get(name, _MISSING) for name in mapping}
    sys.modules.update(mapping)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is _MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
