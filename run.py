import logging
import time
from datetime import datetime
from pathlib import Path

import currency
import monobank
import gsheet


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s",
    filename=(Path("data") / "app.log"),
)
log = logging.getLogger("app")


def main():
    start = time.perf_counter()
    log.info("Start")

    currency_rows = monobank.get_currency()
    if not currency_rows:
        log.info("Currency data from monobank is empty")

    client = gsheet.get_client()
    if not client:
        log.error("File with credentials not found.")
        return

    spreadsheet = client.open("monobank_currency_info")

    previous_data_worksheet = gsheet.get_worksheet(spreadsheet, "previous_data")
    currency_worksheet = gsheet.get_worksheet(
        spreadsheet,
        f"{datetime.now().year}",
    )

    previous_data = gsheet.fetch_previous_data(previous_data_worksheet)

    # api currency processing
    currency_update_data = []
    for currency_row in currency_rows:
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
            log.info(f"Previous currency value update: {currency_row}")
            previous_data[key] = currency_row

            log.info(f"Currency value update: {currency_row}")
            currency_update_data.append(currency_row)

    # add rows to currency worksheet
    if currency_update_data:
        sheet_info = gsheet.SheetInfo(spreadsheet.worksheet("info"))

        start_row = sheet_info.get_currency_rows_count() + 1

        log.info("Update currency worksheet")
        gsheet.write_currency_data(
            worksheet=currency_worksheet,
            row=start_row,
            data=currency_update_data,
        )

        log.info("Update previous worksheet")
        gsheet.write_previous_data(
            worksheet=previous_data_worksheet,
            data=previous_data.values(),
        )

    end = time.perf_counter()
    log.info(
        f"Done. Elapsed time: {end - start:.2f} seconds.",
    )


if __name__ == "__main__":
    main()
