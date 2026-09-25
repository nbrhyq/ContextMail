import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

from app.models.run import RunRecord


class SQLiteRunStore:
    def __init__(self, path: str = "contextmail.db") -> None:
        self.path = path
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

    def save(self, record: RunRecord) -> RunRecord:
        record.updated_at = datetime.now(timezone.utc)
        payload = record.model_dump_json()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO runs(id, payload, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (record.id, payload, record.created_at.isoformat(), record.updated_at.isoformat()),
            )
        return record

    def get(self, run_id: str) -> Optional[RunRecord]:
        with self._connect() as connection:
            row = connection.execute("SELECT payload FROM runs WHERE id = ?", (run_id,)).fetchone()
        return RunRecord.model_validate_json(row["payload"]) if row else None
