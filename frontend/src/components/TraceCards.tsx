import type { Step } from "../api/client";

const LABEL: Record<string, string> = {
  limits_check: "Launch limits", classify: "Classify", brief_by: "Brief-by time",
  check_injection: "Hidden instructions", check_missing: "Missing details", check_panic: "Panic tone",
  cost_total: "Cost total",
};
const label = (name: string) => LABEL[name] ?? name.replace(/^(draft|review)_(\d)$/, (_, kind, n) => `${kind === "draft" ? "Draft" : "Review"} ${n}`);

/** One card per step, placed on a time axis so the three parallel checks visibly overlap. */
export function TraceCards({ steps, total }: { steps: Step[]; total: string }) {
  const t0 = steps.length ? Math.min(...steps.map((s) => Date.parse(s.started_at))) : 0;
  const end = Math.max(1, ...steps.map((s) => Date.parse(s.started_at) - t0 + s.duration_ms));
  return (
    <section className="trace" aria-label="Pipeline trace">
      <header className="panel-head">
        <h2>Trace</h2>
        <span className="mono">total ${total}</span>
      </header>
      <ol className="trace-cards">
        {steps.map((s) => {
          const at = Date.parse(s.started_at) - t0;
          return (
            <li key={s.seq} className="trace-card" data-kind={s.kind} data-status={s.status} id={`step-${s.step}`}>
              <div className="trace-top">
                <span className="tag">{s.kind === "code" ? "CODE" : "MODEL"}</span>
                <strong>{label(s.step)}</strong>
                {s.status !== "ok" ? <span className="tag warn">{s.status}</span> : null}
              </div>
              <div className="trace-bar" aria-hidden="true">
                <span style={{ left: `${(at / end) * 100}%`, width: `max(3px, ${(s.duration_ms / end) * 100}%)` }} />
              </div>
              <div className="trace-meta mono">
                <span>{s.input_tokens} in · {s.output_tokens} out</span>
                <span>{s.duration_ms} ms</span>
                <span>${s.cost_usd}</span>
              </div>
              {s.model ? <div className="trace-model mono">{s.model}</div> : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
