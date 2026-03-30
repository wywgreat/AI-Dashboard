from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CacheItem:
    data: dict[str, Any]
    expires_at: float


class AACache:
    def __init__(self, db_path: str = "backend/data/aa_cache.sqlite", ttl_seconds: int = 900) -> None:
        self.ttl_seconds = ttl_seconds
        self._memory: dict[str, CacheItem] = {}
        self._lock = threading.Lock()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS aa_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            in_memory = self._memory.get(key)
            if in_memory and in_memory.expires_at > now:
                return in_memory.data

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload, expires_at FROM aa_cache WHERE cache_key = ?", (key,)
            ).fetchone()

        if not row:
            return None

        payload, expires_at = row
        if expires_at <= now:
            self.delete(key)
            return None

        data = json.loads(payload)
        with self._lock:
            self._memory[key] = CacheItem(data=data, expires_at=expires_at)
        return data

    def set(self, key: str, data: dict[str, Any]) -> None:
        expires_at = time.time() + self.ttl_seconds
        payload = json.dumps(data, default=str)

        with self._lock:
            self._memory[key] = CacheItem(data=data, expires_at=expires_at)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO aa_cache(cache_key, payload, expires_at)
                VALUES(?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, expires_at = excluded.expires_at
                """,
                (key, payload, expires_at),
            )
            conn.commit()

    def delete(self, key: str) -> None:
        with self._lock:
            self._memory.pop(key, None)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM aa_cache WHERE cache_key = ?", (key,))
            conn.commit()
