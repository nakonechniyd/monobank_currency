from datetime import datetime

import currency
import monobank
import gsheet


def main():
    client = gsheet.get_client()
    spreadsheet = client.open("monobank_currency_info")

    previous_data_worksheet = gsheet.get_worksheet(spreadsheet, "previous_data")
    currency_worksheet = gsheet.get_worksheet(
        spreadsheet,
        f"{datetime.now().year}",
    )

    rewrite_previous_worksheet = False
    previous_data = gsheet.fetch_previous_data(previous_data_worksheet)

    # api currency processing
    currency_update_data = []
    for currency_row in monobank.get_currency():
        key = gsheet.CURRENCY_KEY(
            currency_row.currencyCodeA,
            currency_row.currencyCodeB,
        )
        previous_currency_row = previous_data.get(key)

        update_currency = (
            not previous_currency_row
            or currency.is_currency_changed(previous_currency_row, currency_row)
        )
        if update_currency:
            rewrite_previous_worksheet = True
            print('Previous currency update:', currency_row)
            previous_data[key] = currency_row

            print('Currency update:', currency_row)
            currency_update_data.append(currency_row)

    # add rows to currency worksheet
    if currency_update_data:
        sheet_info = gsheet.SheetInfo(spreadsheet.worksheet("info"))

        start_row = sheet_info.get_currency_rows_count() + 1

        print('Update currency worksheet')
        gsheet.write_currency_data(
            worksheet=currency_worksheet,
            row=start_row,
            data=currency_update_data,
        )

    # rewrite previous currency data worksheet
    if rewrite_previous_worksheet:
        print('Update previous worksheet')
        gsheet.write_previous_data(
            worksheet=previous_data_worksheet,
            data=previous_data.values(),
        )


if __name__ == '__main__':
    main()
