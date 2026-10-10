import { PageIntro } from "../components/Header";
import MetricCard from "../components/MetricCard";
import { useAudit } from "../context/AuditContext";

function Matrix({ metrics }) {
  if (!metrics?.confusion_matrix) return null;
  const [top, bottom] = metrics.confusion_matrix.matrix;
  return (
    <table className="text-sm">
      <thead>
        <tr className="text-xs text-muted">
          <th className="px-2 py-1" />
          <th className="px-2 py-1">Pred normal</th>
          <th className="px-2 py-1">Pred positive</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td className="px-2 py-1 text-xs text-muted">Actual normal</td>
          <td className="px-2 py-1">{top[0]}</td>
          <td className="px-2 py-1">{top[1]}</td>
        </tr>
        <tr>
          <td className="px-2 py-1 text-xs text-muted">Actual positive</td>
          <td className="px-2 py-1">{bottom[0]}</td>
          <td className="px-2 py-1">{bottom[1]}</td>
        </tr>
      </tbody>
    </table>
  );
}

function Detector({ title, metrics }) {
  if (!metrics) return null;
  return (
    <section className="rounded-xl border border-line bg-white p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-xs text-muted">{metrics.definition || metrics.reason}</p>
      {metrics.available === false ? (
        <p className="mt-2 text-sm">Supervised metrics unavailable.</p>
      ) : (
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          <MetricCard label="Precision" value={fmt(metrics.precision)} />
          <MetricCard label="Recall" value={fmt(metrics.recall)} />
          <MetricCard label="F1" value={fmt(metrics.f1)} />
          <MetricCard label="ROC-AUC" value={metrics.roc_auc == null ? "n/a" : fmt(metrics.roc_auc)} />
        </div>
      )}
      <div className="mt-3">
        <Matrix metrics={metrics} />
      </div>
    </section>
  );
}

function fmt(value) {
  return typeof value === "number" ? value.toFixed(4) : "n/a";
}

export default function ResultsEvaluation() {
  const { evaluation, experiment, model } = useAudit();
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageIntro title="Results & Evaluation" subtitle="Supervised scores appear only when the controlled experiment file supplies ground truth." />
      <section className="rounded-xl border border-line bg-white p-4">
        <h3 className="text-sm font-semibold">This dataset</h3>
        {!evaluation && <p className="mt-2 text-sm text-muted">Run an audit to record reconstruction statistics.</p>}
        {evaluation && (
          <div className="mt-3 space-y-3">
            <p className="text-sm text-muted">{evaluation.reason || evaluation.limitation}</p>
            <p className="text-xs font-medium uppercase tracking-wide text-muted">
              Supervised metrics: {evaluation.supervised_metrics_available ? "available" : "unavailable"}
            </p>
            {model?.status === "trained" && (
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard label="Train loss" value={fmt(evaluation.train_loss)} />
                <MetricCard label="Best val loss" value={fmt(evaluation.best_val_loss)} />
                <MetricCard
                  label="Test MSE mean"
                  value={fmt(evaluation.test_reconstruction_error?.mean)}
                />
              </div>
            )}
          </div>
        )}
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold">Controlled experiment on an in-memory copy</h3>
        {!experiment?.available && (
          <p className="text-sm text-muted">{experiment?.reason || "Experiment results are not loaded."}</p>
        )}
        {experiment?.available && (
          <div className="space-y-4">
            <p className="text-sm text-muted">
              Source file unchanged: {String(experiment.source_unchanged)}. Working rows: {experiment.working_rows}.
              These scores use injected labels only after training.
            </p>
            <Detector title="Missing values" metrics={experiment.detectors.missing_values} />
            <Detector title="Duplicate rows" metrics={experiment.detectors.duplicate_rows} />
            <Detector title="Autoencoder outliers" metrics={experiment.detectors.autoencoder_outliers} />
            <Detector title="Modified z-score outliers" metrics={experiment.detectors.modified_zscore_outliers} />
            <div>
              <h4 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">Injected outliers</h4>
              <ul className="text-sm text-muted">
                {(experiment.injections?.outlier_rows || []).map((item) => (
                  <li key={`${item.row}-${item.column}`}>
                    Row {item.row} {item.column} = {item.value}. Flagged by autoencoder:{" "}
                    {experiment.detectors.autoencoder_outliers.flagged_injected_rows?.includes(item.row)
                      ? "yes"
                      : "no"}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </section>
      <section className="text-sm text-muted">
        <h3 className="mb-2 font-semibold text-ink">Limitations</h3>
        <ul className="list-disc space-y-1 pl-5">
          <li>Uploaded files have no anomaly labels, so precision and recall stay unavailable for them.</li>
          <li>A random split can place extreme rows in validation and inflate validation loss.</li>
          <li>The autoencoder does not score categorical fields.</li>
          <li>Synthetic metrics describe the corrupted copy, not the untouched demo file.</li>
        </ul>
      </section>
    </div>
  );
}
