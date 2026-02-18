from __future__ import annotations

from pathlib import Path

import pandas as pd

from restaurant_forecast.config import Config
from restaurant_forecast.ports.data_loader import DataLoader


class CSVDataLoader(DataLoader):
    """Load daily orders from a CSV file."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()

    def load(self) -> pd.DataFrame:
        path: Path = self.config.data_path
        df = pd.read_csv(path)

        # Ensure proper dtypes and ordering
        df[self.config.date_col] = pd.to_datetime(df[self.config.date_col])
        df = df.sort_values(self.config.date_col).reset_index(drop=True)

        return df[[self.config.date_col, self.config.orders_col]]
