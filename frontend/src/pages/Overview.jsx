import { Copy, Sparkles, Table2, TriangleAlert } from "lucide-react";
import FileUpload from "../components/FileUpload";
import MetricCard from "../components/MetricCard";
import { PageIntro } from "../components/Header";
import { useAudit } from "../context/AuditContext";

function formatBytes(size) {
  if (size == null) return "—";
  if (size < 1024) return `${size} B`;
  return `${(size / 1024).toFixed(1)} KB`;
}

export default function Overview() {
  const { dataset, profile, audit, model, busy, error, loadDemo, uploadFile, startAudit } = useAudit();
  const missing = audit?.missing;
  const duplicates = audit?.duplicates;
  const balance = audit?.class_balance;
  const top = missing?.top_columns || [];
  const maxMissing = Math.max(1, ...top.map((item) => item.count), 1);
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <PageIntro
        title="Dataset Overview"
        subtitle="Inspect data quality and identify potential issues before model training."
      />
      <FileUpload onFile={uploadFile} onDemo={loadDemo} disabled={Boolean(busy)} dataset={dataset} profile={profile} />
      {error && <p className="rounded-lg bg-[#ffdad6] px-3 py-2 text-sm text-[#93000a]">{error}</p>}
      {busy && (
        <div className="rounded-lg bg-white px-4 py-3 text-sm text-[#004ac6] shadow-sm">
          {busy}…
          <div className="mt-2 h-1 overflow-hidden rounded bg-[#e9edff]">
            <div className="h-full w-1/2 animate-pulse bg-[#2563eb]" />
          </div>
        </div>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total records"
          icon={<Table2 size={18} />}
          value={profile ? profile.rows.toLocaleString() : "—"}
          detail={profile ? `${profile.columns} columns` : "Load a CSV"}
        />
        <MetricCard
          label="Missing values"
          icon={<TriangleAlert size={18} />}
          value={missing ? missing.missing_cells.toLocaleString() : "—"}
          detail={missing ? `${missing.missing_percentage}% across ${missing.columns_with_missing} columns` : "Run the audit"}
        />
        <MetricCard
          label="Duplicate rows"
          icon={<Copy size={18} />}
          value={duplicates ? duplicates.duplicate_rows.toLocaleString() : "—"}
          detail={duplicates ? `${duplicates.duplicate_percentage}% exact matches` : "Run the audit"}
        />
        <MetricCard
          label="Potential anomalies"
          icon={<Sparkles size={18} />}
          value={model?.status === "trained" ? model.flagged_count.toLocaleString() : "—"}
          detail={
            model?.status === "trained"
              ? `${model.flagged_percentage}% flagged via autoencoder`
              : model?.limitation || "Train during the audit"
          }
        />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold">Dataset Summary</h3>
            <span className="inline-flex items-center gap-1 rounded bg-[#eff6ff] px-2 py-1 text-[11px] font-medium text-[#1d4ed8]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#2563eb]" />
              {model?.status === "trained" ? "Completed" : dataset ? "Loaded" : "Waiting"}
            </span>
          </div>
          <dl className="space-y-3 text-sm">
            <Row label="File name" value={dataset?.name || "—"} />
            <Row label="File size" value={formatBytes(dataset?.byte_size)} />
            <Row label="Numerical features" value={profile ? `${profile.numerical_count} features` : "—"} />
            <Row label="Categorical features" value={profile ? `${profile.categorical_count} features` : "—"} />
            <Row
              label="Target dimension"
              value={balance?.status === "ok" ? `${balance.classes} classes (${balance.target})` : "Select a target and audit"}
            />
          </dl>
          <div className="mt-4 rounded-lg bg-[#f1f3ff] p-4 text-sm text-[#1e3a8a]">
            {audit
              ? `Audit completed. ${missing.missing_cells} missing values and ${duplicates.duplicate_rows} duplicate records detected. ${
                  model?.status === "trained"
                    ? "Deep learning model ready for inspection."
                    : model?.limitation || "The autoencoder was not trained."
                }`
              : "Source rows stay unchanged. Start an audit to measure missing values, duplicates, and reconstruction error."}
          </div>
          <button
            className="mt-4 rounded-lg bg-[#004ac6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1d4ed8]"
            disabled={!dataset || Boolean(busy)}
            onClick={startAudit}
          >
            Start audit
          </button>
        </section>
        <div className="flex flex-col gap-4">
          <section className="rounded-xl bg-white p-6 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">Missing Values by Column</h3>
              <span className="text-xs text-[#6b7280]">
                {missing ? `${missing.columns_with_missing} of ${profile.columns} columns impacted` : "Not measured"}
              </span>
            </div>
            {!missing && <p className="text-sm text-[#6b7280]">Run the audit to fill this chart from the API.</p>}
            {missing && top.length === 0 && <p className="text-sm text-[#6b7280]">No missing values.</p>}
            {top.map((item) => (
              <div key={item.column} className="mb-3">
                <div className="mb-1 flex justify-between text-xs">
                  <span className="rounded bg-[#e9edff] px-1.5 py-0.5 font-medium text-[#003ea8]">{item.column}</span>
                  <span className="text-[#4b5563]">
                    {item.count} missing ({item.percentage}%)
                  </span>
                </div>
                <div className="h-1.5 rounded bg-[#e9edff]">
                  <div className="h-1.5 rounded bg-[#2563eb]" style={{ width: `${(item.count / maxMissing) * 100}%` }} />
                </div>
              </div>
            ))}
          </section>
          <section className="rounded-xl bg-white p-6 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">Key Findings</h3>
              <span className="text-xs text-[#6b7280]">Summary audit</span>
            </div>
            <ol className="space-y-3 text-sm text-[#374151]">
              <li>
                <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#e9edff] text-[11px] text-[#004ac6]">1</span>
                {missing
                  ? top.length
                    ? `Missing values in ${top.map((item) => `${item.column} (${item.count})`).join(", ")}.`
                    : "No missing values were found."
                  : "Missing-value findings appear after the audit."}
              </li>
              <li>
                <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#e9edff] text-[11px] text-[#004ac6]">2</span>
                {duplicates
                  ? `${duplicates.duplicate_rows} duplicate records flagged for verification; source data preserved without automated deletion.`
                  : "Duplicate findings appear after the audit."}
              </li>
              <li>
                <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#e9edff] text-[11px] text-[#004ac6]">3</span>
                {balance?.status === "ok"
                  ? balance.underrepresented.length
                    ? `Underrepresented classes: ${balance.underrepresented
                        .map((item) => `${item.label} (${item.percentage}%)`)
                        .join(", ")}.`
                    : `Class shares were measured for ${balance.target}. None fell under the ${balance.underrepresented_fraction * 100}% rule.`
                  : balance?.reason || "Class balance is measured when a suitable target is selected."}
              </li>
            </ol>
          </section>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[#f3f4f6] pb-2">
      <dt className="text-[#6b7280]">{label}</dt>
      <dd className="tnum text-right font-medium">{value}</dd>
    </div>
  );
}
