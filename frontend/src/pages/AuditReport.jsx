import { useState } from "react";
import { client, reportCsvUrl } from "../api/client";
import { useAudit } from "../context/AuditContext";

export default function AuditReport() {
  const { dataset } = useAudit();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      setReport(await client.report(dataset.id));
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    }
  }

  if (!dataset) return <p className="text-sm text-muted">Load a dataset before exporting a report.</p>;

  return (
    <div className="space-y-4">
      <p className="max-w-3xl text-sm text-muted">
        Downloads list findings and metadata. They do not contain a modified dataset.
      </p>
      <div className="flex flex-wrap gap-3">
        <button className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white" onClick={load}>
          Load JSON report
        </button>
        <a className="rounded-lg border border-line bg-white px-4 py-2 text-sm" href={reportCsvUrl(dataset.id)}>
          Download findings CSV
        </a>
        {report && (
          <button
            className="rounded-lg border border-line bg-white px-4 py-2 text-sm"
            onClick={() => {
              const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const link = document.createElement("a");
              link.href = url;
              link.download = "audit-report.json";
              link.click();
              URL.revokeObjectURL(url);
            }}
          >
            Download JSON
          </button>
        )}
      </div>
      {error && <p className="text-sm text-[#93000a]">{error}</p>}
      {report && (
        <div className="space-y-3">
          <p className="text-sm">{report.export_note}</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
            {(report.manual_review_suggestions || []).map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
          <pre className="max-h-[480px] overflow-auto rounded-xl border border-line bg-white p-4 text-xs">
            {JSON.stringify(report, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
