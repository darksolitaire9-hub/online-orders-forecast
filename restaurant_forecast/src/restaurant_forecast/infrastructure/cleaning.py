from __future__ import annotations
from typing import Final, cast

import pandas as pd

# Column names for the Uber Eats daily export
DATE_COL: Final[str] = "Start Date"
END_DATE_COL: Final[str] = "End Date"
SALES_COL: Final[str] = "Sales"
ORDERS_COL: Final[str] = "Orders"
TICKET_COL: Final[str] = "Ticket Size"


def clean_ubereats_daily(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw Uber Eats daily export DataFrame.

    Input expectations (raw):
      - DATE_COL and END_DATE_COL: string-like date/time columns
      - SALES_COL, ORDERS_COL, TICKET_COL: numeric or numeric-like

    Output guarantees:
      - DATE_COL and END_DATE_COL are Python date objects (no time-of-day)
      - SALES_COL, ORDERS_COL, TICKET_COL are numeric
      - No NaNs in DATE_COL, END_DATE_COL, SALES_COL, ORDERS_COL, TICKET_COL
      - SALES_COL, ORDERS_COL, TICKET_COL are all >= 0
      - Rows with Sales == 0 and Orders == 0 are retained (closed days)
      - DataFrame is sorted by DATE_COL ascending and index is reset
    """
    df = cast(pd.DataFrame, raw.copy())

    # Parse datetimes then normalize to dates
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce").dt.date
    df[END_DATE_COL] = pd.to_datetime(df[END_DATE_COL], errors="coerce").dt.date

    before = len(df)
    df = df.dropna(subset=[DATE_COL, END_DATE_COL])
    print(f"[clean] dropped {before - len(df)} rows with invalid dates")

    # Coerce numerics
    for col in (SALES_COL, ORDERS_COL, TICKET_COL):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=[SALES_COL, ORDERS_COL])
    print(f"[clean] dropped {before - len(df)} rows with missing Sales/Orders")

    # Ticket Size: recompute where missing and orders > 0
    missing_ticket = df[TICKET_COL].isna()
    nonzero_orders = df[ORDERS_COL] > 0

    recompute_mask = missing_ticket & nonzero_orders
    df.loc[recompute_mask, TICKET_COL] = (
        df.loc[recompute_mask, SALES_COL] / df.loc[recompute_mask, ORDERS_COL]
    )

    # For remaining NaNs (e.g., zero orders days), set to 0.0
    df[TICKET_COL] = df[TICKET_COL].fillna(0.0)

    # Remove obviously bad rows (negative values)
    before = len(df)
    df = df[
        (df[SALES_COL] >= 0)
        & (df[ORDERS_COL] >= 0)
        & (df[TICKET_COL] >= 0)
    ]
    print(f"[clean] dropped {before - len(df)} rows with negative values")

    # Keep zero days, just sort by date
    df = df.sort_values(by=DATE_COL, ascending=True)  # type: ignore[arg-type]
    df = df.reset_index(drop=True)

    return cast(pd.DataFrame, df)
