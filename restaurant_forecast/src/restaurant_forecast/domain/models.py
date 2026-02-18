from dataclasses import dataclass
from datetime import date
from typing import Sequence


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
    train_end: date       # use data <= this date (e.g. 2024-10-31)
    forecast_year: int    # e.g. 2024
    forecast_month: int   # e.g. 11 for November


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

