from datetime import datetime
from pathlib import Path

import pandas as pd


class BaseParser:
    def __init__(self, name):

        self.name = name

        self.forecast_path = Path(f"forecast/{name}").resolve()
        self.forecast_path.mkdir(parents=True, exist_ok=True)

    def _parse_weather(self, date: datetime, path: str) -> pd.DataFrame:
        raise NotImplementedError("Subclasses should implement this method")

    def get_weather(self, date: datetime) -> pd.DataFrame:
        raise NotImplementedError("Subclasses should implement this method")

    def get_last_forecast_update(self, date: datetime) -> datetime:
        raise NotImplementedError("Subclasses should implement this method")

    @property
    def empty_frame(self) -> pd.DataFrame:
        return pd.DataFrame({}, columns=["time", "temperature", "precipitation",
                                         "wind-speed"]).astype(float)

    def clean_files(self) -> int:
        return 0
