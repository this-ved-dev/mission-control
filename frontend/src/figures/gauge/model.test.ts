import { describe, expect, it } from "vitest";
import { SCALES, bandOf, sweepOf } from "./model";

describe("gauge model", () => {
  it("maps a reading to a share of the sweep and clamps outside the face", () => {
    expect(sweepOf(SCALES.wind_knots, 0)).toBe(0);
    expect(sweepOf(SCALES.wind_knots, 40)).toBe(1);
    expect(sweepOf(SCALES.wind_knots, 25)).toBeCloseTo(25 / 40);
    expect(sweepOf(SCALES.wind_knots, 90)).toBe(1);
    expect(sweepOf(SCALES.fuel_pct, 50)).toBe(0);
  });

  it("draws the legal band from the published launch limits", () => {
    expect(bandOf(SCALES.wind_knots)).toEqual([0, 25 / 40]);
    expect(bandOf(SCALES.temp_c)).toEqual([14 / 40, 1]);
    const [from, to] = bandOf(SCALES.fuel_pct);
    expect(from).toBeCloseTo(3 / 7);
    expect(to).toBeCloseTo(5 / 7);
  });
});
