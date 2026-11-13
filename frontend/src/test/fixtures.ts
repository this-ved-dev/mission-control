import type { Report, Step } from "../api/client";

export const step = (over: Partial<Step>): Step => ({
  seq: 1, step: "limits_check", kind: "code", model: null, started_at: "2026-11-13T15:00:00.000+00:00",
  duration_ms: 1, input_tokens: 0, output_tokens: 0, cost_usd: "0", status: "ok", output: {}, ...over,
});

export const report = (over: Partial<Report> = {}): Report => ({
  id: 1, created_at: "2026-11-13T15:00:00.000+00:00", name: "Priya Shah", station: "PROP",
  wind_knots: 12, temp_c: 9, fuel_pct: 99, note: "Valve 2 slow to close.", status: "pending_approval",
  verdict: "go", violations: [], subsystem: "propulsion", severity: "medium",
  effective_severity: "medium", classify_fallback: false, brief_by_minutes: 15,
  brief_by_deadline: "2026-11-13T15:15:00.000+00:00", checks: null, rounds: [], briefing: "GO.",
  warnings: [], total_cost_usd: "0", approved_by: null, approved_at: null, steps: [], ...over,
});
