import pandas as pd
from .base import Strategy

class ATRVolatilityFilter(Strategy):
    def __init__(self, atr_col: str = "atr_14", window: int = 50):
        super().__init__()
        self.atr_col = atr_col
        self.window = window

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # Acts as a filter: 1 if vol is high, else 0
        rolling_mean = df[self.atr_col].rolling(self.window).mean()
        return (df[self.atr_col] > rolling_mean).astype(int)
