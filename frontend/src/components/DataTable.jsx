import { useMemo, useState } from "react";

export default function DataTable({ columns, rows, searchKeys = [] }) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState({ key: columns[0]?.key, dir: "asc" });
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    let next = rows || [];
    if (needle) {
      next = next.filter((row) =>
        searchKeys.some((key) => String(row[key] ?? "").toLowerCase().includes(needle))
      );
    }
    const { key, dir } = sort;
    next = [...next].sort((a, b) => {
      const left = a[key];
      const right = b[key];
      if (typeof left === "number" && typeof right === "number") {
        return dir === "asc" ? left - right : right - left;
      }
      return dir === "asc"
        ? String(left ?? "").localeCompare(String(right ?? ""))
        : String(right ?? "").localeCompare(String(left ?? ""));
    });
    return next;
  }, [rows, query, sort, searchKeys]);

  return (
    <div>
      <input
        className="mb-3 w-full rounded-lg border border-line px-3 py-2 text-sm"
        placeholder="Search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <div className="overflow-x-auto rounded-xl border border-line bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-[#f1f3ff] text-xs uppercase tracking-wide text-muted">
            <tr>
              {columns.map((column) => (
                <th key={column.key} className="px-3 py-2 font-medium">
                  <button
                    onClick={() =>
                      setSort((current) => ({
                        key: column.key,
                        dir: current.key === column.key && current.dir === "asc" ? "desc" : "asc",
                      }))
                    }
                  >
                    {column.label}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 && (
              <tr>
                <td className="px-3 py-4 text-muted" colSpan={columns.length}>
                  Nothing to show.
                </td>
              </tr>
            )}
            {visible.map((row, index) => (
              <tr key={index} className="border-t border-line">
                {columns.map((column) => (
                  <td key={column.key} className="px-3 py-2 align-top">
                    {column.render ? column.render(row[column.key], row) : String(row[column.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
