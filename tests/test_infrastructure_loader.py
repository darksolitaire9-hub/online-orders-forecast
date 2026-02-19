from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from restaurant_forecast.infrastructure.loaders import load_daily_series_from_config


def test_load_daily_series_from_config_respects_opening_date(tmp_path: Path):
    # --- 1) Fake CSVs ---
    primary_csv = tmp_path / "oct.csv"
    other_csv = tmp_path / "nov.csv"

    pd.DataFrame(
        {
            "Start Date": ["2025-10-18", "2025-10-19"],
            "Sales": [0.0, 12.0],
            "Orders": [0, 1],
            "Ticket Size": [0.0, 12.0],
            "Currency Code": ["EUR", "EUR"],
        }
    ).to_csv(primary_csv, index=False)

    pd.DataFrame(
        {
            "Start Date": ["2025-11-01", "2025-11-02"],
            "Sales": [10.0, 20.0],
            "Orders": [1, 2],
            "Ticket Size": [10.0, 10.0],
            "Currency Code": ["EUR", "EUR"],
        }
    ).to_csv(other_csv, index=False)

    # --- 2) Fake config.local.yml pointing to those CSVs ---
    cfg_path = tmp_path / "config.local.yml"
    yaml.safe_dump(
        {
            "store_id": "cx",
            "opening_date": "2025-10-19",
            "forecast": {"first_forecast_month": "2025-11"},
            "data": {
                "primary_month_csv": str(primary_csv),
                "other_month_csvs": [str(other_csv)],
            },
        },
        cfg_path.open("w", encoding="utf-8"),
        sort_keys=False,
    )

    # --- 3) Call loader ---
    series, cfg = load_daily_series_from_config(config_path=cfg_path)

    # --- 4) Assertions ---
    assert cfg.store_id == "cx"
    assert cfg.opening_date == date(2025, 10, 19)
    assert cfg.first_forecast_month == "2025-11"

    # Expect 3 observations: 2025-10-19, 2025-11-01, 2025-11-02
    assert series.store_id == "cx"
    assert len(series.observations) == 3

    assert series.observations[0].date == date(2025, 10, 19)
    assert series.observations[0].value == 1.0

    assert series.observations[1].date == date(2025, 11, 1)
    assert series.observations[1].value == 1.0

    assert series.observations[2].date == date(2025, 11, 2)
    assert series.observations[2].value == 2.0
