import numpy as np
import pandas as pd

from src.autoencoder import train_autoencoder
from src.data_loader import load_csv_path, demo_csv_path
from src.report_generator import build_report, report_to_csv


def test_training_flags_extreme_row_without_using_labels():
    rng = np.random.default_rng(0)
    n = 80
    frame = pd.DataFrame(
        {
            "a": rng.normal(0, 1, n),
            "b": rng.normal(5, 1, n),
            "c": rng.normal(-2, 0.5, n),
        }
    )
    frame.loc[5, "a"] = 80
    before = frame.copy(deep=True)
    result = train_autoencoder(frame, max_epochs=15, patience=4)
    pd.testing.assert_frame_equal(frame, before)
    assert result["status"] == "trained"
    assert result["architecture"]["input"] == 3
    assert result["threshold"]["labels_used"] is False
    assert result["training_seconds"] >= 0
    flagged_rows = [row["row_index"] for row in result["suspicious_records"] if row["flagged"]]
    assert 5 in flagged_rows
    errors = result["_errors"]
    assert np.isfinite(errors).all()


def test_too_few_rows_returns_limitation():
    frame = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [1.0, 1.0, 1.0]})
    result = train_autoencoder(frame)
    assert result["status"] == "skipped"
    assert result["metrics_available"] is False
    assert "limitation" in result


def test_no_numeric_features():
    frame = pd.DataFrame({"city": ["a", "b", "c"] * 20})
    result = train_autoencoder(frame)
    assert result["status"] == "skipped"
    assert result["metrics_available"] is False


def test_report_contains_findings_not_full_dataset():
    frame = load_csv_path(demo_csv_path())
    from src.audit_engine import audit_frame

    audit = audit_frame(frame, "program")
    model = train_autoencoder(frame, max_epochs=8, patience=3)
    report = build_report(
        {"id": "demo", "name": "demo_dataset.csv", "rows": len(frame), "columns": frame.shape[1]},
        audit,
        {k: v for k, v in model.items() if not k.startswith("_") and k != "scaling"},
        {"supervised_metrics_available": False},
    )
    text = report_to_csv(report)
    assert "export" in report["export_note"].lower() or "not a cleaned" in report["export_note"]
    assert "student_id" not in text or "S001" not in text
    assert "suggestion" in text
    assert report["checks"]["missing"]["missing_cells"] == 3
