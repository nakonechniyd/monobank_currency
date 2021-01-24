from decimal import Decimal

import requests

import currency


def get_currency() -> list[currency.CurrencyRow]:
    resp = requests.get("https://api.monobank.ua/bank/currency")
    if not resp.ok:
        return []

    result = []
    for item in resp.json():
        row = get_currency_row(item)
        if row.currencyCodeA not in currency.CURRENCY_MAP:
            continue
        result.append(row)
    return result


def get_currency_row(data: dict) -> currency.CurrencyRow:
    return currency.CurrencyRow(
        currencyCodeA=int(data["currencyCodeA"]),
        currencyCodeB=int(data["currencyCodeB"]),
        date=int(data["date"]),
        rateBuy=Decimal(str(data.get("rateBuy", "0.0"))),
        rateSell=Decimal(str(data.get("rateSell", "0.0"))),
        rateCross=Decimal(str(data.get("rateCross", "0.0"))),
    )
