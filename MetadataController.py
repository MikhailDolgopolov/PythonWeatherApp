from datetime import timedelta, datetime
from pathlib import Path
from typing import Union

from Day import Day
from helpers import read_json, write_json


class MetadataController:

    def __init__(self, path: Path):
        self.metadata_file = path / "metadata.json"

    def update_with_now(self, date: datetime) -> None:
        metadata = read_json(self.metadata_file)
        min_date = datetime.today() - timedelta(days=1)
        key = date.strftime("%Y-%m-%d")
        new_meta = {k: v for k, v in metadata.items() if min_date < datetime.strptime(k, "%Y-%m-%d")}
        newstr = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        new_meta[key] = newstr
        write_json(new_meta, str(self.metadata_file))
        # print(f"Metadata updated: {key}:  {newstr}")

    def get_last_update(self, date: datetime) -> Union[datetime, None]:
        given: str = date.strftime("%Y-%m-%d")
        metadata = read_json(self.metadata_file)
        if given in metadata:
            return datetime.strptime(metadata[given], '%Y-%m-%dT%H:%M:%S')
        return None

    def update_is_due(self, day: Day) -> bool:
        last = self.get_last_update(day.date)
        if last is None:
            return True
        diff = datetime.now() - last
        threshold = timedelta(hours=2) if day.offset == 0 else timedelta(hours=3)

        return diff > threshold

    def update_is_overdue(self, day: Day) -> bool:
        last = self.get_last_update(day.date)
        if last is None:
            return True
        diff = datetime.now() - last
        threshold = timedelta(hours=4)

        return diff > threshold
