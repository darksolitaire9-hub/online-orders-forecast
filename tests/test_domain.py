from datetime import date

from restaurant_forecast.domain.models import (
    DailyObservation,
    DailySeries,
    MonthlyBacktestConfig,
    DailyForecast,
    MonthlyForecast,
)


def test_daily_observation_basic():
    obs = DailyObservation(
        date=date(2025, 10, 19),
        sales=100.0,
        orders=10,
        ticket_size=10.0,
    )

    assert obs.date == date(2025, 10, 19)
    assert obs.sales == 100.0
    assert obs.orders == 10
    assert obs.ticket_size == 10.0


def test_daily_series_basic():
    obs = [
        DailyObservation(
            date=date(2025, 10, 19),
            sales=100.0,
            orders=10,
            ticket_size=10.0,
        ),
        DailyObservation(
            date=date(2025, 10, 20),
            sales=120.0,
            orders=12,
            ticket_size=10.0,
        ),
    ]

    series = DailySeries(store_id="cx", observations=obs)

    assert series.store_id == "cx"
    assert len(series.observations) == 2

    first = series.observations[0]
    assert first.date == date(2025, 10, 19)
    assert first.sales == 100.0
    assert first.orders == 10
    assert first.ticket_size == 10.0

    second = series.observations[1]
    assert second.date == date(2025, 10, 20)
    assert second.sales == 120.0
    assert second.orders == 12
    assert second.ticket_size == 10.0


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
    assert cfg.require_full_target is True


def test_daily_forecast_basic():
    f = DailyForecast(
        date=date(2025, 11, 1),
        predicted_orders=15.5,
        predicted_sales=155.0,
    )

    assert f.date == date(2025, 11, 1)
    assert f.predicted_orders == 15.5
    assert f.predicted_sales == 155.0


def test_monthly_forecast_basic():
    daily = [
        DailyForecast(
            date=date(2025, 11, 1),
            predicted_orders=15.0,
            predicted_sales=150.0,
        ),
        DailyForecast(
            date=date(2025, 11, 2),
            predicted_orders=16.0,
            predicted_sales=160.0,
        ),
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

    first = mf.forecasts[0]
    assert first.date == date(2025, 11, 1)
    assert first.predicted_orders == 15.0
    assert first.predicted_sales == 150.0

    second = mf.forecasts[1]
    assert second.date == date(2025, 11, 2)
    assert second.predicted_orders == 16.0
    assert second.predicted_sales == 160.0
