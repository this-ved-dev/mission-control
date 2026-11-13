import { useState } from "react";
import type { Approval, Report } from "../api/client";
import { waitingOnHuman } from "../lib";

export function ApprovePanel({ report, onApprove }: { report: Report; onApprove: (a: Approval) => Promise<void> }) {
  const [approver, setApprover] = useState("");
  const [ack, setAck] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (report.status === "approved") {
    return (
      <div className="approve done" role="status">
        <span className="key-icon" aria-hidden="true">⚿</span>
        Approved by {report.approved_by} at {new Date(report.approved_at!).toLocaleTimeString()}
      </div>
    );
  }
  const flagged = report.status === "needs_review";
  const ready = waitingOnHuman(report) && approver.trim() !== "" && (!flagged || ack) && !busy;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await onApprove({ approver: approver.trim(), acknowledged_flag: flagged && ack });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="approve" onSubmit={submit}>
      <p className="approve-why">Only a person can approve this briefing.</p>
      {flagged ? (
        <label className="ack">
          <input type="checkbox" checked={ack} onChange={(e) => setAck(e.target.checked)} />
          I have read the flagged note
        </label>
      ) : null}
      <div className="approve-row">
        <label>
          <span>Approver</span>
          <input value={approver} onChange={(e) => setApprover(e.target.value)} placeholder="Your name" autoComplete="name" />
        </label>
        <button type="submit" className="btn-approve" disabled={!ready}>
          Approve briefing
        </button>
      </div>
      {!waitingOnHuman(report) ? <p className="muted">Waiting for the pipeline ({report.status}).</p> : null}
      {error ? <p className="field-error" role="alert">{error}</p> : null}
    </form>
  );
}
