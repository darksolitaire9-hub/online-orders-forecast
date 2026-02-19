from pprint import pprint
from pathlib import Path

from restaurant_forecast.config import Config
from restaurant_forecast.application.use_cases import (
    LoadHistoryUseCase,
    LoadHistoryCommand,
)
from restaurant_forecast.infrastructure.csv_loader import CSVDataLoader, CSVConfig


def build_loader_from_config() -> CSVDataLoader:
    cfg = Config.from_yaml()

    csv_config = CSVConfig(
        primary_month_csv=Path(cfg.primary_month_csv),
        other_month_csvs=[Path(p) for p in cfg.other_month_csvs],
        store_id=cfg.store_id,
    )
    return CSVDataLoader(csv_config)


def main() -> None:
    loader = build_loader_from_config()
    use_case = LoadHistoryUseCase(loader)

    cmd = LoadHistoryCommand(store_id="cx")
    series = use_case.execute(cmd)

    print("--- DailySeries ---")
    print("store_id:", series.store_id)
    print("observations:", len(series.observations))
    print("first 3 observations:")
    for obs in list(series.observations)[:3]:
        pprint(obs)


if __name__ == "__main__":
    main()
