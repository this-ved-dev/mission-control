import type { Report } from "../api/client";
import { clock, remaining } from "../lib";

const ICON: Record<string, string> = {
  received: "◌", processing: "◍", pending_approval: "●", needs_review: "⚠", approved: "✓", error: "✕",
};

export function TransmissionQueue({ reports, selected, now, onPick }: {
  reports: Report[]; selected: number | null; now: number; onPick: (id: number) => void;
}) {
  return (
    <section className="panel queue" aria-label="Transmissions">
      <header className="panel-head"><h2>Transmissions</h2><span className="muted mono">{reports.length}</span></header>
      {reports.length === 0 ? <p className="muted empty">No reports yet. File one from the console input.</p> : null}
      <ul>
        {reports.map((r) => {
          const left = r.status === "approved" ? null : remaining(r, now);
          return (
            <li key={r.id}>
              <button className="tx" aria-current={r.id === selected} data-status={r.status} data-verdict={r.verdict ?? ""} onClick={() => onPick(r.id)}>
                <span className="ring" style={{ "--left": left?.fraction ?? 0 } as React.CSSProperties} data-overdue={left?.overdue ? "" : undefined} aria-hidden="true">
                  <span>{ICON[r.status]}</span>
                </span>
                <span className="tx-main">
                  <span className="tx-line"><span className="mono">#{r.id} {r.station}</span>{r.verdict ? <span className="chip" data-verdict={r.verdict}>{r.verdict === "go" ? "GO" : "NO-GO"}</span> : null}</span>
                  <span className="tx-note">{r.note}</span>
                  <span className="tx-line muted mono">
                    <span>{r.effective_severity ?? r.status}</span>
                    <span>{left ? (left.overdue ? "brief overdue" : `brief in ${clock(left.msLeft)}`) : r.status.replace("_", " ")}</span>
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
