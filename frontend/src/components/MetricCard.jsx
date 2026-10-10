export default function MetricCard({ label, value, detail, icon }) {
  return (
    <div className="flex flex-col justify-between rounded-xl bg-white p-6 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wider text-[#6b7280]">{label}</span>
        {icon && <span className="text-[#9ca3af]">{icon}</span>}
      </div>
      <div>
        <div className="tnum text-[28px] font-semibold leading-[34px] tracking-tight">{value}</div>
        {detail && <p className="mt-1 text-[13px] text-[#6b7280]">{detail}</p>}
      </div>
    </div>
  );
}
