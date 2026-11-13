import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { report } from "../test/fixtures";
import { ApprovePanel } from "./ApprovePanel";

it("is locked while the pipeline is still running", () => {
  render(<ApprovePanel report={report({ status: "processing" })} onApprove={vi.fn()} />);
  expect(screen.getByRole("button", { name: /approve/i })).toBeDisabled();
});

it("sends the approver's name when a person approves", async () => {
  const onApprove = vi.fn().mockResolvedValue(undefined);
  render(<ApprovePanel report={report()} onApprove={onApprove} />);
  const button = screen.getByRole("button", { name: /approve/i });
  expect(button).toBeDisabled(); // no name yet
  await userEvent.type(screen.getByLabelText(/approver/i), "FD Ruiz");
  await userEvent.click(button);
  expect(onApprove).toHaveBeenCalledWith({ approver: "FD Ruiz", acknowledged_flag: false });
});

it("needs an explicit acknowledgement for a flagged note", async () => {
  const onApprove = vi.fn().mockResolvedValue(undefined);
  render(<ApprovePanel report={report({ status: "needs_review" })} onApprove={onApprove} />);
  await userEvent.type(screen.getByLabelText(/approver/i), "FD");
  expect(screen.getByRole("button", { name: /approve/i })).toBeDisabled();
  await userEvent.click(screen.getByLabelText(/read the flagged note/i));
  await userEvent.click(screen.getByRole("button", { name: /approve/i }));
  expect(onApprove).toHaveBeenCalledWith({ approver: "FD", acknowledged_flag: true });
});

it("shows who approved once done", () => {
  render(<ApprovePanel report={report({ status: "approved", approved_by: "FD Ruiz", approved_at: "2026-11-13T15:04:00Z" })} onApprove={vi.fn()} />);
  expect(screen.getByText(/approved by FD Ruiz/i)).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /approve/i })).toBeNull();
});
