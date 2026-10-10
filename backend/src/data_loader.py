"""Load CSV datasets without modifying caller-owned bytes."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

MAX_UPLOAD_BYTES = 2_000_000
MAX_ROWS = 20_000
MAX_COLUMNS = 80
DEMO_FILENAME = "demo_dataset.csv"


class DataLoadError(ValueError):
    """Raised when a CSV cannot be accepted for auditing."""


def demo_csv_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / DEMO_FILENAME


def _validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.shape[1] == 0:
        raise DataLoadError("The CSV has no columns.")
    if len(frame) == 0:
        raise DataLoadError("The CSV has no data rows.")
    if len(frame) > MAX_ROWS:
        raise DataLoadError(f"The CSV has {len(frame)} rows; the limit is {MAX_ROWS}.")
    if frame.shape[1] > MAX_COLUMNS:
        raise DataLoadError(
            f"The CSV has {frame.shape[1]} columns; the limit is {MAX_COLUMNS}."
        )
    columns = [str(c).strip() for c in frame.columns]
    if any(c == "" for c in columns):
        raise DataLoadError("The CSV has an empty column name.")
    if len(set(columns)) != len(columns):
        raise DataLoadError("The CSV has duplicate column names.")
    frame = frame.copy()
    frame.columns = columns
    return frame


def load_csv_bytes(payload: bytes, source_name: str = "upload.csv") -> pd.DataFrame:
    if not payload or not payload.strip():
        raise DataLoadError("The file is empty.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise DataLoadError(
            f"The file is {len(payload)} bytes; the limit is {MAX_UPLOAD_BYTES}."
        )
    if not source_name.lower().endswith(".csv"):
        raise DataLoadError("Only .csv files are accepted.")
    try:
        frame = pd.read_csv(io.BytesIO(payload), on_bad_lines="error")
    except pd.errors.EmptyDataError as exc:
        raise DataLoadError("The CSV has no parseable content.") from exc
    except pd.errors.ParserError as exc:
        raise DataLoadError(f"The CSV could not be parsed: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise DataLoadError("The file is not valid UTF-8 or ASCII text.") from exc
    return _validate_frame(frame)


def load_csv_path(path: Path) -> pd.DataFrame:
    payload = path.read_bytes()
    return load_csv_bytes(payload, source_name=path.name)
