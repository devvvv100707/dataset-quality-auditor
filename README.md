# AI Dataset Quality Auditor Using Deep Learning

A local, CPU-only auditor for small CSV datasets. It measures missing values, exact duplicate rows, class imbalance, and numerical reconstruction error with a PyTorch autoencoder. It never imputes, deletes, relabels, or exports a cleaned dataset.

The interface is at http://localhost:5173. The API and OpenAPI docs are at http://localhost:8000 and http://localhost:8000/docs.

## Setup on macOS

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Start the API in one terminal:

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite serves http://localhost:5173 and calls the API at http://localhost:8000.

## Experiments and tests

```bash
source .venv/bin/activate
cd backend
python experiments/run_experiments.py
pytest
```

The experiment reads `backend/data/demo_dataset.csv`, corrupts an in-memory copy, and writes `backend/reports/experiment_results.json`. The demo file is not rewritten. Pytest checks quality rules, training, reports, and the API, and asserts the demo file hash is unchanged.

## Stop the servers

In each terminal, press `Ctrl+C`.

## Demo data

`backend/data/demo_dataset.csv` is a 120-row student-records file with 10 columns: `student_id`, `age`, `study_hours`, `attendance_pct`, `prior_gpa`, `sleep_hours`, `assignments_submitted`, `lab_score`, `program`, and `year`. It includes a few natural missing cells, one repeated row, and an underrepresented `Biology` class. No download is required.

### Optional larger file

For a separate offline exercise you can download the UCI Adult dataset (also called Census Income) from https://archive.ics.uci.edu/dataset/2/adult and the Bank Marketing dataset from https://archive.ics.uci.edu/dataset/222/bank+marketing. Both are maintained by the UCI Machine Learning Repository. Convert the chosen file to CSV yourself, then upload it. The app does not fetch them.

## Model

For a dataset with 8 usable numerical columns the network is:

`Linear(8, 8) → ReLU → Linear(8, 4) → Linear(4, 8) → ReLU → Linear(8, 8)`

Loss is MSE. Optimizer is Adam with learning rate `0.001`. Seed is `42`. Maximum epochs are `40`, with early stopping patience `6`. Hidden sizes are `(8, 4)`. The threshold is the 95th percentile of validation reconstruction MSE. A new dataset gets a new in-memory model and an artifact id under `backend/models/`.

## Methodology and limitations

See [docs/methodology.md](docs/methodology.md). Flagged rows are potential anomalies for human review, not confirmed errors. Supervised precision, recall, and F1 are reported only for the controlled experiment.

## Troubleshooting

- Port already in use: stop the other process on 5173 or 8000, then start again.
- `uvicorn` not found: activate `.venv` before starting the API.
- Upload rejected: use a UTF-8 `.csv` under 2 MB, with a header row, at most 20,000 rows and 80 columns, and unique column names.
- Training skipped: the autoencoder needs at least one varying numerical column and 30 eligible rows. The API returns that limitation instead of metrics.
- Frontend cannot reach the API: keep uvicorn on port 8000. The browser origin must be `http://localhost:5173` or `http://127.0.0.1:5173`.
- Torch install is large. This project expects the CPU wheel and does not use a GPU.
