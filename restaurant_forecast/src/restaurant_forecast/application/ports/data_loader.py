from __future__ import annotations

from datetime import date
from typing import Protocol

from restaurant_forecast.domain.models import DailySeries


class IDataLoader(Protocol):
    """Port for loading cleaned daily history as DailySeries."""

    def load_history(self, store_id: str) -> DailySeries:
        """Load all available history for a store."""
        ...

    def load_range(
        self,
        store_id: str,
        start: date,
        end: date,
    ) -> DailySeries:
        """Load history within a date range for a store."""
        ...
