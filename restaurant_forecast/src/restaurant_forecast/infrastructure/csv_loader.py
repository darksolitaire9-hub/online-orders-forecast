from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, cast

import pandas as pd

from restaurant_forecast.application.ports.data_loader import IDataLoader
from restaurant_forecast.domain.models import DailyObservation, DailySeries


# CSV column names (Uber Eats export schema)
DATE_COL = "Start Date"
END_DATE_COL = "End Date"
SALES_COL = "Sales"
ORDERS_COL = "Orders"
TICKET_COL = "Ticket Size"


@dataclass
class CSVConfig:
    primary_month_csv: Path
    other_month_csvs: List[Path]
    store_id: str
    # You can add more fields later, e.g.:
    # primary_month_full: bool = True
    # ignore_primary_if_partial_unknown: bool = False
    # data_source: str | None = None
    # opening_date: str | None = None


class CSVDataLoader(IDataLoader):
    """
    Infrastructure adapter that:
      - reads multiple monthly CSVs
      - cleans/normalizes them
      - returns a domain DailySeries

    It also exposes load_all_raw_dataframe() for debugging.
    """

    def __init__(self, config: CSVConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------ #
    # Internal helpers: pandas/raw DataFrame handling
    # ------------------------------------------------------------------ #

    def _read_all_raw(self) -> pd.DataFrame:
        """
        Read all configured CSV files and return a cleaned DataFrame.

        Column types after this function:
          - DATE_COL / END_DATE_COL: date
          - SALES_COL / ORDERS_COL / TICKET_COL: numeric (no NaNs, no negatives)
        """
        paths = [self._config.primary_month_csv, *self._config.other_month_csvs]
        frames: list[pd.DataFrame] = []

        for path in paths:
            print(f"Reading: {path}")
            frames.append(pd.read_csv(path))

        df = cast(pd.DataFrame, pd.concat(frames, ignore_index=True))

        # --- Parse datetimes then normalize to dates (no time-of-day) ---
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce").dt.date
        df[END_DATE_COL] = pd.to_datetime(df[END_DATE_COL], errors="coerce").dt.date

        before = len(df)
        df = df.dropna(subset=[DATE_COL, END_DATE_COL])
        print(f"Dropped {before - len(df)} rows with invalid dates")

        # --- Coerce numerics ---
        for col in [SALES_COL, ORDERS_COL, TICKET_COL]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        before = len(df)
        df = df.dropna(subset=[SALES_COL, ORDERS_COL])
        print(f"Dropped {before - len(df)} rows with missing Sales/Orders")

        # --- Ticket Size: recompute where missing and orders > 0 ---
        missing_ticket = df[TICKET_COL].isna()
        nonzero_orders = df[ORDERS_COL] > 0

        recompute_mask = missing_ticket & nonzero_orders
        df.loc[recompute_mask, TICKET_COL] = (
            df.loc[recompute_mask, SALES_COL] / df.loc[recompute_mask, ORDERS_COL]
        )

        # For remaining NaNs (e.g., zero orders days), set to 0.0
        df[TICKET_COL] = df[TICKET_COL].fillna(0.0)

        # --- Remove obviously bad rows (negative values) ---
        before = len(df)
        df = df[
            (df[SALES_COL] >= 0)
            & (df[ORDERS_COL] >= 0)
            & (df[TICKET_COL] >= 0)
        ]
        print(f"Dropped {before - len(df)} rows with negative values")

        # IMPORTANT: we KEEP zero-sales/zero-orders rows here
        # so closed days remain visible for analysis.

        # Sort and reset index by date
        df = df.sort_values(by=DATE_COL, ascending=True)  # type: ignore[arg-type]
        df = df.reset_index(drop=True)
        df = cast(pd.DataFrame, df)

        return df

    @staticmethod
    def _iter_observations(df: pd.DataFrame) -> Iterable[DailyObservation]:
        """
        Convert a cleaned DataFrame row-by-row into DailyObservation objects.

        Assumes df has the types guaranteed by _read_all_raw().
        """
        for _, row in df.iterrows():
            # row[DATE_COL] is a Python date after .dt.date above
            obs_date = cast(date, row[DATE_COL])
            sales = float(row[SALES_COL])
            orders = int(row[ORDERS_COL])
            ticket = float(row[TICKET_COL])

            yield DailyObservation(
                date=obs_date,
                sales=sales,
                orders=orders,
                ticket_size=ticket,
            )

    def _to_daily_series(self, df: pd.DataFrame) -> DailySeries:
        observations = list(self._iter_observations(df))
        return DailySeries(store_id=self._config.store_id, observations=observations)

    # ------------------------------------------------------------------ #
    # IDataLoader implementation
    # ------------------------------------------------------------------ #

    def load_history(self, store_id: str) -> DailySeries:
        # For now we ignore the store_id parameter and use config.store_id.
        df = self._read_all_raw()
        return self._to_daily_series(df)

    def load_range(
        self,
        store_id: str,
        start: date,
        end: date,
    ) -> DailySeries:
        df = self._read_all_raw()
        mask = (df[DATE_COL] >= start) & (df[END_DATE_COL] <= end)
        return self._to_daily_series(df.loc[mask])

    # ------------------------------------------------------------------ #
    # Temporary debug API
    # ------------------------------------------------------------------ #

    def load_all_raw_dataframe(self) -> pd.DataFrame:
        """
        Temporary helper so existing scripts can still inspect the cleaned
        DataFrame directly. New code should prefer load_history / load_range.
        """
        return self._read_all_raw()
