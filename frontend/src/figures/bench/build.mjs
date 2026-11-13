// Writes a static preview of the bench in a chosen pose, for screenshots and the line-end check.
//   node src/figures/bench/build.mjs [--light] [--stop N]
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../iso/iso-kit.ts";
import * as A from "./art.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const arg = (name, fallback) => (process.argv.includes(name) ? process.argv[process.argv.indexOf(name) + 1] : fallback);
const theme = process.argv.includes("--light") ? "light" : "dark";
const stop = Number(arg("--stop", 3));
const x = A.STOPS[stop];

const body = [
  A.ART.back,
  A.gaugePins([0, 12, 0]),
  `<g class="bench-lamp-wrap" data-verdict="no_go">${A.ART.afterPins}</g>`,
  A.flap(A.flapAngle(0)),
  A.timerHands(0, 0.7),
  A.ART.afterFlap,
  `<g transform="${A.translate([-6, 0, 0])}">${A.typeCarriage()}</g>`,
  A.tally(),
  A.ART.afterType,
  A.key(0, false),
  A.ART.afterKey,
  `<g transform="${A.translate([x, 0, 0])}">${A.carriage()}</g>`,
  `<g transform="${A.translate([x, 0, 0])}">${A.canister()}</g>`,
  A.ART.tube,
  A.HEAD_XS.map((hx) => `<g transform="${A.translate([hx, 0, stop === 3 ? -22 : 0])}">${A.plunger()}</g>`).join(""),
  A.ART.heads,
  A.stamp(),
  A.ART.stampArm,
];
const svg = k.figureSvg({ width: A.WIDTH, height: A.HEIGHT, label: "The Go/No-Go Bench", body });
const css = `.bench-led{fill:var(--anatomy-lo)}.bench-lamp-wrap[data-verdict="no_go"] .bench-lamp .iso-top{fill:var(--anatomy-red)}`;
const page = k.pageHtml({
  title: "Go/No-Go Bench",
  theme,
  width: 1100,
  body: `<style>${css}</style>` + k.plateHtml({ fig: "Fig 1", title: "The Go/No-Go Bench", hint: "Preview", readout: `stop ${stop}`, body: `<div class="iso-stage">${svg}</div>` }),
});
const out = join(HERE, theme === "light" ? "preview-light.html" : "preview.html");
writeFileSync(out, page);
console.log("wrote", out);
