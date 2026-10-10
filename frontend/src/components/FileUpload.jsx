export default function FileUpload({ onFile, disabled }) {
  return (
    <label className="flex cursor-pointer flex-col items-start gap-2 rounded-xl border border-dashed border-line bg-white px-4 py-4 text-sm">
      <span className="font-medium">Upload a CSV</span>
      <span className="text-xs text-muted">UTF-8, up to 2 MB and 20,000 rows. The file is stored in memory for this session.</span>
      <input
        className="text-xs"
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
  );
}
