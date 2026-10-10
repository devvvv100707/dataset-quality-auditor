import { BarChart3, Brain, FileText, LayoutDashboard, Menu, Table2, X } from "lucide-react";
import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/profile", label: "Dataset Profile", icon: Table2 },
  { to: "/auditor", label: "Deep Learning Auditor", icon: Brain },
  { to: "/results", label: "Results & Evaluation", icon: BarChart3 },
  { to: "/report", label: "Audit Report", icon: FileText },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && <button className="fixed inset-0 z-30 bg-ink/30 md:hidden" onClick={onClose} aria-label="Close menu" />}
      <aside
        className={`fixed z-40 flex h-full w-64 flex-col border-r border-line bg-white transition-transform md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-5">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-primary">Quality audit</p>
            <h1 className="text-base font-semibold leading-5">Dataset Auditor</h1>
          </div>
          <button className="md:hidden" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          {LINKS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                  isActive ? "bg-[#dbe1ff] font-medium text-[#003ea8]" : "text-muted hover:bg-[#f1f3ff]"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <p className="px-5 py-4 text-xs text-muted">Inspect only. Source rows are never rewritten.</p>
      </aside>
    </>
  );
}

export function MenuButton({ onClick }) {
  return (
    <button className="rounded-md border border-line p-2 md:hidden" onClick={onClick} aria-label="Open menu">
      <Menu size={16} />
    </button>
  );
}
