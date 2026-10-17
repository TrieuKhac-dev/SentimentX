# -*- coding: utf-8 -*-
"""Public configuration entry point for the serving layer.

``load_settings`` is re-exported here so callers can do::

    from serving.config import load_settings
"""

from .specs import ModelSpec, Settings, known_kinds, load_settings, resolve_path

__all__ = [
    "ModelSpec",
    "Settings",
    "known_kinds",
    "load_settings",
    "resolve_path",
]