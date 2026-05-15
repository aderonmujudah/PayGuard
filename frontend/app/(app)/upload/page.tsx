"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Card, CardTitle } from "@/components/ui/primitives";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const inv = await api.uploadInvoice(file);
      router.push(`/invoices/${inv.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-2xl font-bold">Upload Invoice</h1>
      <Card>
        <CardTitle>Invoice file (PDF or image)</CardTitle>
        <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 py-12 text-slate-500 hover:border-brand-400">
          <UploadCloud size={32} />
          <span className="text-sm">
            {file ? file.name : "Click to choose a file"}
          </span>
          <input
            type="file"
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.txt"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <Button
          onClick={submit}
          disabled={!file || busy}
          className="mt-4 w-full"
        >
          {busy ? "Uploading & extracting…" : "Upload & run extraction"}
        </Button>
        <p className="mt-3 text-xs text-slate-400">
          On upload the backend stores the file, runs OCR + the configured
          extraction engine, then you can review and verify.
        </p>
      </Card>
    </div>
  );
}
