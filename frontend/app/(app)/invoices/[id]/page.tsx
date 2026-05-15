"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Badge,
  Button,
  Card,
  CardTitle,
  Input,
  Spinner,
  StatusBadge,
} from "@/components/ui/primitives";
import RiskPanel from "@/components/RiskPanel";
import { formatMoney } from "@/lib/utils";

const EDITABLE = [
  "invoice_number",
  "invoice_date",
  "due_date",
  "currency_code",
  "subtotal",
  "tax_amount",
  "total_amount",
  "beneficiary_account_number",
  "beneficiary_account_name",
  "beneficiary_bank_code",
];

export default function InvoiceDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const id = params.id;
  const [inv, setInv] = useState<any>(null);
  const [checks, setChecks] = useState<any[]>([]);
  const [risk, setRisk] = useState<any>(null);
  const [busy, setBusy] = useState("");
  const [form, setForm] = useState<any>({});

  const load = useCallback(async () => {
    const i = await api.invoice(id);
    setInv(i);
    setForm(
      Object.fromEntries(EDITABLE.map((k) => [k, i[k] ?? ""]))
    );
    api.checks(id).then(setChecks).catch(() => {});
    api.risk(id).then(setRisk).catch(() => setRisk(null));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function run(action: string, fn: () => Promise<any>) {
    setBusy(action);
    try {
      await fn();
      await load();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setBusy("");
    }
  }

  async function saveFields() {
    setBusy("save");
    try {
      const body: any = {};
      for (const k of EDITABLE) if (form[k] !== "") body[k] = form[k];
      await api.updateInvoice(id, body);
      await load();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setBusy("");
    }
  }

  if (!inv) return <Spinner />;

  const confidence = inv.extracted_data?.field_confidence || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {inv.invoice_number || "Invoice"}
          </h1>
          <div className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            <StatusBadge status={inv.status} />
            <span>·</span>
            <span>engine: {inv.extraction_engine || "—"}</span>
            <span>·</span>
            <span>
              OCR {inv.ocr_status} ({Math.round((inv.ocr_confidence || 0) * 100)}
              %)
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={!!busy}
            onClick={() => run("extract", () => api.runExtract(id))}
          >
            {busy === "extract" ? "…" : "Re-extract"}
          </Button>
          <Button
            variant="outline"
            disabled={!!busy}
            onClick={() => run("verify", () => api.runVerify(id))}
          >
            {busy === "verify" ? "…" : "Run verification"}
          </Button>
          <Button
            disabled={!!busy}
            onClick={() => run("assess", () => api.runAssess(id))}
          >
            {busy === "assess" ? "…" : "Run risk assessment"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardTitle>Extracted Fields (editable)</CardTitle>
            <div className="grid grid-cols-2 gap-4">
              {EDITABLE.map((k) => (
                <div key={k}>
                  <label className="mb-1 flex items-center justify-between text-xs font-medium text-slate-600">
                    <span>{k}</span>
                    {confidence[k] != null && (
                      <Badge tone={confidence[k] >= 0.7 ? "green" : "amber"}>
                        {Math.round(confidence[k] * 100)}%
                      </Badge>
                    )}
                  </label>
                  <Input
                    value={form[k] ?? ""}
                    onChange={(e) =>
                      setForm({ ...form, [k]: e.target.value })
                    }
                  />
                </div>
              ))}
            </div>
            <Button
              className="mt-4"
              onClick={saveFields}
              disabled={busy === "save"}
            >
              {busy === "save" ? "Saving…" : "Save fields"}
            </Button>
          </Card>

          <Card>
            <CardTitle>Verification Checks</CardTitle>
            {checks.length === 0 ? (
              <p className="text-sm text-slate-400">
                No checks yet. Run verification above.
              </p>
            ) : (
              <ul className="space-y-3">
                {checks.map((c) => (
                  <li
                    key={c.id}
                    className="rounded-lg border border-slate-100 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{c.check_type}</span>
                      <StatusBadge status={c.status} />
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      provider: {c.provider_name}
                    </div>
                    <pre className="mt-2 overflow-x-auto rounded bg-slate-50 p-2 text-xs">
                      {JSON.stringify(c.normalized_result, null, 2)}
                    </pre>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardTitle>File Preview</CardTitle>
            <a
              href={inv.source_file_url}
              target="_blank"
              rel="noreferrer"
              className="block"
            >
              <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-brand-600">
                Open {inv.source_file_name}
              </div>
            </a>
            <div className="mt-3 text-xs text-slate-400">
              file hash: {inv.file_hash?.slice(0, 16)}…
            </div>
            {inv.vendor_id && (
              <Link
                href={`/vendors/${inv.vendor_id}`}
                className="mt-3 inline-block text-sm text-brand-600 hover:underline"
              >
                View vendor →
              </Link>
            )}
          </Card>

          <RiskPanel risk={risk} />

          <Card>
            <CardTitle>Payment Actions</CardTitle>
            <p className="mb-3 text-sm text-slate-500">
              Total: {formatMoney(inv.total_amount, inv.currency_code)}
            </p>
            <div className="flex flex-col gap-2">
              <Button
                variant="success"
                disabled={!!busy}
                onClick={() =>
                  run("release", () => api.paymentAction(id, "release"))
                }
              >
                Release payment
              </Button>
              <Button
                variant="warn"
                disabled={!!busy}
                onClick={() =>
                  run("hold", () => api.paymentAction(id, "hold"))
                }
              >
                Hold payment
              </Button>
              <Button
                variant="danger"
                disabled={!!busy}
                onClick={() =>
                  run("block", () => api.paymentAction(id, "block"))
                }
              >
                Block payment
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
