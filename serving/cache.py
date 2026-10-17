# -*- coding: utf-8 -*-
"""In-memory TTL cache for the serving layer.

A small, thread-safe, in-memory cache backed by an :class:`~collections.OrderedDict`.
It is intentionally disk-free and disabled by default (see ``configs/serving.yaml``).
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple


class TTLCache:
    """A bounded in-memory cache with per-entry time-to-live.

    Entries expire after ``ttl_s`` seconds and the cache never grows beyond
    ``max_entries`` (least-recently-used entries are evicted first).
    """

    def __init__(self, max_entries: int = 512, ttl_s: float = 900.0) -> None:
        self.max_entries = max(1, int(max_entries))
        self.ttl_s = max(0.0, float(ttl_s))
        self._store: "OrderedDict[str, Tuple[float, Any]]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Return the cached value for ``key``, or ``None`` if absent/expired."""
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if now >= expires_at:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key``, evicting expired/oldest entries."""
        now = time.monotonic()
        with self._lock:
            self._store[key] = (now + self.ttl_s, value)
            self._store.move_to_end(key)
            while len(self._store) > self.max_entries:
                self._store.popitem(last=False)

    def clear(self) -> None:
        """Drop every cached entry."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


__all__ = ["TTLCache"]