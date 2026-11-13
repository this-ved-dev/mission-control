import { useState } from "react";
import { api, type Approval, type Report } from "../api/client";
import { DialGauge } from "../figures/gauge/DialGauge";
import { SCALES } from "../figures/gauge/model";
import { ApprovePanel } from "./ApprovePanel";

const READINGS = ["wind_knots", "temp_c", "fuel_pct"] as const;

function Quarantine({ note, phrases }: { note: string; phrases: string[] }) {
  if (!phrases.length) return <blockquote className="note quarantine">{note}</blockquote>;
  const pattern = new RegExp(`(${phrases.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  return (
    <blockquote className="note quarantine">
      {note.split(pattern).map((part, i) => (i % 2 ? <mark key={i}>{part}</mark> : part))}
    </blockquote>
  );
}

export function Dossier({ report, onChanged }: { report: Report; onChanged: () => void }) {
  const [tab, setTab] = useState<number | null>(null);
  const checks = report.checks;
  const flagged = checks?.injection.flagged ?? false;
  const rounds = report.rounds;
  const shown = rounds.find((r) => r.round === tab) ?? rounds.at(-1);

  async function approve(body: Approval) {
    await api.approve(report.id, body);
    onChanged();
  }

  return (
    <section className="panel dossier" aria-label={`Report ${report.id}`}>
      <header className="dossier-head">
        <div>
          <p className="muted mono">#{report.id} · {report.station} · {report.name}</p>
          <p className="muted mono">{report.subsystem ?? "sorting…"}{report.classify_fallback ? " (fallback)" : ""} · {report.effective_severity ?? "—"}{report.severity && report.effective_severity !== report.severity ? ` (model said ${report.severity})` : ""}</p>
        </div>
        {report.verdict ? (
          <div className="stamp" data-verdict={report.verdict} role="status">
            <strong>{report.verdict === "go" ? "GO" : "NO-GO"}</strong>
            <span>from launch limits</span>
          </div>
        ) : <div className="stamp" data-verdict="pending">…</div>}
      </header>

      {report.violations.length ? (
        <ul className="violations">{report.violations.map((v) => <li key={v.field}>{v.message}</li>)}</ul>
      ) : null}

      <div className="gauges compact">
        {READINGS.map((k, i) => (
          <DialGauge key={k} fig={`Fig 2${"abc"[i]}`} scale={SCALES[k]} value={report[k]}
            violated={report.verdict ? report.violations.some((v) => v.field === k) : null} />
        ))}
      </div>

      {flagged ? (
        <div className="banner hazard" role="alert">
          <strong>Hidden instructions flagged.</strong> Verdict computed from readings only. {checks?.injection.reason}
        </div>
      ) : null}
      <Quarantine note={report.note} phrases={checks?.injection.phrases ?? []} />

      {checks ? (
        <div className="checks">
          <div className="check" data-on={flagged ? "" : undefined}><span className="check-icon" aria-hidden="true">⛨</span><div><strong>Instructions</strong><p>{flagged ? "flagged" : "none found"}</p></div></div>
          <div className="check" data-on={checks.missing.missing.length ? "" : undefined}><span className="check-icon" aria-hidden="true">☐</span><div><strong>Missing details</strong>
            {checks.missing.missing.length ? <ul>{checks.missing.missing.map((m) => <li key={m}>{m}</li>)}</ul> : <p>complete</p>}</div></div>
          <div className="check" data-on={checks.panic.panic ? "" : undefined}><span className={`wave${checks.panic.panic ? " rough" : ""}`} aria-hidden="true" /><div><strong>Tone</strong><p>{checks.panic.panic ? "panicked" : "calm"}</p></div></div>
        </div>
      ) : null}

      <div className="briefing">
        <div className="panel-head">
          <h3>Briefing</h3>
          <div className="tabs" role="tablist">
            {rounds.map((r) => (
              <button key={r.round} role="tab" aria-selected={shown?.round === r.round} onClick={() => setTab(r.round)}>
                Draft {r.round} {r.approved ? "✓" : "✗"}
              </button>
            ))}
          </div>
        </div>
        {shown ? (
          <>
            <p className="briefing-text">{shown.draft}</p>
            {shown.feedback ? <p className="margin-note"><span className="mono">REVIEWER</span> {shown.feedback}</p> : null}
          </>
        ) : <p className="muted">{report.status === "error" ? "Pipeline stopped before a briefing was drafted." : "Drafting…"}</p>}
      </div>

      {report.warnings.length ? <ul className="warnings">{report.warnings.map((w) => <li key={w}>{w}</li>)}</ul> : null}
      {report.status === "error" ? (
        <button className="btn-secondary" onClick={() => api.retry(report.id).then(onChanged)}>Retry pipeline</button>
      ) : null}
      <ApprovePanel report={report} onApprove={approve} />
    </section>
  );
}
