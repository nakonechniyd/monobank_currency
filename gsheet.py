import logging
from typing import Iterable
from typing import Iterator
from decimal import Decimal
from pathlib import Path

import gspread
from oauth2client.service_account import ServiceAccountCredentials

import currency

log = logging.getLogger(__name__)


HEADER_FIELDS = [
    "currencyCodeA",
    "currencyCodeB",
    "date",
    "rateBuy",
    "rateSell",
    "rateCross",
]

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CURRENCY_KEY = "{}:{}".format


class SheetInfo:
    def __init__(self, worksheet: gspread.Worksheet):
        self._worksheet = worksheet

    def get_currency_rows_count(self) -> int:
        return int(self._worksheet.get("A1").first())


def get_client():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            Path("data") / "credentials.json",
            SCOPE,
        )
    except FileNotFoundError:
        return None
    return gspread.authorize(creds)


def get_worksheet(
    spreadsheet: gspread.Spreadsheet,
    name: str,
) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound as e:
        log.info(f"{name} worksheet doesn't found")
        raise e


def get_currency_row(data: list) -> currency.CurrencyRow:
    return currency.CurrencyRow(
        currencyCodeA=int(data[0]),
        currencyCodeB=int(data[1]),
        date=int(data[2]),
        rateBuy=Decimal(data[3]),
        rateSell=Decimal(data[4]),
        rateCross=Decimal(data[5]),
    )


def fetch_previous_data(
    worksheet: gspread.Worksheet,
) -> dict[str, currency.CurrencyRow]:
    """
    Get mapping of previous currency values
    """
    return {
        CURRENCY_KEY(row.currencyCodeA, row.currencyCodeB): row
        for raw in worksheet.get_all_values()[1:]
        if (row := get_currency_row(raw))
    }


def write_previous_data(
    worksheet: gspread.Worksheet,
    data: Iterable[currency.CurrencyRow],
):
    # write header
    worksheet.update("A1:F1", [HEADER_FIELDS])

    # write all rows at once
    worksheet.batch_update(
        write_worksheet_row("A2:F2", data),
    )


def write_worksheet_row(
    start_range: str, data: Iterable[currency.CurrencyRow]
) -> Iterator[dict]:
    """
    Write rows as batch update
    """

    # split A1:F1 by parts
    # l - letter; n - number; f - first; l - last;
    lf, nf, __, ll, nl = start_range

    for num, row in enumerate(data, start=int(nf)):
        yield {
            "range": f"{lf}{num}:{ll}{num}",
            "values": [[str(getattr(row, hf)) for hf in HEADER_FIELDS]],
        }


def write_currency_data(
    worksheet: gspread.Worksheet,
    row: int,
    data: Iterable[currency.CurrencyRow],
):

    # write all rows at once
    worksheet.batch_update(
        write_worksheet_row(f"A{row}:F{row}", data),
    )
