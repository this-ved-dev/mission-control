import { useEffect, useRef } from "react";
import type { Report } from "../../api/client";
import { Plate } from "../../iso/react/draw";
import { follow, spring, useInView, useLoop, useReadout, useStillness, type Spring } from "../../iso/react/live";
import { ART, HEAD_XS, HEIGHT, STOPS, WIDTH, canister, carriage, flap, flapAngle, gaugePins, key, plunger, stamp, tally, timerHands, translate, typeCarriage } from "./art";
import { poseOf, type Pose } from "./model";

const html = (s: string) => ({ __html: s });
const PIN_LIFT = 12;
const DROP = 70;
const PLUNGE = 22;

// shortcut: the idle tour replays one canned report; swap for a recorded real run if one is wanted
const TOUR: Pose[] = [0, 1, 2, 3, 4, 5].map((stop) => ({
  stop, pins: [false, stop >= 1, false], verdict: stop >= 1 ? "no_go" : null, bin: stop >= 2 ? 0 : null, timer: 0.8,
  inspecting: stop === 3, found: [stop >= 3, false, stop >= 3], rounds: stop >= 4 ? 2 : 0, reviewing: stop === 4,
  keyTurned: false, readout: "demo run · select a transmission to load its report",
}));

export function Bench({ report }: { report: Report | undefined }) {
  const stage = useRef<HTMLDivElement>(null);
  const inView = useInView(stage);
  const calm = useStillness();
  const { anchor, say } = useReadout<HTMLDivElement>();
  const refs = {
    pins: useRef<SVGGElement>(null), lamp: useRef<SVGGElement>(null), flap: useRef<SVGGElement>(null),
    hands: useRef<SVGGElement>(null), type: useRef<SVGGElement>(null), tally: useRef<SVGGElement>(null),
    key: useRef<SVGGElement>(null), carriage: useRef<SVGGElement>(null), canister: useRef<SVGGElement>(null),
    plungers: useRef<SVGGElement>(null), heads: useRef<SVGGElement>(null), stamp: useRef<SVGGElement>(null),
  };
  const s = useRef({
    x: { at: STOPS[0], rate: 0 } as Spring, drop: { at: 0, rate: 0 } as Spring, pins: [0, 0, 0].map(() => ({ at: 0, rate: 0 }) as Spring),
    flap: flapAngle(1), plunge: 0, type: 0, key: 0, clock: 0, last: { pins: "", flap: NaN, key: NaN, hands: "" }, id: -1,
  });
  const reportRef = useRef(report);
  useEffect(() => {
    reportRef.current = report;
  }, [report]);

  // A newly selected report drops out of the pneumatic tube.
  useEffect(() => {
    if (report && report.id !== s.current.id) {
      s.current.id = report.id;
      s.current.drop = { at: DROP, rate: 0 };
      s.current.x = { at: STOPS[0], rate: 0 };
    }
  }, [report]);

  const kick = useLoop((dt, still) => {
    const st = s.current;
    st.clock += dt;
    const r = reportRef.current;
    const pose = r ? poseOf(r, Date.now()) : TOUR[Math.floor(st.clock / 2.6) % TOUR.length];
    const moving = [
      !spring(st.x, STOPS[pose.stop], dt, 40, 11, still),
      !spring(st.drop, 0, dt, 60, 9, still),
      ...pose.pins.map((v, i) => !spring(st.pins[i], v && pose.stop >= 1 ? PIN_LIFT : 0, dt, 120, 12, still)),
    ].some(Boolean);
    const want = {
      flap: pose.bin === null ? flapAngle(1) : flapAngle(pose.bin),
      plunge: pose.stop === 3 ? PLUNGE : 0,
      type: -6 * pose.rounds,
      key: pose.keyTurned ? 1 : 0,
    };
    st.flap = follow(st.flap, want.flap, dt, 0.35, still);
    st.plunge = follow(st.plunge, want.plunge, dt, 0.3, still);
    st.type = follow(st.type, want.type, dt, 0.4, still);
    st.key = follow(st.key, want.key, dt, 0.5, still);
    const press = pose.reviewing && pose.stop === 4 && !still ? 6 * Math.max(0, Math.sin(st.clock * 4)) : 0;

    refs.carriage.current?.setAttribute("transform", translate([st.x.at, 0, 0]));
    refs.canister.current?.setAttribute("transform", translate([st.x.at, 0, st.drop.at]));
    const pins = st.pins.map((p) => p.at.toFixed(2)).join();
    if (pins !== st.last.pins && refs.pins.current) refs.pins.current.innerHTML = gaugePins(st.pins.map((p) => p.at));
    if (Math.abs(st.flap - st.last.flap) > 1e-3 || Number.isNaN(st.last.flap)) {
      if (refs.flap.current) refs.flap.current.innerHTML = flap(st.flap);
      st.last.flap = st.flap;
    }
    const hands = `${pose.bin}:${pose.timer.toFixed(3)}`;
    if (hands !== st.last.hands && refs.hands.current) refs.hands.current.innerHTML = timerHands(pose.bin, pose.timer);
    if (Math.abs(st.key - st.last.key) > 1e-3 || Number.isNaN(st.last.key)) {
      if (refs.key.current) refs.key.current.innerHTML = key(st.key, pose.keyTurned);
      st.last.key = st.key;
    }
    st.last = { ...st.last, pins, hands };
    refs.type.current?.setAttribute("transform", translate([st.type, 0, 0]));
    refs.stamp.current?.setAttribute("transform", translate([0, 0, -press]));
    refs.plungers.current?.querySelectorAll(":scope > g").forEach((g, i) => g.setAttribute("transform", translate([HEAD_XS[i], 0, -st.plunge])));
    refs.lamp.current?.setAttribute("data-verdict", pose.stop >= 1 && pose.verdict ? pose.verdict : "");
    refs.heads.current?.querySelectorAll(".bench-led").forEach((led, i) => led.toggleAttribute("data-on", pose.found[i] && pose.stop >= 3));
    refs.tally.current?.querySelectorAll(".bench-tally").forEach((t, i) => t.toggleAttribute("data-on", i < pose.rounds));
    say(pose.readout);
    // keep running while something moves, a stamp is pressing, a timer runs, or the tour plays
    return inView && (moving || press > 0 || !r || pose.bin !== null || Math.abs(st.flap - want.flap) > 1e-3 || Math.abs(st.plunge - want.plunge) > 1e-3 || Math.abs(st.type - want.type) > 1e-3 || Math.abs(st.key - want.key) > 1e-3);
  }, inView);

  useEffect(() => {
    if (inView) kick();
  }, [report, inView, calm, kick]);

  return (
    <div className="bench" ref={anchor}>
      <Plate
        fig="Fig 1"
        title="The Go/No-Go Bench"
        hint="Select a transmission to run it"
        readout={report ? poseOf(report, 0).readout : "demo run"}
        keys={[
          { mark: "lit", label: "The report's canister" },
          { mark: "raised", label: "Six stations, one per pipeline step" },
          { mark: "green", label: "Lamp: the verdict from plain code" },
        ]}
        caption="The canister drops from the pneumatic tube and rides the rail. Three go/no-go gauges test the readings and a pin that stops high is a limit broken. The flap sorts it into the 5, 15 or 30 minute bin, and that bin's timer runs down to the brief-by deadline. Three inspection heads drop together because the checks run in parallel. The typewriter advances one step per draft and the stamp presses on each review, up to three. The key turns only when a person approves."
      >
        <div className="iso-stage bench-stage" ref={stage}>
          <svg className="iso-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="An isometric bench machine that shows the report moving through the pipeline">
            <g dangerouslySetInnerHTML={html(ART.back)} />
            <g ref={refs.pins} dangerouslySetInnerHTML={html(gaugePins([0, 0, 0]))} />
            <g ref={refs.lamp} className="bench-lamp-wrap" dangerouslySetInnerHTML={html(ART.afterPins)} />
            <g ref={refs.flap} dangerouslySetInnerHTML={html(flap(flapAngle(1)))} />
            <g ref={refs.hands} dangerouslySetInnerHTML={html(timerHands(null, 0))} />
            <g dangerouslySetInnerHTML={html(ART.afterFlap)} />
            <g ref={refs.type} dangerouslySetInnerHTML={html(typeCarriage())} />
            <g ref={refs.tally} dangerouslySetInnerHTML={html(tally())} />
            <g dangerouslySetInnerHTML={html(ART.afterType)} />
            <g ref={refs.key} dangerouslySetInnerHTML={html(key(0, false))} />
            <g dangerouslySetInnerHTML={html(ART.afterKey)} />
            <g ref={refs.carriage} transform={translate([STOPS[0], 0, 0])} dangerouslySetInnerHTML={html(carriage())} />
            <g ref={refs.canister} transform={translate([STOPS[0], 0, 0])} dangerouslySetInnerHTML={html(canister())} />
            <g dangerouslySetInnerHTML={html(ART.tube)} />
            <g ref={refs.plungers} dangerouslySetInnerHTML={html(HEAD_XS.map((x) => `<g transform="${translate([x, 0, 0])}">${plunger()}</g>`).join(""))} />
            <g ref={refs.heads} dangerouslySetInnerHTML={html(ART.heads)} />
            <g ref={refs.stamp} dangerouslySetInnerHTML={html(stamp())} />
            <g dangerouslySetInnerHTML={html(ART.stampArm)} />
          </svg>
        </div>
      </Plate>
    </div>
  );
}
