import { useCallback, useEffect, useState } from "react";
import { api, type Report } from "../api/client";
import { Dossier } from "../components/Dossier";
import { GoNoGoBoard } from "../components/GoNoGoBoard";
import { TraceCards } from "../components/TraceCards";
import { TransmissionQueue } from "../components/TransmissionQueue";

export function Console({ selected, onPick, bench }: { selected: number | null; onPick: (id: number) => void; bench?: (r: Report | undefined) => React.ReactNode }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState("");
  const [now, setNow] = useState(() => Date.now());

  const load = useCallback(() => {
    api.reports().then((r) => { setReports(r); setError(""); }, (e) => setError(String(e.message ?? e)));
  }, []);
  useEffect(() => {
    load();
    // shortcut: 1.5 s polling, upgrade to server-sent events if many consoles watch at once
    const poll = setInterval(load, 1500);
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => { clearInterval(poll); clearInterval(tick); };
  }, [load]);

  const current = reports.find((r) => r.id === selected) ?? reports[0];
  return (
    <div className="console">
      <GoNoGoBoard reports={reports} onPick={onPick} />
      {error ? <p className="banner" role="alert">Console offline: {error}</p> : null}
      <div className="console-grid">
        <TransmissionQueue reports={reports} selected={current?.id ?? null} now={now} onPick={onPick} />
        <div className="center">
          {bench?.(current)}
          {current ? <TraceCards steps={current.steps} total={current.total_cost_usd} /> : null}
        </div>
        {current ? <Dossier report={current} onChanged={load} /> : <section className="panel dossier empty muted">Select a transmission.</section>}
      </div>
    </div>
  );
}
