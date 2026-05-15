"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, Empty, Spinner, StatusBadge } from "@/components/ui/primitives";
import { formatDate, formatMoney } from "@/lib/utils";

export default function ReviewQueuePage() {
  const [rows, setRows] = useState<any[] | null>(null);

  useEffect(() => {
    api.reviewQueue().then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Review Queue</h1>
      <p className="text-sm text-slate-500">
        Invoices flagged REVIEW or HOLD that need a manual decision.
      </p>
      <Card className="p-0 overflow-hidden">
        {rows === null ? (
          <Spinner />
        ) : rows.length === 0 ? (
          <Empty label="Queue is clear — nothing needs review." />
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Invoice #</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.id}
                  className="border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/invoices/${r.id}`}
                      className="font-medium text-brand-600 hover:underline"
                    >
                      {r.invoice_number || "(pending)"}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {formatMoney(r.total_amount, r.currency_code)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {formatDate(r.created_at)}
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
