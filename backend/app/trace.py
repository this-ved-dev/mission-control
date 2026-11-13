"""One record per pipeline step: timing, tokens and cost, written as each step finishes."""

import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from decimal import Decimal

from app.cost import Price, report_cost, step_cost
from app.db import now
from app.llm.base import LLMResult


class StepRecord(dict):
    def use(self, result: LLMResult) -> None:
        self.update(
            model=result.model,
            input_tokens=self["input_tokens"] + result.input_tokens,
            output_tokens=self["output_tokens"] + result.output_tokens,
        )


class Tracer:
    def __init__(self, prices: Mapping[str, Price], sink: Callable[[dict], None] | None = None):
        self.prices = prices
        self.sink = sink
        self.steps: list[StepRecord] = []
        self._seq = 0

    @contextmanager
    def step(self, name: str, kind: str = "model") -> Iterator[StepRecord]:
        self._seq += 1
        rec = StepRecord(
            seq=self._seq,
            step=name,
            kind=kind,
            model=None,
            started_at=now(),
            duration_ms=0,
            input_tokens=0,
            output_tokens=0,
            cost_usd="0",
            status="ok",
            output={},
        )
        t0 = time.perf_counter()
        try:
            yield rec
        except Exception as e:
            rec.update(status="error", output={"error": f"{type(e).__name__}: {e}"})
            raise
        finally:
            rec["duration_ms"] = round((time.perf_counter() - t0) * 1000)
            if rec["model"]:
                cost = step_cost(
                    rec["model"], rec["input_tokens"], rec["output_tokens"], self.prices
                )
                rec["cost_usd"] = str(cost)
            self.steps.append(rec)
            if self.sink:
                self.sink(dict(rec))

    def total(self) -> Decimal:
        return report_cost(self.steps, self.prices)
