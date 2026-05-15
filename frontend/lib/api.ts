const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

const TOKEN_KEY = "payguard_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401 && typeof window !== "undefined") {
    clearToken();
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: async (email: string, password: string) => {
    const res = await request<{ access_token: string }>("/auth/login-json", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(res.access_token);
    return res;
  },
  me: () => request<any>("/auth/me"),
  dashboard: () => request<any>("/dashboard/summary"),
  invoices: (status?: string) =>
    request<any[]>(`/invoices${status ? `?status=${status}` : ""}`),
  reviewQueue: () => request<any[]>("/invoices/review-queue"),
  invoice: (id: string) => request<any>(`/invoices/${id}`),
  uploadInvoice: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<any>("/invoices/upload", { method: "POST", body: fd });
  },
  updateInvoice: (id: string, body: any) =>
    request<any>(`/invoices/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  extractionStatus: (id: string) =>
    request<any>(`/invoices/${id}/extraction-status`),
  checks: (id: string) => request<any[]>(`/invoices/${id}/verification-checks`),
  risk: (id: string) => request<any>(`/invoices/${id}/risk`),
  runExtract: (id: string) =>
    request<any>(`/pipeline/${id}/extract`, { method: "POST" }),
  runVerify: (id: string) =>
    request<any[]>(`/pipeline/${id}/verify`, { method: "POST" }),
  runAssess: (id: string) =>
    request<any>(`/pipeline/${id}/assess`, { method: "POST" }),
  vendor: (id: string) => request<any>(`/vendors/${id}`),
  vendorInvoices: (id: string) => request<any[]>(`/vendors/${id}/invoices`),
  vendorHistory: (id: string) =>
    request<any[]>(`/vendors/${id}/verification-history`),
  paymentAction: (id: string, action: string) =>
    request<any>(`/payments/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  payments: () => request<any[]>("/payments"),
  audit: (entityType?: string, entityId?: string) => {
    const q = new URLSearchParams();
    if (entityType) q.set("entity_type", entityType);
    if (entityId) q.set("entity_id", entityId);
    const qs = q.toString();
    return request<any[]>(`/audit${qs ? `?${qs}` : ""}`);
  },
};
