import { BalanceChart, MissingChart } from "../components/Charts";
import DataTable from "../components/DataTable";
import MetricCard from "../components/MetricCard";
import { useAudit } from "../context/AuditContext";

export default function DatasetProfile() {
  const { profile, audit, target, setTarget, dataset } = useAudit();
  if (!dataset || !profile) {
    return <p className="text-sm text-muted">Load a dataset from Overview first.</p>;
  }
  const missing = audit?.missing;
  const duplicates = audit?.duplicates;
  const balance = audit?.class_balance;
  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Numerical" value={profile.numerical_count} />
        <MetricCard label="Categorical" value={profile.categorical_count} />
        <MetricCard label="Constant columns" value={profile.constant_columns.length} />
        <MetricCard
          label="Infinite values"
          value={Object.values(profile.infinite_values).reduce((sum, n) => sum + n, 0)}
        />
      </div>
      <section>
        <h3 className="mb-2 text-sm font-semibold">Preview</h3>
        <DataTable
          columns={profile.column_details.map((column) => ({ key: column.name, label: column.name }))}
          rows={profile.preview}
          searchKeys={profile.column_details.map((column) => column.name)}
        />
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold">Column types</h3>
        <DataTable
          columns={[
            { key: "name", label: "Column" },
            { key: "dtype", label: "Dtype" },
            { key: "kind", label: "Kind" },
            { key: "missing", label: "Missing" },
            { key: "unique", label: "Unique" },
            { key: "constant", label: "Constant", render: (value) => (value ? "yes" : "no") },
            { key: "infinite", label: "Infinite" },
          ]}
          rows={profile.column_details}
          searchKeys={["name", "dtype", "kind"]}
        />
      </section>
      <section className="grid gap-6 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold">Missing values</h3>
          {missing ? (
            <>
              <p className="mb-2 text-sm text-muted">
                {missing.missing_cells} cells ({missing.missing_percentage}%)
              </p>
              <MissingChart data={missing.chart} />
            </>
          ) : (
            <p className="text-sm text-muted">Run the audit to measure missing values.</p>
          )}
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold">Duplicates and target</h3>
          <p className="mb-3 text-sm text-muted">
            {duplicates
              ? `${duplicates.duplicate_rows} rows (${duplicates.duplicate_percentage}%) sit in duplicate groups. They are not removed.`
              : "Duplicate counts appear after the audit."}
          </p>
          <label className="mb-3 block text-sm">
            Class target
            <select
              className="mt-1 w-full rounded-lg border border-line bg-white px-3 py-2"
              value={target}
              onChange={(event) => setTarget(event.target.value)}
            >
              <option value="">None</option>
              {profile.column_details.map((column) => (
                <option key={column.name} value={column.name}>
                  {column.name}
                </option>
              ))}
            </select>
          </label>
          {balance?.status === "ok" ? (
            <>
              <BalanceChart data={balance.distribution} />
              <p className="mt-2 text-xs text-muted">
                Underrepresented: {balance.underrepresented.map((item) => item.label).join(", ") || "none"}
              </p>
            </>
          ) : (
            <p className="text-sm text-muted">{balance?.reason || "Class balance is computed during the audit."}</p>
          )}
        </div>
      </section>
    </div>
  );
}
