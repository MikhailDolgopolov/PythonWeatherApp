from typing import Self

from Parsers.BaseParser import BaseParser


class SeekParser(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.home=True

    def find(self, name:str) -> Self:
        raise NotImplementedError("It's up to child classes!")