import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { step } from "../test/fixtures";
import { TraceCards } from "./TraceCards";

const steps = [
  step({ seq: 1, step: "limits_check", kind: "code" }),
  step({ seq: 2, step: "classify", kind: "model", model: "qwen3:14b", input_tokens: 312, output_tokens: 41, cost_usd: "0.000518" }),
  step({ seq: 3, step: "check_injection", kind: "model", model: "qwen3:14b", input_tokens: 290, output_tokens: 12, status: "fallback" }),
];

it("shows one card per step with its tokens", () => {
  render(<TraceCards steps={steps} total="0.000518" />);
  const cards = screen.getAllByRole("listitem");
  expect(cards).toHaveLength(3);
  expect(within(cards[0]).getByText("CODE")).toBeInTheDocument();
  expect(within(cards[0]).getByText(/0 in · 0 out/)).toBeInTheDocument();
  expect(within(cards[1]).getByText(/312 in · 41 out/)).toBeInTheDocument();
  expect(within(cards[1]).getByText("$0.000518")).toBeInTheDocument();
  expect(within(cards[2]).getByText("fallback")).toBeInTheDocument();
});

it("shows the report total computed by the server", () => {
  render(<TraceCards steps={steps} total="0.000518" />);
  expect(screen.getByText(/total \$0\.000518/i)).toBeInTheDocument();
});
