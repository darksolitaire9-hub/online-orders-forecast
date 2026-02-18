from datetime import date

from restaurant_forecast.domain.models import (
    DailyObservation,
    DailySeries,
    MonthlyBacktestConfig,
    DailyForecast,
    MonthlyForecast,
)


def test_daily_observation_basic():
    obs = DailyObservation(date=date(2025, 10, 19), value=10.0)

    assert obs.date == date(2025, 10, 19)
    assert obs.value == 10.0


def test_daily_series_basic():
    obs = [
        DailyObservation(date=date(2025, 10, 19), value=10.0),
        DailyObservation(date=date(2025, 10, 20), value=12.0),
    ]

    series = DailySeries(store_id="cx", observations=obs)

    assert series.store_id == "cx"
    assert len(series.observations) == 2
    assert series.observations[0].date == date(2025, 10, 19)
    assert series.observations[0].value == 10.0
    assert series.observations[1].date == date(2025, 10, 20)
    assert series.observations[1].value == 12.0


def test_monthly_backtest_config_basic():
    cfg = MonthlyBacktestConfig(
        store_id="cx",
        train_end=date(2025, 10, 31),
        forecast_year=2025,
        forecast_month=11,
    )

    assert cfg.store_id == "cx"
    assert cfg.train_end == date(2025, 10, 31)
    assert cfg.forecast_year == 2025
    assert cfg.forecast_month == 11


def test_daily_forecast_basic():
    f = DailyForecast(date=date(2025, 11, 1), predicted=15.5)

    assert f.date == date(2025, 11, 1)
    assert f.predicted == 15.5


def test_monthly_forecast_basic():
    daily = [
        DailyForecast(date=date(2025, 11, 1), predicted=15.0),
        DailyForecast(date=date(2025, 11, 2), predicted=16.0),
    ]

    mf = MonthlyForecast(
        store_id="cx",
        year=2025,
        month=11,
        forecasts=daily,
    )

    assert mf.store_id == "cx"
    assert mf.year == 2025
    assert mf.month == 11
    assert len(mf.forecasts) == 2
    assert mf.forecasts[0].date == date(2025, 11, 1)
    assert mf.forecasts[0].predicted == 15.0
    assert mf.forecasts[1].date == date(2025, 11, 2)
    assert mf.forecasts[1].predicted == 16.0
