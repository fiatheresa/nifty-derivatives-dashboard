
import os
import csv
from datetime import datetime

import pandas as pd
import yfinance as yf


RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw")


def fetch_nifty_history(period="3y"):
    """
    Download NIFTY 50 historical daily data
    and save it in the raw data folder.
    """

    os.makedirs(RAW_DIR, exist_ok=True)

    nifty = yf.download(
        "^NSEI",
        period=period,
        interval="1d",
        auto_adjust=False
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = (
        f"{RAW_DIR}/"
        f"nifty50_{timestamp}.csv"
    )

    nifty.to_csv(file_path)

    return nifty, file_path


def read_nse_option_csv(file_path):
    """
    Read the NSE downloaded option-chain CSV
    and convert it into a structured DataFrame.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8-sig"
    ) as f:

        reader = csv.reader(f)
        rows = list(reader)

    columns = [
        "call_oi",
        "call_change_oi",
        "call_volume",
        "call_iv",
        "call_ltp",
        "call_change",
        "call_bid_qty",
        "call_bid",
        "call_ask",
        "call_ask_qty",
        "strike",
        "put_bid_qty",
        "put_bid",
        "put_ask",
        "put_ask_qty",
        "put_change",
        "put_ltp",
        "put_iv",
        "put_volume",
        "put_change_oi",
        "put_oi"
    ]

    data_rows = rows[2:]

    clean_rows = []

    for row in data_rows:

        row = row[1:-1]

        if len(row) == 21:
            clean_rows.append(row)

    option_df = pd.DataFrame(
        clean_rows,
        columns=columns
    )

    return option_df


if __name__ == "__main__":

    print("Data Fetch Module")
    print("Ready to download NIFTY data.")
