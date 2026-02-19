from __future__ import annotations

from dataclasses import dataclass

from restaurant_forecast.application.ports.data_loader import IDataLoader
from restaurant_forecast.domain.models import DailySeries


@dataclass
class LoadHistoryCommand:
    store_id: str


class LoadHistoryUseCase:
    """Simple application use case: load cleaned history for a store."""

    def __init__(self, loader: IDataLoader) -> None:
        self._loader = loader

    def execute(self, cmd: LoadHistoryCommand) -> DailySeries:
        # Application talks to the port, not to CSV directly.
        return self._loader.load_history(cmd.store_id)
