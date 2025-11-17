"""Synthetic trade provider for deterministic testing."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Sequence

from backend.data_provider import TradeDataProvider, TradeRecord


class SyntheticTradeProvider(TradeDataProvider):
    """Returns deterministic trade disclosures within the requested date window."""

    def get_trades(self, symbol: str, start_date: date, end_date: date) -> Sequence[TradeRecord]:
        trades = []
        current = start_date
        while current <= end_date:
            executed_at = datetime.combine(current, datetime.min.time())
            trades.append(
                TradeRecord(
                    symbol=symbol,
                    trader="Test Trader",
                    action="buy",
                    quantity=10.0,
                    price=100.0 + (current - start_date).days,
                    executed_at=executed_at,
                    source="synthetic",
                )
            )
            current += timedelta(days=1)
        return trades
