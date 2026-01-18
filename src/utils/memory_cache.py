from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Callable, Generic, Hashable, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class _Entry(Generic[T]):
    value: T
    expires_at: float | None


class MemoryCache(Generic[T]):
    """线程安全的进程内缓存（LRU + 可选 TTL）。

    设计目标：
    - 轻量、零依赖
    - 适合缓存 QPixmap、解析后的 JSON、扫描结果等
    """

    def __init__(self, *, maxsize: int = 512, default_ttl_s: float | None = None):
        if maxsize <= 0:
            raise ValueError("maxsize must be > 0")
        self._maxsize = int(maxsize)
        self._default_ttl_s = default_ttl_s
        self._lock = RLock()
        self._data: OrderedDict[Hashable, _Entry[T]] = OrderedDict()

    def get(self, key: Hashable) -> Optional[T]:
        now = time.time()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None

            if entry.expires_at is not None and now >= entry.expires_at:
                # 过期清理
                self._data.pop(key, None)
                return None

            # LRU: 标记为最近使用
            self._data.move_to_end(key, last=True)
            return entry.value

    def set(self, key: Hashable, value: T, *, ttl_s: float | None = None) -> None:
        expires_at: float | None
        if ttl_s is None:
            ttl_s = self._default_ttl_s
        if ttl_s is None:
            expires_at = None
        else:
            expires_at = time.time() + float(ttl_s)

        with self._lock:
            self._data[key] = _Entry(value=value, expires_at=expires_at)
            self._data.move_to_end(key, last=True)

            # LRU 淘汰
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def get_or_set(self, key: Hashable, factory: Callable[[], T], *, ttl_s: float | None = None) -> T:
        val = self.get(key)
        if val is not None:
            return val

        created = factory()
        self.set(key, created, ttl_s=ttl_s)
        return created

    def invalidate(self, key: Hashable) -> None:
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
