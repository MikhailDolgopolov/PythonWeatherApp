from typing import Self

from Parsers.BaseParser import BaseParser


class SeekParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active = True
        self.home = True
        self._current_city="Лыткарино, Московская область"

    def find_city(self, name:str):
        self._current_city = name
