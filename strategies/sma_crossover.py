import pandas as pd
from strategies.base import Strategy

class SMACrossover(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50):
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signal = pd.Series(0, index=df.index)
        condition_buy = df[f"sma_{self.fast}"] > df[f"sma_{self.slow}"]
        condition_sell = df[f"sma_{self_fast}"] < df[f"sma_{self_slow}"]
        signal[condition_buy] = 1
        signal[condition_sell] = -1
        return signal
