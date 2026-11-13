/**
 * Fig 1: the Go/No-Go Bench. A report is a canister on a carriage that rides one rail past six
 * stations; each station's motion is one pipeline step.
 *
 * Parts list (about 110 solids):
 *  base     bench plate, 6 feet (pad + foot), inset groove, 4 corner screws, ruler strip with
 *           ticks, engraved label plate, 2 rails, 2 end stops
 *  carriage carriage plate, cradle collar, canister body (lit), 2 end caps, top knob, 4 bolt heads
 *  tube     post + foot collar, cantilever arm, clamp collar, tube, 2 band collars, flare, top cap
 *  gauges   rack base, 3 slot gauges with slot lines, 3 guide blocks, 3 pins + knobs, lamp
 *           pedestal, lamp housing, lens (verdict colour)
 *  sorter   back plate, 3 open bins, pivot post, hub, flap bar, 3 kitchen-timer dials with
 *           ticks, knurls and hands
 *  inspect  2 posts + foot collars, beam, 3 arms, 3 heads, 3 plungers + tips, lens ring, feeler
 *           comb, seismograph trace, 3 indicator lamps
 *  type     typewriter body, key field, carriage, 2 platen knobs, paper, 3 tally lamps;
 *           stamp post, 2 arms, rod, stamp block, ink pad
 *  key      console box, 4 screws, lock barrel, key bar + bow (lit when a person approves),
 *           guard posts + bar
 */
import * as k from "../../iso/iso-kit.ts";

export const WIDTH = 760;
export const HEIGHT = 400;

const BASE: k.Plan = { x: -236, y: -80, w: 472, d: 150, r: 8 };
const BASE_H = 10;
const FOOT_H = 6;
const RAILS = [30, 46];
const RAIL_TOP = 3;
export const STOPS = [-190, -110, -30, 60, 140, 205];
const CY = 40; // canister centre line on the carriage

export const P = k.fitProjection(
  [...k.boxCorners(BASE, -BASE_H - FOOT_H, 0), [-190, 38, 164], [-190, -30, 152], [60, -24, 122], [205, 40, 40]],
  WIDTH,
  HEIGHT,
  { pad: 16, azimuth: 58 },
);

const at = (p: k.Point3) => k.iso(p, P);
const S = (paths: k.SolidPaths, style: k.SolidStyle = {}) => k.solidSvg(paths, style);
const L = (d: string, style: Parameters<typeof k.lineSvg>[1] = {}) => k.lineSvg(d, style);
const D = (points: k.Flat[], style: Parameters<typeof k.dotsSvg>[1] = {}) => k.dotsSvg(points, style);
const slab = (x: number, y: number, w: number, d: number, z: number, h: number, r = 1, bevel = 0) =>
  k.slabOf({ x, y, w, d, r }, z, h, P, 6, bevel);
const cyl = (x: number, y: number, r: number, z: number, h: number, steps = 28) => k.cylinder(x, y, r, z, h, P, steps);
const byDepth = (points: k.Plane[]) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));

/** A bar lying flat, turned in plan about one end. */
function barRing(cx: number, cy: number, length: number, width: number, angle: number): k.Plane[] {
  const ux = Math.cos(angle), uy = Math.sin(angle), nx = -uy * width / 2, ny = ux * width / 2;
  return [[cx + nx, cy + ny], [cx + ux * length + nx, cy + uy * length + ny], [cx + ux * length - nx, cy + uy * length - ny], [cx - nx, cy - ny]];
}

function base() {
  const out = [`<path class="iso-halo" d="${k.haloOf(BASE, -BASE_H - FOOT_H, BASE_H, P)}"/>`];
  const feet: k.Plane[] = [[-218, -62], [0, -62], [218, -62], [-218, 52], [0, 52], [218, 52]];
  for (const [x, y] of byDepth(feet)) {
    out.push(S(cyl(x, y, 8, -BASE_H - FOOT_H, 1.8), { tone: "lo" }));
    out.push(S(cyl(x, y, 6, -BASE_H - FOOT_H + 1.8, FOOT_H - 1.8), { tone: "mid" }));
  }
  out.push(S(k.slabOf(BASE, -BASE_H, BASE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(BASE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(BASE, 11);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.4, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  const label = { x: -222, y: -71, w: 58, d: 11, r: 1 };
  out.push(S(k.slabOf(label, 0, 0.6, P, 3), { tone: "lo", crease: "none" }));
  out.push(D([at([label.x + 2.5, label.y + 5.5, 0.6]), at([label.x + label.w - 2.5, label.y + 5.5, 0.6])], { size: 0.4 }));
  out.push(k.faceTextSvg(k.topMatrix([label.x + label.w / 2, label.y + 7.4], 0.6, P), "GO / NO-GO", { size: 4.2, tone: "mid", anchor: "middle" }));
  return out.join("");
}

function ruler() {
  const strip = { x: -214, y: 57, w: 428, d: 7, r: 1 };
  const ticks = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 5, 5, strip.y + 0.8, 0.6, [2, 3.6], P);
  return [
    S(k.slabOf(strip, 0, 0.6, P, 3), { tone: "lo", crease: "none" }),
    L(ticks.minor, { tone: "lo" }),
    L(ticks.major, { tone: "mid" }),
    D([at([strip.x + 2, strip.y + 3.5, 0.6]), at([strip.x + strip.w - 2, strip.y + 3.5, 0.6])], { size: 0.45 }),
    // a station mark for each stop, so the canister's positions read off the ruler
    D(STOPS.map((x) => at([x, strip.y + 5.2, 0.6])), { size: 0.9, tone: "hi" }),
  ].join("");
}

function rails() {
  const out = [];
  for (const y of RAILS) {
    out.push(S(slab(-222, y, 444, 4, 0, RAIL_TOP, 1, 0.4), { tone: "mid" }));
    out.push(D([-214, -100, 0, 100, 214].map((x) => at([x, y + 2, RAIL_TOP])), { size: 0.4 }));
  }
  for (const x of [-230, 224]) {
    out.push(S(slab(x, 25, 6, 30, 0, 9, 1.2, 0.5), { tone: "mid" }));
    out.push(D([at([x + 3, 29, 9]), at([x + 3, 51, 9])], { size: 0.45 }));
  }
  return out.join("");
}

/** Drawn at x = 0; the live code moves it with translateAlong. */
export function carriage() {
  const out = [`<path class="iso-halo" d="${k.haloOf({ x: -13, y: 26, w: 26, d: 26, r: 3 }, 3, 0.1, P)}" style="filter:blur(4px)"/>`];
  out.push(S(slab(-15, 24, 30, 30, RAIL_TOP, 5, 2.5, 0.6), { tone: "mid" }));
  out.push(D([[-11, 28], [11, 28], [-11, 50], [11, 50]].map(([x, y]) => at([x, y, RAIL_TOP + 5])), { size: 0.5, tone: "lo" }));
  out.push(S(cyl(0, CY, 10, 8, 3, 36), { tone: "mid" }));
  return out.join("");
}

export function canister() {
  return [
    S(cyl(0, CY, 8.2, 11, 2.5, 32), { tone: "hi", crease: "lo" }),
    S(cyl(0, CY, 7.4, 13.5, 21, 32), { tone: "hi", lit: true, crease: "none" }),
    L(k.sideArc(0, CY, 7.4, 21, P, 20) + k.sideArc(0, CY, 7.4, 27, P, 20), { tone: "faint" }),
    S(cyl(0, CY, 8.2, 34.5, 2.5, 32), { tone: "hi", crease: "lo" }),
    S(cyl(0, CY, 2.6, 37, 3, 16), { tone: "mid" }),
  ].join("");
}

function tubePost() {
  const [x, y] = [-190, -30];
  return [
    S(cyl(x, y, 8, 0, 4), { tone: "mid" }),
    S(cyl(x, y, 4.5, 4, 146), { tone: "mid", crease: "none" }),
    L(k.sideArc(x, y, 4.5, 60, P, 14) + k.sideArc(x, y, 4.5, 100, P, 14), { tone: "faint" }),
  ].join("");
}

/** The pneumatic tube hangs over the rail, so it is drawn after the canister it delivers. */
function tube() {
  const [x, y] = [-190, CY];
  const out = [];
  out.push(S(cyl(x, y, 11.5, 44, 4, 36), { tone: "mid" }));
  out.push(S(cyl(x, y, 9.5, 48, 112, 36), { tone: "hi", crease: "none" }));
  for (const z of [78, 112]) {
    out.push(S(cyl(x, y, 10.6, z, 3, 36), { tone: "mid" }));
    out.push(D([at([x + 10.6 * 0.53, y + 10.6 * 0.85, z + 1.5])], { size: 0.45 }));
  }
  out.push(S(slab(x - 5, -34, 10, 72, 138, 8, 1.5, 0.5), { tone: "mid" }));
  out.push(D([at([x, -28, 146]), at([x, 26, 146])], { size: 0.45 }));
  out.push(S(cyl(x, y, 12.5, 134, 14, 36), { tone: "mid" }));
  out.push(L(k.knurl(x, y, 12.5, 134, 148, 40, P), { tone: "faint" }));
  out.push(S(cyl(x, y, 11, 160, 3, 36), { tone: "mid" }));
  out.push(L(k.ring(x, y, 7, 163, P, 32), { tone: "lo" }));
  return out.join("");
}

const GAUGE_X = [-126, -110, -94];
const GUIDE_TOP = 56;

function gaugeRack() {
  const out = [S(slab(-134, -52, 48, 32, 0, 6, 2, 0.6), { tone: "mid" })];
  out.push(D([[-130, -48], [-90, -48], [-130, -24], [-90, -24]].map(([x, y]) => at([x, y, 6])), { size: 0.45 }));
  for (const gx of GAUGE_X) {
    out.push(S(slab(gx - 2.2, -48, 4.4, 24, 6, 44, 0.6), { tone: "hi", crease: "lo" }));
    // the slot: GO depth at the bottom, NO-GO step above it
    out.push(L(k.pathOf([at([gx - 0.9, -24, 50]), at([gx - 0.9, -24, 16]), at([gx + 0.9, -24, 16]), at([gx + 0.9, -24, 50])]), { tone: "lo" }));
    out.push(L(k.segment([gx - 2.2, -24, 28], [gx + 2.2, -24, 28], P), { tone: "faint" }));
  }
  return out.join("");
}

/** A pin rides in its guide; one stopped high (lift > 0) is a reading that failed its gauge. */
export function gaugePins(lifts: number[]) {
  return GAUGE_X.map((gx, i) => {
    const lift = lifts[i] ?? 0;
    return [
      S(slab(gx - 4.5, -41, 9, 10, 50, GUIDE_TOP - 50, 1, 0.4), { tone: "mid" }),
      S(cyl(gx, -36, 1.8, GUIDE_TOP, 8 + lift, 16), { tone: "hi", crease: "none" }),
      S(cyl(gx, -36, 3, GUIDE_TOP + 8 + lift, 3, 20), { tone: "hi", crease: "lo" }),
    ].join("");
  }).join("");
}

function verdictLamp() {
  const [x, y] = [-110, -10];
  return [
    S(cyl(x, y, 6, 0, 3), { tone: "mid" }),
    S(cyl(x, y, 3, 3, 17), { tone: "mid", crease: "none" }),
    S(cyl(x, y, 7.5, 20, 5, 32), { tone: "mid" }),
    `<g class="bench-lamp">${S(cyl(x, y, 5.6, 25, 2.4, 32), { tone: "hi" })}</g>`,
  ].join("");
}

const BIN_X = [-52, -30, -8];
const PIVOT: k.Plane = [-30, -4];
const TIMER_Y = -16;

function sorter() {
  const out = [S(slab(-64, -66, 68, 5, 0, 46, 1, 0.5), { tone: "mid" })];
  out.push(D([-58, -2].map((x) => at([x, -61, 40])), { size: 0.45 }));
  for (const bx of BIN_X) {
    const bin = { x: bx - 9.5, y: -58, w: 19, d: 30, r: 1.5 };
    out.push(S(k.slabOf(bin, 0, 22, P, 4, 0.4), { tone: "hi", crease: "lo" }));
    out.push(S(k.slabOf(k.insetPlan(bin, 1.6), 21.99, 0.01, P, 4), { tone: "lo", flat: true }));
  }
  for (const bx of BIN_X) {
    out.push(S(cyl(bx, TIMER_Y, 6.4, 0, 7, 36), { tone: "hi", crease: "lo" }));
    out.push(L(k.knurl(bx, TIMER_Y, 6.4, 4.4, 7, 30, P, 0.2), { tone: "lo" }));
    const ticks = k.radialTicks(bx, TIMER_Y, 5.2, 12, 3, 7, [0.8, 1.6], P);
    out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  }
  out.push(S(cyl(PIVOT[0], PIVOT[1], 6, 0, 3), { tone: "mid" }));
  out.push(S(cyl(PIVOT[0], PIVOT[1], 2.8, 3, 31), { tone: "mid", crease: "none" }));
  return out.join("");
}

/** The flap turns from the pivot toward the chosen bin. */
export function flap(angle: number) {
  const [x, y] = PIVOT;
  return [
    S(k.extrude(barRing(x, y, 30, 4.2, angle), 34.5, 2.4, P, { convex: true }), { tone: "hi", crease: "lo" }),
    S(cyl(x, y, 4.4, 34, 3.6, 24), { tone: "mid" }),
    D([at([x, y, 37.6])], { size: 0.5, tone: "hi" }),
  ].join("");
}

export function flapAngle(bin: number) {
  return Math.atan2(-43 - PIVOT[1], BIN_X[bin] - PIVOT[0]);
}

/** Hands on the three timers; only the chosen bin's runs, showing the brief-by time left. */
export function timerHands(bin: number | null, left: number) {
  return BIN_X.map((bx, i) => {
    const turn = i === bin ? left : 0;
    const angle = turn * Math.PI * 2;
    const d = k.lineOnTop([bx, TIMER_Y], [bx + Math.sin(angle) * 4.6, TIMER_Y - Math.cos(angle) * 4.6], 7.1, P);
    return L(d, { tone: i === bin ? "lit" : "lo", free: "start" }) + D([at([bx, TIMER_Y, 7.1])], { size: 0.5, tone: i === bin ? "hi" : "lo" });
  }).join("");
}

const HEAD_X = [46, 60, 74];

function gantryBack() {
  const out = [];
  for (const px of [34, 86]) {
    out.push(S(cyl(px, -24, 7, 0, 3), { tone: "mid" }));
    out.push(S(cyl(px, -24, 4, 3, 109), { tone: "mid", crease: "none" }));
  }
  return out.join("");
}

function gantryTop() {
  const out = [S(slab(28, -30, 64, 12, 112, 8, 1.5, 0.5), { tone: "mid" })];
  out.push(D([34, 86].map((x) => at([x, -24, 120])), { size: 0.5 }));
  for (const hx of HEAD_X) out.push(S(slab(hx - 3, -18, 6, 61, 106, 6, 1, 0.3), { tone: "mid" }));
  return out.join("");
}

/** Plungers hang from the heads; the three drop together because the checks run together. */
export function plunger() {
  return S(cyl(0, 37, 1.6, 64, 26, 14), { tone: "hi", crease: "none" }) + S(cyl(0, 37, 2.6, 62, 2, 18), { tone: "hi", crease: "lo" });
}

function heads() {
  return HEAD_X.map((hx, i) => {
    const out = [S(slab(hx - 6, 30, 12, 13, 88, 18, 1.5, 0.5), { tone: "hi", crease: "lo" })];
    const face = 43;
    if (i === 0) out.push(L(k.sideRing([hx, face, 98], 3.4, "y", P, 24), { tone: "mid" }) + L(k.sideRing([hx, face, 98], 1.6, "y", P, 16), { tone: "lo" }));
    if (i === 1) out.push(L([-3, -1, 1, 3].map((dx) => k.segment([hx + dx, face, 88], [hx + dx, face, 106], P)).join(""), { tone: "mid" }));
    if (i === 2) out.push(L(k.pathOf([-6, -4.5, -3, -1.5, 0, 1.5, 3, 4.5, 6].map((dx, j) => at([hx + dx, face, 98 + (j % 2 ? 2.4 : -2.4) * (1 - Math.abs(dx) / 6)]))), { tone: "mid" }));
    out.push(`<circle class="bench-led" data-led="${i}" cx="${at([hx + 4, face, 91])[0].toFixed(1)}" cy="${at([hx + 4, face, 91])[1].toFixed(1)}" r="1.3"/>`);
    return out.join("");
  }).join("");
}

function typewriter() {
  const out = [S(slab(118, -60, 44, 38, 0, 12, 4, 1), { tone: "mid" })];
  out.push(D(k.dotGrid(123, -42, 9, 3, 2.8, 12, P), { size: 0.8, tone: "mid" }));
  out.push(L(k.lineOnTop([118, -46], [162, -46], 12, P), { tone: "faint" }));
  return out.join("");
}

/** Carriage and paper shift left one step per draft. */
export function typeCarriage() {
  return [
    S(cyl(119, -56, 3, 12, 9, 18), { tone: "mid" }),
    S(slab(121, -61, 38, 9, 12, 8, 2, 0.5), { tone: "mid" }),
    S(slab(128, -57.5, 24, 1.2, 20, 26, 0.2), { tone: "hi", crease: "lo" }),
    L([25, 29, 33, 37].map((z) => k.segment([131, -56.3, z], [148, -56.3, z], P)).join(""), { tone: "faint", free: true }),
    S(cyl(161, -56, 3, 12, 9, 18), { tone: "mid" }),
  ].join("");
}

export function tally() {
  return [150, 155, 160].map((x, i) => `<g class="bench-tally" data-tally="${i}">${S(cyl(x, -30, 1.8, 12, 1.6, 16), { tone: "hi" })}</g>`).join("");
}

function stampBack() {
  return S(cyl(176, -34, 7, 0, 3), { tone: "mid" }) + S(cyl(176, -34, 4, 3, 97), { tone: "mid", crease: "none" });
}

/** The stamp presses on each review. */
export function stamp() {
  return [
    S(cyl(140, 37, 1.6, 62, 44, 14), { tone: "hi", crease: "none" }),
    S(slab(132, 30, 16, 14, 48, 14, 1.5, 0.5), { tone: "hi", crease: "lo" }),
    S(slab(133, 31, 14, 12, 46, 2, 1), { tone: "lo" }),
  ].join("");
}

function stampArm() {
  return [
    S(slab(137, -38, 43, 7, 100, 6, 1.2, 0.4), { tone: "mid" }),
    S(slab(137, -31, 6, 74, 96, 6, 1.2, 0.4), { tone: "mid" }),
    D([at([176, -34.5, 106]), at([140, -34.5, 106])], { size: 0.45 }),
  ].join("");
}

const LOCK: k.Plane = [205, -33];

function console_() {
  const box = { x: 190, y: -52, w: 30, d: 36, r: 3 };
  return [
    S(k.slabOf(box, 0, 18, P, 6, 1), { tone: "mid" }),
    D(k.corners(box, 4).map(([x, y]) => at([x, y, 18])), { size: 0.5 }),
    S(cyl(LOCK[0], LOCK[1], 6.2, 18, 3, 36), { tone: "hi", crease: "lo" }),
    L(k.ring(LOCK[0], LOCK[1], 4.6, 21, P, 32), { tone: "lo" }),
    S(cyl(196, -44, 1.4, 18, 14, 12), { tone: "mid", crease: "none" }),
    S(cyl(214, -44, 1.4, 18, 14, 12), { tone: "mid", crease: "none" }),
  ].join("");
}

/** Only a person turns the key: angle 0 is locked, a quarter turn is approved. */
export function key(turn: number, lit: boolean) {
  const angle = -Math.PI / 2 + turn * (Math.PI / 2);
  const [x, y] = LOCK;
  const tip: k.Plane = [x + Math.cos(angle) * 13, y + Math.sin(angle) * 13];
  return [
    S(k.extrude(barRing(x, y, 13, 2.6, angle), 21, 1.6, P, { convex: true }), { tone: "hi", lit, crease: "lo" }),
    S(cyl(tip[0], tip[1], 3.6, 21, 1.6, 20), { tone: "hi", lit, crease: "lo" }),
    L(k.ring(tip[0], tip[1], 1.2, 22.6, P, 12), { tone: "lo" }),
  ].join("");
}

function guardFront() {
  return [
    S(cyl(196, -22, 1.4, 18, 14, 12), { tone: "mid", crease: "none" }),
    S(cyl(214, -22, 1.4, 18, 14, 12), { tone: "mid", crease: "none" }),
    S(slab(194.5, -45.4, 21, 2.8, 32, 2, 0.6), { tone: "mid" }),
    S(slab(194.5, -23.4, 21, 2.8, 32, 2, 0.6), { tone: "mid" }),
  ].join("");
}

/** Static layers in painter's order, split around the live parts. */
export const ART = {
  back: [base(), ruler(), tubePost(), gaugeRack()].join(""),
  afterPins: [verdictLamp(), sorter()].join(""),
  afterFlap: [gantryBack(), typewriter()].join(""),
  afterType: [stampBack(), console_()].join(""),
  afterKey: [guardFront(), rails()].join(""),
  tube: tube(),
  heads: [heads(), gantryTop()].join(""),
  stampArm: stampArm(),
};

export const HEAD_XS = HEAD_X;
export const translate = (by: k.Point3) => k.translateAlong(P, by);
