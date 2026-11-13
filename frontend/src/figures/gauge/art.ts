/** Fig 2: a panel dial gauge on a small bench base. Static parts are built once as SVG strings. */
import * as k from "../../iso/iso-kit";
import { bandOf, type Scale } from "./model";

export const WIDTH = 300;
export const HEIGHT = 210;

const BASE = { x: -58, y: -46, w: 116, d: 92, r: 7 };
const BASE_H = 7;
const FOOT_H = 4;
const C: k.Plane = [0, -4];
const R = 34;
const BODY_Z = 10;
const BODY_H = 11;
const FACE = BODY_Z + BODY_H;
const SPAN = (Math.PI * 3) / 2;

export const P = k.fitProjection(
  [...k.boxCorners(BASE, -BASE_H - FOOT_H, 0), [C[0] - R, C[1] - R, FACE + 2], [C[0] + R, C[1] + R, FACE + 2]],
  WIDTH,
  HEIGHT,
  { pad: 10, azimuth: 40 },
);

// The sweep is centred on the direction away from the viewer, like a gauge on a desk.
const [vx, vy] = k.towardViewer(P);
const AWAY = Math.atan2(-vx, vy);
export const FROM = AWAY - SPAN / 2;

const at = (p: k.Point3) => k.iso(p, P);
const S = (paths: k.SolidPaths, style: k.SolidStyle) => k.solidSvg(paths, style);
const L = (d: string, style: Parameters<typeof k.lineSvg>[1]) => k.lineSvg(d, style);
const D = (points: k.Flat[], style: Parameters<typeof k.dotsSvg>[1]) => k.dotsSvg(points, style);
const byDepth = (points: k.Plane[]) => [...points].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const polar = (angle: number, r: number): k.Plane => [C[0] + Math.sin(angle) * r, C[1] - Math.cos(angle) * r];

function arc(r: number, from: number, to: number, z: number) {
  const steps = Math.max(2, Math.ceil(Math.abs(to - from) / SPAN * 48));
  return k.onTop(Array.from({ length: steps + 1 }, (_, i) => polar(FROM + (from + ((to - from) * i) / steps) * SPAN, r)), z, P);
}

function base() {
  const out = [`<path class="iso-halo" d="${k.haloOf(BASE, -BASE_H - FOOT_H, BASE_H, P)}"/>`];
  for (const [x, y] of byDepth(k.corners(BASE, 13))) {
    out.push(S(k.cylinder(x, y, 5.6, -BASE_H - FOOT_H, 1.4, P, 24), { tone: "lo" }));
    out.push(S(k.cylinder(x, y, 4.2, -BASE_H - FOOT_H + 1.4, FOOT_H - 1.4, P, 24), { tone: "mid" }));
  }
  out.push(S(k.slabOf(BASE, -BASE_H, BASE_H, P, 8, 1.2), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(BASE, 4), 0, P), { tone: "lo" }));
  const screws = k.corners(BASE, 8);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 1.8, 0, P, 14)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.45 }));
  return out.join("");
}

function labelPlate(scale: Scale) {
  const plate = { x: -22, y: BASE.y + BASE.d - 13, w: 44, d: 8, r: 1 };
  return [
    S(k.slabOf(plate, 0, 0.6, P, 3), { tone: "lo", crease: "none" }),
    D([at([plate.x + 2.4, plate.y + 4, 0.6]), at([plate.x + plate.w - 2.4, plate.y + 4, 0.6])], { size: 0.4 }),
    k.faceTextSvg(k.topMatrix([0, plate.y + 5.4], 0.6, P), `${scale.label.toUpperCase()} ${scale.unit}`, { size: 3.4, tone: "mid", anchor: "middle" }),
  ].join("");
}

function body() {
  const [x, y] = C;
  const out = [];
  out.push(S(k.cylinder(x, y, R * 0.62, 0, 3, P, 48, 0.4), { tone: "mid" }));
  out.push(S(k.cylinder(x, y, R * 0.5, 3, BODY_Z - 3, P, 48), { tone: "mid", crease: "none" }));
  out.push(D(k.circleRing(x, y, R * 0.56, 6).map(([px, py]) => at([px, py, 3])), { size: 0.4 }));
  out.push(S(k.cylinder(x, y, R, BODY_Z, BODY_H, P, 72, 0.8), { tone: "hi", crease: "lo" }));
  out.push(L(k.knurl(x, y, R, FACE - 3.6, FACE, 90, P, 0.3), { tone: "lo" }));
  out.push(L(k.sideArc(x, y, R, FACE - 3.6, P, 40), { tone: "faint" }));
  // zero-adjust screw on the side of the bezel
  const side = polar(AWAY + Math.PI / 2, R + 2.2);
  out.push(S(k.cylinder(side[0], side[1], 2.4, BODY_Z + 3, 4, P, 18), { tone: "mid" }));
  out.push(L(k.knurl(side[0], side[1], 2.4, BODY_Z + 3, BODY_Z + 7, 14, P), { tone: "lo" }));
  return out.join("");
}

function face(scale: Scale) {
  const [x, y] = C;
  const out = [];
  out.push(L(k.ring(x, y, R - 2.4, FACE, P, 72), { tone: "lo" }));
  const count = Math.round((scale.max - scale.min) / scale.step);
  const ticks = k.radialTicks(x, y, R - 4, count, scale.every, FACE, [1.6, 3.4], P, FROM, SPAN);
  out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  const [b0, b1] = bandOf(scale);
  // The legal band is the subject of this gauge, so it is the one place colour appears.
  for (const r of [R - 9, R - 9.8, R - 10.6]) out.push(L(arc(r, b0, b1, FACE), { tone: "green" }));
  out.push(D([polar(FROM + b0 * SPAN, R - 9.8), polar(FROM + b1 * SPAN, R - 9.8)].map(([px, py]) => at([px, py, FACE])), { size: 0.6, tone: "hi" }));
  out.push(L(k.lineOnTop(polar(FROM, R - 4), polar(FROM, R - 9), FACE, P), { tone: "hi" }));
  out.push(k.faceTextSvg(k.topMatrix(polar(AWAY + Math.PI, R * 0.42), FACE, P), String(scale.min), { size: 3, tone: "lo", anchor: "middle" }));
  return out.join("");
}

export function needlePath(share: number) {
  const angle = FROM + share * SPAN;
  return k.onTop([polar(angle + Math.PI, 5), polar(angle, R - 6)], FACE + 0.3, P);
}

export function hub() {
  const [x, y] = C;
  return [
    S(k.cylinder(x, y, 2.6, FACE, 1.4, P, 20), { tone: "hi", lit: true }),
    D([at([x, y, FACE + 1.4])], { size: 0.5, tone: "hi" }),
  ].join("");
}

const cache = new Map<string, string>();
export function staticArt(scale: Scale) {
  if (!cache.has(scale.key)) cache.set(scale.key, [base(), labelPlate(scale), body(), face(scale)].join(""));
  return cache.get(scale.key)!;
}
