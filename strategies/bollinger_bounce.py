import pandas as pd
from .base import Strategy

class BollingerBounce(Strategy):
    def __init__(self, bb_window: int = 20):
        self.lower = f"bb_lower_{bb_window}"
        self.upper = f"bb_upper_{bb_window}"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signal = pd.Series(0, index=df.index)
        signal[df["close"] < df[self.lower]] = 1
        signal[df["close"] > df[self.upper]] = -1
        return signal
