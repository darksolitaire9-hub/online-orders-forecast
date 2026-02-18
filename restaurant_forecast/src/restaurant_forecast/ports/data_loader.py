from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from restaurant_forecast.domain.models import DailySeries


class DataLoader(ABC):
    """
    Port for loading historical daily data from any source (CSV, DB, API).
    """
    @abstractmethod
    def load_series(
        self,
        store_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> DailySeries:
        raise NotImplementedError
