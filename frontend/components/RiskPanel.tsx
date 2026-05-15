import { Badge, Card, CardTitle } from "@/components/ui/primitives";

const VERDICT: Record<
  string,
  { tone: "green" | "amber" | "red"; ring: string; bar: string }
> = {
  CLEAR: { tone: "green", ring: "ring-emerald-200", bar: "bg-emerald-500" },
  REVIEW: { tone: "amber", ring: "ring-amber-200", bar: "bg-amber-500" },
  HOLD: { tone: "amber", ring: "ring-amber-300", bar: "bg-orange-500" },
  BLOCK: { tone: "red", ring: "ring-red-200", bar: "bg-red-500" },
};

export default function RiskPanel({ risk }: { risk: any }) {
  if (!risk) return null;
  const v = VERDICT[risk.verdict] || VERDICT.REVIEW;
  return (
    <Card>
      <CardTitle>Risk Assessment</CardTitle>
      <div className="flex items-center gap-6">
        <div
          className={`flex h-24 w-24 flex-col items-center justify-center rounded-full ring-8 ${v.ring}`}
        >
          <span className="text-3xl font-bold">{risk.score}</span>
          <span className="text-[10px] text-slate-400">/ 100</span>
        </div>
        <div>
          <Badge tone={v.tone}>{risk.verdict}</Badge>
          <div className="mt-2 h-2 w-56 rounded-full bg-slate-100">
            <div
              className={`h-2 rounded-full ${v.bar}`}
              style={{ width: `${Math.min(100, risk.score)}%` }}
            />
          </div>
        </div>
      </div>

      <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
        {risk.explanation}
      </pre>

      <div className="mt-4">
        <CardTitle>Triggered Signals</CardTitle>
        {risk.signals?.length === 0 && (
          <p className="text-sm text-slate-400">
            No signals triggered — invoice is clean.
          </p>
        )}
        <ul className="space-y-2">
          {risk.signals?.map((s: any) => (
            <li
              key={s.signal_code}
              className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2"
            >
              <div>
                <div className="text-sm font-medium">{s.signal_label}</div>
                <div className="text-xs text-slate-400">
                  {s.signal_code} · {JSON.stringify(s.details)}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  tone={
                    s.severity === "high"
                      ? "red"
                      : s.severity === "medium"
                      ? "amber"
                      : "slate"
                  }
                >
                  {s.severity}
                </Badge>
                <span className="text-sm font-semibold text-slate-700">
                  +{s.signal_score}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}
