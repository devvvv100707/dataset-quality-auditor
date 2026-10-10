export default function Header({ title, subtitle, dataset, busy, menu }) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-3 border-b border-[#e5e7eb] bg-white/90 px-4 backdrop-blur md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        {menu}
        <div className="min-w-0">
          <p className="truncate text-[13px] text-[#6b7280]">
            Audit Workspace <span className="text-[#d1d5db]">/</span>{" "}
            <span className="font-medium text-[#111827]">{busy ? busy : "Session Active"}</span>
          </p>
          <p className="truncate text-base font-semibold tracking-tight md:hidden">{title}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-2 rounded border border-[#e5e7eb] bg-[#f3f4f6] px-2.5 py-1 text-xs sm:inline-flex">
          <span className={`h-1.5 w-1.5 rounded-full ${dataset ? "bg-[#2563eb]" : "bg-[#9ca3af]"}`} />
          <span className="max-w-[180px] truncate font-medium">{dataset ? dataset.name : "No dataset"}</span>
          {dataset && <span className="text-[#6b7280]">• {dataset.rows.toLocaleString()} rows</span>}
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#004ac6] text-xs font-medium text-white">QA</div>
      </div>
      <span className="sr-only">{subtitle}</span>
    </header>
  );
}

export function PageIntro({ title, subtitle }) {
  return (
    <div className="pb-1">
      <h1 className="text-2xl font-semibold tracking-tight text-[#111827]">{title}</h1>
      <p className="mt-1 text-sm text-[#4b5563]">{subtitle}</p>
    </div>
  );
}
