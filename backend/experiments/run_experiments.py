"""Controlled corruption experiment on an in-memory copy of the demo CSV.

Ground-truth labels are used only when scoring detectors. They are not passed
to the autoencoder or used to choose its threshold.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.audit_engine import audit_frame, train_on_frame  # noqa: E402
from src.data_loader import demo_csv_path  # noqa: E402
from src.evaluation import binary_detection_metrics  # noqa: E402

REPORT_PATH = ROOT / "reports" / "experiment_results.json"
NUMERIC = [
    "age",
    "study_hours",
    "attendance_pct",
    "prior_gpa",
    "sleep_hours",
    "assignments_submitted",
    "lab_score",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statistical_outlier_scores(raw: np.ndarray, train_idx: np.ndarray) -> np.ndarray:
    """Modified z-score using median and MAD fit on the training rows only."""
    train = raw[train_idx]
    median = np.nanmedian(train, axis=0)
    mad = np.nanmedian(np.abs(train - median), axis=0)
    mad = np.where(mad < 1e-8, 1e-8, mad)
    filled = raw.copy()
    inds = np.where(np.isnan(filled))
    filled[inds] = np.take(median, inds[1])
    modified_z = 0.6745 * (filled - median) / mad
    return np.max(np.abs(modified_z), axis=1)


def main() -> None:
    source = demo_csv_path()
    digest_before = sha256_file(source)
    original = pd.read_csv(source)
    work = original.copy(deep=True)
    n = len(work)

    missing_cells = [
        (10, "study_hours"),
        (11, "sleep_hours"),
        (12, "lab_score"),
        (25, "attendance_pct"),
        (26, "prior_gpa"),
        (40, "assignments_submitted"),
        (41, "age"),
        (55, "study_hours"),
    ]
    natural_missing = [
        (int(i), col)
        for i, row in original.iterrows()
        for col in original.columns
        if pd.isna(row[col])
    ]
    for row_index, column in missing_cells:
        work.iat[row_index, work.columns.get_loc(column)] = np.nan

    duplicate_sources = [0, 1, 2]
    appended = work.iloc[duplicate_sources].copy()
    work = pd.concat([work, appended], ignore_index=True)
    injected_duplicate_rows = list(range(n, n + len(duplicate_sources)))

    outlier_rows = {
        20: ("lab_score", 5000.0),
        21: ("age", -40.0),
        22: ("study_hours", 400.0),
        23: ("prior_gpa", 40.0),
        24: ("sleep_hours", 30.0),
    }
    for row_index, (column, value) in outlier_rows.items():
        work.iat[row_index, work.columns.get_loc(column)] = value

    audit = audit_frame(work, target="program")
    model = train_on_frame(work)

    # Missing-value detector: a cell is predicted missing when it is null.
    injected_missing = set(missing_cells)
    natural_set = set(natural_missing)
    predicted_missing = {
        (int(i), col)
        for i, row in work.iterrows()
        for col in work.columns
        if pd.isna(row[col])
    }
    # Restrict the universe to original row indices so appended copies are not double-counted.
    original_index_cells = {(i, c) for i in range(n) for c in work.columns}
    positives = injected_missing
    detected = predicted_missing & original_index_cells
    tp_cells = positives & detected
    fp_cells = detected - positives
    fn_cells = positives - detected
    fp_natural = fp_cells & natural_set
    fp_other = fp_cells - natural_set
    prec_den = len(tp_cells) + len(fp_cells)
    rec_den = len(tp_cells) + len(fn_cells)
    missing_metrics = {
        "definition": (
            "Positive cells are the injected coordinates. "
            "A cell is detected when it is null. Natural missing cells count as false positives."
        ),
        "injected_cells": len(positives),
        "true_positives": len(tp_cells),
        "false_positives": len(fp_cells),
        "false_positives_natural_missing": len(fp_natural),
        "false_positives_other": len(fp_other),
        "false_negatives": len(fn_cells),
        "precision": (len(tp_cells) / prec_den) if prec_den else None,
        "recall": (len(tp_cells) / rec_den) if rec_den else None,
        "f1": None,
    }
    if missing_metrics["precision"] is not None and missing_metrics["recall"] is not None:
        p = missing_metrics["precision"]
        r = missing_metrics["recall"]
        missing_metrics["f1"] = (2 * p * r / (p + r)) if (p + r) else 0.0

    duplicate_flags = work.duplicated(keep=False).to_numpy()
    y_true_dup = np.zeros(len(work), dtype=int)
    y_true_dup[injected_duplicate_rows] = 1
    dup_metrics = binary_detection_metrics(y_true_dup, duplicate_flags.astype(int))
    dup_metrics["definition"] = (
        "Positive rows are the appended copies. "
        "Every row in an exact duplicate group is predicted positive, "
        "so original partner rows and any natural duplicates count as false positives."
    )
    dup_metrics["false_positive_row_indexes"] = [
        int(i) for i in np.flatnonzero(duplicate_flags & (y_true_dup == 0))
    ]

    if model.get("status") != "trained":
        outlier_metrics = {
            "available": False,
            "reason": model.get("limitation"),
        }
        baseline_metrics = {"available": False, "reason": "Autoencoder was not trained."}
    else:
        positions = model["_row_positions"]
        errors = model["_errors"]
        flagged = model["_flagged_local"].astype(int)
        y_true = np.isin(positions, list(outlier_rows)).astype(int)
        outlier_metrics = binary_detection_metrics(y_true, flagged, errors)
        outlier_metrics["definition"] = (
            "Positive rows are the five injected numerical outliers. "
            "The autoencoder and the 95th percentile validation threshold did not see these labels."
        )
        outlier_metrics["injected_rows"] = sorted(outlier_rows)
        outlier_metrics["flagged_injected_rows"] = [
            int(positions[i]) for i in np.flatnonzero((y_true == 1) & (flagged == 1))
        ]
        outlier_metrics["flagged_non_injected_rows"] = [
            int(positions[i]) for i in np.flatnonzero((y_true == 0) & (flagged == 1))
        ]

        from sklearn.model_selection import train_test_split

        local = np.arange(len(positions))
        train_idx, temp_idx = train_test_split(local, test_size=0.4, random_state=42)
        raw = work.iloc[positions][NUMERIC].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        scores = statistical_outlier_scores(raw, train_idx)
        baseline_pred = (scores > 3.5).astype(int)
        baseline_metrics = binary_detection_metrics(y_true, baseline_pred, scores)
        baseline_metrics["definition"] = (
            "Modified z-score (0.6745 * (x-median)/MAD) fit on the same training split. "
            "A row is flagged when its largest absolute feature z-score exceeds 3.5. "
            "The cutoff was not tuned on the injected labels."
        )
        baseline_metrics["flagged_non_injected_rows"] = [
            int(positions[i]) for i in np.flatnonzero((y_true == 0) & (baseline_pred == 1))
        ]

    public_model = {
        key: model.get(key)
        for key in (
            "status",
            "seed",
            "features",
            "architecture",
            "train_loss",
            "best_val_loss",
            "test_reconstruction_error",
            "threshold",
            "flagged_count",
            "flagged_percentage",
            "training_seconds",
            "split",
            "history",
        )
    }
    digest_after = sha256_file(source)
    payload = {
        "dataset": "demo_dataset.csv in-memory copy",
        "source_sha256_before": digest_before,
        "source_sha256_after": digest_after,
        "source_unchanged": digest_before == digest_after,
        "original_rows": int(len(original)),
        "working_rows": int(len(work)),
        "injections": {
            "missing_cells": [{"row": r, "column": c} for r, c in missing_cells],
            "duplicate_source_rows": duplicate_sources,
            "appended_duplicate_rows": injected_duplicate_rows,
            "outlier_rows": [
                {"row": r, "column": c, "value": v} for r, (c, v) in outlier_rows.items()
            ],
        },
        "natural_missing_cells_in_source": [
            {"row": r, "column": c} for r, c in natural_missing
        ],
        "statistical_audit_on_corrupted_copy": {
            "missing_cells": audit["missing"]["missing_cells"],
            "missing_percentage": audit["missing"]["missing_percentage"],
            "duplicate_rows": audit["duplicates"]["duplicate_rows"],
            "duplicate_percentage": audit["duplicates"]["duplicate_percentage"],
        },
        "detectors": {
            "missing_values": missing_metrics,
            "duplicate_rows": dup_metrics,
            "autoencoder_outliers": outlier_metrics,
            "modified_zscore_outliers": baseline_metrics,
        },
        "autoencoder": public_model,
        "notes": [
            "Synthetic corruption lives only in the working copy.",
            "Injected labels were not used to train the network or set its threshold.",
            "False positives against the synthetic labels can be natural quirks of the demo file.",
        ],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
