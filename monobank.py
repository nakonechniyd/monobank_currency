from decimal import Decimal
import logging

import requests

import currency

log = logging.getLogger(__name__) 


def get_currency() -> list[currency.CurrencyRow]:
    resp = requests.get("https://api.monobank.ua/bank/currency")
    log.info(f'monobank api resp status: {resp.status_code}, {resp.reason}')
    resp.raise_for_status()

    items = resp.json()
    log.info(f'monobank api got: {len(items)} items')
    result = []
    for item in items:
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
