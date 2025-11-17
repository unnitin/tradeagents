"""Deterministic synthetic provider for tests and offline runs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
import random
from typing import List

from backend.data_provider import MarketDataProvider, PriceCandle


@dataclass(frozen=True)
class SyntheticMarketDataProvider(MarketDataProvider):
    base_price: float = 100.0
    daily_volatility: float = 2.0

    @staticmethod
    def _seed_from_symbol(symbol: str) -> int:
        return sum(ord(char) for char in symbol.upper())

    def get_price_series(self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d") -> List[PriceCandle]:
        start_day = start_date.date()
        end_day = end_date.date()
        if start_day > end_day:
            raise ValueError("start_date must be on or before end_date")

        rng = random.Random(self._seed_from_symbol(symbol))
        current_day = start_day
        current_price = self.base_price + (self._seed_from_symbol(symbol) % 50)
        day_index = 0
        candles: List[PriceCandle] = []

        while current_day <= end_day:
            drift = math.sin(day_index / 6.0) * 0.5
            noise = rng.normalvariate(0, self.daily_volatility * 0.2)
            delta = drift + noise
            open_price = current_price
            close_price = max(1.0, current_price + delta)
            high = max(open_price, close_price) + abs(noise) * 0.5
            low = min(open_price, close_price) - abs(noise) * 0.5
            volume = int(1_000_000 + abs(delta) * 50_000 + rng.randint(-20_000, 20_000))

            candles.append(
                PriceCandle(
                    date=datetime.combine(current_day, datetime.min.time()),
                    open=round(open_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close_price, 2),
                    volume=max(100_000, volume),
                )
            )

            current_price = close_price
            current_day += timedelta(days=1)
            day_index += 1

        return candles
