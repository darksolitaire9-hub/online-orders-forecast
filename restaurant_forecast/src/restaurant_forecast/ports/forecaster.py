from abc import ABC, abstractmethod

from restaurant_forecast.domain.models import DailySeries, MonthlyForecast, MonthlyBacktestConfig


class Forecaster(ABC):
    """
    Port for any forecasting engine (simple baseline now, ML later).
    """
    @abstractmethod
    def fit(self, series: DailySeries):
        """
        Fit a model on historical daily data.
        Returns a model object (type is up to the implementation).
        """
        raise NotImplementedError

    @abstractmethod
    def forecast_month(
        self,
        model,
        config: MonthlyBacktestConfig,
    ) -> MonthlyForecast:
        """
        Forecast all days of config.forecast_month / config.forecast_year.
        """
        raise NotImplementedError
