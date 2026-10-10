import { createContext, useContext, useMemo, useState } from "react";
import { client, errorMessage } from "../api/client";

const AuditContext = createContext(null);

export function AuditProvider({ children }) {
  const [dataset, setDataset] = useState(null);
  const [profile, setProfile] = useState(null);
  const [audit, setAudit] = useState(null);
  const [model, setModel] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [experiment, setExperiment] = useState(null);
  const [target, setTarget] = useState("program");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function adopt(summary) {
    setDataset(summary);
    setAudit(null);
    setModel(null);
    setEvaluation(null);
    setError("");
    const profileBody = await client.profile(summary.id);
    setProfile(profileBody.profile);
    if (!profileBody.profile.categorical_columns.includes(target) && profileBody.profile.categorical_columns[0]) {
      setTarget(profileBody.profile.categorical_columns[0]);
    }
    try {
      setExperiment(await client.experiment());
    } catch (err) {
      setExperiment({ available: false, reason: errorMessage(err) });
    }
  }

  async function loadDemo() {
    setBusy("Loading the built-in demo dataset");
    setError("");
    try {
      await adopt(await client.demo());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function uploadFile(file) {
    setBusy("Uploading CSV");
    setError("");
    try {
      await adopt(await client.upload(file));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function changeTarget(next) {
    setTarget(next);
    if (!dataset || !audit) return;
    setBusy("Updating class balance");
    setError("");
    try {
      const audited = await client.audit(dataset.id, next);
      setAudit(audited.audit);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  async function startAudit() {
    if (!dataset) return;
    setError("");
    try {
      setBusy("Running statistical checks");
      const audited = await client.audit(dataset.id, target);
      setAudit(audited.audit);
      setBusy("Training the autoencoder on CPU");
      const trained = await client.train(dataset.id);
      setModel(trained.model);
      setBusy("Collecting evaluation");
      const scored = await client.evaluation(dataset.id);
      setEvaluation(scored.evaluation);
      setExperiment(scored.experiment);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  }

  const value = useMemo(
    () => ({
      dataset,
      profile,
      audit,
      model,
      evaluation,
      experiment,
      target,
      setTarget: changeTarget,
      busy,
      error,
      loadDemo,
      uploadFile,
      startAudit,
    }),
    [dataset, profile, audit, model, evaluation, experiment, target, busy, error]
  );

  return <AuditContext.Provider value={value}>{children}</AuditContext.Provider>;
}

export function useAudit() {
  return useContext(AuditContext);
}
