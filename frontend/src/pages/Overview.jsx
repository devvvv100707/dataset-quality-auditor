import FileUpload from "../components/FileUpload";
import MetricCard from "../components/MetricCard";
import { useAudit } from "../context/AuditContext";

export default function Overview() {
  const { dataset, profile, audit, model, busy, error, loadDemo, uploadFile, startAudit } = useAudit();
  return (
    <div className="space-y-6">
      <section className="max-w-3xl">
        <p className="text-sm leading-6 text-muted">
          This tool audits a tabular dataset. It measures missing values, exact duplicate rows, class
          imbalance, and numerical reconstruction error from a small PyTorch autoencoder. It does not
          impute, delete, relabel, or export a cleaned copy.
        </p>
      </section>
      <div className="grid gap-4 md:grid-cols-2">
        <FileUpload onFile={uploadFile} disabled={Boolean(busy)} />
        <button
          className="rounded-xl border border-line bg-white px-4 py-4 text-left text-sm"
          onClick={loadDemo}
          disabled={Boolean(busy)}
        >
          <span className="block font-medium">Load demo dataset</span>
          <span className="mt-1 block text-xs text-muted">
            Offline student-records CSV bundled with the backend. Nothing is downloaded.
          </span>
        </button>
      </div>
      {error && <p className="rounded-lg bg-[#ffdad6] px-3 py-2 text-sm text-[#93000a]">{error}</p>}
      {busy && <p className="text-sm text-primary">{busy}…</p>}
      {dataset && profile && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Dataset" value={dataset.name} />
          <MetricCard label="Rows" value={profile.rows} />
          <MetricCard label="Columns" value={profile.columns} />
          <MetricCard
            label="Findings"
            value={audit ? "Checked" : "Not run"}
            detail={
              model
                ? `${model.flagged_count ?? 0} reconstruction flags`
                : "Start an audit to train the autoencoder"
            }
          />
        </div>
      )}
      <button
        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white"
        disabled={!dataset || Boolean(busy)}
        onClick={startAudit}
      >
        Start audit
      </button>
    </div>
  );
}
