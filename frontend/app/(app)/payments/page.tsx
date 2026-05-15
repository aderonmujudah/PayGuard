"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Card, Empty, Spinner, StatusBadge } from "@/components/ui/primitives";
import { formatDate, formatMoney } from "@/lib/utils";

export default function PaymentsPage() {
  const [rows, setRows] = useState<any[] | null>(null);

  useEffect(() => {
    api.payments().then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Payment Action Log</h1>
      <Card className="p-0 overflow-hidden">
        {rows === null ? (
          <Spinner />
        ) : rows.length === 0 ? (
          <Empty label="No payment actions yet." />
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Invoice</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Provider Ref</th>
                <th className="px-4 py-3">When</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium uppercase">
                    {p.payment_action}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/invoices/${p.invoice_id}`}
                      className="text-brand-600 hover:underline"
                    >
                      {p.invoice_id.slice(0, 8)}…
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {formatMoney(p.amount, p.currency_code)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={p.payment_status} />
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {p.squad_transaction_ref || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {formatDate(p.created_at)}
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
