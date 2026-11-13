import type { Report } from "./api/client";

export function remaining(report: Report, now: number) {
  if (!report.brief_by_deadline || !report.brief_by_minutes) return null;
  const msLeft = Date.parse(report.brief_by_deadline) - now;
  const fraction = Math.min(1, Math.max(0, msLeft / (report.brief_by_minutes * 60_000)));
  return { msLeft, fraction, overdue: msLeft <= 0 };
}

export const clock = (ms: number) => {
  const s = Math.max(0, Math.round(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

export function boardOf(reports: Report[]) {
  const latest = new Map<string, Report>();
  for (const r of reports) if ((latest.get(r.station)?.id ?? -1) < r.id) latest.set(r.station, r);
  return [...latest.values()]
    .sort((a, b) => a.station.localeCompare(b.station))
    .map(({ station, verdict, status, id }) => ({ station, verdict, status, id }));
}

export const waitingOnHuman = (r: Report) => r.status === "pending_approval" || r.status === "needs_review";
