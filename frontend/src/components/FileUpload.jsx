import { Plus, RefreshCw, UploadCloud } from "lucide-react";

export default function FileUpload({ onFile, onDemo, disabled, dataset, profile }) {
  return (
    <div className="w-full max-w-3xl rounded-xl bg-white p-8 shadow-sm">
      <div className="flex flex-col items-center text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#e9edff] text-[#004ac6]">
          <UploadCloud size={22} />
        </div>
        <h2 className="text-base font-semibold">Upload your dataset</h2>
        <p className="mb-6 mt-1 max-w-md text-sm text-[#4b5563]">Choose a CSV file to begin your audit.</p>
        <div className="mb-4 flex flex-wrap items-center justify-center gap-2">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-[#004ac6] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1d4ed8]">
            <Plus size={16} />
            Choose CSV
            <input
              className="hidden"
              type="file"
              accept=".csv,text/csv"
              disabled={disabled}
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) onFile(file);
                event.target.value = "";
              }}
            />
          </label>
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2.5 text-sm font-medium shadow-sm hover:bg-[#f8f9fa]"
            onClick={onDemo}
            disabled={disabled}
          >
            <RefreshCw size={16} className="text-[#6b7280]" />
            Load demo dataset
          </button>
        </div>
        {dataset && (
          <div className="inline-flex items-center gap-2 rounded-full bg-[#f1f3ff] px-3 py-1.5 text-[11px] font-medium text-[#434655]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#2563eb]" />
            <span className="text-xs font-medium text-[#111827]">Loaded:</span>
            <span>
              {dataset.name} ({dataset.rows.toLocaleString()} records, {profile?.columns ?? dataset.columns} features)
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
