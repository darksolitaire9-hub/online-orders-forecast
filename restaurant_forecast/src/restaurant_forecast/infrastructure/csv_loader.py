from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from restaurant_forecast.application.ports.data_loader import IDataLoader
from restaurant_forecast.domain.models import DailyObservation, DailySeries


@dataclass
class CSVConfig:
    primary_month_csv: Path
    other_month_csvs: list[Path]
    store_id: str
    # keep flags here if you want:
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
    """

    def __init__(self, config: CSVConfig) -> None:
        self._config = config

    # --- INTERNAL: pandas/raw helpers -------------------------------------

    def _read_all_raw(self) -> pd.DataFrame:
        paths = [self._config.primary_month_csv, *self._config.other_month_csvs]
        frames: list[pd.DataFrame] = []

        for path in paths:
            print(f"Reading: {path}")
            frames.append(pd.read_csv(path))

        df = pd.concat(frames, ignore_index=True)

        # Your columns (from debug output):
        # ['Period', 'Start Date', 'End Date', 'Time Increment',
        #  'Sales', 'Orders', 'Ticket Size', 'Currency Code']
        df["Start Date"] = pd.to_datetime(df["Start Date"])
        df["End Date"] = pd.to_datetime(df["End Date"])
        df = df.sort_values("Start Date")
        return df

    def _to_daily_series(self, df: pd.DataFrame) -> DailySeries:
        observations: list[DailyObservation] = []

        for _, row in df.iterrows():
            observations.append(
                DailyObservation(
                    date=row["Start Date"].date(),
                    sales=float(row["Sales"]),
                    orders=int(row["Orders"]),
                    ticket_size=float(row["Ticket Size"]),
                )
            )

        return DailySeries(store_id=self._config.store_id, observations=observations)

    # --- PORT IMPLEMENTATION (IDataLoader) ---------------------------------

    def load_history(self, store_id: str) -> DailySeries:
        # for now we ignore the store_id parameter and just use config.store_id
        df = self._read_all_raw()
        return self._to_daily_series(df)

    def load_range(
        self,
        store_id: str,
        start: date,
        end: date,
    ) -> DailySeries:
        df = self._read_all_raw()
        mask = (df["Start Date"] >= pd.Timestamp(start)) & (
            df["End Date"] <= pd.Timestamp(end)
        )
        return self._to_daily_series(df.loc[mask])

    # --- TEMP: keep old DataFrame-based API for debug scripts --------------

    def load_all_raw_dataframe(self) -> pd.DataFrame:
        """
        Temporary helper so existing scripts can still print the DataFrame.

        Replace old calls to `load_all()` with `load_all_raw_dataframe()`.
        """
        return self._read_all_raw()
