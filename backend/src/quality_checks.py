"""Read-only dataset quality measurements."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

PREVIEW_ROWS = 8
UNDERREPRESENTED_FRACTION = 0.05


def _json_safe(value: Any) -> Any:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    if isinstance(value, (np.floating,)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def column_kinds(frame: pd.DataFrame) -> dict[str, list[str]]:
    numerical = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c])]
    categorical = [c for c in frame.columns if c not in numerical]
    return {"numerical": numerical, "categorical": categorical}


def profile_dataset(frame: pd.DataFrame) -> dict[str, Any]:
    kinds = column_kinds(frame)
    columns = []
    constant = []
    infinite_counts = {}
    for name in frame.columns:
        series = frame[name]
        nunique = int(series.nunique(dropna=True))
        is_constant = nunique <= 1
        if is_constant:
            constant.append(name)
        inf_count = 0
        if pd.api.types.is_numeric_dtype(series):
            inf_count = int(np.isinf(pd.to_numeric(series, errors="coerce")).sum())
            if inf_count:
                infinite_counts[name] = inf_count
        columns.append(
            {
                "name": name,
                "dtype": str(series.dtype),
                "kind": "numerical" if name in kinds["numerical"] else "categorical",
                "missing": int(series.isna().sum()),
                "unique": nunique,
                "constant": is_constant,
                "infinite": inf_count,
            }
        )
    preview_frame = frame.head(PREVIEW_ROWS)
    preview = [
        {column: _json_safe(preview_frame.iloc[i][column]) for column in preview_frame.columns}
        for i in range(len(preview_frame))
    ]
    return {
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "numerical_count": len(kinds["numerical"]),
        "categorical_count": len(kinds["categorical"]),
        "numerical_columns": kinds["numerical"],
        "categorical_columns": kinds["categorical"],
        "column_details": columns,
        "constant_columns": constant,
        "infinite_values": infinite_counts,
        "preview": preview,
    }


def missing_values(frame: pd.DataFrame) -> dict[str, Any]:
    total_cells = int(frame.shape[0] * frame.shape[1])
    missing_count = int(frame.isna().sum().sum())
    by_column = []
    for name in frame.columns:
        count = int(frame[name].isna().sum())
        if count == 0:
            continue
        by_column.append(
            {
                "column": name,
                "count": count,
                "percentage": round(100.0 * count / len(frame), 4) if len(frame) else 0.0,
            }
        )
    by_column.sort(key=lambda item: item["count"], reverse=True)
    return {
        "total_cells": total_cells,
        "missing_cells": missing_count,
        "missing_percentage": round(100.0 * missing_count / total_cells, 4) if total_cells else 0.0,
        "columns_with_missing": len(by_column),
        "top_columns": by_column[:10],
        "chart": [{"column": item["column"], "count": item["count"]} for item in by_column[:10]],
    }


def duplicate_rows(frame: pd.DataFrame) -> dict[str, Any]:
    if len(frame) == 0:
        return {"duplicate_rows": 0, "duplicate_percentage": 0.0, "duplicate_groups": 0}
    flags = frame.duplicated(keep=False)
    duplicate_count = int(flags.sum())
    groups = 0
    if duplicate_count:
        groups = int(frame.loc[flags].groupby(list(frame.columns), dropna=False).ngroups)
    return {
        "duplicate_rows": duplicate_count,
        "duplicate_percentage": round(100.0 * duplicate_count / len(frame), 4),
        "duplicate_groups": groups,
        "note": "Duplicate rows were counted and left in place.",
    }


def class_balance(
    frame: pd.DataFrame,
    target: str | None,
    underrepresented_fraction: float = UNDERREPRESENTED_FRACTION,
) -> dict[str, Any]:
    if target is None or target == "":
        return {
            "status": "skipped",
            "reason": "No target column was selected.",
            "underrepresented_fraction": underrepresented_fraction,
        }
    if target not in frame.columns:
        return {
            "status": "skipped",
            "reason": f"Column '{target}' is not in the dataset.",
            "underrepresented_fraction": underrepresented_fraction,
        }
    series = frame[target]
    if pd.api.types.is_numeric_dtype(series) and series.nunique(dropna=True) > 20:
        return {
            "status": "skipped",
            "reason": (
                f"'{target}' has {int(series.nunique(dropna=True))} distinct numeric values, "
                "so it is treated as continuous and not a class label."
            ),
            "underrepresented_fraction": underrepresented_fraction,
        }
    counts = series.fillna("(missing)").astype(str).value_counts(dropna=False)
    total = int(counts.sum())
    distribution = []
    underrepresented = []
    for label, count in counts.items():
        percentage = round(100.0 * int(count) / total, 4) if total else 0.0
        item = {"label": str(label), "count": int(count), "percentage": percentage}
        distribution.append(item)
        if total and (int(count) / total) < underrepresented_fraction:
            underrepresented.append(item)
    return {
        "status": "ok",
        "target": target,
        "classes": len(distribution),
        "distribution": distribution,
        "underrepresented": underrepresented,
        "underrepresented_fraction": underrepresented_fraction,
        "rule": f"A class is highlighted when it is under {underrepresented_fraction:.0%} of rows.",
    }


def run_statistical_checks(
    frame: pd.DataFrame,
    target: str | None = None,
    underrepresented_fraction: float = UNDERREPRESENTED_FRACTION,
) -> dict[str, Any]:
    """Measure quality. The frame is not modified."""
    return {
        "profile": profile_dataset(frame),
        "missing": missing_values(frame),
        "duplicates": duplicate_rows(frame),
        "class_balance": class_balance(frame, target, underrepresented_fraction),
    }
