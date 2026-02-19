# scripts/debug_loader.py
from pprint import pprint
from pathlib import Path

from restaurant_forecast.config import Config
from restaurant_forecast.infrastructure.csv_loader import CSVDataLoader, CSVConfig

cfg = Config.from_yaml()
print("--- Config ---")
pprint(cfg.__dict__)

csv_config = CSVConfig(
    primary_month_csv=Path(cfg.primary_month_csv),
    other_month_csvs=[Path(p) for p in cfg.other_month_csvs],
    store_id=cfg.store_id,
    # you can add more fields later if needed:
    # primary_month_full=cfg.primary_month_full,
    # ignore_primary_if_partial_unknown=cfg.ignore_primary_if_partial_unknown,
    # data_source=cfg.data_source,
    # opening_date=cfg.opening_date,
)

loader = CSVDataLoader(csv_config)

df = loader.load_all_raw_dataframe()
print("\n--- Loaded DataFrame ---")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head())
print("tail below")
print(df.tail())
