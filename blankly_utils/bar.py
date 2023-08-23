from typing import Dict
from pydantic import BaseModel
import pandas as pd


class Bar(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_dict(cls, d):
        return cls(
            time=d["time"],
            open=d["open"],
            high=d["high"],
            low=d["low"],
            close=d["close"],
            volume=d["volume"],
        )


class Bars(BaseModel):
    time: int
    symbols: Dict[str, Bar]
