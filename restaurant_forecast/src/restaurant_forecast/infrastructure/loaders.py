from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List

import pandas as pd
import yaml
from pandas import DataFrame

from restaurant_forecast.domain.models import DailyObservation, DailySeries

CONFIG_PATH = Path("config.local.yml")


@dataclass(frozen=True)
class LocalConfig:
    """
    Configuration loaded from config.local.yml.

    Fields
    ------
    store_id:
        Logical identifier for this store (e.g. "cx").
    opening_date:
        First date the store should be considered "open" for forecasting.
        If None, all rows from the CSVs are used.
    primary_month_csv:
        Path to the CSV for the primary month (typically the month before
        the first forecast month, e.g. October if first_forecast_month is November).
    other_month_csvs:
        Paths to additional monthly CSVs (subsequent months).
    first_forecast_month:
        First month we intend to forecast, as "YYYY-MM" (e.g. "2025-11").
    """

    store_id: str
    opening_date: date | None  # None means "unsure"
    primary_month_csv: Path
    other_month_csvs: List[Path]
    first_forecast_month: str  # "YYYY-MM"


def load_local_config(path: Path = CONFIG_PATH) -> LocalConfig:
    """
    Load LocalConfig from a YAML file (config.local.yml).

    The expected structure is what your init script writes:

    store_id: "cx"
    opening_date: "2025-10-19"  # or "unsure"
    forecast:
      first_forecast_month: "2025-11"
    data:
      primary_month_csv: "/path/to/oct.csv"
      other_month_csvs:
        - "/path/to/nov.csv"
        - "/path/to/dec.csv"
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    opening_raw = raw.get("opening_date", "unsure")
    if opening_raw == "unsure":
        opening_date: date | None = None
    else:
        opening_date = datetime.strptime(opening_raw, "%Y-%m-%d").date()

    data = raw["data"]

    return LocalConfig(
        store_id=raw["store_id"],
        opening_date=opening_date,
        primary_month_csv=Path(data["primary_month_csv"]),
        other_month_csvs=[Path(p) for p in data["other_month_csvs"]],
        first_forecast_month=raw["forecast"]["first_forecast_month"],
    )


def _load_one_csv(path: Path) -> DataFrame:
    """
    Load one monthly CSV into a normalized DataFrame.

    Returns
    -------
    DataFrame
        With exactly two columns:
          - "date":  python datetime.date
          - "orders": float (daily number of orders)

    Assumptions
    -----------
    - CSV has a column "Start Date" with a full timestamp string.
    - CSV has a column "Orders" with the daily order count.
      (If you decide to forecast revenue instead, this is where we would
       switch to the "Sales" column.)
    """
    df = pd.read_csv(path)

    # Normalize the date column to datetime.date
    df["Start Date"] = pd.to_datetime(df["Start Date"]).dt.date
    df = df.rename(columns={"Start Date": "date", "Orders": "orders"})

    # Use .loc with a list to ensure the result is typed as DataFrame
    return df.loc[:, ["date", "orders"]]


def load_daily_series_from_config(
    config_path: Path = CONFIG_PATH,
) -> tuple[DailySeries, LocalConfig]:
    """
    Build a DailySeries for a single store using config.local.yml and CSV files.

    High-level behavior
    -------------------
    - Reads config.local.yml to obtain:
        * store_id
        * opening_date (first day the store is considered active)
        * primary_month_csv (e.g. October)
        * other_month_csvs (e.g. November, December, ...)
    - Loads and concatenates all CSVs into one time-ordered DataFrame.
    - If opening_date is provided, drops all rows with date < opening_date.
    - Converts each remaining row into a DailyObservation:
        date  -> observation.date
        Orders -> observation.value
    - Wraps them in a DailySeries for that store.

    Why this matches the “partial month” design
    -------------------------------------------
    - If the store opened mid-month (e.g. 2025-10-19), all earlier rows
      (including zeros) are ignored, so the DailySeries starts at 2025-10-19.
    - Later code (e.g. evaluate_month) works with whatever dates exist in
      DailySeries.observations, so partial vs full months are handled
      automatically without changing domain logic.

    Returns
    -------
    (DailySeries, LocalConfig)
        DailySeries: cleaned, filtered daily orders for this store.
        LocalConfig: the parsed configuration (useful for first_forecast_month).
    """
    cfg = load_local_config(config_path)

    # 1) Load all configured CSVs
    dfs: list[DataFrame] = []
    dfs.append(_load_one_csv(cfg.primary_month_csv))
    for p in cfg.other_month_csvs:
        dfs.append(_load_one_csv(p))

    # 2) Concatenate and sort by date
    df = pd.concat(dfs, ignore_index=True).sort_values("date")

    # 3) Filter by opening_date if provided
    if cfg.opening_date is not None:
        df = df[df["date"] >= cfg.opening_date]

    # 4) Convert to list[DailyObservation]
    # df has columns ["date", "orders"] in that order
    observations: list[DailyObservation] = [
        DailyObservation(date=row[0], value=float(row[1]))
        for row in df.itertuples(index=False, name=None)
    ]

    series = DailySeries(store_id=cfg.store_id, observations=observations)
    return series, cfg
