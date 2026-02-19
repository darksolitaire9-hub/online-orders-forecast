# restaurant_forecast/domain/services.py
from math import sqrt
from statistics import mean, median

from restaurant_forecast.domain.models import (
    DailySeries,
    MonthlyForecast,
    MonthlyBacktestConfig,
    MonthlyBacktestResult,
)


def evaluate_month(
    actual_series: DailySeries,
    forecast: MonthlyForecast,
    config: MonthlyBacktestConfig,
) -> MonthlyBacktestResult:
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

        e_orders = df.predicted_orders - actual.orders
        e_sales = df.predicted_sales - actual.sales

        abs_err_orders.append(abs(e_orders))
        sq_err_orders.append(e_orders * e_orders)

        abs_err_sales.append(abs(e_sales))
        sq_err_sales.append(e_sales * e_sales)

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
