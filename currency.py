from dataclasses import dataclass
from decimal import Decimal


CURRENCY_MAP = {
    980: 'uah',
    840: 'usd',
    978: 'eur',
    643: 'rub',
    985: 'pln',
}


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
    Does previous value different from actual currency
    """
    return not (
        a.rateBuy == b.rateBuy
        or a.rateSell == b.rateSell
        or a.rateCross == b.rateCross
    )
