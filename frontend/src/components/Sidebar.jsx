import { BarChart3, Brain, FileText, LayoutGrid, Menu, Table2, X } from "lucide-react";
import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Overview", icon: LayoutGrid },
  { to: "/profile", label: "Dataset Profile", icon: Table2 },
  { to: "/auditor", label: "Deep Learning Auditor", icon: Brain },
  { to: "/results", label: "Results & Evaluation", icon: BarChart3 },
  { to: "/report", label: "Audit Report", icon: FileText },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <button className="fixed inset-0 z-30 bg-[#111827]/40 md:hidden" onClick={onClose} aria-label="Close menu" />}
      <aside
        className={`fixed z-40 flex h-full w-[230px] flex-col justify-between border-r border-[#e5e7eb] bg-white transition-transform md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div>
          <div className="flex h-16 items-center gap-2 border-b border-[#f3f4f6] px-4">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#004ac6] text-xs font-semibold text-white">DL</div>
            <div className="min-w-0 leading-none">
              <p className="truncate text-sm font-semibold tracking-tight">DataLens</p>
              <p className="mt-1 truncate text-[11px] font-medium text-[#6b7280]">Dataset Quality Auditor</p>
            </div>
            <button className="ml-auto md:hidden" onClick={onClose} aria-label="Close">
              <X size={16} />
            </button>
          </div>
          <nav className="flex flex-col gap-1 p-2">
            {LINKS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded px-2 py-2 text-[13px] ${
                    isActive ? "bg-[#e9edff] font-medium text-[#004ac6]" : "text-[#434655] hover:bg-[#f1f3ff]"
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <p className="border-t border-[#f3f4f6] px-4 py-4 text-xs font-medium text-[#6b7280]">v1.0 • Academic Capstone</p>
      </aside>
    </>
  );
}

export function MenuButton({ onClick }) {
  return (
    <button className="rounded-md border border-[#e5e7eb] p-2 md:hidden" onClick={onClick} aria-label="Open menu">
      <Menu size={16} />
    </button>
  );
}
