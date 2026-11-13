/** Maps one report (the API response) to the pose of every moving part on the bench. Pure. */
import type { Report } from "../../api/client.ts";

export const STATIONS = ["tube", "gauges", "sorter", "inspect", "typewriter", "key"] as const;
const READINGS = ["wind_knots", "temp_c", "fuel_pct"] as const;
const BINS = { high: 0, medium: 1, low: 2 } as const;

export interface Pose {
  stop: number;
  pins: [boolean, boolean, boolean];
  verdict: "go" | "no_go" | null;
  bin: 0 | 1 | 2 | null;
  timer: number;
  inspecting: boolean;
  found: [boolean, boolean, boolean];
  rounds: number;
  reviewing: boolean;
  keyTurned: boolean;
  readout: string;
}

function stopOf(r: Report): number {
  if (r.status === "pending_approval" || r.status === "needs_review" || r.status === "approved") return 5;
  const names = r.steps.map((s) => s.step);
  if (names.some((n) => /^(draft|review)_/.test(n))) return 4;
  if (names.some((n) => n.startsWith("check_"))) return 3;
  if (names.includes("brief_by") || names.includes("classify")) return 2;
  if (names.includes("limits_check")) return 1;
  return 0;
}

export function poseOf(r: Report, now: number): Pose {
  const violated = (k: string) => r.violations.some((v) => v.field === k);
  const deadline = r.brief_by_deadline ? Date.parse(r.brief_by_deadline) : null;
  const timer = deadline && r.brief_by_minutes ? Math.min(1, Math.max(0, (deadline - now) / (r.brief_by_minutes * 60_000))) : 0;
  const c = r.checks;
  const last = r.steps.at(-1)?.step ?? "";
  const verdict = r.verdict ?? null;
  const waiting = r.status === "pending_approval" || r.status === "needs_review";
  const parts = [
    `#${r.id} ${r.station}`,
    verdict ? (verdict === "go" ? "GO" : "NO-GO") : "checking limits",
    r.brief_by_minutes ? `brief in ${r.brief_by_minutes} min` : null,
    r.status === "approved" ? `approved by ${r.approved_by}` : waiting ? "waiting for a person" : r.status === "error" ? "pipeline stopped" : "in the pipeline",
  ];
  return {
    stop: stopOf(r),
    pins: READINGS.map(violated) as Pose["pins"],
    verdict,
    bin: r.effective_severity ? BINS[r.effective_severity] : null,
    timer,
    inspecting: r.status === "processing" && last.startsWith("check_"),
    found: [c?.injection.flagged ?? false, (c?.missing.missing.length ?? 0) > 0, c?.panic.panic ?? false],
    rounds: Math.min(3, r.rounds.length || r.steps.filter((s) => s.step.startsWith("draft_")).length),
    reviewing: r.status === "processing" && last.startsWith("draft_"),
    keyTurned: r.status === "approved",
    readout: parts.filter(Boolean).join(" · "),
  };
}
