"""Metrics for reconstruction results and labeled experiments."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def binary_detection_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray | None = None) -> dict[str, Any]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    if len(y_true) == 0:
        return {"available": False, "reason": "No rows to score."}
    if len(np.unique(y_true)) < 2:
        matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
        return {
            "available": False,
            "reason": "Ground truth has only one class, so discrimination metrics were not computed.",
            "confusion_matrix": {"labels": ["normal", "positive"], "matrix": matrix},
            "support_positive": int(y_true.sum()),
            "predicted_positive": int(y_pred.sum()),
        }
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    negatives = tn + fp
    payload: dict[str, Any] = {
        "available": True,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": float(fp / negatives) if negatives else None,
        "confusion_matrix": {
            "labels": ["normal", "positive"],
            "matrix": matrix.tolist(),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }
    if y_score is not None:
        score = np.asarray(y_score, dtype=float)
        try:
            payload["roc_auc"] = float(roc_auc_score(y_true, score))
        except ValueError:
            payload["roc_auc"] = None
        try:
            payload["average_precision"] = float(average_precision_score(y_true, score))
        except ValueError:
            payload["average_precision"] = None
    return payload


def unsupervised_summary(model_result: dict[str, Any] | None) -> dict[str, Any]:
    if not model_result or model_result.get("status") != "trained":
        return {
            "supervised_metrics_available": False,
            "reason": "No ground-truth labels are available for this dataset.",
            "model_status": None if not model_result else model_result.get("status"),
            "limitation": None if not model_result else model_result.get("limitation"),
        }
    return {
        "supervised_metrics_available": False,
        "reason": (
            "This uploaded dataset has no anomaly ground truth. "
            "Precision, recall, F1, and ROC-AUC are not reported for it. "
            "Reconstruction statistics below were measured on the held-out split."
        ),
        "train_loss": model_result.get("train_loss"),
        "best_val_loss": model_result.get("best_val_loss"),
        "test_reconstruction_error": model_result.get("test_reconstruction_error"),
        "threshold": model_result.get("threshold"),
        "flagged_count": model_result.get("flagged_count"),
        "flagged_percentage": model_result.get("flagged_percentage"),
        "training_seconds": model_result.get("training_seconds"),
        "epochs_ran": (model_result.get("architecture") or {}).get("epochs_ran"),
    }
