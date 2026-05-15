"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge, Card, Empty, Spinner } from "@/components/ui/primitives";
import { formatDate } from "@/lib/utils";

export default function AuditPage() {
  const [rows, setRows] = useState<any[] | null>(null);

  useEffect(() => {
    api.audit().then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Audit Trail</h1>
      <Card className="p-0 overflow-hidden">
        {rows === null ? (
          <Spinner />
        ) : rows.length === 0 ? (
          <Empty label="No audit events recorded." />
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Details</th>
                <th className="px-4 py-3">When</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id} className="border-t border-slate-100 align-top">
                  <td className="px-4 py-3">
                    <Badge tone="blue">{a.action}</Badge>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {a.entity_type} · {a.entity_id.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3">
                    <pre className="max-w-md overflow-x-auto rounded bg-slate-50 p-2 text-xs">
                      {JSON.stringify(
                        { ...a.new_values, ...a.audit_metadata },
                        null,
                        2
                      )}
                    </pre>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {formatDate(a.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
