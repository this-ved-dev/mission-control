import { useEffect, useLayoutEffect, useRef } from "react";
import { Plate } from "../../iso/react/draw";
import { spring, useLoop, useStillness, type Spring } from "../../iso/react/live";
import { HEIGHT, WIDTH, hub, needlePath, staticArt } from "./art";
import { sweepOf, type Scale } from "./model";

interface Props {
  scale: Scale;
  value: number | null;
  /** From the API's limits check: the browser never judges a limit itself. */
  violated: boolean | null;
  fig: string;
}

export function DialGauge({ scale, value, violated, fig }: Props) {
  const needle = useRef<SVGPathElement>(null);
  const target = value === null || Number.isNaN(value) ? 0 : sweepOf(scale, value);
  const state = useRef<Spring>({ at: target, rate: 0 });
  const calm = useStillness();

  const kick = useLoop((dt, still) => {
    const done = spring(state.current, target, dt, 160, 14, still);
    needle.current?.setAttribute("d", needlePath(state.current.at));
    return !done;
  }, false);
  useLayoutEffect(() => {
    needle.current?.setAttribute("d", needlePath(state.current.at));
  }, []);
  useEffect(() => {
    kick();
  }, [target, kick, calm]);

  const reading = value === null || Number.isNaN(value) ? "—" : `${value} ${scale.unit}`;
  const status = violated === null ? "" : violated ? " · outside limit" : " · within limit";
  return (
    <div className="gauge" data-violated={violated ? "" : undefined}>
      <Plate fig={fig} title={scale.label} readout={reading + status}>
        <div className="iso-stage">
          <svg className="iso-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`${scale.label} gauge reading ${reading}${status}`}>
            <g dangerouslySetInnerHTML={{ __html: staticArt(scale) }} />
            <path ref={needle} className="iso-line" data-tone={violated ? "red" : "lit"} data-free="start" style={{ strokeWidth: 1.2 }} />
            <g dangerouslySetInnerHTML={{ __html: hub() }} />
          </svg>
        </div>
      </Plate>
    </div>
  );
}
