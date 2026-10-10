import hashlib

from fastapi.testclient import TestClient

from main import app
from src.data_loader import demo_csv_path
from src.session import reset_sessions

client = TestClient(app)


def setup_function():
    reset_sessions()


def test_health_and_invalid_id():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    missing = client.get("/api/datasets/not-a-real-id/profile")
    assert missing.status_code == 404


def test_upload_validation_and_demo_roundtrip():
    empty = client.post(
        "/api/datasets/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert empty.status_code == 400
    demo_path = demo_csv_path()
    digest = hashlib.sha256(demo_path.read_bytes()).hexdigest()
    loaded = client.get("/api/demo")
    assert loaded.status_code == 200
    dataset_id = loaded.json()["id"]
    profile = client.get(f"/api/datasets/{dataset_id}/profile")
    assert profile.status_code == 200
    assert profile.json()["profile"]["rows"] == 120
    audit = client.post(f"/api/datasets/{dataset_id}/audit", json={"target": "program"})
    assert audit.status_code == 200
    assert audit.json()["audit"]["duplicates"]["duplicate_rows"] == 2
    trained = client.post(f"/api/datasets/{dataset_id}/model/train")
    assert trained.status_code == 200
    body = trained.json()["model"]
    assert body["status"] == "trained"
    assert body["threshold"]["labels_used"] is False
    results = client.get(f"/api/datasets/{dataset_id}/model/results")
    assert results.status_code == 200
    evaluation = client.get(f"/api/datasets/{dataset_id}/evaluation")
    assert evaluation.status_code == 200
    assert evaluation.json()["evaluation"]["supervised_metrics_available"] is False
    report = client.get(f"/api/datasets/{dataset_id}/report")
    assert report.status_code == 200
    assert "cleaned dataset" in report.json()["export_note"]
    csv_report = client.get(f"/api/datasets/{dataset_id}/report.csv")
    assert csv_report.status_code == 200
    assert "section,key,value" in csv_report.text
    assert hashlib.sha256(demo_path.read_bytes()).hexdigest() == digest


def test_model_results_before_training():
    loaded = client.get("/api/demo")
    dataset_id = loaded.json()["id"]
    response = client.get(f"/api/datasets/{dataset_id}/model/results")
    assert response.status_code == 404
