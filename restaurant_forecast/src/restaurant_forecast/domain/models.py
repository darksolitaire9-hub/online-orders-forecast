# domain/models.py
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class DailyObservation:
    date: date
    sales: float
    orders: int
    ticket_size: float

@dataclass(frozen=True)
class DailySeries:
    store_id: str
    observations: Sequence[DailyObservation]

@dataclass(frozen=True)
class MonthlyBacktestConfig:
    store_id: str
    train_end: date
    forecast_year: int
    forecast_month: int
    require_full_target: bool = True

@dataclass(frozen=True)
class DailyForecast:
    date: date
    predicted_orders: float
    predicted_sales: float

@dataclass(frozen=True)
class MonthlyForecast:
    store_id: str
    year: int
    month: int
    forecasts: Sequence[DailyForecast]

@dataclass(frozen=True)
class MonthlyBacktestResult:
    config: MonthlyBacktestConfig
    forecast: MonthlyForecast

    mae_orders: float
    rmse_orders: float
    med_ae_orders: float

    mae_sales: float
    rmse_sales: float
    med_ae_sales: float

    n_days: int

    monthly_orders_error: float
    monthly_sales_error: float
