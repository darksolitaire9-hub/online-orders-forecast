from __future__ import annotations

from dataclasses import dataclass
from datetime import date as DateType
from pathlib import Path
from typing import Iterable, List, cast

import pandas as pd

from restaurant_forecast.application.ports.data_loader import IDataLoader
from restaurant_forecast.domain.models import DailyObservation, DailySeries
from restaurant_forecast.infrastructure.cleaning import (
    DATE_COL,
    END_DATE_COL,
    SALES_COL,
    ORDERS_COL,
    TICKET_COL,
    clean_daily,
)
from restaurant_forecast.infrastructure.schema import (
    CoreSchemaDataFrame,
    select_core_columns,
)


@dataclass
class CSVConfig:
    """
    Configuration for CSVDataLoader.

    Attributes:
      primary_month_csv: Path to the primary month CSV file
      other_month_csvs: Paths to additional month CSV files
      store_id: Identifier for the store (used in DailySeries)
    """

    primary_month_csv: Path
    other_month_csvs: List[Path]
    store_id: str


class CSVDataLoader(IDataLoader):
    """
    Infrastructure adapter that:
      - reads multiple monthly CSV files,
      - cleans/normalizes them using clean_daily,
      - normalizes to the core schema via select_core_columns,
      - converts the result into domain DailySeries.

    It also exposes load_all_raw_dataframe() for debugging.
    """

    def __init__(self, config: CSVConfig) -> None:
        self._config = config

    # ---------- raw loading ---------- #

    def _load_raw_frames(self) -> list[pd.DataFrame]:
        """
        Read all configured CSV files into separate raw DataFrames.
        No cleaning is performed here.
        """
        paths: list[Path] = [
            self._config.primary_month_csv,
            *self._config.other_month_csvs,
        ]
        frames: list[pd.DataFrame] = []

        for path in paths:
            print(f"[csv_loader] reading: {path}")
            frames.append(pd.read_csv(path))

        return frames

    def _read_all_raw(self) -> pd.DataFrame:
        """
        Read all CSVs and return a single cleaned DataFrame.

        This is the internal boundary where:
          - I/O (CSV reading) and
          - cleaning (clean_daily)
        are composed.
        """
        frames = self._load_raw_frames()
        raw_df = pd.concat(frames, ignore_index=True)
        cleaned = clean_daily(raw_df)
        return cleaned

    def _read_core(self) -> CoreSchemaDataFrame:
        """
        Read, clean, and normalize CSV data into the core schema
        (Start Date, Sales, Orders, Ticket Size).
        """
        cleaned = self._read_all_raw()
        return select_core_columns(cleaned)

    # ---------- DataFrame -> domain ---------- #

    @staticmethod
    def _iter_observations(df: CoreSchemaDataFrame) -> Iterable[DailyObservation]:
        """
        Convert a core-schema DataFrame row-by-row into DailyObservation objects.

        Precondition:
          - df has already been processed by clean_daily and select_core_columns,
            so column types and invariants described there hold.
        """
        for _, row in df.iterrows():
            obs_date = cast(DateType, row[DATE_COL])
            sales = float(row[SALES_COL])
            orders = int(row[ORDERS_COL])
            ticket = float(row[TICKET_COL])

            yield DailyObservation(
                date=obs_date,
                sales=sales,
                orders=orders,
                ticket_size=ticket,
            )

    def _to_daily_series(self, df: CoreSchemaDataFrame) -> DailySeries:
        observations = list(self._iter_observations(df))
        return DailySeries(store_id=self._config.store_id, observations=observations)

    # ---------- IDataLoader implementation ---------- #

    def load_history(self, store_id: str) -> DailySeries:
        """
        Load all available history for the configured store as a DailySeries.

        The store_id argument is currently ignored; CSVConfig.store_id is used
        as the identifier in the resulting DailySeries.
        """
        df_core = self._read_core()
        return self._to_daily_series(df_core)

    def load_range(
        self,
        store_id: str,
        start: DateType,
        end: DateType,
    ) -> DailySeries:
        """
        Load history for the configured store restricted to [start, end].

        Dates are inclusive and are compared at date precision (no time-of-day).
        """
        df_core = self._read_core()
        mask = (df_core[DATE_COL] >= start) & (df_core[DATE_COL] <= end)
        sliced = df_core.loc[mask]
        return self._to_daily_series(sliced)

    # ---------- debug API ---------- #

    def load_all_raw_dataframe(self) -> pd.DataFrame:
        """
        Return the cleaned DataFrame for debugging and exploration.

        New code should prefer load_history / load_range, which operate
        in terms of domain models.
        """
        return self._read_all_raw()
