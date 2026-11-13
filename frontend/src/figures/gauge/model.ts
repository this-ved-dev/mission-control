/** Gauge faces. The bands mirror backend/app/limits.py for drawing only; the verdict always comes from the API. */
export interface Scale {
  key: "wind_knots" | "temp_c" | "fuel_pct";
  label: string;
  unit: string;
  min: number;
  max: number;
  lo?: number;
  hi?: number;
  step: number;
  every: number;
}

export const SCALES = {
  wind_knots: { key: "wind_knots", label: "Wind", unit: "kt", min: 0, max: 40, hi: 25, step: 1, every: 5 },
  temp_c: { key: "temp_c", label: "Temp", unit: "°C", min: -10, max: 30, lo: 4, step: 1, every: 5 },
  fuel_pct: { key: "fuel_pct", label: "Fuel", unit: "%", min: 95, max: 102, lo: 98, hi: 100, step: 0.25, every: 4 },
} satisfies Record<string, Scale>;

const share = (s: Scale, v: number) => Math.min(1, Math.max(0, (v - s.min) / (s.max - s.min)));

export const sweepOf = (s: Scale, value: number) => share(s, value);

export const bandOf = (s: Scale): [number, number] => [share(s, s.lo ?? s.min), share(s, s.hi ?? s.max)];
