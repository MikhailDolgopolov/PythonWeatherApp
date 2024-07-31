from datetime import timedelta, datetime
from typing import Union

from Day import Day
from helpers import read_json, write_json

metadata_filename = "metadata.json"


class MetadataController:
    @classmethod
    def update_with_now(cls, day: Day) -> None:
        metadata = read_json(metadata_filename)
        min_date = datetime.today() - timedelta(days=1)
        max_date = datetime.today() + timedelta(days=1)
        new_meta = {k: v for k, v in metadata.items() if min_date < datetime.strptime(k, "%Y%m%d") < max_date}
        newstr = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        new_meta[day.short_date] = newstr
        write_json(new_meta, metadata_filename)
        print(f"Metadata updated: {day.short_date}:  {newstr}")

    @classmethod
    def get_last_update(cls, day: Day) -> Union[datetime, None]:
        given: str = day.date.strftime("%Y%m%d")
        metadata = read_json(metadata_filename)
        if given in metadata:
            return datetime.strptime(metadata[given], '%Y-%m-%dT%H:%M:%S')
        return None

    @classmethod
    def update_is_due(cls, day: Day) -> bool:
        last = cls.get_last_update(day)
        if last is None:
            return True
        diff = datetime.now() - last
        threshold = timedelta(hours=2) if day.offset == 0 else timedelta(hours=3)

        return diff > threshold

    @classmethod
    def update_is_overdue(cls, day: Day) -> bool:
        last = cls.get_last_update(day)
        if last is None:
            return True
        diff = datetime.now() - last
        threshold = timedelta(hours=4)

        return diff > threshold

