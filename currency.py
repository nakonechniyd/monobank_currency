from dataclasses import dataclass
from decimal import Decimal


CURRENCY_MAP = {
    980: "uah",
    840: "usd",
    978: "eur",
    643: "rub",
    985: "pln",
}

ONE_PENNY = Decimal("0.01")


@dataclass(frozen=True)
class CurrencyRow:
    currencyCodeA: int
    currencyCodeB: int
    date: int
    rateBuy: Decimal = Decimal("0.0")
    rateSell: Decimal = Decimal("0.0")
    rateCross: Decimal = Decimal("0.0")


def is_currency_changed(a: CurrencyRow, b: CurrencyRow) -> bool:
    """
    Does previous value different from actual currency at least 0.01
    """
    return (
        abs(a.rateBuy - b.rateBuy) >= ONE_PENNY
        or abs(a.rateSell - b.rateSell) >= ONE_PENNY
        or abs(a.rateCross - b.rateCross) >= ONE_PENNY
    )
