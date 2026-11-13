import { describe, expect, it } from "vitest";
import { boardOf, remaining } from "./lib";
import { report } from "./test/fixtures";

describe("remaining", () => {
  it("drains from 1 to 0 across the brief-by window", () => {
    const r = report({ brief_by_minutes: 5, brief_by_deadline: "2026-11-13T15:05:00.000+00:00" });
    expect(remaining(r, Date.parse("2026-11-13T15:00:00Z")).fraction).toBeCloseTo(1);
    expect(remaining(r, Date.parse("2026-11-13T15:02:30Z")).fraction).toBeCloseTo(0.5);
    expect(remaining(r, Date.parse("2026-11-13T15:09:00Z"))).toMatchObject({ fraction: 0, overdue: true });
  });

  it("is null until the pipeline sets a deadline", () => {
    expect(remaining(report({ brief_by_deadline: null }), 0)).toBeNull();
  });
});

describe("boardOf", () => {
  it("shows the latest report per station", () => {
    const board = boardOf([
      report({ id: 1, station: "PROP", verdict: "go" }),
      report({ id: 3, station: "PROP", verdict: "no_go" }),
      report({ id: 2, station: "WX", verdict: "go", status: "needs_review" }),
    ]);
    expect(board).toEqual([
      { station: "PROP", verdict: "no_go", status: "pending_approval", id: 3 },
      { station: "WX", verdict: "go", status: "needs_review", id: 2 },
    ]);
  });
});
