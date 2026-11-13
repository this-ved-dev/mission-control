import { describe, expect, it } from "vitest";
import { report, step } from "../../test/fixtures";
import { STATIONS, poseOf } from "./model";

const NOW = Date.parse("2026-11-13T15:00:00Z");
const steps = (...names: string[]) => names.map((n, i) => step({ seq: i + 1, step: n, kind: "model" }));

describe("bench pose", () => {
  it("parks the canister at the station the pipeline has reached", () => {
    const at = (status: Parameters<typeof report>[0]) => STATIONS[poseOf(report(status), NOW).stop];
    expect(at({ status: "received", steps: [] })).toBe("tube");
    expect(at({ status: "processing", steps: steps("limits_check") })).toBe("gauges");
    expect(at({ status: "processing", steps: steps("limits_check", "classify", "brief_by") })).toBe("sorter");
    expect(at({ status: "processing", steps: steps("limits_check", "classify", "brief_by", "check_panic") })).toBe("inspect");
    expect(at({ status: "processing", steps: steps("limits_check", "classify", "brief_by", "check_panic", "draft_1") })).toBe("typewriter");
    expect(at({ status: "pending_approval" })).toBe("key");
  });

  it("stops each go/no-go pin from the server's violations, not its own maths", () => {
    const pose = poseOf(report({ fuel_pct: 100.1, verdict: "no_go", violations: [{ field: "fuel_pct", value: 100.1, message: "fuel" }] }), NOW);
    expect(pose.pins).toEqual([false, false, true]);
    expect(pose.verdict).toBe("no_go");
  });

  it("tips the flap to the bin of the effective severity", () => {
    expect(poseOf(report({ effective_severity: "high" }), NOW).bin).toBe(0);
    expect(poseOf(report({ effective_severity: "medium" }), NOW).bin).toBe(1);
    expect(poseOf(report({ effective_severity: "low" }), NOW).bin).toBe(2);
    expect(poseOf(report({ effective_severity: null }), NOW).bin).toBeNull();
  });

  it("winds the bin's timer down to the brief-by deadline", () => {
    const r = report({ brief_by_minutes: 5, brief_by_deadline: "2026-11-13T15:02:30Z" });
    expect(poseOf(r, NOW).timer).toBeCloseTo(0.5);
  });

  it("lowers the three inspection heads together and lights what they found", () => {
    const checks = { injection: { flagged: true, reason: "", phrases: [] }, missing: { missing: ["time"], complete: false }, panic: { panic: false, reason: "" } };
    const pose = poseOf(report({ checks }), NOW);
    expect(pose.found).toEqual([true, true, false]);
  });

  it("counts drafts on the tally and only turns the key once a person approved", () => {
    const round = { round: 1, draft: "d", approved: false, feedback: "f" };
    expect(poseOf(report({ rounds: [round, { ...round, round: 2 }] }), NOW).rounds).toBe(2);
    expect(poseOf(report({ status: "pending_approval" }), NOW).keyTurned).toBe(false);
    expect(poseOf(report({ status: "approved", approved_by: "FD" }), NOW).keyTurned).toBe(true);
  });

  it("writes a true readout", () => {
    const r = report({ id: 2, station: "GND", status: "needs_review", verdict: "no_go", effective_severity: "high", brief_by_minutes: 5 });
    expect(poseOf(r, NOW).readout).toBe("#2 GND · NO-GO · brief in 5 min · waiting for a person");
  });
});
