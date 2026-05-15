"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import { Card, CardTitle, Spinner, StatusBadge } from "@/components/ui/primitives";
import { formatDate } from "@/lib/utils";

function Metric({ label, value, tone }: any) {
  return (
    <Card>
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-bold ${tone}`}>{value}</div>
    </Card>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="text-red-600">{err}</p>;
  if (!data) return <Spinner />;

  const chart = Object.entries(data.invoices_by_status || {}).map(
    ([status, count]) => ({ status, count })
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Metric label="Total Invoices" value={data.total_invoices} tone="" />
        <Metric label="Cleared" value={data.cleared} tone="text-emerald-600" />
        <Metric label="In Review" value={data.in_review} tone="text-amber-600" />
        <Metric label="On Hold" value={data.held} tone="text-orange-600" />
        <Metric label="Blocked" value={data.blocked} tone="text-red-600" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardTitle>Invoices by Status</CardTitle>
          {chart.length === 0 ? (
            <p className="text-sm text-slate-400">No invoices yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chart}>
                <XAxis dataKey="status" fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b6cff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <CardTitle>Recent Activity</CardTitle>
          {data.recent_activity?.length === 0 ? (
            <p className="text-sm text-slate-400">No activity yet.</p>
          ) : (
            <ul className="space-y-2">
              {data.recent_activity?.map((a: any) => (
                <li
                  key={a.id}
                  className="flex items-center justify-between border-b border-slate-100 pb-2 text-sm"
                >
                  <div>
                    <span className="font-medium">{a.action}</span>
                    <span className="text-slate-400">
                      {" "}
                      · {a.entity_type}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400">
                    {formatDate(a.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
