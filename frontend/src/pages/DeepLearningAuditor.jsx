import { ErrorChart, LossChart } from "../components/Charts";
import DataTable from "../components/DataTable";
import { PageIntro } from "../components/Header";
import MetricCard from "../components/MetricCard";
import { useAudit } from "../context/AuditContext";

export default function DeepLearningAuditor() {
  const { model, busy, error } = useAudit();
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageIntro title="Deep Learning Auditor" subtitle="A fully connected autoencoder scores numerical rows. Flags need human verification." />
      <section className="max-w-3xl rounded-xl bg-white p-6 text-sm leading-6 text-[#4b5563] shadow-sm">
        <p>
          The auditor trains a fully connected autoencoder on numerical columns only. The encoder is
          Linear then ReLU into a bottleneck. The decoder mirrors it and is trained with mean squared
          error and Adam. Scaling statistics and median fills are fit on the training split of a
          temporary matrix. Records above the 95th percentile of validation reconstruction error are
          marked as potential anomalies for a person to check.
        </p>
      </section>
      {busy && <p className="text-sm text-primary">{busy}…</p>}
      {error && <p className="rounded-lg bg-[#ffdad6] px-3 py-2 text-sm text-[#93000a]">{error}</p>}
      {!model && <p className="text-sm text-muted">Start an audit from Overview to train a model for this dataset.</p>}
      {model?.status === "skipped" && (
        <p className="rounded-lg border border-line bg-white px-4 py-3 text-sm">{model.limitation}</p>
      )}
      {model?.status === "trained" && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Epochs ran" value={model.architecture.epochs_ran} detail={`Seed ${model.seed}`} />
            <MetricCard label="Best val MSE" value={Number(model.best_val_loss).toFixed(4)} />
            <MetricCard label="Threshold" value={Number(model.threshold.value).toFixed(4)} />
            <MetricCard
              label="Flagged"
              value={model.flagged_count}
              detail={`${model.flagged_percentage}% of eligible rows`}
            />
          </div>
          <p className="text-xs text-muted">
            Layers: {model.architecture.layers.join(" → ")}. {model.interpretation}
          </p>
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm font-semibold">Loss</h3>
              <LossChart history={model.history} />
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold">Reconstruction error</h3>
              <ErrorChart histogram={model.error_histogram} threshold={model.threshold.value} />
            </div>
          </div>
          <section>
            <h3 className="mb-2 text-sm font-semibold">Suspicious records</h3>
            <DataTable
              columns={[
                { key: "row_index", label: "Row" },
                {
                  key: "reconstruction_error",
                  label: "Error",
                  render: (value) => Number(value).toFixed(6),
                },
                { key: "flagged", label: "Flagged", render: (value) => (value ? "yes" : "no") },
                {
                  key: "feature_contributions",
                  label: "Top features",
                  render: (value) =>
                    (value || [])
                      .map((item) => `${item.feature} (${Number(item.squared_error).toFixed(3)})`)
                      .join(", "),
                },
              ]}
              rows={model.suspicious_records}
              searchKeys={["row_index", "flagged"]}
            />
          </section>
        </>
      )}
    </div>
  );
}
