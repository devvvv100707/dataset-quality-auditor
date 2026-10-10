import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function MissingChart({ data }) {
  if (!data?.length) return <p className="text-sm text-muted">No missing values in the loaded dataset.</p>;
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="#e1e8fd" vertical={false} />
          <XAxis dataKey="column" tick={{ fontSize: 11 }} interval={0} angle={-20} height={60} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BalanceChart({ data }) {
  if (!data?.length) return <p className="text-sm text-muted">No class distribution to chart.</p>;
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="#e1e8fd" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LossChart({ history }) {
  if (!history?.length) return <p className="text-sm text-muted">Train the model to see the loss curve.</p>;
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={history}>
          <CartesianGrid stroke="#e1e8fd" />
          <XAxis dataKey="epoch" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="train_loss" stroke="#2563eb" dot={false} name="Train MSE" />
          <Line type="monotone" dataKey="val_loss" stroke="#bc4800" dot={false} name="Validation MSE" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ErrorChart({ histogram, threshold }) {
  if (!histogram?.length) return <p className="text-sm text-muted">No reconstruction errors yet.</p>;
  const data = histogram.map((bin) => ({
    label: bin.bin_start.toFixed(2),
    count: bin.count,
  }));
  return (
    <div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="#e1e8fd" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" fill="#4069f2" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      {threshold != null && (
        <p className="mt-2 text-xs text-muted">Validation threshold: {Number(threshold).toFixed(6)}</p>
      )}
    </div>
  );
}
