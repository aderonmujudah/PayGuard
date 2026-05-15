"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Badge,
  Card,
  CardTitle,
  Spinner,
  StatusBadge,
} from "@/components/ui/primitives";
import { formatDate, formatMoney } from "@/lib/utils";

export default function VendorDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = params.id;
  const [vendor, setVendor] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    api.vendor(id).then(setVendor);
    api.vendorInvoices(id).then(setInvoices).catch(() => {});
    api.vendorHistory(id).then(setHistory).catch(() => {});
  }, [id]);

  if (!vendor) return <Spinner />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{vendor.legal_name}</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardTitle>Profile</CardTitle>
          <dl className="space-y-2 text-sm">
            {[
              ["RC Number", vendor.rc_number],
              ["TIN", vendor.tin],
              ["Email", vendor.email],
              ["Phone", vendor.phone],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-slate-500">{k}</dt>
                <dd>{v || "—"}</dd>
              </div>
            ))}
            <div className="flex justify-between">
              <dt className="text-slate-500">Verification</dt>
              <dd>
                <StatusBadge status={vendor.verification_status} />
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Onboarding</dt>
              <dd>
                <Badge>{vendor.onboarding_status}</Badge>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Risk level</dt>
              <dd>
                <Badge
                  tone={
                    vendor.risk_level === "high"
                      ? "red"
                      : vendor.risk_level === "low"
                      ? "green"
                      : "amber"
                  }
                >
                  {vendor.risk_level}
                </Badge>
              </dd>
            </div>
          </dl>
        </Card>

        <Card>
          <CardTitle>Bank Accounts</CardTitle>
          {vendor.bank_accounts?.length === 0 ? (
            <p className="text-sm text-slate-400">No bank accounts.</p>
          ) : (
            <ul className="space-y-3">
              {vendor.bank_accounts?.map((b: any) => (
                <li
                  key={b.id}
                  className="rounded-lg border border-slate-100 p-3 text-sm"
                >
                  <div className="font-medium">{b.account_name}</div>
                  <div className="text-slate-500">
                    {b.account_number} · {b.bank_name || b.bank_code}
                  </div>
                  <div className="mt-1 flex gap-2">
                    {b.is_primary && <Badge tone="blue">primary</Badge>}
                    <Badge tone={b.is_verified ? "green" : "slate"}>
                      {b.is_verified ? "verified" : "unverified"}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardTitle>Verification History</CardTitle>
          {history.length === 0 ? (
            <p className="text-sm text-slate-400">No history.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {history.map((h) => (
                <li
                  key={h.id}
                  className="flex items-center justify-between border-b border-slate-100 pb-2"
                >
                  <span>{h.check_type}</span>
                  <StatusBadge status={h.status} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="p-5 pb-0">
          <CardTitle>Recent Invoices</CardTitle>
        </div>
        {invoices.length === 0 ? (
          <p className="p-5 text-sm text-slate-400">No invoices.</p>
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
              {invoices.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <Link
                      href={`/invoices/${r.id}`}
                      className="text-brand-600 hover:underline"
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
