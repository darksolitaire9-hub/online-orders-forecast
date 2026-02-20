from __future__ import annotations

from typing import cast

import pandas as pd

from restaurant_forecast.infrastructure.cleaning import (
    DATE_COL,
    SALES_COL,
    ORDERS_COL,
    TICKET_COL,
)


# Alias to document intent: this DataFrame follows the core schema
CoreSchemaDataFrame = pd.DataFrame


def select_core_columns(df: pd.DataFrame) -> CoreSchemaDataFrame:
    """
    Restrict a cleaned DataFrame to the core schema used by the domain.

    Input:
      - df is expected to be the output of clean_daily(), so:
          * DATE_COL is a Python date (no time-of-day)
          * SALES_COL, ORDERS_COL, TICKET_COL are numeric and non-negative

    Output:
      - A new DataFrame with exactly these columns, in this order:
          [DATE_COL, SALES_COL, ORDERS_COL, TICKET_COL]
    """
    core_columns: list[str] = [
        DATE_COL,
        SALES_COL,
        ORDERS_COL,
        TICKET_COL,
    ]

    core_df = df[core_columns].copy()

    return cast(CoreSchemaDataFrame, core_df)
