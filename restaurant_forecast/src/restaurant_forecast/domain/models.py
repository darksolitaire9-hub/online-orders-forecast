from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from math import sqrt
from statistics import mean, median


@dataclass(frozen=True)
class DailyObservation:
    """
    One day's demand signal for a single store.
    """

    date: date
    value: float  # daily online orders


@dataclass(frozen=True)
class DailySeries:
    """
    Time-ordered sequence of daily observations for one store.
    """

    store_id: str
    observations: Sequence[DailyObservation]


@dataclass(frozen=True)
class MonthlyBacktestConfig:
    """
    Configuration for a single month backtest.
    Example: train until 31 Oct, forecast Nov.
    """

    store_id: str
    train_end: date  # use data <= this date (e.g. 2024-10-31)
    forecast_year: int  # e.g. 2024
    forecast_month: int  # e.g. 11 for November


@dataclass(frozen=True)
class DailyForecast:
    """
    Forecast for one day.
    """

    date: date
    predicted: float


@dataclass(frozen=True)
class MonthlyForecast:
    """
    Forecasted daily values for a given month and store.
    """

    store_id: str
    year: int
    month: int
    forecasts: Sequence[DailyForecast]


@dataclass(frozen=True)
class MonthlyBacktestResult:
    """
    Evaluation of one month-ahead forecast.
    """
    config: MonthlyBacktestConfig
    forecast: MonthlyForecast
    mae: float          # mean absolute error
    rmse: float         # root mean squared error
    med_ae: float       # median absolute error


def evaluate_month(
    actual_series: DailySeries,
    forecast: MonthlyForecast,
    config: MonthlyBacktestConfig,
) -> MonthlyBacktestResult:
    """
    Compare forecasted daily values vs actuals for that month.
    Only days that exist in both actual and forecast are used.
    """
    actual_by_date = {obs.date: obs.value for obs in actual_series.observations}

    abs_errors: list[float] = []
    sq_errors: list[float] = []

    for df in forecast.forecasts:
        if df.date in actual_by_date:
            err = df.predicted - actual_by_date[df.date]
            abs_errors.append(abs(err))
            sq_errors.append(err * err)

    mae = mean(abs_errors)
    rmse = sqrt(mean(sq_errors))
    med_ae = median(abs_errors)

    return MonthlyBacktestResult(
        config=config,
        forecast=forecast,
        mae=mae,
        rmse=rmse,
        med_ae=med_ae,
    )
