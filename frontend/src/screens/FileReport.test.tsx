import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { FileReport } from "./FileReport";

afterEach(() => vi.unstubAllGlobals());

const json = (status: number, body: unknown) =>
  Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } }));

async function fill() {
  await userEvent.type(screen.getByRole("textbox", { name: /^name/i }), "Priya");
  await userEvent.type(screen.getByRole("combobox", { name: /station/i }), "PROP");
  await userEvent.type(screen.getByRole("spinbutton", { name: /wind/i }), "12");
  await userEvent.type(screen.getByRole("spinbutton", { name: /temp/i }), "9");
  await userEvent.type(screen.getByRole("spinbutton", { name: /fuel/i }), "99");
  await userEvent.type(screen.getByRole("textbox", { name: /note/i }), "Valve slow");
}

it("sends every field and reports the new id", async () => {
  const fetch = vi.fn((url: string, _init?: RequestInit) =>
    url.includes("/limits") ? json(200, { verdict: "go", violations: [] }) : json(202, { id: 7 }));
  vi.stubGlobal("fetch", fetch);
  const onFiled = vi.fn();
  render(<FileReport onFiled={onFiled} />);
  await fill();
  await userEvent.click(screen.getByRole("button", { name: /file report/i }));
  const [, init] = fetch.mock.calls.find(([url]) => url === "/api/reports")!;
  expect(JSON.parse((init as RequestInit).body as string)).toEqual({
    name: "Priya", station: "PROP", wind_knots: 12, temp_c: 9, fuel_pct: 99, note: "Valve slow",
  });
  expect(onFiled).toHaveBeenCalledWith(7);
});

it("shows the server's message next to the field it is about", async () => {
  vi.stubGlobal("fetch", vi.fn((url: string) =>
    url.includes("/limits")
      ? json(200, { verdict: "go", violations: [] })
      : json(422, { errors: { fuel_pct: "fuel_pct: Input should be less than or equal to 150" } })));
  render(<FileReport onFiled={vi.fn()} />);
  await fill();
  await userEvent.click(screen.getByRole("button", { name: /file report/i }));
  const field = screen.getByRole("spinbutton", { name: /fuel/i });
  expect(field).toHaveAttribute("aria-invalid", "true");
  expect(await screen.findByText(/less than or equal to 150/)).toBeInTheDocument();
});
