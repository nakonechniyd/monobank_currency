from typing import Iterable
from typing import Iterator
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

import gspread
from gspread import Worksheet
from gspread import Spreadsheet
from gspread.exceptions import WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials

import monobank


CURRENCY_KEY = "{}:{}".format

HEADER_FIELDS = [
    "currencyCodeA",
    "currencyCodeB",
    "date",
    "rateBuy",
    "rateSell",
    "rateCross",
]

CURRENCY_MAP = {
    980: 'uah',
    840: 'usd',
    978: 'eur',
    643: 'rub',
    985: 'pln',
}

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",  # ?
    "https://www.googleapis.com/auth/drive",
]


class SheetInfo():
    def __init__(self, worksheet: Worksheet):
        self._worksheet = worksheet

    def get_currency_rows_count(self) -> int:
        return int(self._worksheet.get('A1').first())


@dataclass(frozen=True)
class CurrencyRow:
    currencyCodeA: int
    currencyCodeB: int
    date: int
    rateBuy: Decimal = Decimal("0.0")
    rateSell: Decimal = Decimal("0.0")
    rateCross: Decimal = Decimal("0.0")

    @staticmethod
    def from_row(row: list[str]) -> "CurrencyRow":
        return CurrencyRow(
            currencyCodeA=int(row[0]),
            currencyCodeB=int(row[1]),
            date=int(row[2]),
            rateBuy=Decimal(row[3]),
            rateSell=Decimal(row[4]),
            rateCross=Decimal(row[5]),
        )

    @staticmethod
    def from_api(item: dict) -> "CurrencyRow":
        return CurrencyRow(
            currencyCodeA=int(item["currencyCodeA"]),
            currencyCodeB=int(item["currencyCodeB"]),
            date=int(item["date"]),
            rateBuy=Decimal(str(item.get("rateBuy", "0.0"))),
            rateSell=Decimal(str(item.get("rateSell", "0.0"))),
            rateCross=Decimal(str(item.get("rateCross", '0'))),
        )


def fetch_previous_data(worksheet: Worksheet) -> dict[str, CurrencyRow]:
    """
    Get mapping of previous currency values
    """
    return {
        CURRENCY_KEY(row.currencyCodeA, row.currencyCodeB): row
        for raw in worksheet.get_all_values()[1:]
        if (row := CurrencyRow.from_row(raw))
    }


def write_worksheet_row(
    start_range: str,
    data: Iterable[CurrencyRow]
) -> Iterator[dict]:
    """
    Write rows as batch update
    """

    # split A1:F1 by parts: l - letter, n - number, f - first, l - last
    lf, nf, __, ll, nl = start_range

    for num, row in enumerate(data, start=int(nf)):
        yield {
            'range': f'{lf}{num}:{ll}{num}',
            'values': [[str(getattr(row, hf)) for hf in HEADER_FIELDS]],
        }


def write_previous_data(worksheet: Worksheet, data: Iterable[CurrencyRow]):
    # write header
    worksheet.update('A1:F1', [HEADER_FIELDS])

    # write all rows at once
    worksheet.batch_update(
        write_worksheet_row('A2:F2', data),
    )


def write_currency_data(worksheet: Worksheet, row: int, data: Iterable[CurrencyRow]):

    # write all rows at once
    worksheet.batch_update(
        write_worksheet_row(f'A{row}:F{row}', data),
    )


def is_currency_changed(a: CurrencyRow, b: CurrencyRow) -> bool:
    """
    Are previous values different from actual currency
    """
    return not (
        a.rateBuy == b.rateBuy
        or a.rateSell == b.rateSell
        or a.rateCross == b.rateCross
    )


# TODO: debug local data
# import data


# Assign credentials ann path of style sheet
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", SCOPE,
)
client = gspread.authorize(creds)

spreadsheet = client.open("monobank_currency_info")

try:
    previous_data_worksheet = spreadsheet.worksheet("previous_data")
except WorksheetNotFound:
    print('Previous data worksheet not found')
    exit(1)

try:
    currency_worksheet = spreadsheet.worksheet(f"{datetime.now().year}")
except WorksheetNotFound:
    print('Currency worksheet not found')
    exit(1)

currency_update_data = []
previous_data = fetch_previous_data(previous_data_worksheet)

rewrite_previous_worksheet = False

# api currency processing
for currency in monobank.get_currency():
    currency_row = CurrencyRow.from_api(currency)

    # filter only interesting currency
    if currency_row.currencyCodeA not in CURRENCY_MAP:
        continue

    key = CURRENCY_KEY(currency_row.currencyCodeA, currency_row.currencyCodeB)
    previous_currency_row = previous_data.get(key)

    update_currency = (
        not previous_currency_row
        or is_currency_changed(previous_currency_row, currency_row)
    )
    if update_currency:
        rewrite_previous_worksheet = True
        print('Previous currency update:', currency_row)
        previous_data[key] = currency_row

        print('Currency update:', currency_row)
        currency_update_data.append(currency_row)

# rewrite worksheets
if currency_update_data:
    sheet_info = SheetInfo(spreadsheet.worksheet("info"))

    start_row = sheet_info.get_currency_rows_count() + 1

    print('Update currency worksheet')
    write_currency_data(currency_worksheet, start_row, currency_update_data)

if rewrite_previous_worksheet:
    print('Update previous worksheet')
    write_previous_data(previous_data_worksheet, previous_data.values())
