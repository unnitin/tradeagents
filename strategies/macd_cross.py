import pandas as pd
from strategies.base import Strategy

class MACDCross(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signal = pd.Series(0, index=df.index)
        signal[df["macd"] > df["macd_signal"]] = 1
        signal[df["macd"] < df["macd_signal"]] = -1
        return signal
