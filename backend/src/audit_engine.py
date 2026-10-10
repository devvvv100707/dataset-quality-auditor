"""Coordinate read-only audits. Source frames stay unchanged."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.autoencoder import public_model_result, train_autoencoder
from src.evaluation import unsupervised_summary
from src.quality_checks import run_statistical_checks
from src.report_generator import build_report


def audit_frame(
    frame: pd.DataFrame,
    target: str | None = None,
    underrepresented_fraction: float = 0.05,
) -> dict[str, Any]:
    before = frame.copy(deep=True)
    checks = run_statistical_checks(frame, target, underrepresented_fraction)
    if not frame.equals(before):
        raise RuntimeError("Statistical checks modified the dataset.")
    return checks


def train_on_frame(frame: pd.DataFrame) -> dict[str, Any]:
    before = pd.util.hash_pandas_object(frame, index=True).to_numpy().copy()
    result = train_autoencoder(frame)
    after = pd.util.hash_pandas_object(frame, index=True).to_numpy()
    if not (before == after).all():
        raise RuntimeError("Training modified the dataset.")
    return result


def evaluation_for(model: dict[str, Any] | None) -> dict[str, Any]:
    return unsupervised_summary(public_model_result(model) if model else None)


def full_report(dataset_meta: dict[str, Any], audit: dict | None, model: dict | None) -> dict:
    public = public_model_result(model) if model else None
    return build_report(dataset_meta, audit, public, evaluation_for(model))
