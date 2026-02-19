# restaurant_forecast/config.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CONFIG_PATH = Path("config.local.yml")


@dataclass
class Config:
    """
    Runtime configuration loaded from config.local.yml.

    YAML shape:

    store_id: str
    opening_date: str | "unsure"
    forecast:
      first_forecast_month: "YYYY-MM"
    data_source: str
    data:
      primary_month_csv: str
      other_month_csvs: list[str]
      primary_month_full: bool
      ignore_primary_if_partial_unknown: bool
    """

    store_id: str
    opening_date: str
    first_forecast_month: str
    data_source: str

    primary_month_csv: Path
    other_month_csvs: list[Path]
    primary_month_full: bool
    ignore_primary_if_partial_unknown: bool

    @classmethod
    def from_yaml(cls, path: Path = CONFIG_PATH) -> "Config":
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run the init script to create config.local.yml."
            )

        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))

        try:
            store_id = raw["store_id"]
            opening_date = raw["opening_date"]
            first_forecast_month = raw["forecast"]["first_forecast_month"]
            data_source = raw.get("data_source", "unknown")

            data = raw["data"]
            primary_month_csv = data["primary_month_csv"]
            other_month_csvs = data["other_month_csvs"]
            primary_month_full = data["primary_month_full"]
            ignore_primary_if_partial_unknown = data["ignore_primary_if_partial_unknown"]
        except KeyError as exc:
            raise KeyError(f"Missing key in config.local.yml: {exc}") from exc

        return cls(
            store_id=store_id,
            opening_date=opening_date,
            first_forecast_month=first_forecast_month,
            data_source=data_source,
            primary_month_csv=Path(primary_month_csv),
            other_month_csvs=[Path(p) for p in other_month_csvs],
            primary_month_full=bool(primary_month_full),
            ignore_primary_if_partial_unknown=bool(
                ignore_primary_if_partial_unknown
            ),
        )
