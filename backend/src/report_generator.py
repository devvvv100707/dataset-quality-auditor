"""Build audit reports that contain findings, not a rewritten dataset."""

from __future__ import annotations

import csv
import io
from typing import Any


def suggestions(audit: dict[str, Any], model: dict[str, Any] | None) -> list[str]:
    notes = [
        "Suggestions are informational. This auditor does not modify, impute, or delete source rows."
    ]
    missing = (audit or {}).get("missing") or {}
    for column in missing.get("top_columns") or []:
        notes.append(
            f"Column '{column['column']}' has {column['count']} missing values "
            f"({column['percentage']}% of rows). A reviewer could check collection or encoding. "
            "The file was not filled in."
        )
    duplicates = (audit or {}).get("duplicates") or {}
    if duplicates.get("duplicate_rows"):
        notes.append(
            f"{duplicates['duplicate_rows']} rows participate in exact duplicate groups. "
            "Review whether repeated records are intentional. None were deleted."
        )
    balance = (audit or {}).get("class_balance") or {}
    for item in balance.get("underrepresented") or []:
        notes.append(
            f"Class '{item['label']}' in '{balance.get('target')}' is {item['percentage']}% of rows. "
            "Confirm whether that share matches the population."
        )
    profile = (audit or {}).get("profile") or {}
    for name in profile.get("constant_columns") or []:
        notes.append(f"Column '{name}' is constant. It cannot separate records.")
    if model and model.get("status") == "trained" and model.get("flagged_count"):
        notes.append(
            f"{model['flagged_count']} records exceed the validation reconstruction threshold. "
            "Treat them as candidates for human review, not confirmed errors."
        )
    if model and model.get("limitation"):
        notes.append(str(model["limitation"]))
    return notes


def limitations(audit: dict[str, Any] | None, model: dict[str, Any] | None) -> list[str]:
    items = [
        "The autoencoder flags unusual numerical combinations. It does not prove a value is wrong.",
        "Threshold selection uses the validation error percentile and ignores any anomaly labels.",
        "Missing numbers are median-filled only inside the temporary model matrix.",
        "Categorical columns are profiled and used for class balance, not reconstructed by the autoencoder.",
        "Supervised scores exist only for the controlled experiment, which uses a separate in-memory copy.",
    ]
    if model and model.get("limitation"):
        items.append(str(model["limitation"]))
    if audit and (audit.get("class_balance") or {}).get("status") == "skipped":
        items.append(audit["class_balance"].get("reason") or "Class balance was skipped.")
    return items


def build_report(
    dataset: dict[str, Any],
    audit: dict[str, Any] | None,
    model: dict[str, Any] | None,
    evaluation: dict[str, Any] | None,
) -> dict[str, Any]:
    public_model = None
    if model:
        public_model = {
            key: model[key]
            for key in (
                "status",
                "limitation",
                "seed",
                "features",
                "excluded_columns",
                "eligible_rows",
                "split",
                "architecture",
                "train_loss",
                "best_val_loss",
                "final_val_loss",
                "test_reconstruction_error",
                "threshold",
                "flagged_count",
                "flagged_percentage",
                "suspicious_records",
                "training_seconds",
                "interpretation",
                "imputation_note",
                "metrics_available",
            )
            if key in model
        }
    return {
        "dataset": {
            "id": dataset.get("id"),
            "name": dataset.get("name"),
            "rows": dataset.get("rows"),
            "columns": dataset.get("columns"),
        },
        "profile": None if not audit else audit.get("profile"),
        "checks": None
        if not audit
        else {
            "missing": audit.get("missing"),
            "duplicates": audit.get("duplicates"),
            "class_balance": audit.get("class_balance"),
        },
        "model": public_model,
        "evaluation": evaluation,
        "manual_review_suggestions": suggestions(audit or {}, model),
        "limitations": limitations(audit, model),
        "export_note": "This file lists findings and metadata only. It is not a cleaned dataset.",
    }


def report_to_csv(report: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "key", "value"])
    dataset = report.get("dataset") or {}
    for key, value in dataset.items():
        writer.writerow(["dataset", key, value])
    checks = report.get("checks") or {}
    missing = checks.get("missing") or {}
    writer.writerow(["missing", "missing_cells", missing.get("missing_cells")])
    writer.writerow(["missing", "missing_percentage", missing.get("missing_percentage")])
    for column in missing.get("top_columns") or []:
        writer.writerow(["missing_column", column.get("column"), column.get("count")])
    duplicates = checks.get("duplicates") or {}
    writer.writerow(["duplicates", "duplicate_rows", duplicates.get("duplicate_rows")])
    writer.writerow(["duplicates", "duplicate_percentage", duplicates.get("duplicate_percentage")])
    model = report.get("model") or {}
    writer.writerow(["model", "status", model.get("status")])
    threshold = model.get("threshold") or {}
    writer.writerow(["model", "threshold", threshold.get("value")])
    writer.writerow(["model", "flagged_count", model.get("flagged_count")])
    writer.writerow(["model", "training_seconds", model.get("training_seconds")])
    for record in model.get("suspicious_records") or []:
        writer.writerow(
            [
                "suspicious_record",
                record.get("row_index"),
                record.get("reconstruction_error"),
            ]
        )
    for note in report.get("manual_review_suggestions") or []:
        writer.writerow(["suggestion", "", note])
    for note in report.get("limitations") or []:
        writer.writerow(["limitation", "", note])
    evaluation = report.get("evaluation") or {}
    writer.writerow(
        [
            "evaluation",
            "supervised_metrics_available",
            evaluation.get("supervised_metrics_available"),
        ]
    )
    return buffer.getvalue()
