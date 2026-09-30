"""Simple LRU cache for translation results.

Stores recent translations keyed by (text_hash, direction) to avoid
re-translating identical inputs. Cache is in-memory and bounded.
"""

import hashlib
import time
from collections import OrderedDict

_MAX_ENTRIES = 500
_TTL_SECONDS = 3600  # 1 hour


class TranslationCache:
    def __init__(self, max_entries: int = _MAX_ENTRIES, ttl: int = _TTL_SECONDS):
        self._max = max_entries
        self._ttl = ttl
        self._cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()

    @staticmethod
    def _key(text: str, direction: str) -> str:
        raw = f"{text.strip().lower()}|{direction}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, text: str, direction: str) -> dict | None:
        key = self._key(text, direction)
        if key in self._cache:
            entry, ts = self._cache[key]
            if time.time() - ts < self._ttl:
                self._cache.move_to_end(key)
                return entry
            del self._cache[key]
        return None

    def put(self, text: str, direction: str, result: dict):
        key = self._key(text, direction)
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self._max:
            self._cache.popitem(last=False)
        self._cache[key] = (result, time.time())

    def clear(self):
        self._cache.clear()

    def __len__(self):
        return len(self._cache)


# Global singleton
translation_cache = TranslationCache()
