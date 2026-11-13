from decimal import Decimal

from app.cost import Price
from app.trace import Tracer

PRICES = {"m": Price(Decimal("1"), Decimal("2")), "fast": Price(Decimal(0), Decimal(0))}


def tracer() -> Tracer:
    return Tracer(PRICES)
