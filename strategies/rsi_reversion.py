import pandas as pd
from strategies.base import Strategy

class RSIReversion(Strategy):
    def __init__(self, rsi_col: str = "rsi_14", low_thresh: float = 30, high_thresh: float = 70):
        self.rsi_col = rsi_col
        self.low = low_thresh
        self.high = high_thresh

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signal = pd.Series(0, index=df.index)
        signal[df[self.rsi_col] < self.low] = 1
        signal[df[self.rsi_col] > self.high] = -1
        return signal
