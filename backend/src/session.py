"""In-memory dataset sessions. No database and no path exposure."""

from __future__ import annotations

import uuid
from typing import Any

import pandas as pd

from src.data_loader import load_csv_bytes, load_csv_path, demo_csv_path

SESSIONS: dict[str, dict[str, Any]] = {}


def reset_sessions() -> None:
    SESSIONS.clear()


def _store(name: str, frame: pd.DataFrame, byte_size: int) -> dict[str, Any]:
    dataset_id = str(uuid.uuid4())
    record = {
        "id": dataset_id,
        "name": name,
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "byte_size": int(byte_size),
        "column_names": [str(c) for c in frame.columns],
        "frame": frame.copy(deep=True),
        "audit": None,
        "model": None,
    }
    SESSIONS[dataset_id] = record
    return record


def load_demo() -> dict[str, Any]:
    path = demo_csv_path()
    frame = load_csv_path(path)
    return _store("demo_dataset.csv", frame, path.stat().st_size)


def load_upload(filename: str, payload: bytes) -> dict[str, Any]:
    frame = load_csv_bytes(payload, source_name=filename or "upload.csv")
    return _store(filename or "upload.csv", frame, len(payload))


def get_session(dataset_id: str) -> dict[str, Any] | None:
    return SESSIONS.get(dataset_id)


def original_frame(dataset_id: str) -> pd.DataFrame:
    session = SESSIONS[dataset_id]
    return session["frame"].copy(deep=True)
