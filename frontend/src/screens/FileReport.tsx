import { useEffect, useState } from "react";
import { ApiError, api, type LimitResult } from "../api/client";
import { DialGauge } from "../figures/gauge/DialGauge";
import { SCALES } from "../figures/gauge/model";

const FIELDS = [
  { key: "name", label: "Name", kind: "text" },
  { key: "station", label: "Station", kind: "text" },
  { key: "wind_knots", label: "Wind (kt)", kind: "number" },
  { key: "temp_c", label: "Temp (°C)", kind: "number" },
  { key: "fuel_pct", label: "Fuel (%)", kind: "number" },
] as const;
const READINGS = ["wind_knots", "temp_c", "fuel_pct"] as const;
const STATIONS = ["PROP", "GNC", "COMMS", "WX", "GND", "RSO", "AVIONICS"];
const EMPTY = { name: "", station: "", wind_knots: "", temp_c: "", fuel_pct: "", note: "" };
type Form = typeof EMPTY;

const num = (v: string) => (v.trim() === "" ? null : Number(v));

export function FileReport({ onFiled }: { onFiled: (id: number) => void }) {
  const [form, setForm] = useState<Form>(EMPTY);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [checked, setChecked] = useState<{ key: string; result: LimitResult } | null>(null);
  const [busy, setBusy] = useState(false);

  // Live gauges ask the server's plain-code limits check; no rule is copied into the browser.
  const readings = READINGS.map((k) => num(form[k]));
  const key = readings.join("|");
  useEffect(() => {
    const [wind_knots, temp_c, fuel_pct] = key.split("|").map((v) => (v === "" ? null : Number(v)));
    if ([wind_knots, temp_c, fuel_pct].some((v) => v === null || Number.isNaN(v))) return;
    const timer = setTimeout(() => {
      api.limits({ wind_knots: wind_knots!, temp_c: temp_c!, fuel_pct: fuel_pct! }).then((result) => setChecked({ key, result }), () => {});
    }, 250);
    return () => clearTimeout(timer);
  }, [key]);

  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    try {
      const body = { ...form, wind_knots: num(form.wind_knots), temp_c: num(form.temp_c), fuel_pct: num(form.fuel_pct) };
      const { id } = await api.file(body as never);
      setForm(EMPTY);
      onFiled(id);
    } catch (err) {
      setErrors(err instanceof ApiError ? { ...err.fields, ...(err.status !== 422 ? { body: err.message } : {}) } : { body: String(err) });
    } finally {
      setBusy(false);
    }
  }

  // Only trust a check made for the readings currently in the form.
  const limits = checked?.key === key ? checked.result : null;
  const violated = (k: string) => (limits ? limits.violations.some((v) => v.field === k) : null);
  const field = (k: keyof Form, label: string, input: React.ReactNode) => (
    <label className="field" key={k}>
      <span>{label}</span>
      {input}
      {errors[k] ? <span className="field-error" id={`${k}-error`}>{errors[k]}</span> : null}
    </label>
  );
  const aria = (k: string) => ({ "aria-invalid": errors[k] ? true : undefined, "aria-describedby": errors[k] ? `${k}-error` : undefined });

  return (
    <div className="file-screen">
      <form className="panel file-form" onSubmit={submit} noValidate>
        <header className="panel-head">
          <h2>File anomaly report</h2>
          <span className="muted">Goes straight to the Flight Director's console</span>
        </header>
        <div className="field-grid">
          {FIELDS.map(({ key: k, label, kind }) =>
            field(k, label, (
              <input
                name={k} value={form[k]} onChange={set(k)} type={kind} step={kind === "number" ? "any" : undefined}
                inputMode={kind === "number" ? "decimal" : undefined} list={k === "station" ? "stations" : undefined}
                className={kind === "number" ? "mono" : undefined} {...aria(k)}
              />
            )),
          )}
        </div>
        <datalist id="stations">{STATIONS.map((s) => <option key={s} value={s} />)}</datalist>
        {field("note", "Note", <textarea name="note" rows={5} value={form.note} onChange={set("note")} {...aria("note")} placeholder="What did you see, when, which component, measured value, did it recover?" />)}
        {errors.body ? <p className="field-error" role="alert">{errors.body}</p> : null}
        <div className="file-actions">
          <span className="muted mono">
            {limits ? (limits.verdict === "go" ? "Readings within launch limits" : `${limits.violations.length} reading(s) outside launch limits`) : "Enter all three readings to check limits"}
          </span>
          <button type="submit" className="btn-primary" disabled={busy}>File report</button>
        </div>
      </form>
      <div className="gauges" aria-label="Live readings against launch limits">
        {READINGS.map((k, i) => (
          <DialGauge key={k} fig={`Fig 2${"abc"[i]}`} scale={SCALES[k]} value={readings[i]} violated={violated(k)} />
        ))}
      </div>
    </div>
  );
}
