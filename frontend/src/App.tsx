import { useEffect, useState } from "react";
import { Bench } from "./figures/bench/Bench";
import { Console } from "./screens/Console";
import { FileReport } from "./screens/FileReport";

function useHash() {
  const [hash, setHash] = useState(location.hash);
  useEffect(() => {
    const on = () => setHash(location.hash);
    addEventListener("hashchange", on);
    return () => removeEventListener("hashchange", on);
  }, []);
  return hash;
}

function launchTime() {
  try {
    const saved = Number(sessionStorage.getItem("launch-at"));
    if (saved > Date.now()) return saved;
    const at = Date.now() + 90 * 60_000;
    sessionStorage.setItem("launch-at", String(at));
    return at;
  } catch {
    return Date.now() + 90 * 60_000;
  }
}

function TMinus() {
  const [at] = useState(launchTime);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const s = Math.max(0, Math.round((at - now) / 1000));
  const text = `T-${String(Math.floor(s / 3600)).padStart(2, "0")}:${String(Math.floor((s % 3600) / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
  return <span className="tminus mono" aria-label="Time to launch">{text}</span>;
}

export default function App() {
  const hash = useHash();
  const filing = hash.startsWith("#/file");
  const selected = Number(hash.match(/#\/report\/(\d+)/)?.[1]) || null;
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand"><span className="brand-mark" aria-hidden="true" />Mission Control<span className="muted"> · Meridian Launch Services</span></div>
        <TMinus />
        <nav className="nav">
          <a href="#/" aria-current={!filing ? "page" : undefined}>Flight Director</a>
          <a href="#/file" aria-current={filing ? "page" : undefined}>File report</a>
        </nav>
      </header>
      <main>
        {filing
          ? <FileReport onFiled={(id) => (location.hash = `#/report/${id}`)} />
          : <Console selected={selected} onPick={(id) => (location.hash = `#/report/${id}`)} bench={(r) => <Bench report={r} />} />}
      </main>
    </div>
  );
}
