import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_loader import DataLoadError, demo_csv_path, load_csv_bytes, load_csv_path
from src.quality_checks import class_balance, duplicate_rows, missing_values, profile_dataset, run_statistical_checks

DEMO = demo_csv_path()


def test_demo_profile_and_known_issues():
    frame = load_csv_path(DEMO)
    profile = profile_dataset(frame)
    assert profile["rows"] == 120
    assert profile["columns"] == 10
    assert "study_hours" in profile["numerical_columns"]
    assert "program" in profile["categorical_columns"]
    missing = missing_values(frame)
    assert missing["missing_cells"] == 3
    duplicates = duplicate_rows(frame)
    assert duplicates["duplicate_rows"] == 2
    balance = class_balance(frame, "program")
    labels = {item["label"] for item in balance["underrepresented"]}
    assert "Biology" in labels


def test_checks_do_not_mutate_frame():
    frame = load_csv_path(DEMO)
    before = frame.copy(deep=True)
    run_statistical_checks(frame, "program")
    pd.testing.assert_frame_equal(frame, before)


def test_empty_and_malformed_csv():
    try:
        load_csv_bytes(b"", "empty.csv")
        raise AssertionError("expected error")
    except DataLoadError:
        pass
    try:
        load_csv_bytes(b'name,score\n"unterminated,1\n', "bad.csv")
        raise AssertionError("expected error")
    except DataLoadError:
        pass


def test_infinite_and_constant_columns():
    frame = pd.DataFrame(
        {
            "value": [1.0, np.inf, 3.0, -np.inf],
            "steady": [5, 5, 5, 5],
            "label": ["a", "a", "b", "b"],
        }
    )
    profile = profile_dataset(frame)
    assert profile["infinite_values"]["value"] == 2
    assert "steady" in profile["constant_columns"]
    skipped = class_balance(frame, "missing_target")
    assert skipped["status"] == "skipped"


def test_demo_file_hash_stable_after_read():
    digest = hashlib.sha256(DEMO.read_bytes()).hexdigest()
    load_csv_path(DEMO)
    assert hashlib.sha256(Path(DEMO).read_bytes()).hexdigest() == digest
