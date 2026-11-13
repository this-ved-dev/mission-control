import type { Report } from "../api/client";
import { boardOf } from "../lib";

const stateOf = (b: ReturnType<typeof boardOf>[number]) =>
  b.status === "needs_review" ? "review" : b.verdict === "no_go" ? "no_go" : b.verdict === "go" ? "go" : "pending";
const TEXT = { go: "GO", no_go: "NO-GO", review: "REVIEW", pending: "…" };

export function GoNoGoBoard({ reports, onPick }: { reports: Report[]; onPick: (id: number) => void }) {
  const board = boardOf(reports);
  return (
    <nav className="board" aria-label="Go/No-Go board, latest report per station">
      <span className="board-title">GO / NO-GO</span>
      {board.length === 0 ? <span className="muted">No stations reporting yet</span> : null}
      {board.map((b) => {
        const s = stateOf(b);
        return (
          <button key={b.station} className="board-tile" data-state={s} onClick={() => onPick(b.id)}>
            <span className="lamp" aria-hidden="true" />
            <span className="mono">{b.station}</span>
            <strong>{TEXT[s]}</strong>
          </button>
        );
      })}
    </nav>
  );
}
