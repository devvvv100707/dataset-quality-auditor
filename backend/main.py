"""FastAPI application for the dataset quality auditor."""

from __future__ import annotations

import json
from pathlib import Path

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from src.audit_engine import audit_frame, evaluation_for, full_report, train_on_frame
from src.autoencoder import public_model_result
from src.data_loader import DataLoadError
from src.report_generator import report_to_csv
from src.session import get_session, load_demo, load_upload, original_frame

app = FastAPI(
    title="AI Dataset Quality Auditor",
    description=(
        "Inspects tabular CSV files for missing values, duplicate rows, "
        "class imbalance, and numerical reconstruction anomalies. "
        "It never modifies the uploaded dataset."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_DIR = Path(__file__).resolve().parent / "models"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


class AuditRequest(BaseModel):
    target: str | None = None
    underrepresented_fraction: float = Field(default=0.05, gt=0, lt=1)


def _session_or_404(dataset_id: str) -> dict:
    session = get_session(dataset_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown dataset id.")
    return session


def _summary(session: dict) -> dict:
    return {
        "id": session["id"],
        "name": session["name"],
        "rows": session["rows"],
        "columns": session["columns"],
        "byte_size": session.get("byte_size"),
        "column_names": session["column_names"],
        "audited": session["audit"] is not None,
        "model_trained": bool(session["model"] and session["model"].get("status") == "trained"),
    }


def _save_artifact(dataset_id: str, model: dict) -> None:
    if model.get("status") != "trained" or "_model_state" not in model:
        return
    folder = MODELS_DIR / dataset_id
    folder.mkdir(parents=True, exist_ok=True)
    torch.save(model["_model_state"], folder / "autoencoder.pt")
    meta = public_model_result(model)
    meta["artifact_id"] = dataset_id
    (folder / "metadata.json").write_text(json.dumps(meta, indent=2))


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "dataset-quality-auditor"}


@app.get("/api/demo")
def demo() -> dict:
    session = load_demo()
    return _summary(session)


@app.post("/api/datasets/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    filename = file.filename or "upload.csv"
    payload = await file.read()
    try:
        session = load_upload(filename, payload)
    except DataLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _summary(session)


@app.get("/api/datasets/{dataset_id}/profile")
def profile(dataset_id: str) -> dict:
    session = _session_or_404(dataset_id)
    frame = original_frame(dataset_id)
    from src.quality_checks import profile_dataset

    return {"dataset": _summary(session), "profile": profile_dataset(frame)}


@app.post("/api/datasets/{dataset_id}/audit")
def audit(dataset_id: str, body: AuditRequest) -> dict:
    session = _session_or_404(dataset_id)
    frame = original_frame(dataset_id)
    result = audit_frame(frame, body.target, body.underrepresented_fraction)
    session["audit"] = result
    return {"dataset": _summary(session), "audit": result}


@app.post("/api/datasets/{dataset_id}/model/train")
def train(dataset_id: str) -> dict:
    session = _session_or_404(dataset_id)
    frame = original_frame(dataset_id)
    try:
        result = train_on_frame(frame)
    except Exception as exc:  # training failure stays a client-visible error
        raise HTTPException(status_code=422, detail=f"Training failed: {exc}") from exc
    session["model"] = result
    _save_artifact(dataset_id, result)
    return {"dataset": _summary(session), "model": public_model_result(result)}


@app.get("/api/datasets/{dataset_id}/model/results")
def model_results(dataset_id: str) -> dict:
    session = _session_or_404(dataset_id)
    if session["model"] is None:
        raise HTTPException(status_code=404, detail="This dataset has no trained model yet.")
    artifact = MODELS_DIR / dataset_id / "metadata.json"
    if session["model"].get("status") == "trained" and not artifact.exists():
        raise HTTPException(status_code=409, detail="Model artifact is missing for this dataset.")
    return {"dataset": _summary(session), "model": public_model_result(session["model"])}


@app.get("/api/datasets/{dataset_id}/evaluation")
def evaluation(dataset_id: str) -> dict:
    session = _session_or_404(dataset_id)
    return {
        "dataset": _summary(session),
        "evaluation": evaluation_for(session["model"]),
        "experiment": _load_experiment_file(),
    }


@app.get("/api/datasets/{dataset_id}/report")
def report(dataset_id: str) -> JSONResponse:
    session = _session_or_404(dataset_id)
    payload = full_report(
        {"id": session["id"], "name": session["name"], "rows": session["rows"], "columns": session["columns"]},
        session["audit"],
        session["model"],
    )
    return JSONResponse(payload)


@app.get("/api/datasets/{dataset_id}/report.csv")
def report_csv(dataset_id: str) -> PlainTextResponse:
    session = _session_or_404(dataset_id)
    payload = full_report(
        {"id": session["id"], "name": session["name"], "rows": session["rows"], "columns": session["columns"]},
        session["audit"],
        session["model"],
    )
    return PlainTextResponse(report_to_csv(payload), media_type="text/csv")


@app.get("/api/experiments/latest")
def latest_experiment() -> dict:
    return _load_experiment_file()


def _load_experiment_file() -> dict:
    path = REPORTS_DIR / "experiment_results.json"
    if not path.exists():
        return {
            "available": False,
            "reason": "backend/reports/experiment_results.json has not been generated.",
        }
    data = json.loads(path.read_text())
    data["available"] = True
    data["source"] = "controlled in-memory experiment"
    return data
