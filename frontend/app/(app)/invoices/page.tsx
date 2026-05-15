"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, Empty, Spinner, StatusBadge } from "@/components/ui/primitives";
import { formatDate, formatMoney } from "@/lib/utils";

export default function InvoicesPage() {
  const [rows, setRows] = useState<any[] | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.invoices(filter || undefined).then(setRows).catch(() => setRows([]));
  }, [filter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Invoices</h1>
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          {["uploaded", "extracted", "verified", "cleared", "review", "hold", "blocked"].map(
            (s) => (
              <option key={s} value={s}>
                {s}
              </option>
            )
          )}
        </select>
      </div>
      <Card className="p-0 overflow-hidden">
        {rows === null ? (
          <Spinner />
        ) : rows.length === 0 ? (
          <Empty label="No invoices found." />
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
                      {r.invoice_number || "(pending extraction)"}
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
