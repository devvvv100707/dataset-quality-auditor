import { useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Header from "./components/Header";
import Sidebar, { MenuButton } from "./components/Sidebar";
import { useAudit } from "./context/AuditContext";
import AuditReport from "./pages/AuditReport";
import DatasetProfile from "./pages/DatasetProfile";
import DeepLearningAuditor from "./pages/DeepLearningAuditor";
import Overview from "./pages/Overview";
import ResultsEvaluation from "./pages/ResultsEvaluation";

const TITLES = {
  "/": "Overview",
  "/profile": "Dataset Profile",
  "/auditor": "Deep Learning Auditor",
  "/results": "Results & Evaluation",
  "/report": "Audit Report",
};

export default function App() {
  const { dataset, busy } = useAudit();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="md:pl-64">
        <Header
          title={TITLES[location.pathname] || "Auditor"}
          dataset={dataset}
          busy={busy}
          menu={<MenuButton onClick={() => setOpen(true)} />}
        />
        <main className="px-4 py-6 md:px-8">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/profile" element={<DatasetProfile />} />
            <Route path="/auditor" element={<DeepLearningAuditor />} />
            <Route path="/results" element={<ResultsEvaluation />} />
            <Route path="/report" element={<AuditReport />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
