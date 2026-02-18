
"""

Use cases for running forecasts and backtests.

Wire up DataLoader and Forecaster ports here.

"""

from dataclasses import dataclass

from datetime import date



from restaurant_forecast.ports.data_loader import DataLoader

from restaurant_forecast.ports.forecaster import Forecaster





@dataclass

class BacktestConfig:

    store_id: str

    start_date: date

    end_date: date

    forecast_month: int

    forecast_year: int





def run_monthly_backtest(

    config: BacktestConfig,

    data_loader: DataLoader,

    forecaster: Forecaster,

):

    series = data_loader.load_series(

        store_id=config.store_id,

        start_date=config.start_date,

        end_date=config.end_date,

    )

    model = forecaster.fit(series)

    forecasts = forecaster.forecast_month(

        model=model,

        year=config.forecast_year,

        month=config.forecast_month,

    )

    return forecasts

