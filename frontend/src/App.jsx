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
  "/": ["Dataset Overview", "Inspect data quality and identify potential issues before model training."],
  "/profile": ["Dataset Profile", "Column types, preview, missing values, duplicates, and class balance."],
  "/auditor": ["Deep Learning Auditor", "Reconstruction errors from a small autoencoder trained for this dataset only."],
  "/results": ["Results & Evaluation", "Held-out reconstruction stats and the controlled experiment file."],
  "/report": ["Audit Report", "Download findings and metadata. The source dataset is not rewritten."],
};

export default function App() {
  const { dataset, busy } = useAudit();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="md:pl-[230px]">
        <Header
          title={(TITLES[location.pathname] || ["Auditor"])[0]}
          subtitle={(TITLES[location.pathname] || ["", ""])[1]}
          dataset={dataset}
          busy={busy}
          menu={<MenuButton onClick={() => setOpen(true)} />}
        />
        <main className="min-h-[calc(100vh-4rem)] bg-[#f7f8fb] px-4 py-6 md:px-6">
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
