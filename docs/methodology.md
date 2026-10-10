# Methodology

Numbers in this note come from `python experiments/run_experiments.py` and `pytest` in `backend/`. The written experiment file is `backend/reports/experiment_results.json`.

## What is measured

Statistical checks count missing cells, exact duplicate rows, column types, constant columns, non-finite values, and class shares. Nothing is deleted or filled in the stored table.

The deep model is a fully connected autoencoder. On the corrupted experiment copy the usable numerical columns were `age`, `study_hours`, `attendance_pct`, `prior_gpa`, `sleep_hours`, `assignments_submitted`, `lab_score`, and `year` (8 inputs). Architecture: Linear(8, 8), ReLU, Linear(8, 4) bottleneck, Linear(4, 8), ReLU, Linear(8, 8). Seed 42, Adam, learning rate 0.001, MSE, max 40 epochs, patience 6. The run stopped after 7 epochs. Training took 0.7271669089999477 seconds. Split: 73 train, 25 validation, 25 test. Median imputation and standardization were fit on the training split only, inside a temporary matrix.

Final training loss was 1.0029680927594502. Best validation loss was 54.66534434238061. Test reconstruction MSE: mean 6.236375967458807, std 27.12949772366556, min 0.1275288595753607, median 0.6641319283980546, max 139.12832003919064. Threshold (95th percentile of validation reconstruction MSE, labels unused) was 1.7251438340344465. The model flagged 8 rows, 6.5041% of eligible rows.

The high validation loss is expected when a random split places an injected outlier in validation. The threshold was still taken from that validation distribution and was not tuned on the labels.

## Controlled injections

The script copied `demo_dataset.csv` in memory (120 rows). It set 8 cells to missing, appended 3 exact copies of rows 0, 1, and 2, and overwrote five numeric cells:

| Row | Column | Injected value |
| --- | --- | --- |
| 20 | lab_score | 5000 |
| 21 | age | -40 |
| 22 | study_hours | 400 |
| 23 | prior_gpa | 40 |
| 24 | sleep_hours | 30 |

Source SHA-256 before and after the run was `9dcc13988492b6a50a75d770328ccdb47bca749ef05636d68f41f0c8b6283c22`. `source_unchanged` was true.

On the corrupted copy, statistical checks reported 11 missing cells (0.8943%) and 8 duplicate-group rows (6.5041%).

## Detector scores

Labels were applied only at scoring time.

Missing cells (null means detected; the 3 natural missing cells are false positives):

- true positives 8, false positives 3, false negatives 0
- precision 0.7272727272727273, recall 1.0, F1 0.8421052631578948

Appended duplicate rows:

- confusion matrix tn 115, fp 5, fn 0, tp 3
- precision 0.375, recall 1.0, F1 0.5454545454545454, FPR 0.041666666666666664
- The 5 false positives are the original partners of the appended rows plus the natural duplicate pair.

Autoencoder versus the five injected outlier rows:

- confusion matrix tn 115, fp 3, fn 0, tp 5
- precision 0.625, recall 1.0, F1 0.7692307692307693, FPR 0.025423728813559324
- ROC-AUC 1.0, average precision 1.0
- flagged injected rows: 20, 21, 22, 23, 24
- flagged non-injected rows: 11, 16, 94

Modified z-score baseline (median and MAD on the training split, cutoff 3.5, not tuned on labels):

- confusion matrix tn 116, fp 2, fn 0, tp 5
- precision 0.7142857142857143, recall 1.0, F1 0.8333333333333334, FPR 0.01694915254237288
- ROC-AUC 1.0, average precision 1.0

On an ordinary upload there is no anomaly ground truth. The API sets `supervised_metrics_available` to false and returns reconstruction statistics only.

## Pytest

`python -m pytest -q` reported `12 passed`.

## Limitations

- Reconstruction error is not proof that a cell is wrong.
- Categorical columns are not reconstructed.
- Constant, empty, or non-finite numerical columns are dropped from the model and named in the report.
- Fewer than 30 eligible rows skips training and does not invent metrics.
- Injected outliers can land in the validation split and dominate validation loss.
- Synthetic scores describe the corrupted copy, not the original demo file.
- The modified z-score baseline was stronger than the autoencoder on this particular injection (F1 0.8333 versus 0.7692) because the corruptions are single-column extremes.
