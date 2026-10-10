import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 120000,
});

export function errorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(" ");
  return error?.message || "The request failed.";
}

export const client = {
  health: () => api.get("/api/health").then((r) => r.data),
  demo: () => api.get("/api/demo").then((r) => r.data),
  upload: (file) => {
    const body = new FormData();
    body.append("file", file);
    return api.post("/api/datasets/upload", body).then((r) => r.data);
  },
  profile: (id) => api.get(`/api/datasets/${id}/profile`).then((r) => r.data),
  audit: (id, target) =>
    api.post(`/api/datasets/${id}/audit`, { target: target || null, underrepresented_fraction: 0.05 }).then((r) => r.data),
  train: (id) => api.post(`/api/datasets/${id}/model/train`).then((r) => r.data),
  modelResults: (id) => api.get(`/api/datasets/${id}/model/results`).then((r) => r.data),
  evaluation: (id) => api.get(`/api/datasets/${id}/evaluation`).then((r) => r.data),
  report: (id) => api.get(`/api/datasets/${id}/report`).then((r) => r.data),
  experiment: () => api.get("/api/experiments/latest").then((r) => r.data),
};

export function reportCsvUrl(id) {
  return `http://localhost:8000/api/datasets/${id}/report.csv`;
}
