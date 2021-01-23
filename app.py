from dataclasses import dataclass
from decimal import Decimal

import gspread
from oauth2client.service_account import ServiceAccountCredentials

CURRENCY_KEY = "{}:{}".format

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]


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


# EMPTY_CURRENCY_ROW = CurrencyRow(0, 0, 0)


def get_previous_data(worksheet) -> dict[str, CurrencyRow]:
    """
    Get mapping of previous currency values
    """
    return {
        CURRENCY_KEY(row.currencyCodeA, row.currencyCodeB): row
        for raw in worksheet.get_all_values()[1:]
        if (row := CurrencyRow.from_row(raw))
    }


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


def write_previous_data(worksheet, data: dict[str, CurrencyRow]):
    # header
    worksheet.update('A1:F1', [HEADER_FIELDS])
    # all rows at once
    worksheet.batch_update(
        [
            {
                'range': f'A{row_num}:F{row_num}',
                'values': [[str(getattr(row, hf)) for hf in HEADER_FIELDS]],
            }
            for row_num, row in enumerate(data.values(), start=2)
        ]
    )


def is_modified(a: CurrencyRow, b: CurrencyRow) -> bool:
    """
    Are previous values different from actual currency
    """
    return not (
        a.rateBuy == b.rateBuy
        or a.rateSell == b.rateSell
        or a.rateCross == b.rateCross
    )


# TODO: debug local data
import data


# Assign credentials ann path of style sheet
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)
client = gspread.authorize(creds)

spreadsheet = client.open("monobank_currency_info")

# previous data fetching
previous_data_worksheet = spreadsheet.worksheet("previous_data")
previous_data = get_previous_data(previous_data_worksheet)

rewrite_previous_worksheet = False

# api currency processing
for currency in data.currency_data:
    currency_row = CurrencyRow.from_api(currency)

    # filter only interesting currency
    if currency_row.currencyCodeA not in CURRENCY_MAP:
        continue

    key = CURRENCY_KEY(currency_row.currencyCodeA, currency_row.currencyCodeB)

    previous_currency_row = previous_data.get(key)
    if previous_currency_row:
        if is_modified(previous_currency_row, currency_row):
            print('NEW currency', currency_row)
    else:
        rewrite_previous_worksheet = True
        print('UPDATE previous', currency_row)
        print('NEW currency', currency_row)
        previous_data[key] = currency_row

# rewrite worksheet `previous_data`
if rewrite_previous_worksheet:
    print('Update previous worksheet')
    write_previous_data(previous_data_worksheet, previous_data)
