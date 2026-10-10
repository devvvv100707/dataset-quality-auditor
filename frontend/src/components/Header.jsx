export default function Header({ title, dataset, busy, menu }) {
  return (
    <header className="flex items-center justify-between gap-4 border-b border-line bg-white px-4 py-4 md:px-8">
      <div className="flex items-center gap-3">
        {menu}
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-xs text-muted">{busy || "Local CPU audit"}</p>
        </div>
      </div>
      <div className="text-right text-sm">
        {dataset ? (
          <>
            <p className="font-medium">{dataset.name}</p>
            <p className="text-xs text-muted">
              {dataset.rows} rows · {dataset.columns} columns
            </p>
          </>
        ) : (
          <p className="text-muted">No dataset loaded</p>
        )}
      </div>
    </header>
  );
}
