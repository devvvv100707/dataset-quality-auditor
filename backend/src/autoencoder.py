"""Small fully connected autoencoder for numerical reconstruction error."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch import nn

SEED = 42
DEFAULT_HIDDEN = (8, 4)
MAX_EPOCHS = 40
PATIENCE = 6
LEARNING_RATE = 1e-3
BATCH_SIZE = 32
THRESHOLD_PERCENTILE = 95
MIN_ELIGIBLE_ROWS = 30


class Autoencoder(nn.Module):
    def __init__(self, n_features: int, hidden_dims: tuple[int, int] = DEFAULT_HIDDEN):
        super().__init__()
        hidden, bottleneck = hidden_dims
        self.encoder = nn.Sequential(
            nn.Linear(n_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, bottleneck),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_features),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(inputs))


@dataclass
class PreparedMatrix:
    features: list[str]
    excluded: list[dict[str, str]]
    row_positions: np.ndarray
    values: np.ndarray


def select_model_matrix(frame: pd.DataFrame) -> PreparedMatrix:
    """Build a model matrix from a copy. Infinite values become missing here only."""
    excluded: list[dict[str, str]] = []
    features: list[str] = []
    columns: list[np.ndarray] = []
    for name in frame.columns:
        series = frame[name]
        if not pd.api.types.is_numeric_dtype(series):
            continue
        values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
        values = values.copy()
        finite = np.isfinite(values)
        if not finite.any():
            excluded.append({"column": name, "reason": "No finite numeric values."})
            continue
        values[~np.isfinite(values)] = np.nan
        observed = values[~np.isnan(values)]
        if np.nanstd(observed) == 0 or len(np.unique(observed)) <= 1:
            excluded.append({"column": name, "reason": "Constant or zero-variance feature."})
            continue
        features.append(name)
        columns.append(values)
    if not features:
        return PreparedMatrix([], excluded, np.array([], dtype=int), np.empty((0, 0)))
    matrix = np.column_stack(columns)
    eligible = ~np.isnan(matrix).all(axis=1)
    positions = np.flatnonzero(eligible)
    return PreparedMatrix(features, excluded, positions, matrix[eligible])


def _impute_with_train_medians(train: np.ndarray, others: list[np.ndarray]) -> tuple[np.ndarray, list[np.ndarray], np.ndarray]:
    medians = np.nanmedian(train, axis=0)
    medians = np.where(np.isnan(medians), 0.0, medians)

    def fill(block: np.ndarray) -> np.ndarray:
        out = block.copy()
        inds = np.where(np.isnan(out))
        out[inds] = np.take(medians, inds[1])
        return out

    return fill(train), [fill(block) for block in others], medians


def _standardize(train: np.ndarray, others: list[np.ndarray]) -> tuple[np.ndarray, list[np.ndarray], np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    std = train.std(axis=0)
    std = np.where(std < 1e-8, 1.0, std)

    def scale(block: np.ndarray) -> np.ndarray:
        return (block - mean) / std

    return scale(train), [scale(block) for block in others], mean, std


def _batches(x: np.ndarray, batch_size: int, rng: np.random.Generator):
    order = rng.permutation(len(x))
    for start in range(0, len(x), batch_size):
        yield x[order[start : start + batch_size]]


def reconstruction_mse(model: nn.Module, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        tensor = torch.tensor(x, dtype=torch.float32)
        pred = model(tensor).numpy()
    return np.mean((pred - x) ** 2, axis=1)


def feature_squared_error(model: nn.Module, x: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        tensor = torch.tensor(x, dtype=torch.float32)
        pred = model(tensor).numpy()
    return (pred - x) ** 2


def train_autoencoder(
    frame: pd.DataFrame,
    hidden_dims: tuple[int, int] = DEFAULT_HIDDEN,
    seed: int = SEED,
    max_epochs: int = MAX_EPOCHS,
    patience: int = PATIENCE,
    learning_rate: float = LEARNING_RATE,
    threshold_percentile: float = THRESHOLD_PERCENTILE,
) -> dict[str, Any]:
    """Fit on a temporary numeric matrix. `frame` is not written back to."""
    started = time.perf_counter()
    prepared = select_model_matrix(frame)
    limitation = None
    if len(prepared.features) < 1:
        return {
            "status": "skipped",
            "limitation": "No usable numerical features. The autoencoder was not trained.",
            "excluded_columns": prepared.excluded,
            "architecture": None,
            "metrics_available": False,
        }
    n_rows = len(prepared.row_positions)
    if n_rows < MIN_ELIGIBLE_ROWS:
        return {
            "status": "skipped",
            "limitation": (
                f"Only {n_rows} eligible numerical rows. At least {MIN_ELIGIBLE_ROWS} "
                "are required, so the autoencoder was not trained and no metrics were invented."
            ),
            "excluded_columns": prepared.excluded,
            "eligible_rows": n_rows,
            "features": prepared.features,
            "architecture": None,
            "metrics_available": False,
        }

    torch.manual_seed(seed)
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    indices = np.arange(n_rows)
    train_idx, temp_idx = train_test_split(indices, test_size=0.4, random_state=seed)
    val_idx, test_idx = train_test_split(temp_idx, test_size=0.5, random_state=seed)

    raw = prepared.values
    train_raw = raw[train_idx]
    val_raw = raw[val_idx]
    test_raw = raw[test_idx]
    train_imp, (val_imp, test_imp, all_imp), medians = _impute_with_train_medians(
        train_raw, [val_raw, test_raw, raw]
    )
    train_x, (val_x, test_x, all_x), mean, std = _standardize(train_imp, [val_imp, test_imp, all_imp])

    model = Autoencoder(len(prepared.features), hidden_dims)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.MSELoss()
    history: list[dict[str, float]] = []
    best_state = None
    best_val = float("inf")
    wait = 0
    for epoch in range(1, max_epochs + 1):
        model.train()
        losses = []
        for batch in _batches(train_x, BATCH_SIZE, rng):
            tensor = torch.tensor(batch, dtype=torch.float32)
            optimizer.zero_grad()
            loss = loss_fn(model(tensor), tensor)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        train_loss = float(np.mean(losses))
        val_errors = reconstruction_mse(model, val_x)
        val_loss = float(np.mean(val_errors))
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
        if val_loss + 1e-8 < best_val:
            best_val = val_loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)

    val_errors = reconstruction_mse(model, val_x)
    test_errors = reconstruction_mse(model, test_x)
    all_errors = reconstruction_mse(model, all_x)
    threshold = float(np.percentile(val_errors, threshold_percentile))
    flagged_local = all_errors > threshold
    contributions = feature_squared_error(model, all_x)
    order = np.argsort(-all_errors)
    top = []
    for local in order[:15]:
        if not flagged_local[local] and len(top) >= 8:
            break
        source_row = int(prepared.row_positions[local])
        contrib = contributions[local]
        ranked = np.argsort(-contrib)[: min(5, len(prepared.features))]
        top.append(
            {
                "row_index": source_row,
                "reconstruction_error": float(all_errors[local]),
                "flagged": bool(flagged_local[local]),
                "feature_contributions": [
                    {"feature": prepared.features[int(j)], "squared_error": float(contrib[int(j)])}
                    for j in ranked
                ],
            }
        )

    histogram = _histogram(all_errors)
    duration = time.perf_counter() - started
    return {
        "status": "trained",
        "metrics_available": True,
        "limitation": limitation,
        "seed": seed,
        "features": prepared.features,
        "excluded_columns": prepared.excluded,
        "eligible_rows": n_rows,
        "split": {
            "train": int(len(train_idx)),
            "validation": int(len(val_idx)),
            "test": int(len(test_idx)),
        },
        "architecture": {
            "type": "fully_connected_autoencoder",
            "input": len(prepared.features),
            "hidden": list(hidden_dims),
            "bottleneck": hidden_dims[-1],
            "layers": [
                f"Linear({len(prepared.features)}, {hidden_dims[0]})",
                "ReLU",
                f"Linear({hidden_dims[0]}, {hidden_dims[1]})",
                f"Linear({hidden_dims[1]}, {hidden_dims[0]})",
                "ReLU",
                f"Linear({hidden_dims[0]}, {len(prepared.features)})",
            ],
            "loss": "MSE",
            "optimizer": "Adam",
            "learning_rate": learning_rate,
            "max_epochs": max_epochs,
            "epochs_ran": len(history),
            "early_stopping_patience": patience,
        },
        "history": history,
        "train_loss": history[-1]["train_loss"] if history else None,
        "best_val_loss": best_val if best_state is not None else None,
        "final_val_loss": history[-1]["val_loss"] if history else None,
        "test_reconstruction_error": {
            "mean": float(np.mean(test_errors)),
            "std": float(np.std(test_errors)),
            "min": float(np.min(test_errors)),
            "max": float(np.max(test_errors)),
            "median": float(np.median(test_errors)),
        },
        "threshold": {
            "method": f"{threshold_percentile}th percentile of validation reconstruction MSE",
            "value": threshold,
            "labels_used": False,
        },
        "flagged_count": int(flagged_local.sum()),
        "flagged_percentage": round(100.0 * float(flagged_local.mean()), 4),
        "error_histogram": histogram,
        "suspicious_records": top,
        "training_seconds": duration,
        "interpretation": (
            "Flagged records are potential anomalies that need human verification. "
            "A high reconstruction error is not automatically a data error."
        ),
        "imputation_note": (
            "Missing and non-finite numbers were filled with training-set medians "
            "only inside the temporary model matrix. The stored dataset was not changed."
        ),
        "scaling": {"mean": mean.tolist(), "std": std.tolist(), "train_medians": medians.tolist()},
        "_errors": all_errors,
        "_flagged_local": flagged_local,
        "_row_positions": prepared.row_positions,
        "_model_state": {k: v.detach().cpu() for k, v in model.state_dict().items()},
    }


def _histogram(errors: np.ndarray, bins: int = 12) -> list[dict[str, float]]:
    if len(errors) == 0:
        return []
    counts, edges = np.histogram(errors, bins=bins)
    rows = []
    for count, left, right in zip(counts, edges[:-1], edges[1:]):
        rows.append(
            {
                "bin_start": float(left),
                "bin_end": float(right),
                "count": int(count),
            }
        )
    return rows


def public_model_result(result: dict[str, Any]) -> dict[str, Any]:
    hidden = {"_errors", "_flagged_local", "_row_positions", "_model_state", "scaling"}
    return {key: value for key, value in result.items() if key not in hidden}
