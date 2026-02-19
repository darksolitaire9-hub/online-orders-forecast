# tests/test_config.py
from pathlib import Path

from restaurant_forecast.config import Config


def test_config_from_yaml_uses_expected_shape(tmp_path, monkeypatch):
    yaml_path = tmp_path / "config.local.yml"
    yaml_path.write_text(
        """
        store_id: cx
        opening_date: 2025-10-19
        forecast:
          first_forecast_month: 2025-11
        data:
          primary_month_csv: /tmp/primary.csv
          other_month_csvs:
            - /tmp/other1.csv
            - /tmp/other2.csv
        """.strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr("restaurant_forecast.config.CONFIG_PATH", yaml_path)

    cfg = Config.from_yaml()

    assert cfg.store_id == "cx"
    assert cfg.opening_date == "2025-10-19"
    assert cfg.first_forecast_month == "2025-10"
    assert cfg.primary_month_csv == Path("/tmp/primary.csv")
    assert cfg.other_month_csvs == [Path("/tmp/other1.csv"), Path("/tmp/other2.csv")]
    assert cfg.date_col == "date"
    assert cfg.sales_col == "sales"
    assert cfg.orders_col == "orders"
    assert cfg.ticket_size_col == "ticket_size"
