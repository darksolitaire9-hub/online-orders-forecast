from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from math import sqrt
from statistics import mean, median


# ========= DOMAIN MODEL (ENTITIES / VALUE OBJECTS) =========

@dataclass(frozen=True)
class DailyObservation:
    """
    One day's demand signal for a single store.
    """

    date: date
    sales: float        # daily revenue / value
    orders: int         # daily online orders (count)
    ticket_size: float  # average value per order for that day


@dataclass(frozen=True)
class DailySeries:
    """
    Time-ordered sequence of daily observations for one store.
    Pure data; no behavior.
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
    require_full_target: bool = True


@dataclass(frozen=True)
class DailyForecast:
    """
    Forecast for one day.
    """

    date: date
    predicted_orders: float
    predicted_sales: float


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
    Evaluation of one month-ahead forecast (orders + sales).
    Pure data; computed by a service.
    """

    config: MonthlyBacktestConfig
    forecast: MonthlyForecast

    # daily metrics
    mae_orders: float
    rmse_orders: float
    med_ae_orders: float

    mae_sales: float
    rmse_sales: float
    med_ae_sales: float

    n_days: int  # how many days used

    # monthly aggregate errors (forecasted - actual)
    monthly_orders_error: float
    monthly_sales_error: float


# ========= DOMAIN SERVICE (USE CASE) =========

def evaluate_month(
    actual_series: DailySeries,
    forecast: MonthlyForecast,
    config: MonthlyBacktestConfig,
) -> MonthlyBacktestResult:
    """
    Domain service: compare forecasted daily values vs actuals for that month.
    Only days that exist in both actual and forecast are used.

    Assumes the target month is a full month; the 'require_full_target' flag
    is carried in config and should be enforced by higher-level orchestration
    using monthly metadata.
    """
    actual_by_date = {obs.date: obs for obs in actual_series.observations}

    abs_err_orders: list[float] = []
    sq_err_orders: list[float] = []

    abs_err_sales: list[float] = []
    sq_err_sales: list[float] = []

    total_actual_orders = 0.0
    total_pred_orders = 0.0

    total_actual_sales = 0.0
    total_pred_sales = 0.0

    for df in forecast.forecasts:
        actual = actual_by_date.get(df.date)
        if actual is None:
            continue

        # per-day errors
        e_orders = df.predicted_orders - actual.orders
        e_sales = df.predicted_sales - actual.sales

        abs_err_orders.append(abs(e_orders))
        sq_err_orders.append(e_orders * e_orders)

        abs_err_sales.append(abs(e_sales))
        sq_err_sales.append(e_sales * e_sales)

        # monthly aggregates
        total_actual_orders += actual.orders
        total_pred_orders += df.predicted_orders

        total_actual_sales += actual.sales
        total_pred_sales += df.predicted_sales

    if not abs_err_orders:
        raise ValueError("No overlapping days between forecast and actuals.")

    mae_orders = mean(abs_err_orders)
    rmse_orders = sqrt(mean(sq_err_orders))
    med_ae_orders = median(abs_err_orders)

    mae_sales = mean(abs_err_sales)
    rmse_sales = sqrt(mean(sq_err_sales))
    med_ae_sales = median(abs_err_sales)

    monthly_orders_error = total_pred_orders - total_actual_orders
    monthly_sales_error = total_pred_sales - total_actual_sales

    return MonthlyBacktestResult(
        config=config,
        forecast=forecast,
        mae_orders=mae_orders,
        rmse_orders=rmse_orders,
        med_ae_orders=med_ae_orders,
        mae_sales=mae_sales,
        rmse_sales=rmse_sales,
        med_ae_sales=med_ae_sales,
        n_days=len(abs_err_orders),
        monthly_orders_error=monthly_orders_error,
        monthly_sales_error=monthly_sales_error,
    )
