
import pandas as pd

NSE_HOLIDAYS_2026 = [
    "2026-01-15", "2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31",
    "2026-04-03", "2026-04-14", "2026-05-01", "2026-05-28", "2026-06-26",
    "2026-09-14", "2026-10-02", "2026-10-20", "2026-11-10", "2026-11-24",
    "2026-12-25",
]


NUMERIC_COLUMNS = [
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


def convert_numeric(df):
    """Convert text market values into numeric values."""

    df = df.copy()

    for col in NUMERIC_COLUMNS:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .replace("-", pd.NA)
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


def remove_duplicates(df):
    """Remove duplicate option records."""

    return (
        df
        .drop_duplicates()
        .reset_index(drop=True)
    )


def validate_strikes(df):
    """Keep only valid positive strike prices."""

    df = df.dropna(subset=["strike"])

    df = df[df["strike"] > 0]

    return df.reset_index(drop=True)


def add_expiry(df, expiry_date):
    """Add and standardise the option expiry date."""

    df = df.copy()

    df["expiry"] = pd.to_datetime(
        expiry_date,
        errors="coerce"
    )

    return df


def validate_expiry(df):
    """Check that expiry dates are valid."""

    df = df.copy()

    df["expiry_valid"] = (
        df["expiry"].notna()
    )

    return df


def check_nse_holiday(df, holidays):
    """Flag contracts whose expiry falls on an NSE holiday."""

    df = df.copy()

    holidays = pd.to_datetime(holidays)

    df["is_holiday"] = (
        df["expiry"].isin(holidays)
    )

    return df


def add_quality_flags(df):
    """Add option-data quality indicators, distinguishing which side is missing."""
    df = df.copy()

    df["call_data_available"] = df["call_ltp"].notna()
    df["put_data_available"] = df["put_ltp"].notna()

    df["data_quality"] = "OK"
    df.loc[(~df["call_data_available"]) & (df["put_data_available"]), "data_quality"] = "Missing call LTP"
    df.loc[(df["call_data_available"]) & (~df["put_data_available"]), "data_quality"] = "Missing put LTP"
    df.loc[(~df["call_data_available"]) & (~df["put_data_available"]), "data_quality"] = "Missing both LTP"

    return df


def clean_option_data(df, spot_price, valuation_date, expiry_date=None, holidays=None, day_count_convention="calendar/365"):
    df = df.copy()
    df = convert_numeric(df)
    df = remove_duplicates(df)
    df = validate_strikes(df)
    if expiry_date is not None:
        df = add_expiry(df, expiry_date)
        df = validate_expiry(df)
    if holidays is not None:
        df = check_nse_holiday(df, holidays)
    df = add_quality_flags(df)
    df = add_market_context(df, spot_price, valuation_date, day_count_convention)
    return df
    """
    Complete Phase 3 option-chain
    data-cleaning pipeline.
    """

    df = df.copy()

    # 1. Convert values to numeric
    df = convert_numeric(df)

    # 2. Remove duplicates
    df = remove_duplicates(df)

    # 3. Validate strike prices
    df = validate_strikes(df)

    # 4. Add expiry date if supplied
    if expiry_date is not None:
        df = add_expiry(
            df,
            expiry_date
        )

        df = validate_expiry(df)

    # 5. Check NSE holidays
    if holidays is not None:
        df = check_nse_holiday(
            df,
            holidays
        )

    # 6. Add data-quality flags
    df = add_quality_flags(df)

    return df

def get_reliable_spot(history_df):
    """Return (spot_price, valuation_date, was_fallback_used) from a NIFTY history frame."""
    history_df = history_df.sort_values("Date").reset_index(drop=True)
    latest = history_df.iloc[-1]
    if latest["Volume"] == 0:
        reliable_rows = history_df[history_df["Volume"] > 0]
        if reliable_rows.empty:
            raise ValueError("No row with non-zero volume found in NIFTY history.")
        reliable = reliable_rows.iloc[-1]
        return float(reliable["Close"]), reliable["Date"], True
    return float(latest["Close"]), latest["Date"], False


def add_market_context(df, spot_price, valuation_date, day_count_convention="calendar/365"):
    """Join spot price, valuation date, and time-to-expiry (T) onto the option chain."""
    df = df.copy()
    df["spot_price"] = spot_price
    df["valuation_date"] = pd.to_datetime(valuation_date)
    days_to_expiry = (df["expiry"] - df["valuation_date"]).dt.days
    df["days_to_expiry"] = days_to_expiry
    if day_count_convention == "calendar/365":
        df["T"] = days_to_expiry / 365.0
    elif day_count_convention == "trading/252":
        df["T"] = days_to_expiry / 252.0
    else:
        raise ValueError("day_count_convention must be 'calendar/365' or 'trading/252'")
    return df


if __name__ == "__main__":

    print("Data Cleaning Module")
    print("Ready for Phase 3 processing.")
