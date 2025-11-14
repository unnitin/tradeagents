import pandas as pd
from .base import Strategy

class MACDCross(Strategy):
    """
    MACD crossover strategy.
    Generates signals when MACD line crosses above/below signal line.
    """
    def __init__(self, macd_col: str = "macd", signal_col: str = "macd_signal"):
        super().__init__()
        self.macd_col = macd_col
        self.signal_col = signal_col

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MACD crossovers.
        
        Returns:
            1 when MACD crosses ABOVE signal line (bullish)
            -1 when MACD crosses BELOW signal line (bearish)  
            0 otherwise (no crossover)
        """
        signal = pd.Series(0, index=df.index)
        
        macd = df[self.macd_col]
        macd_signal = df[self.signal_col]
        
        # Detect crossovers by comparing current vs previous relationships
        # Bullish crossover: MACD was below signal, now above signal
        prev_macd_below = (macd.shift(1) <= macd_signal.shift(1))
        curr_macd_above = (macd > macd_signal)
        bullish_crossover = prev_macd_below & curr_macd_above
        
        # Bearish crossover: MACD was above signal, now below signal
        prev_macd_above = (macd.shift(1) >= macd_signal.shift(1))
        curr_macd_below = (macd < macd_signal)
        bearish_crossover = prev_macd_above & curr_macd_below
        
        signal[bullish_crossover] = 1
        signal[bearish_crossover] = -1
        
        return signal
