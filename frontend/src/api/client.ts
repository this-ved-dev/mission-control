import type { components } from "./schema";

type S = components["schemas"];
export type Report = S["ReportOut"];
export type Step = S["Step"];
export type ReportIn = S["ReportIn"];
export type LimitResult = S["LimitResult"];
export type Approval = S["Approval"];

export class ApiError extends Error {
  status: number;
  fields: Record<string, string>;
  constructor(status: number, fields: Record<string, string>, message: string) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

async function call<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init && { ...init, headers: { "content-type": "application/json" } });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const fields = body.errors ?? {};
    throw new ApiError(res.status, fields, body.detail ?? Object.values(fields).join("; ") ?? res.statusText);
  }
  return body as T;
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  reports: () => call<Report[]>("/api/reports"),
  file: (report: ReportIn) => call<{ id: number }>("/api/reports", post(report)),
  limits: (r: Pick<ReportIn, "wind_knots" | "temp_c" | "fuel_pct">) => call<LimitResult>("/api/limits/check", post(r)),
  approve: (id: number, body: Approval) => call<Report>(`/api/reports/${id}/approve`, post(body)),
  retry: (id: number) => call<{ id: number }>(`/api/reports/${id}/retry`, post({})),
};
