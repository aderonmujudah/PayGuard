import * as React from "react";
import { cn } from "@/lib/utils";

export function Button({
  className,
  variant = "default",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost" | "danger" | "success" | "warn";
}) {
  const variants: Record<string, string> = {
    default: "bg-brand-600 text-white hover:bg-brand-700",
    outline: "border border-slate-300 bg-white hover:bg-slate-50",
    ghost: "hover:bg-slate-100",
    danger: "bg-red-600 text-white hover:bg-red-700",
    success: "bg-emerald-600 text-white hover:bg-emerald-700",
    warn: "bg-amber-500 text-white hover:bg-amber-600",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("card p-5", className)} {...props} />;
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-sm font-semibold text-slate-500 mb-3", className)}
      {...props}
    />
  );
}

export function Input({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100",
        className
      )}
      {...props}
    />
  );
}

export function Badge({
  children,
  tone = "slate",
}: {
  children: React.ReactNode;
  tone?: "slate" | "green" | "red" | "amber" | "blue";
}) {
  const tones: Record<string, string> = {
    slate: "bg-slate-100 text-slate-700",
    green: "bg-emerald-100 text-emerald-700",
    red: "bg-red-100 text-red-700",
    amber: "bg-amber-100 text-amber-800",
    blue: "bg-blue-100 text-blue-700",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tones[tone]
      )}
    >
      {children}
    </span>
  );
}

const STATUS_TONE: Record<string, "slate" | "green" | "red" | "amber" | "blue"> =
  {
    uploaded: "slate",
    extracting: "blue",
    extracted: "blue",
    verifying: "blue",
    verified: "blue",
    cleared: "green",
    CLEAR: "green",
    review: "amber",
    REVIEW: "amber",
    hold: "amber",
    HOLD: "amber",
    blocked: "red",
    BLOCK: "red",
    failed: "red",
    passed: "green",
    pending: "slate",
    success: "green",
  };

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={STATUS_TONE[status] || "slate"}>{status}</Badge>;
}

export function Empty({ label }: { label: string }) {
  return (
    <div className="py-10 text-center text-sm text-slate-400">{label}</div>
  );
}

export function Spinner() {
  return (
    <div className="py-10 text-center text-sm text-slate-400 animate-pulse">
      Loading…
    </div>
  );
}
